"""
Zero-Cost Documentation Fetcher Service (Milestone 3.1).

Retrieves, extracts, and validates publicly accessible official developer documentation
and OAuth discovery metadata (RFC 8414 / OpenID Connect) without paid search APIs.

Security Protections:
- Strict SSRF defense: blocks localhost, private, loopback, link-local, multicast,
  reserved, CGNAT, and cloud metadata IP ranges.
- DNS resolution validation before connection.
- Manual redirect tracking with per-hop SSRF re-validation (DNS rebinding defense).
- Standard HTTP/HTTPS port enforcement.
- Response size limits (max 1 MB per document).
- Per-request timeout limits (10s).
- Concurrency limiting (max 3 concurrent outbound requests).
- Safe HTML parsing without JS execution.
- In-memory thread-safe/asyncio-safe document caching with TTL.
"""
import re
import socket
import logging
import asyncio
import ipaddress
import urllib.parse
from datetime import datetime, timezone
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
import httpcore
from httpcore._backends.auto import AutoBackend
from httpcore import ConnectError

from app.core.config import settings
from app.core.security import redact_sensitive_data

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class OAuthDiscoveryMetadata:
    """Structured representation of RFC 8414 / OpenID Connect discovery document."""
    issuer: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    scopes_supported: List[str] = field(default_factory=list)
    response_types_supported: List[str] = field(default_factory=list)
    grant_types_supported: List[str] = field(default_factory=list)
    code_challenge_methods_supported: List[str] = field(default_factory=list)
    token_endpoint_auth_methods_supported: List[str] = field(default_factory=list)
    raw_json: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FetchedDoc:
    """Representation of retrieved and cleaned documentation content."""
    url: str
    final_url: str
    domain: str
    title: str
    text: str
    status_code: int
    content_type: str
    is_oauth_metadata: bool = False
    oauth_metadata: Optional[OAuthDiscoveryMetadata] = None
    evidence_excerpt: Optional[str] = None
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# SSRF & Network Security Validator
# ---------------------------------------------------------------------------

