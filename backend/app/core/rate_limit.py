"""
API Rate Limiting, Abuse Prevention, and Quota Controls (Milestone 3.1).

Provides in-process, asynchronous rate limiting and abuse controls for OAuth
research endpoints to protect backend resources and external quotas at zero cost.

Architectural Note on Worker Scope:
This rate limiter implementation is process-local (in-memory). For single-worker
processes, standard development, and local agent deployments, it provides zero-cost,
sub-millisecond rate enforcement without external infrastructure. In multi-worker
or distributed cluster deployments (e.g. multi-process Gunicorn/Uvicorn), rate limits
are enforced per-worker process unless backed by an external distributed store
(such as Redis).
"""
import time
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from fastapi import Request

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_client_ip(request: Request, trusted_proxies: Optional[List[str]] = None) -> str:
    """
    Safely resolves the client IP address without trusting arbitrary, spoofable
    forwarded headers by default.

    Only if the direct connection originates from an explicitly configured trusted
    reverse proxy will the 'X-Forwarded-For' header be consulted.
    """
    direct_ip = request.client.host if request.client else "127.0.0.1"

    proxies = trusted_proxies or settings.TRUSTED_PROXY_IPS
    if proxies and direct_ip in proxies:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # First non-empty client IP in the chain
            candidates = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
            if candidates:
                return candidates[0]

    return direct_ip


