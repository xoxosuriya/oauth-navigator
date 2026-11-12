"""
Comprehensive Unit and Integration Tests for Milestone 3.1:
Zero-Cost Documentation Fetcher, SSRF Protection, Rate Limiting, and Quota Controls.

All tests run fully offline without live external requests or paid APIs.
"""
import sys
import os
import unittest
import asyncio
import time
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

# Ensure backend root is the first entry in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app
from app.core.config import settings
from app.core.rate_limit import (
    ResearchRateLimiter,
    GeminiQuotaProtection,
    get_client_ip,
    research_rate_limiter,
)
from app.services.doc_fetcher import (
    DocFetcherService,
    DocCache,
    FetchedDoc,
    OAuthDiscoveryMetadata,
    SSRFSecurityValidator,
    SafeHTMLTextExtractor,
)


class TestDocFetcherAndSecurity(unittest.TestCase):
    """Test suite covering DocFetcher, SSRF security, rate limiting, and quota controls."""

    def run_async(self, coro):
        return asyncio.run(coro)

    # -----------------------------------------------------------------
    # 1. SSRF & IP Validation Tests
    # -----------------------------------------------------------------
    def test_ssrf_blocks_localhost_and_loopback(self):
        """Verify that localhost, 127.0.0.1, and loopback addresses are strictly rejected."""
        test_urls = [
            "http://localhost/docs",
            "http://localhost:80/docs",
            "http://127.0.0.1/oauth",
            "http://127.0.0.2:80/test",
            "https://sub.localhost/api",
            "http://[::1]/oauth",
        ]
        for url in test_urls:
            valid, reason, _ = SSRFSecurityValidator.validate_url(url)
            self.assertFalse(valid, f"URL should be blocked by SSRF check: {url}")
            self.assertTrue(any(k in reason.lower() for k in ("loopback", "blocked", "prohibited", "localhost")))

    def test_ssrf_blocks_private_ip_ranges(self):
        """Verify that RFC 1918 private IP subnets (10/8, 172.16/12, 192.168/16) are blocked."""
        private_urls = [
            "http://10.0.0.1/admin",
            "http://10.255.255.254/oauth",
            "http://172.16.0.1/docs",
            "http://172.31.255.255/config",
            "http://192.168.1.1/router",
            "http://192.168.0.100/well-known",
            "http://0.0.0.0/test",
        ]
        for url in private_urls:
            valid, reason, _ = SSRFSecurityValidator.validate_url(url)
            self.assertFalse(valid, f"Private IP URL should be blocked: {url}")
            self.assertIn("blocked", reason.lower())

    def test_ssrf_blocks_cloud_metadata_endpoints(self):
        """Verify that cloud metadata IPs (169.254.169.254, 100.100.100.200) are blocked."""
        metadata_urls = [
            "http://169.254.169.254/latest/meta-data/",
            "http://169.254.169.254/computeMetadata/v1/",
            "http://100.100.100.200/latest/meta-data/",
            "http://metadata.google.internal/computeMetadata/v1/",
        ]
        for url in metadata_urls:
            valid, reason, _ = SSRFSecurityValidator.validate_url(url)
            self.assertFalse(valid, f"Cloud metadata URL should be blocked: {url}")

    def test_ssrf_rejects_unsafe_schemes_and_ports(self):
        """Verify that non-HTTP/HTTPS schemes and non-standard ports are rejected."""
        invalid_urls = [
            "ftp://example.com/file.txt",
            "gopher://example.com/7",
            "file:///etc/passwd",
            "data:text/html,<h1>test</h1>",
            "http://example.com:22/ssh",
            "http://example.com:3306/mysql",
            "http://example.com:6379/redis",
            "http://example.com:8080/test",
            "https://user:password@example.com/docs",  # Userinfo credentials
        ]
        for url in invalid_urls:
            valid, reason, _ = SSRFSecurityValidator.validate_url(url)
            self.assertFalse(valid, f"Unsafe URL should be rejected: {url}")

    def test_dns_rebinding_defense_on_redirect(self):
        """Verify that if an initial public URL redirects to a private IP, redirect is blocked."""
        service = DocFetcherService()

        # Mock client where initial request succeeds but returns a redirect to 169.254.169.254
        mock_res_redirect = MagicMock()
        mock_res_redirect.is_redirect = True
        mock_res_redirect.status_code = 302
        mock_res_redirect.headers = {"Location": "http://169.254.169.254/latest/meta-data"}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_res_redirect)

        # Patch DNS check to allow initial example.com
        with patch.object(
            SSRFSecurityValidator, "resolve_and_validate_host", return_value=(True, None, ["93.184.216.34"])
        ):
            doc = self.run_async(service.fetch_url("https://example.com/login", client=mock_client))
            # The redirect to 169.254.169.254 must be blocked, returning None
            self.assertIsNone(doc)

    # -----------------------------------------------------------------
    # 2. OAuth Metadata & OIDC Discovery Parsing
    # -----------------------------------------------------------------
    def test_parse_valid_rfc8414_oauth_metadata(self):
        """Verify that RFC 8414 metadata JSON correctly extracts exact endpoints and grant types."""
        sample_json = {
            "issuer": "https://auth.example.com",
            "authorization_endpoint": "https://auth.example.com/oauth/authorize",
            "token_endpoint": "https://auth.example.com/oauth/token",
            "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
            "scopes_supported": ["read", "write", "offline_access"],
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        }
        service = DocFetcherService()
        meta = service.parse_oauth_metadata_json(sample_json)

        self.assertIsNotNone(meta)
        self.assertEqual(meta.issuer, "https://auth.example.com")
        self.assertEqual(meta.authorization_endpoint, "https://auth.example.com/oauth/authorize")
        self.assertEqual(meta.token_endpoint, "https://auth.example.com/oauth/token")
        self.assertEqual(meta.scopes_supported, ["read", "write", "offline_access"])
        self.assertEqual(meta.grant_types_supported, ["authorization_code", "refresh_token"])
        self.assertEqual(meta.code_challenge_methods_supported, ["S256"])

    def test_parse_valid_openid_configuration(self):
        """Verify that OpenID Connect discovery metadata extracts userinfo and endpoints."""
        sample_oidc = {
            "issuer": "https://accounts.example.org",
            "authorization_endpoint": "https://accounts.example.org/o/oauth2/v2/auth",
            "token_endpoint": "https://oauth2.example.org/token",
            "userinfo_endpoint": "https://openidconnect.example.org/v1/userinfo",
            "scopes_supported": ["openid", "profile", "email"],
        }
        service = DocFetcherService()
        meta = service.parse_oauth_metadata_json(sample_oidc)

        self.assertIsNotNone(meta)
        self.assertEqual(meta.userinfo_endpoint, "https://openidconnect.example.org/v1/userinfo")
        self.assertIn("openid", meta.scopes_supported)

    def test_parse_non_oauth_json_returns_none(self):
        """Verify that arbitrary JSON lacking OAuth endpoints yields None."""
        service = DocFetcherService()
        meta = service.parse_oauth_metadata_json({"status": "ok", "message": "hello world"})
        self.assertIsNone(meta)

    # -----------------------------------------------------------------
    # 3. HTML Sanitization & Untrusted Content
    # -----------------------------------------------------------------
    def test_html_text_extractor_strips_scripts_and_styles(self):
        """Verify that HTML parsing completely ignores <script>, <style>, <nav> tags without executing code."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>  Example Developer Documentation  </title>
            <link rel="canonical" href="https://developers.example.com/oauth" />
            <style>body { color: red; }</style>
            <script>alert('malicious payload');</script>
        </head>
        <body>
            <nav><a href="/home">Home</a></nav>
            <h1>OAuth 2.0 Integration Guide</h1>
            <p>To register an app, visit the developer console and obtain a Client ID.</p>
            <script>console.log("secret leak");</script>
        </body>
        </html>
        """
        extractor = SafeHTMLTextExtractor()
        extractor.feed(html)

        clean_text = extractor.get_clean_text()
        title = extractor.get_title()

        self.assertEqual(title, "Example Developer Documentation")
        self.assertEqual(extractor.canonical_url, "https://developers.example.com/oauth")
        self.assertIn("OAuth 2.0 Integration Guide", clean_text)
        self.assertIn("developer console", clean_text)
        self.assertNotIn("alert('malicious payload')", clean_text)
        self.assertNotIn("console.log", clean_text)
        self.assertNotIn("color: red", clean_text)

    # -----------------------------------------------------------------
    # 4. Error Handling: 404, 403, Timeouts, Oversized Responses
    # -----------------------------------------------------------------
    def test_fetch_handles_404_and_403_gracefully(self):
        """Verify that 404 and 403 HTTP statuses return None without throwing unhandled exceptions."""
        service = DocFetcherService()

        for status_code in (404, 403):
            mock_res = MagicMock()
            mock_res.status_code = status_code
            mock_res.is_redirect = False

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_res)

            with patch.object(
                SSRFSecurityValidator, "resolve_and_validate_host", return_value=(True, None, ["93.184.216.34"])
            ):
                doc = self.run_async(service.fetch_url(f"https://example.com/{status_code}", client=mock_client))
                self.assertIsNone(doc)

    def test_fetch_handles_timeout_gracefully(self):
        """Verify that request timeouts return None without crashing."""
        service = DocFetcherService()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Read timed out"))

        with patch.object(
            SSRFSecurityValidator, "resolve_and_validate_host", return_value=(True, None, ["93.184.216.34"])
        ):
            doc = self.run_async(service.fetch_url("https://example.com/slow", client=mock_client))
            self.assertIsNone(doc)

    def test_fetch_rejects_oversized_responses(self):
        """Verify that responses exceeding maximum response bytes (1 MB) are rejected."""
        service = DocFetcherService(max_response_bytes=1000)

        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.is_redirect = False
        mock_res.headers = {"content-length": "5000000", "content-type": "text/html"}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_res)

        with patch.object(
            SSRFSecurityValidator, "resolve_and_validate_host", return_value=(True, None, ["93.184.216.34"])
        ):
            doc = self.run_async(service.fetch_url("https://example.com/huge", client=mock_client))
            self.assertIsNone(doc)

    # -----------------------------------------------------------------
    # 5. In-Memory Documentation Cache
    # -----------------------------------------------------------------
    def test_doc_cache_hits_and_expiry(self):
        """Verify that DocCache correctly returns cached docs and expires entries after TTL."""
        cache = DocCache(default_ttl_seconds=1)
        doc = FetchedDoc(
            url="https://example.com/docs",
            final_url="https://example.com/docs",
            domain="example.com",
            title="Cached Title",
            text="Cached documentation text.",
            status_code=200,
            content_type="text/html",
        )

        # 1. Store
        self.run_async(cache.set("https://example.com/docs", doc, ttl_seconds=1))

        # 2. Hit
        retrieved = self.run_async(cache.get("https://example.com/docs"))
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Cached Title")

        # 3. Wait for TTL expiry
        time.sleep(1.05)
        expired = self.run_async(cache.get("https://example.com/docs"))
        self.assertIsNone(expired)

    # -----------------------------------------------------------------
    # 6. Candidate URL Discovery & Domain Normalization
    # -----------------------------------------------------------------
    def test_discover_candidate_urls(self):
        """Verify that candidate URL generator produces well-known RFC 8414 and doc paths."""
        service = DocFetcherService()
        urls = service.discover_candidate_urls(
            app_name="Notion",
            website_or_domain="notion.so",
            composio_doc_url="https://developers.notion.com/docs/authorization",
        )

        # Composio URL is prioritized first
        self.assertEqual(urls[0], "https://developers.notion.com/docs/authorization")
        # RFC 8414 metadata URL included
        self.assertIn("https://notion.so/.well-known/oauth-authorization-server", urls)
        # OIDC metadata URL included
        self.assertIn("https://notion.so/.well-known/openid-configuration", urls)
        # Standard developer subdomains included
        self.assertIn("https://developers.notion.so", urls)

    def test_discover_candidate_urls_regression_www_notion(self):
        """
        Regression: For 'www.notion.com', verify base domain 'notion.com' is derived
        and developer subdomains do NOT retain www prefix (e.g. no 'developers.www.notion.com').
        """
        service = DocFetcherService()
        urls = service.discover_candidate_urls(
            app_name="Notion",
            website_or_domain="https://www.notion.com",
        )

        # Sensible candidates generated on base domain
        self.assertIn("https://developers.notion.com", urls)
        self.assertIn("https://docs.notion.com", urls)
        self.assertIn("https://api.notion.com", urls)
        self.assertIn("https://notion.com/.well-known/oauth-authorization-server", urls)
        self.assertIn("https://notion.com/.well-known/openid-configuration", urls)

        # Original supplied website attempted where appropriate
        self.assertIn("https://www.notion.com", urls)

        # Developers subdomain must be in top 5 candidates
        self.assertIn("https://developers.notion.com", urls[:5])

        # Regression: MUST NOT generate invalid hostnames retaining www
        self.assertNotIn("https://developers.www.notion.com", urls)
        self.assertNotIn("https://docs.www.notion.com", urls)
        self.assertNotIn("https://api.www.notion.com", urls)

    def test_discover_candidate_urls_regression_plain_domain_notion(self):
        """
        Regression: For 'notion.com', verify developer subdomains and discovery paths
        are generated cleanly on base domain.
        """
        service = DocFetcherService()
        urls = service.discover_candidate_urls(
            app_name="Notion",
            website_or_domain="notion.com",
        )

        self.assertIn("https://developers.notion.com", urls)
        self.assertIn("https://docs.notion.com", urls)
        self.assertIn("https://api.notion.com", urls)
        self.assertIn("https://notion.com/.well-known/oauth-authorization-server", urls)
        self.assertIn("https://notion.com", urls)
        self.assertIn("https://developers.notion.com", urls[:5])

    def test_discover_candidate_urls_regression_developers_notion(self):
        """
        Regression: For 'https://developers.notion.com', verify the developer portal
        is prioritized and does NOT generate double-prefixed 'developers.developers.notion.com'.
        """
        service = DocFetcherService()
        urls = service.discover_candidate_urls(
            app_name="Notion",
            website_or_domain="https://developers.notion.com",
        )

        # Supplied developer portal prioritized
        self.assertEqual(urls[0], "https://developers.notion.com")
        self.assertIn("https://docs.notion.com", urls)
        self.assertIn("https://api.notion.com", urls)
        self.assertIn("https://notion.com/.well-known/oauth-authorization-server", urls)

        # Regression: MUST NOT generate redundant double prefixes
        self.assertNotIn("https://developers.developers.notion.com", urls)
        self.assertNotIn("https://docs.developers.notion.com", urls)

    def test_discover_candidate_urls_regression_legitimate_nested_subdomain(self):
        """
        Regression: When user supplies a legitimate nested non-www subdomain (e.g. 'auth.corp.example.com'),
        verify the subdomain is preserved for discovery and doc paths, and apex domain is also probed.
        """
        service = DocFetcherService()
        urls = service.discover_candidate_urls(
            app_name="Acme",
            website_or_domain="https://auth.corp.example.com",
        )

        # Preserves the legitimate nested subdomain
        self.assertIn("https://auth.corp.example.com", urls)
        self.assertIn("https://auth.corp.example.com/.well-known/oauth-authorization-server", urls)
        self.assertIn("https://auth.corp.example.com/.well-known/openid-configuration", urls)
        self.assertIn("https://auth.corp.example.com/docs", urls)

        # Probes apex domain documentation
        self.assertIn("https://developers.example.com", urls)
        self.assertIn("https://docs.example.com", urls)

        # Regression: MUST NOT blindly prepend to already nested subdomain
        self.assertNotIn("https://developers.auth.corp.example.com", urls)
        self.assertNotIn("https://docs.auth.corp.example.com", urls)

    # -----------------------------------------------------------------
    # 7. API Rate Limiting: Per-Minute, Daily, and Global Limits
    # -----------------------------------------------------------------
    def test_rate_limiter_per_minute_limit(self):
        """Verify that client IP exceeding 5 requests in 60s is blocked with 429 Retry-After."""
        limiter = ResearchRateLimiter(per_minute_per_ip=5, per_day_per_ip=30, global_per_day=500)
        self.run_async(limiter.reset())

        # First 5 requests must succeed
        for i in range(5):
            allowed, retry_after, reason = self.run_async(limiter.acquire("198.51.100.1"))
            self.assertTrue(allowed, f"Request {i+1} should be permitted")

        # 6th request must be rate limited
        allowed, retry_after, reason = self.run_async(limiter.acquire("198.51.100.1"))
        self.assertFalse(allowed)
        self.assertIsNotNone(retry_after)
        self.assertGreater(retry_after, 0)
        self.assertIn("5 per minute", reason)

        # Different IP should still be allowed
        other_allowed, _, _ = self.run_async(limiter.acquire("198.51.100.2"))
        self.assertTrue(other_allowed)

    def test_rate_limiter_daily_limit(self):
        """Verify that client IP exceeding 30 requests in a day is blocked."""
        limiter = ResearchRateLimiter(per_minute_per_ip=100, per_day_per_ip=3, global_per_day=500)
        self.run_async(limiter.reset())

        for i in range(3):
            allowed, _, _ = self.run_async(limiter.acquire("198.51.100.5"))
            self.assertTrue(allowed)

        allowed, retry_after, reason = self.run_async(limiter.acquire("198.51.100.5"))
        self.assertFalse(allowed)
        self.assertIn("3 per day", reason)

    def test_rate_limiter_global_daily_cap(self):
        """Verify that total requests across all IPs exceeding global cap are blocked."""
        limiter = ResearchRateLimiter(per_minute_per_ip=100, per_day_per_ip=100, global_per_day=3)
        self.run_async(limiter.reset())

        self.run_async(limiter.acquire("1.1.1.1"))
        self.run_async(limiter.acquire("2.2.2.2"))
        self.run_async(limiter.acquire("3.3.3.3"))

        # 4th request from another new IP exceeds global limit
        allowed, retry_after, reason = self.run_async(limiter.acquire("4.4.4.4"))
        self.assertFalse(allowed)
        self.assertIn("Global daily research", reason)

    def test_rate_limiter_concurrency_safety(self):
        """Verify that concurrent requests safely increment counters without race conditions."""
        limiter = ResearchRateLimiter(per_minute_per_ip=20, per_day_per_ip=50, global_per_day=100)
        self.run_async(limiter.reset())

        async def make_requests():
            tasks = [limiter.acquire("198.51.100.50") for _ in range(25)]
            results = await asyncio.gather(*tasks)
            return results

        results = self.run_async(make_requests())
        allowed_count = sum(1 for (allowed, _, _) in results if allowed)
        denied_count = sum(1 for (allowed, _, _) in results if not allowed)

        self.assertEqual(allowed_count, 20)
        self.assertEqual(denied_count, 5)

    # -----------------------------------------------------------------
    # 8. Client IP Extraction & Anti-Spoofing
    # -----------------------------------------------------------------
    def test_get_client_ip_does_not_trust_untrusted_forwarded_for(self):
        """Verify that X-Forwarded-For is ignored when request comes from untrusted client."""
        mock_req = MagicMock()
        mock_req.client.host = "203.0.113.10"
        mock_req.headers = {"x-forwarded-for": "10.0.0.1, 1.1.1.1"}

        # Untrusted client: should return direct connection IP, NOT the header
        ip = get_client_ip(mock_req, trusted_proxies=[])
        self.assertEqual(ip, "203.0.113.10")

    def test_get_client_ip_trusts_configured_proxy(self):
        """Verify that X-Forwarded-For is respected ONLY when connection comes from trusted proxy."""
        mock_req = MagicMock()
        mock_req.client.host = "10.0.0.5"  # Trusted internal load balancer
        mock_req.headers = {"x-forwarded-for": "198.51.100.77, 10.0.0.5"}

        ip = get_client_ip(mock_req, trusted_proxies=["10.0.0.5"])
        self.assertEqual(ip, "198.51.100.77")

    # -----------------------------------------------------------------
    # 9. Gemini Quota Protection Controls
    # -----------------------------------------------------------------
    def test_gemini_quota_protection_controls(self):
        """Verify Gemini quota protection enforces limits on max calls and daily budget."""
        quota = GeminiQuotaProtection(
            max_calls_per_request=1,
            max_input_chars=100,
            max_daily_requests=2,
            retry_on_quota=False,
        )
        self.run_async(quota.reset())

        # Check call allowance
        can_call, _ = self.run_async(quota.can_call())
        self.assertTrue(can_call)

        self.run_async(quota.record_call())
        self.run_async(quota.record_call())

        # Daily budget exhausted
        can_call, reason = self.run_async(quota.can_call())
        self.assertFalse(can_call)
        self.assertIn("quota limit reached", reason)

        # Truncation check
        long_prompt = "A" * 200
        truncated = quota.sanitize_prompt_length(long_prompt)
        self.assertEqual(len(truncated), 100)
        self.assertFalse(quota.retry_on_quota)

    # -----------------------------------------------------------------
    # 10. FastAPI Research Endpoint Integration: Rate Limit & Body Limit
    # -----------------------------------------------------------------
    def test_fastapi_research_endpoint_rate_limit_and_payload_cap(self):
        """Verify that HTTP POST /api/v1/research returns 429 when rate limited and 413 on huge body."""
        from app.services.research import gemini_research_service, build_research_result, ResearchStatus

        mock_result = build_research_result(
            app_name="Linear",
            website_or_domain="linear.app",
            status=ResearchStatus.COMPLETED,
            parsed_data={"supports_oauth": True, "summary": "Linear mock"},
            citations=[],
            search_queries=[],
            composio_status=None,
        )

        async def run_endpoint_checks():
            # Reset rate limiter
            await research_rate_limiter.reset()

            with patch.object(gemini_research_service, "research_app", AsyncMock(return_value=mock_result)):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://testserver",
                ) as client:
                    # 1. Huge body check: Content-Length > MAX_REQUEST_BODY_BYTES (10240)
                    resp_huge = await client.post(
                        "/api/v1/research",
                        content=b'{"app_name": "Test"}',
                        headers={"content-length": "500000", "content-type": "application/json"},
                    )
                    self.assertEqual(resp_huge.status_code, 413)
                    self.assertIn("too large", resp_huge.json()["detail"].lower())

                    # 2. Trigger 429 rate limit
                    # Rate limit is 5 per minute per IP
                    # Exceed it by performing 6 calls
                    for i in range(5):
                        resp = await client.post("/api/v1/research", json={"app_name": "Linear"})
                        self.assertEqual(resp.status_code, 200)

                    # 6th call must return 429
                    resp_rate = await client.post("/api/v1/research", json={"app_name": "Linear"})
                    self.assertEqual(resp_rate.status_code, 429)
                    self.assertIn("Retry-After", resp_rate.headers)

            # Reset rate limiter after test
            await research_rate_limiter.reset()

        self.run_async(run_endpoint_checks())


if __name__ == "__main__":
    unittest.main(verbosity=2)