class SSRFSecurityValidator:
    """
    Validates URL syntax, protocols, ports, and resolved IP addresses to prevent
    SSRF, DNS rebinding, and unauthorized internal network probing.
    """

    ALLOWED_SCHEMES: Set[str] = {"http", "https"}
    ALLOWED_PORTS: Set[int] = {80, 443}

    # Cloud metadata and internal service IPs
    BLOCKED_METADATA_IPS: Set[str] = {
        "169.254.169.254",   # AWS, GCP, Azure, OpenStack
        "100.100.100.200",   # Alibaba Cloud
        "fd00:ec2::254",     # AWS IPv6 metadata
    }

    BLOCKED_HOSTNAMES: Set[str] = {
        "localhost",
        "metadata.google.internal",
        "metadata.goog",
        "instance-data",
    }

    # Additional restricted subnets
    RESTRICTED_NETWORKS = [
        ipaddress.ip_network("100.64.0.0/10"),    # Carrier-grade NAT (RFC 6598)
        ipaddress.ip_network("198.18.0.0/15"),    # Benchmark testing (RFC 2544)
        ipaddress.ip_network("192.0.2.0/24"),     # Documentation TEST-NET-1 (RFC 5737)
        ipaddress.ip_network("198.51.100.0/24"),  # Documentation TEST-NET-2 (RFC 5737)
        ipaddress.ip_network("203.0.113.0/24"),   # Documentation TEST-NET-3 (RFC 5737)
        ipaddress.ip_network("240.0.0.0/4"),      # Reserved for future use (RFC 1112)
    ]

    @classmethod
    def is_ip_blocked(cls, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> Tuple[bool, str]:
        """Checks whether an IP address belongs to a private, loopback, or reserved range."""
        ip_str = str(ip)

        if ip_str in cls.BLOCKED_METADATA_IPS:
            return True, f"Cloud metadata endpoint IP blocked: {ip_str}"

        # RFC 6052 / RFC 8215 Well-Known NAT64 Prefix (64:ff9b::/96)
        # On IPv6 transition networks, DNS synthesizes IPv4 hosts into 64:ff9b::<ipv4>.
        # Python's ip.is_reserved returns True for this prefix.
        # Check the embedded IPv4 address to determine if it is public vs private/blocked.
        if ip.version == 6 and ip in ipaddress.IPv6Network("64:ff9b::/96"):
            embedded_v4 = ipaddress.IPv4Address(ip.packed[-4:])
            return cls.is_ip_blocked(embedded_v4)

        if ip.is_loopback:
            return True, f"Loopback address blocked: {ip_str}"
        if ip.is_private:
            return True, f"Private address blocked: {ip_str}"
        if ip.is_link_local:
            return True, f"Link-local address blocked: {ip_str}"
        if ip.is_multicast:
            return True, f"Multicast address blocked: {ip_str}"
        if ip.is_reserved:
            return True, f"Reserved address blocked: {ip_str}"
        if ip.is_unspecified:
            return True, f"Unspecified address blocked: {ip_str}"

        for net in cls.RESTRICTED_NETWORKS:
            if ip in net:
                return True, f"Restricted network {net} blocked: {ip_str}"

        return False, ""

    @classmethod
    def resolve_and_validate_host(cls, hostname: str, port: int) -> Tuple[bool, Optional[str], List[str]]:
        """
        Performs DNS resolution and validates every resolved IP against security boundaries.
        Returns (is_valid, error_reason, list_of_resolved_ips).
        """
        lowered_host = hostname.strip().lower()
        if lowered_host in cls.BLOCKED_HOSTNAMES:
            return False, f"Blocked hostname: {lowered_host}", []

        if lowered_host.endswith(".localhost") or lowered_host.endswith(".local") or lowered_host.endswith(".internal"):
            return False, f"Internal domain suffix blocked: {lowered_host}", []

        # Check if the hostname is directly an IP literal
        try:
            direct_ip = ipaddress.ip_address(lowered_host)
            blocked, reason = cls.is_ip_blocked(direct_ip)
            if blocked:
                return False, reason, []
            return True, None, [str(direct_ip)]
        except ValueError:
            # Not a direct IP literal, proceed with DNS resolution
            pass

        try:
            addr_info = socket.getaddrinfo(lowered_host, port, proto=socket.IPPROTO_TCP)
        except socket.gaierror as exc:
            return False, f"DNS resolution failed for {lowered_host}: {str(exc)}", []
        except Exception as exc:
            return False, f"Socket error resolving {lowered_host}: {str(exc)}", []

        if not addr_info:
            return False, f"No DNS records found for {lowered_host}", []

        resolved_ips: List[str] = []
        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = sockaddr[0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
                blocked, reason = cls.is_ip_blocked(ip_obj)
                if blocked:
                    return False, f"DNS resolved to prohibited destination: {reason}", []
                resolved_ips.append(ip_str)
            except ValueError:
                return False, f"Invalid resolved IP format: {ip_str}", []

        if not resolved_ips:
            return False, f"Zero valid IP addresses resolved for {lowered_host}", []

        return True, None, resolved_ips

    @classmethod
    def validate_url(cls, url: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        Comprehensive SSRF validation for a URL string.
        Validates scheme, userinfo, port, and DNS-resolved IPs.
        """
        if not url or not isinstance(url, str):
            return False, "URL must be a non-empty string", []

        try:
            parsed = urllib.parse.urlsplit(url.strip())
        except Exception as exc:
            return False, f"Malformed URL syntax: {str(exc)}", []

        # 1. Scheme check
        scheme = parsed.scheme.lower()
        if scheme not in cls.ALLOWED_SCHEMES:
            return False, f"Prohibited URL scheme '{scheme}'. Only HTTP and HTTPS are permitted.", []

        # 2. Reject credentials in URL
        if parsed.username or parsed.password:
            return False, "Userinfo credentials in URL are prohibited.", []

        # 3. Hostname presence
        hostname = parsed.hostname
        if not hostname:
            return False, "URL must contain a valid hostname.", []

        # 4. Port validation
        port = parsed.port
        if port is not None and port not in cls.ALLOWED_PORTS:
            return False, f"Prohibited port {port}. Only standard ports (80, 443) are allowed.", []

        effective_port = port if port is not None else (443 if scheme == "https" else 80)

        # 5. DNS Resolution and IP Validation
        return cls.resolve_and_validate_host(hostname, effective_port)


class SSRFSafeNetworkBackend(AutoBackend):
    """
    Network backend that enforces strict SSRF and DNS rebinding protections
    directly at the TCP socket creation boundary.
    - Resolves DNS and validates all IP answers before establishing connection.
    - Rejects loopback, private, link-local, multicast, cloud metadata, and reserved IPs.
    - Rejects mixed public/private DNS answers.
    - Enforces standard ports (80, 443).
    - Pins TCP socket connection directly to the validated IP literal, guaranteeing
      that the operating system cannot re-resolve the hostname to a different IP (anti-rebinding).
    - Preserves TLS SNI and certificate verification through httpcore's start_tls(server_hostname).
    """

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: Optional[float] = None,
        local_address: Optional[str] = None,
        socket_options: Any = None,
    ) -> httpcore.AsyncNetworkStream:
        # Enforce standard ports
        if port not in SSRFSecurityValidator.ALLOWED_PORTS:
            raise ConnectError(f"SSRF blocked: Prohibited port {port}. Only standard ports (80, 443) are allowed.")

        # Resolve host to IP addresses
        lowered_host = host.strip().lower()
        if lowered_host in SSRFSecurityValidator.BLOCKED_HOSTNAMES:
            raise ConnectError(f"SSRF blocked: Blocked hostname '{lowered_host}'")

        try:
            # Check if host is already an IP literal
            ip_obj = ipaddress.ip_address(lowered_host)
            blocked, reason = SSRFSecurityValidator.is_ip_blocked(ip_obj)
            if blocked:
                raise ConnectError(f"SSRF blocked: Prohibited IP address '{lowered_host}' ({reason})")
            validated_ip = str(ip_obj)
        except ValueError:
            # Domain name: resolve DNS
            try:
                addr_info = socket.getaddrinfo(lowered_host, port, proto=socket.IPPROTO_TCP)
            except socket.gaierror as exc:
                raise ConnectError(f"SSRF DNS resolution failed for '{lowered_host}': {exc}")
            except Exception as exc:
                raise ConnectError(f"SSRF socket error resolving '{lowered_host}': {exc}")

            if not addr_info:
                raise ConnectError(f"SSRF: Zero DNS records returned for '{lowered_host}'")

            # Validate EVERY resolved address; reject if any IP is prohibited (anti-mixed rebinding)
            safe_ips: List[str] = []
            for entry in addr_info:
                sockaddr = entry[4]
                ip_str = sockaddr[0]
                try:
                    ip_addr = ipaddress.ip_address(ip_str)
                    blocked, reason = SSRFSecurityValidator.is_ip_blocked(ip_addr)
                    if blocked:
                        raise ConnectError(f"SSRF blocked: DNS answer '{ip_str}' for '{lowered_host}' is prohibited: {reason}")
                    safe_ips.append(ip_str)
                except ValueError:
                    raise ConnectError(f"SSRF blocked: Invalid resolved IP format '{ip_str}'")

            if not safe_ips:
                raise ConnectError(f"SSRF blocked: No permitted public IPs resolved for '{lowered_host}'")

            validated_ip = safe_ips[0]

        # Connect directly to the validated IP literal to prevent DNS rebinding
        return await super().connect_tcp(
            validated_ip,
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )


def create_ssrf_safe_transport(verify: bool = True) -> httpx.AsyncHTTPTransport:
    """Creates an httpx AsyncHTTPTransport configured with SSRFSafeNetworkBackend."""
    backend = SSRFSafeNetworkBackend()
    pool = httpcore.AsyncConnectionPool(network_backend=backend, http1=True, http2=False)
    transport = httpx.AsyncHTTPTransport(verify=verify)
    transport._pool = pool
    return transport


# ---------------------------------------------------------------------------
# HTML Sanitization and Text Extraction
# ---------------------------------------------------------------------------

class SafeHTMLTextExtractor(HTMLParser):
    """
    Lightweight, secure HTML text extractor using standard library HTMLParser.
    Completely ignores scripts, styles, embedded objects, and navigation elements.
    """

    IGNORED_TAGS = {
        "script",
        "style",
        "noscript",
        "svg",
        "iframe",
        "object",
        "embed",
        "header",
        "footer",
        "nav",
        "aside",
    }

    def __init__(self):
        super().__init__()
        self._ignore_depth = 0
        self._in_title = False
        self.title = ""
        self.canonical_url: Optional[str] = None
        self._text_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        t = tag.lower()
        if t in self.IGNORED_TAGS:
            self._ignore_depth += 1
        elif t == "title" and self._ignore_depth == 0:
            self._in_title = True
        elif t == "link":
            attr_dict = {k.lower(): (v or "") for k, v in attrs}
            if attr_dict.get("rel", "").lower() == "canonical":
                self.canonical_url = attr_dict.get("href")

    def handle_endtag(self, tag: str):
        t = tag.lower()
        if t in self.IGNORED_TAGS:
            self._ignore_depth = max(0, self._ignore_depth - 1)
        elif t == "title":
            self._in_title = False

    def handle_data(self, data: str):
        if self._ignore_depth > 0:
            return
        if self._in_title:
            self.title += data
        else:
            cleaned = data.strip()
            if cleaned:
                self._text_parts.append(cleaned)

    def get_clean_text(self, max_chars: int = 50000) -> str:
        """Returns normalized readable text collapsed by single spaces and paragraphs."""
        combined = " ".join(self._text_parts)
        # Collapse multiple spaces
        combined = re.sub(r"\s+", " ", combined).strip()
        if len(combined) > max_chars:
            return combined[:max_chars].rsplit(" ", 1)[0] + "..."
        return combined

    def get_title(self) -> str:
        """Returns clean page title or default."""
        t = re.sub(r"\s+", " ", self.title).strip()
        return t or "Documentation Source"


# ---------------------------------------------------------------------------
# In-Memory Documentation Cache
# ---------------------------------------------------------------------------

class DocCache:
    """
    Thread-safe / asyncio-safe in-memory cache for fetched documentation pages.
    Keys are normalized URLs, values are (FetchedDoc, expire_timestamp).
    """

    def __init__(self, default_ttl_seconds: Optional[int] = None):
        self.default_ttl = default_ttl_seconds or settings.DOC_CACHE_TTL_SECONDS
        self._cache: Dict[str, Tuple[FetchedDoc, float]] = {}
        self._lock = asyncio.Lock()

    def _normalize_key(self, url: str) -> str:
        return url.strip().rstrip("/")

    async def get(self, url: str) -> Optional[FetchedDoc]:
        """Retrieves cached document if present and not expired."""
        key = self._normalize_key(url)
        async with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            doc, expires_at = entry
            if time_now := datetime.now(timezone.utc).timestamp() > expires_at:
                # Expired
                del self._cache[key]
                return None
            return doc

    async def set(self, url: str, doc: FetchedDoc, ttl_seconds: Optional[int] = None) -> None:
        """Stores a document with a TTL."""
        key = self._normalize_key(url)
        ttl = ttl_seconds or self.default_ttl
        expires_at = datetime.now(timezone.utc).timestamp() + ttl
        async with self._lock:
            self._cache[key] = (doc, expires_at)

    async def clear(self) -> None:
        """Clears all cached documents."""
        async with self._lock:
            self._cache.clear()

    async def size(self) -> int:
        """Returns count of active unexpired items."""
        async with self._lock:
            now = datetime.now(timezone.utc).timestamp()
            # Prune expired
            self._cache = {k: v for k, v in self._cache.items() if v[1] > now}
            return len(self._cache)


# ---------------------------------------------------------------------------
# Zero-Cost Documentation Fetcher Service
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Constants & Helpers for Domain Normalization
# ---------------------------------------------------------------------------

TWO_PART_TLDS = {
    "co.uk", "org.uk", "gov.uk", "ac.uk", "me.uk", "ltd.uk",
    "com.au", "net.au", "org.au", "edu.au",
    "co.nz", "net.nz", "org.nz",
    "co.jp", "ne.jp", "or.jp",
    "com.br", "net.br", "org.br",
    "co.in", "net.in", "org.in", "gen.in",
    "com.sg", "edu.sg",
    "com.mx", "org.mx",
    "co.za", "org.za",
}

DOC_PREFIXES = ("developers.", "developer.", "docs.", "doc.", "api.", "dev.")

# Explicit, verified domain mappings for popular developer platforms where TLD != .com or brand is well-established
KNOWN_APP_DOMAINS: Dict[str, str] = {
    "linear": "linear.app",
    "notion": "notion.com",
    "slack": "slack.com",
    "shopify": "shopify.com",
    "github": "github.com",
    "gitlab": "gitlab.com",
    "jira": "atlassian.com",
    "confluence": "atlassian.com",
    "atlassian": "atlassian.com",
    "airtable": "airtable.com",
    "hubspot": "hubspot.com",
    "salesforce": "salesforce.com",
    "zendesk": "zendesk.com",
    "stripe": "stripe.com",
    "figma": "figma.com",
    "asana": "asana.com",
    "discord": "discord.com",
    "zoom": "zoom.us",
    "postman": "postman.com",
    "miro": "miro.com",
    "clickup": "clickup.com",
    "trello": "trello.com",
}


def extract_apex_domain(host: str) -> str:
    """
    Extracts the root/apex domain from a given hostname.
    Handles standard single TLDs (e.g. 'notion.com' -> 'notion.com',
    'auth.eu.auth0.com' -> 'auth0.com') and common two-part ccTLDs
    (e.g. 'auth.staging.example.co.uk' -> 'example.co.uk').
    """
    parts = host.lower().split(".")
    if len(parts) <= 2:
        return host
    last_two = f"{parts[-2]}.{parts[-1]}"
    if last_two in TWO_PART_TLDS:
        return ".".join(parts[-3:]) if len(parts) >= 3 else host
    return ".".join(parts[-2:])


class DocFetcherService:
    """
    Modular documentation discovery and retrieval service.
    Fetches RFC 8414 metadata and developer documentation pages using HTTP requests.
    """

    def __init__(
        self,
        timeout_seconds: Optional[float] = None,
        max_response_bytes: Optional[int] = None,
        max_concurrent: Optional[int] = None,
        cache: Optional[DocCache] = None,
    ):
        self.timeout = timeout_seconds or settings.DOC_REQUEST_TIMEOUT_SECONDS
        self.max_response_bytes = max_response_bytes or settings.DOC_MAX_RESPONSE_BYTES
        self.semaphore = asyncio.Semaphore(max_concurrent or settings.DOC_MAX_CONCURRENT_FETCHES)
        self.cache = cache or DocCache()
        self.validator = SSRFSecurityValidator

    def parse_oauth_metadata_json(self, data: Dict[str, Any]) -> Optional[OAuthDiscoveryMetadata]:
        """
        Parses RFC 8414 / OpenID Connect metadata JSON, preserving exact endpoint strings.
        Returns None if the payload does not contain OAuth authorization or token endpoints.
        """
        if not isinstance(data, dict):
            return None

        # Check for core OAuth/OIDC indicators
        auth_ep = data.get("authorization_endpoint")
        token_ep = data.get("token_endpoint")
        issuer = data.get("issuer")

        if not (auth_ep or token_ep or issuer):
            return None

        def _as_str_list(val: Any) -> List[str]:
            if isinstance(val, list):
                return [str(item) for item in val if item is not None]
            return []

        return OAuthDiscoveryMetadata(
            issuer=str(issuer) if issuer else None,
            authorization_endpoint=str(auth_ep) if auth_ep else None,
            token_endpoint=str(token_ep) if token_ep else None,
            jwks_uri=str(data.get("jwks_uri")) if data.get("jwks_uri") else None,
            userinfo_endpoint=str(data.get("userinfo_endpoint")) if data.get("userinfo_endpoint") else None,
            scopes_supported=_as_str_list(data.get("scopes_supported")),
            response_types_supported=_as_str_list(data.get("response_types_supported")),
            grant_types_supported=_as_str_list(data.get("grant_types_supported")),
            code_challenge_methods_supported=_as_str_list(data.get("code_challenge_methods_supported")),
            token_endpoint_auth_methods_supported=_as_str_list(data.get("token_endpoint_auth_methods_supported")),
            raw_json=redact_sensitive_data(data),
        )

    @staticmethod
    def extract_connected_peer_ip(response: httpx.Response) -> Optional[str]:
        """
        Extracts the actual remote peer IP address from the underlying live network socket
        to protect against Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding attacks.
        """
        stream = response.extensions.get("network_stream")
        if not stream:
            return None

        # Check anyio remote_address attribute
        try:
            import anyio.abc
            inner = getattr(stream, "_stream", stream)
            ts = getattr(inner, "transport_stream", inner)
            if hasattr(ts, "extra"):
                addr = ts.extra(anyio.abc.SocketAttribute.remote_address, None)
                if addr and isinstance(addr, tuple) and len(addr) >= 1:
                    return str(addr[0])
        except Exception:
            pass

        # Check raw socket fallback
        try:
            inner = getattr(stream, "_stream", stream)
            ts = getattr(inner, "transport_stream", inner)
            raw_sock = getattr(ts, "_raw_socket", None)
            if raw_sock and hasattr(raw_sock, "getpeername"):
                peer = raw_sock.getpeername()
                if peer and isinstance(peer, tuple) and len(peer) >= 1:
                    return str(peer[0])
        except Exception:
            pass

        return None

    def discover_candidate_urls(
        self,
        app_name: str,
        website_or_domain: Optional[str] = None,
        composio_doc_url: Optional[str] = None,
    ) -> List[str]:
        """
        Generates candidate documentation and discovery URLs based on app domain,
        RFC 8414 well-known paths, and Composio metadata.
        Normalizes hostnames (e.g. stripping www prefix to derive base domain),
        preserves legitimate non-www subdomains, and avoids redundant double prefixes.
        """
        candidates: List[str] = []
        seen: Set[str] = set()

        def _add(u: Optional[str]):
            if u and isinstance(u, str):
                cleaned = u.strip()
                if cleaned and cleaned not in seen:
                    # Quick scheme check
                    if cleaned.startswith("http://") or cleaned.startswith("https://"):
                        seen.add(cleaned)
                        candidates.append(cleaned)

        # 1. Prioritize known Composio documentation link if available
        _add(composio_doc_url)

        # 2. Extract and normalize supplied hostname
        supplied_host = None
        supplied_url = None
        has_specific_path = False

        if website_or_domain:
            raw = website_or_domain.strip()
            if raw:
                raw_url = raw if raw.startswith(("http://", "https://")) else "https://" + raw
                try:
                    parsed = urllib.parse.urlsplit(raw_url)
                    if parsed.hostname:
                        supplied_host = parsed.hostname.lower().strip()
                        supplied_url = raw_url
                        if parsed.path and parsed.path.strip("/") != "":
                            has_specific_path = True
                except Exception:
                    pass

        if not supplied_host:
            slug = re.sub(r"[^a-z0-9\-]", "", app_name.lower().strip())
            # 2a. Check explicit verified mapping for known apps (e.g. 'Linear' -> 'linear.app', 'Zoom' -> 'zoom.us')
            if slug in KNOWN_APP_DOMAINS:
                supplied_host = KNOWN_APP_DOMAINS[slug]
                supplied_url = f"https://{supplied_host}"
            elif composio_doc_url:
                try:
                    p = urllib.parse.urlsplit(composio_doc_url)
                    if p.hostname:
                        supplied_host = p.hostname.lower().strip()
                        supplied_url = composio_doc_url
                        if p.path and p.path.strip("/") != "":
                            has_specific_path = True
                except Exception:
                    pass
            elif slug and len(slug) >= 3 and not slug.isdigit():
                # Derive tentative fallback domain for standard brands without asserting as verified fact
                supplied_host = f"{slug}.com"
                supplied_url = f"https://{supplied_host}"

        if not supplied_host:
            return candidates

        # 3. Handle www prefix and developer/doc prefixes
        is_www = supplied_host.startswith("www.")
        host_without_www = supplied_host[4:] if is_www else supplied_host

        matched_doc_prefix = None
        for p in DOC_PREFIXES:
            if host_without_www.startswith(p):
                matched_doc_prefix = p
                break

        if matched_doc_prefix:
            base_domain = host_without_www[len(matched_doc_prefix):]
        else:
            base_domain = host_without_www

        apex_domain = extract_apex_domain(base_domain)

        # If user supplied a deep-link path or explicit developer portal URL, prioritize it
        if has_specific_path or matched_doc_prefix:
            _add(supplied_url)

        # 4. Legitimate nested subdomain handling (e.g. auth.eu.auth0.com)
        if base_domain != apex_domain and not matched_doc_prefix:
            # Preserve the legitimate non-www subdomain and probe discovery on it directly
            _add(supplied_url)
            _add(f"https://{base_domain}/.well-known/oauth-authorization-server")
            _add(f"https://{base_domain}/.well-known/openid-configuration")
            _add(f"https://{base_domain}/docs")
            _add(f"https://{base_domain}/developers")

            # Also probe apex domain documentation
            _add(f"https://developers.{apex_domain}")
            _add(f"https://docs.{apex_domain}")
            _add(f"https://api.{apex_domain}")
            _add(f"https://{apex_domain}/docs")
            _add(f"https://{apex_domain}/developers")
            _add(f"https://{apex_domain}/.well-known/oauth-authorization-server")
            _add(f"https://{apex_domain}/.well-known/openid-configuration")
            _add(f"https://{apex_domain}")
        else:
            # Standard domain handling (base_domain == apex_domain or user supplied doc portal)
            _add(f"https://developers.{base_domain}")
            _add(f"https://docs.{base_domain}")
            _add(f"https://api.{base_domain}")
            _add(f"https://{base_domain}/.well-known/oauth-authorization-server")
            _add(f"https://{base_domain}/.well-known/openid-configuration")
            # Attempt original supplied website if not already added
            _add(supplied_url)
            _add(f"https://{base_domain}/docs")
            _add(f"https://{base_domain}/developers")
            _add(f"https://{base_domain}")

        return candidates

    async def fetch_url(
        self,
        url: str,
        client: Optional[httpx.AsyncClient] = None,
        max_redirects: int = 3,
    ) -> Optional[FetchedDoc]:
        """
        Safely fetches a single URL with SSRF protection, size caps, and redirect validation.
        """
        # Check cache first
        cached = await self.cache.get(url)
        if cached:
            return cached

        # Validate initial URL
        is_valid, reason, _ = self.validator.validate_url(url)
        if not is_valid:
            logger.warning("SSRF check blocked initial URL '%s': %s", url, reason)
            return None

        current_url = url
        redirect_count = 0
        seen_redirects = {url}

        headers = {
            "User-Agent": "OAuthNavigator/1.0 (Developer Documentation Research Engine)",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with self.semaphore:
            owns_client = client is None
            if client is not None:
                http_client = client
            else:
                transport = create_ssrf_safe_transport(verify=True)
                http_client = httpx.AsyncClient(
                    transport=transport,
                    verify=True,
                    follow_redirects=False,  # Manual redirect validation
                    timeout=httpx.Timeout(self.timeout),
                )

            try:
                while True:
                    try:
                        response = await http_client.get(current_url, headers=headers)
                    except (httpx.TimeoutException, asyncio.TimeoutError):
                        logger.warning("HTTP request timed out for %s", current_url)
                        return None
                    except Exception as exc:
                        logger.warning("HTTP request error fetching %s: %s", current_url, str(exc))
                        return None

                    # Handle HTTP redirects manually
                    if response.is_redirect:
                        redirect_count += 1
                        if redirect_count > max_redirects:
                            logger.warning("Exceeded max redirects (%d) for %s", max_redirects, url)
                            return None

                        location = response.headers.get("Location")
                        if not location:
                            logger.warning("Redirect status without Location header for %s", current_url)
                            return None

                        target_url = urllib.parse.urljoin(current_url, location)
                        if target_url in seen_redirects:
                            logger.warning("Redirect loop detected for %s -> %s", current_url, target_url)
                            return None

                        seen_redirects.add(target_url)

                        # Re-run full SSRF validation on redirect target
                        is_valid, reason, _ = self.validator.validate_url(target_url)
                        if not is_valid:
                            logger.warning("SSRF blocked redirect target '%s': %s", target_url, reason)
                            return None

                        current_url = target_url
                        continue

                    # Final response reached
                    break

                # Live Connection SSRF Check (DNS Rebinding / TOCTOU defense on active socket)
                connected_peer_ip = self.extract_connected_peer_ip(response)
                if connected_peer_ip:
                    try:
                        ip_obj = ipaddress.ip_address(connected_peer_ip)
                        blocked, reason = self.validator.is_ip_blocked(ip_obj)
                        if blocked:
                            logger.warning(
                                "SSRF blocked live socket destination '%s' for %s: %s",
                                connected_peer_ip,
                                current_url,
                                reason,
                            )
                            return None
                    except ValueError:
                        pass

                # Enforce response status
                if response.status_code >= 400:
                    logger.debug("HTTP status %d received for %s", response.status_code, current_url)
                    return None

                # Enforce response size limits
                content_len = response.headers.get("content-length")
                if content_len and content_len.isdigit() and int(content_len) > self.max_response_bytes:
                    logger.warning(
                        "Response content-length %s exceeds max %d bytes for %s",
                        content_len,
                        self.max_response_bytes,
                        current_url,
                    )
                    return None

                raw_bytes = response.content
                if len(raw_bytes) > self.max_response_bytes:
                    logger.warning("Response payload size %d exceeds max for %s", len(raw_bytes), current_url)
                    raw_bytes = raw_bytes[: self.max_response_bytes]

                content_type = response.headers.get("content-type", "").lower()
                domain = urllib.parse.urlsplit(current_url).netloc.lower()

                # Case A: JSON Response (e.g. RFC 8414 metadata)
                if "application/json" in content_type or current_url.endswith(".json") or "/.well-known/" in current_url:
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            oauth_meta = self.parse_oauth_metadata_json(data)
                            title = f"OAuth Discovery Metadata ({domain})"
                            text_summary = (
                                f"RFC 8414 OAuth Metadata: authorization_endpoint={oauth_meta.authorization_endpoint or 'N/A'}, "
                                f"token_endpoint={oauth_meta.token_endpoint or 'N/A'}, "
                                f"scopes_supported={len(oauth_meta.scopes_supported) if oauth_meta else 0}"
                            )
                            doc = FetchedDoc(
                                url=url,
                                final_url=current_url,
                                domain=domain,
                                title=title,
                                text=text_summary,
                                status_code=response.status_code,
                                content_type=content_type,
                                is_oauth_metadata=bool(oauth_meta),
                                oauth_metadata=oauth_meta,
                                evidence_excerpt=text_summary,
                            )
                            await self.cache.set(url, doc)
                            return doc
                    except Exception:
                        # Failed to parse as JSON, fall through to HTML parser
                        pass

                # Case B: HTML/Text Response
                charset = response.encoding or "utf-8"
                html_text = raw_bytes.decode(charset, errors="replace")

                extractor = SafeHTMLTextExtractor()
                try:
                    extractor.feed(html_text)
                except Exception as exc:
                    logger.debug("HTML parser encountered non-fatal error: %s", str(exc))

                clean_text = extractor.get_clean_text()
                title = extractor.get_title()

                doc = FetchedDoc(
                    url=url,
                    final_url=current_url,
                    domain=domain,
                    title=title,
                    text=clean_text,
                    status_code=response.status_code,
                    content_type=content_type,
                    is_oauth_metadata=False,
                    oauth_metadata=None,
                    evidence_excerpt=clean_text[:500] if clean_text else None,
                )

                await self.cache.set(url, doc)
                return doc

            finally:
                if owns_client:
                    await http_client.aclose()

    async def fetch_documentation_for_app(
        self,
        app_name: str,
        website_or_domain: Optional[str] = None,
        composio_doc_url: Optional[str] = None,
        max_pages: Optional[int] = None,
    ) -> List[FetchedDoc]:
        """
        Discovers and retrieves documentation pages for an application up to the configured limit.
        Guarantees that 404s on discovery endpoints do not cause failure.
        """
        limit = max_pages or settings.DOC_MAX_PAGES_PER_REQUEST
        candidates = self.discover_candidate_urls(app_name, website_or_domain, composio_doc_url)

        results: List[FetchedDoc] = []

        safe_transport = create_ssrf_safe_transport(verify=True)
        async with httpx.AsyncClient(
            transport=safe_transport,
            verify=True,
            follow_redirects=False,
            timeout=httpx.Timeout(self.timeout),
        ) as client:
            tasks = [self.fetch_url(u, client=client) for u in candidates[:limit]]
            fetched_items = await asyncio.gather(*tasks, return_exceptions=True)

            for item in fetched_items:
                if isinstance(item, FetchedDoc) and item.text:
                    results.append(item)

        return results


# Global singleton instance
doc_fetcher_service = DocFetcherService()