class ResearchRateLimiter:
    """
    In-memory, asyncio-safe sliding-window rate limiter for research endpoints.
    Enforces per-minute, per-day (per IP), and global daily caps.
    """

    def __init__(
        self,
        per_minute_per_ip: Optional[int] = None,
        per_day_per_ip: Optional[int] = None,
        global_per_day: Optional[int] = None,
    ):
        self.per_minute_per_ip = per_minute_per_ip or settings.RATE_LIMIT_PER_MINUTE_PER_IP
        self.per_day_per_ip = per_day_per_ip or settings.RATE_LIMIT_PER_DAY_PER_IP
        self.global_per_day = global_per_day or settings.RATE_LIMIT_GLOBAL_PER_DAY

        self._ip_minute: Dict[str, List[float]] = {}
        self._ip_day: Dict[str, List[float]] = {}
        self._global_day: List[float] = []
        self._lock = asyncio.Lock()

    def _prune(self, timestamps: List[float], cutoff: float) -> List[float]:
        """Removes timestamps older than the cutoff threshold."""
        return [t for t in timestamps if t > cutoff]

    async def acquire(self, client_ip: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Attempts to acquire a rate limit token for the given client IP.

        Returns:
            Tuple[bool, Optional[int], Optional[str]]:
                - allowed: True if request is permitted, False if limit exceeded.
                - retry_after: Recommended integer seconds to wait before retrying.
                - reason: Descriptive error message explaining which limit was hit.
        """
        async with self._lock:
            now = time.time()
            one_min_ago = now - 60.0
            one_day_ago = now - 86400.0

            # 1. Global daily cap check
            self._global_day = self._prune(self._global_day, one_day_ago)
            if len(self._global_day) >= self.global_per_day:
                retry_after = max(1, int(86400.0 - (now - self._global_day[0])))
                logger.warning("Global daily research limit (%d/day) reached", self.global_per_day)
                return False, retry_after, "Global daily research request capacity exceeded. Please try again tomorrow."

            # 2. Per-IP minute cap check (default 5/min)
            ip_min = self._prune(self._ip_minute.get(client_ip, []), one_min_ago)
            self._ip_minute[client_ip] = ip_min
            if len(ip_min) >= self.per_minute_per_ip:
                retry_after = max(1, int(60.0 - (now - ip_min[0])))
                logger.warning("Rate limit exceeded for IP %s (5/minute limit)", client_ip)
                return False, retry_after, f"Too many research requests. Limit is {self.per_minute_per_ip} per minute."

            # 3. Per-IP daily cap check (default 30/day)
            ip_day = self._prune(self._ip_day.get(client_ip, []), one_day_ago)
            self._ip_day[client_ip] = ip_day
            if len(ip_day) >= self.per_day_per_ip:
                retry_after = max(1, int(86400.0 - (now - ip_day[0])))
                logger.warning("Daily limit exceeded for IP %s (30/day limit)", client_ip)
                return False, retry_after, f"Daily research quota exceeded for this IP. Limit is {self.per_day_per_ip} per day."

            # Grant token: record timestamps
            ip_min.append(now)
            ip_day.append(now)
            self._global_day.append(now)

            return True, None, None

    async def reset(self) -> None:
        """Resets all tracking windows (primarily for unit test isolation)."""
        async with self._lock:
            self._ip_minute.clear()
            self._ip_day.clear()
            self._global_day.clear()

    async def get_stats(self, client_ip: str) -> dict:
        """Returns current usage counters for diagnostic or test purposes."""
        async with self._lock:
            now = time.time()
            min_count = len(self._prune(self._ip_minute.get(client_ip, []), now - 60.0))
            day_count = len(self._prune(self._ip_day.get(client_ip, []), now - 86400.0))
            global_count = len(self._prune(self._global_day, now - 86400.0))
            return {
                "client_ip": client_ip,
                "requests_last_minute": min_count,
                "requests_last_day": day_count,
                "global_requests_last_day": global_count,
                "minute_limit": self.per_minute_per_ip,
                "day_limit": self.per_day_per_ip,
                "global_day_limit": self.global_per_day,
            }


class GeminiQuotaProtection:
    """
    Configurable Gemini API quota and abuse controls (Milestone 3.1).
    Ensures that when Gemini is integrated, calls are strictly bounded:
    - Maximum 1 call per research request.
    - Strict input token/character limits.
    - Maximum output token cap.
    - Global daily request cap.
    - No automatic retries on quota-exceeded (429 / ResourceExhausted) errors.
    """

    def __init__(
        self,
        max_calls_per_request: Optional[int] = None,
        max_input_chars: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        max_daily_requests: Optional[int] = None,
        retry_on_quota: Optional[bool] = None,
    ):
        self.max_calls_per_request = max_calls_per_request or settings.GEMINI_MAX_CALLS_PER_REQUEST
        self.max_input_chars = max_input_chars or settings.GEMINI_MAX_INPUT_CHARS
        self.max_output_tokens = max_output_tokens or settings.GEMINI_MAX_OUTPUT_TOKENS
        self.max_daily_requests = max_daily_requests or settings.GEMINI_MAX_DAILY_REQUESTS
        self.retry_on_quota = retry_on_quota if retry_on_quota is not None else settings.GEMINI_RETRY_ON_QUOTA

        self._daily_calls: List[float] = []
        self._lock = asyncio.Lock()

    async def can_call(self) -> Tuple[bool, Optional[str]]:
        """Checks if a Gemini call is permitted under daily quota limits."""
        async with self._lock:
            now = time.time()
            one_day_ago = now - 86400.0
            self._daily_calls = [t for t in self._daily_calls if t > one_day_ago]

            if len(self._daily_calls) >= self.max_daily_requests:
                return False, f"Gemini daily quota limit reached ({self.max_daily_requests} calls/day)."
            return True, None

    async def record_call(self) -> None:
        """Records a completed Gemini invocation timestamp."""
        async with self._lock:
            self._daily_calls.append(time.time())

    def sanitize_prompt_length(self, prompt: str) -> str:
        """Truncates prompt to maximum configured character budget if needed."""
        if len(prompt) > self.max_input_chars:
            logger.warning(
                "Prompt length (%d chars) exceeded max limit (%d chars). Truncating.",
                len(prompt),
                self.max_input_chars,
            )
            return prompt[: self.max_input_chars]
        return prompt

    async def reset(self) -> None:
        """Resets call counters."""
        async with self._lock:
            self._daily_calls.clear()


class EndpointRateLimiter:
    """
    Sliding-window rate limiter for public endpoints (Investigate, Share, Connection, Toolkit).
    Provides process-local abuse prevention with per-minute and per-day caps.
    """

    def __init__(self, name: str, per_minute_per_ip: int = 10, per_day_per_ip: int = 100):
        self.name = name
        self.per_minute_per_ip = per_minute_per_ip
        self.per_day_per_ip = per_day_per_ip
        self._ip_minute: Dict[str, List[float]] = {}
        self._ip_day: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    def _prune(self, timestamps: List[float], cutoff: float) -> List[float]:
        return [t for t in timestamps if t > cutoff]

    async def acquire(self, client_ip: str) -> Tuple[bool, Optional[int], Optional[str]]:
        async with self._lock:
            now = time.time()
            one_min_ago = now - 60.0
            one_day_ago = now - 86400.0

            ip_min = self._prune(self._ip_minute.get(client_ip, []), one_min_ago)
            self._ip_minute[client_ip] = ip_min
            if len(ip_min) >= self.per_minute_per_ip:
                retry_after = max(1, int(60.0 - (now - ip_min[0])))
                return False, retry_after, f"Too many {self.name} requests. Rate limit is {self.per_minute_per_ip} per minute."

            ip_day = self._prune(self._ip_day.get(client_ip, []), one_day_ago)
            self._ip_day[client_ip] = ip_day
            if len(ip_day) >= self.per_day_per_ip:
                retry_after = max(1, int(86400.0 - (now - ip_day[0])))
                return False, retry_after, f"Daily limit exceeded for {self.name}. Quota is {self.per_day_per_ip} per day."

            ip_min.append(now)
            ip_day.append(now)
            return True, None, None

    async def reset(self) -> None:
        async with self._lock:
            self._ip_minute.clear()
            self._ip_day.clear()


# Global singleton instances
research_rate_limiter = ResearchRateLimiter()
gemini_quota_protection = GeminiQuotaProtection()

investigate_rate_limiter = EndpointRateLimiter(name="investigate", per_minute_per_ip=10, per_day_per_ip=60)
share_rate_limiter = EndpointRateLimiter(name="share", per_minute_per_ip=15, per_day_per_ip=100)
connection_rate_limiter = EndpointRateLimiter(name="connection", per_minute_per_ip=10, per_day_per_ip=50)
toolkit_rate_limiter = EndpointRateLimiter(name="toolkit", per_minute_per_ip=30, per_day_per_ip=300)

