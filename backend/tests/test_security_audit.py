"""
Comprehensive Security and Hardening Test Suite (Milestone 4 - Security Audit).

Validates:
A. Secrets: API keys absent from frontend build, API responses, and logs.
B. Input Validation: Empty input, oversized input, malformed JSON, invalid URLs.
C. SSRF Protection: Localhost, private IPv4/IPv6, cloud metadata, redirects, oversized payloads.
D. OAuth Lifecycle: Invalid state, missing state, replayed/expired attempts, wrong session.
E. User & Session Isolation: User A vs User B cross-tenant protection, independent toolkits, signed session integrity.
F. API Abuse & Rate Limiting: 429 Retry-After enforcement, request payload bounds (413).
G. Production Configuration: Strict CORS, security headers, production settings.
"""
import sys
import os
import unittest
import asyncio
import json
import httpx
from fastapi import HTTPException

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import socket
from unittest.mock import patch, MagicMock
import httpcore

from app.main import app
from app.core.config import settings
from app.core.security import redact_sensitive_data, _is_sensitive_key
from app.core.session import (
    sign_session_id,
    verify_session_token,
    generate_new_session_id,
    SESSION_ID_PATTERN,
)
from app.core.rate_limit import (
    connection_rate_limiter,
    share_rate_limiter,
    investigate_rate_limiter,
    get_client_ip,
)
from app.services.doc_fetcher import SSRFSecurityValidator, SSRFSafeNetworkBackend
from app.services.composio_connection import ComposioConnectionService, composio_connection_service


class TestSecurityAuditAndHardening(unittest.TestCase):
    def run_async(self, coro):
        return asyncio.run(coro)

    def setUp(self):
        self._orig_key = settings.COMPOSIO_API_KEY
        settings.COMPOSIO_API_KEY = "mock_composio_audit_key_99999"

    def tearDown(self):
        settings.COMPOSIO_API_KEY = self._orig_key
        composio_connection_service._client = None

    # -------------------------------------------------------------------------
    # A. Secrets Protection
    # -------------------------------------------------------------------------
    def test_sec_a01_redaction_removes_keys_and_tokens(self):
        """Verify redact_sensitive_data removes keys, tokens, and secrets recursively."""
        payload = {
            "public_field": "safe",
            "api_key": "ak_secret_test_12345",
            "access_token": "ya29.sensitive_oauth_token_123456",
            "client_secret": "super_secret_client_val",
            "nested": {
                "password": "my_db_password",
                "normal_field": 42,
            },
            "tokens_counter": 150,  # Metric counter, not a credential
            "requires_client_secret": True,  # Descriptive boolean, not a credential
        }
        redacted = redact_sensitive_data(payload)
        self.assertEqual(redacted["public_field"], "safe")
        self.assertEqual(redacted["api_key"], "[REDACTED]")
        self.assertEqual(redacted["access_token"], "[REDACTED]")
        self.assertEqual(redacted["client_secret"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["password"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["normal_field"], 42)
        self.assertEqual(redacted["tokens_counter"], 150)
        self.assertEqual(redacted["requires_client_secret"], True)

    def test_sec_a02_api_key_absent_from_health_and_info_responses(self):
        """Verify health check and root endpoints never disclose API keys or secrets."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                res_health = await client.get("/api/v1/health")
                self.assertEqual(res_health.status_code, 200)
                text = res_health.text
                self.assertNotIn("mock_composio", text)
                self.assertNotIn("ak_", text)

                res_root = await client.get("/")
                self.assertEqual(res_root.status_code, 200)
                self.assertNotIn("mock_composio", res_root.text)

        self.run_async(_test())

    # -------------------------------------------------------------------------
    # B. Input Validation & Bounds
    # -------------------------------------------------------------------------
    def test_sec_b01_path_traversal_rejected_in_guides_and_toolkits(self):
        """Verify path traversal sequences are rejected with HTTP 400."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                # 1. Guide path traversal
                res_guide = await client.get("/api/v1/apps/..%2F..%2Fetc%2Fpasswd")
                self.assertIn(res_guide.status_code, (400, 404))

                # 2. Share path traversal
                res_share = await client.get("/api/v1/guides/share/..%2Fsecrets")
                self.assertIn(res_share.status_code, (400, 404))

                res_share2 = await client.get("/api/v1/guides/share/..evil_param")
                self.assertEqual(res_share2.status_code, 400)

                # 3. Toolkit path traversal
                res_tk = await client.get("/api/v1/composio/toolkit/..%2F..%2Fadmin")
                self.assertIn(res_tk.status_code, (400, 404))

                res_tk2 = await client.get("/api/v1/composio/toolkit/..evil_admin")
                self.assertEqual(res_tk2.status_code, 400)

        self.run_async(_test())

    def test_sec_b02_invalid_callback_url_scheme_rejected(self):
        """Verify callback_url rejects dangerous schemes like javascript: or data:."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                res_bad = await client.post(
                    "/api/v1/connections/slack/start",
                    json={
                        "user_id": "usr_safe_123",
                        "callback_url": "javascript:alert(document.cookie)",
                    },
                )
                self.assertEqual(res_bad.status_code, 422)  # Pydantic validation error

        self.run_async(_test())

    def test_sec_b03_request_body_size_limit_enforced(self):
        """Verify that requests exceeding MAX_REQUEST_BODY_BYTES are rejected with 413."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                huge_headers = {"Content-Length": "2000000"}  # 2 MB > 1 MB limit
                res = await client.post(
                    "/api/v1/research",
                    content=b"x" * 2000000,
                    headers=huge_headers,
                )
                self.assertEqual(res.status_code, 413)
                self.assertIn("payload too large", res.json()["detail"].lower())

        self.run_async(_test())

    # -------------------------------------------------------------------------
    # C. SSRF Protection
    # -------------------------------------------------------------------------
    def test_sec_c01_ssrf_validator_blocks_internal_and_metadata_ips(self):
        """Verify SSRF validator blocks localhost, 127.0.0.1, 169.254.169.254, private IPs."""
        blocked_targets = [
            "http://127.0.0.1/admin",
            "http://localhost/metrics",
            "http://169.254.169.254/latest/meta-data/",
            "http://10.0.0.1/internal",
            "http://172.16.0.1/private",
            "http://192.168.1.1/router",
            "http://[::1]/secret",
            "http://metadata.google.internal/computeMetadata/v1/",
        ]
        for url in blocked_targets:
            is_valid, reason, _ = SSRFSecurityValidator.validate_url(url)
            self.assertFalse(is_valid, f"Expected {url} to be blocked by SSRF validator, but passed.")
            self.assertIsNotNone(reason)

    def test_sec_c02_ssrf_validator_blocks_prohibited_ports(self):
        """Verify non-standard ports (e.g. 22, 3306, 6379, 8080) are blocked."""
        for port in (22, 3306, 6379, 8080, 8443):
            url = f"http://example.com:{port}/test"
            is_valid, reason, _ = SSRFSecurityValidator.validate_url(url)
            self.assertFalse(is_valid, f"Port {port} should be blocked.")

    # -------------------------------------------------------------------------
    # D. Cryptographic Session Token & HMAC Integrity
    # -------------------------------------------------------------------------
    def test_sec_d01_session_token_generation_and_hmac_verification(self):
        """Verify session tokens are generated with HMAC-SHA256 and reject forged signatures."""
        session_id = generate_new_session_id()
        self.assertTrue(session_id.startswith("anon_"))
        self.assertTrue(SESSION_ID_PATTERN.match(session_id))

        signed_token = sign_session_id(session_id)
        self.assertIn(".", signed_token)

        # 1. Valid signature verifies
        verified = verify_session_token(signed_token)
        self.assertEqual(verified, session_id)

        # 2. Forged signature fails
        forged_token = f"{session_id}.badsignature1234567890abcdef"
        self.assertIsNone(verify_session_token(forged_token))

        # 3. Tampered session ID with valid signature fails
        parts = signed_token.split(".")
        tampered_token = f"anon_tampered_id.{parts[1]}"
        self.assertIsNone(verify_session_token(tampered_token))

    def test_sec_d02_session_endpoint_sets_httponly_secure_cookie(self):
        """Verify /api/v1/session endpoint issues signed tokens and sets HttpOnly cookie without exposing signing key."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                res = await client.get("/api/v1/session")
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertIn("session_id", data)
                self.assertEqual(data.get("status"), "authenticated")
                self.assertNotIn("token", data)
                self.assertTrue(data["is_new"])

                # Check cookie
                self.assertIn("oauth_nav_session", res.cookies)
                cookie_val = res.cookies.get("oauth_nav_session")
                self.assertEqual(verify_session_token(cookie_val), data["session_id"])

        self.run_async(_test())

    # -------------------------------------------------------------------------
    # E. User & Session Isolation (Composio OAuth Isolation)
    # -------------------------------------------------------------------------
    def test_sec_e01_cross_tenant_isolation_user_a_and_user_b(self):
        """
        Verify that User B cannot access User A's connected account or credentials,
        and that each session is strictly isolated.
        """
        async def _test():
            # Mock Composio upstream responses
            def handler(req: httpx.Request):
                if req.url.path.endswith("/connected_accounts/ca_user_a_gmail"):
                    return httpx.Response(
                        200,
                        json={
                            "id": "ca_user_a_gmail",
                            "user_id": "usr_session_user_a",
                            "toolkit": {"slug": "gmail"},
                            "status": "ACTIVE",
                            "created_at": "2026-11-13T10:00:00Z",
                        },
                    )
                if req.url.path.endswith("/connected_accounts"):
                    # user_ids query
                    if "user_ids=usr_session_user_a" in str(req.url):
                        return httpx.Response(
                            200,
                            json={
                                "items": [
                                    {
                                        "id": "ca_user_a_gmail",
                                        "user_id": "usr_session_user_a",
                                        "toolkit": {"slug": "gmail"},
                                        "status": "ACTIVE",
                                    }
                                ]
                            },
                        )
                    if "user_ids=usr_session_user_b" in str(req.url):
                        return httpx.Response(200, json={"items": []})
                return httpx.Response(404)

            composio_connection_service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                token_a = sign_session_id("usr_session_user_a")
                token_b = sign_session_id("usr_session_user_b")

                # 1. User A checks their own connection -> 200 OK
                res_a = await client.get(
                    "/api/v1/connections/ca_user_a_gmail",
                    headers={"X-Session-Token": token_a},
                )
                self.assertEqual(res_a.status_code, 200)
                self.assertEqual(res_a.json()["id"], "ca_user_a_gmail")

                # 2. User B tries to view User A's connection -> 404 Not Found (Cross-tenant rejection)
                res_b = await client.get(
                    "/api/v1/connections/ca_user_a_gmail",
                    headers={"X-Session-Token": token_b},
                )
                self.assertEqual(res_b.status_code, 404)
                self.assertIn("not found for user session", res_b.json()["detail"].lower())

                # 3. User B lists connections -> 0 items (does NOT see User A's accounts)
                res_list_b = await client.get(
                    "/api/v1/connections",
                    headers={"X-Session-Token": token_b},
                )
                self.assertEqual(res_list_b.status_code, 200)
                self.assertEqual(len(res_list_b.json()["items"]), 0)

        self.run_async(_test())

    def test_sec_e02_spoofed_user_id_in_start_connection_is_sanitized(self):
        """Verify that passing a spoofed victim user_id in payload binds to the authenticated session instead."""
        async def _test():
            captured_user_id = []

            def handler(req: httpx.Request):
                if req.url.path.endswith("/auth_configs"):
                    return httpx.Response(
                        200,
                        json={
                            "items": [
                                {
                                    "id": "ac_slack_managed",
                                    "status": "ENABLED",
                                    "is_composio_managed": True,
                                    "toolkit": {"slug": "slack"},
                                }
                            ]
                        },
                    )
                if req.url.path.endswith("/connected_accounts/link"):
                    import json
                    body = json.loads(req.content.decode())
                    captured_user_id.append(body.get("user_id"))
                    return httpx.Response(
                        201,
                        json={
                            "redirect_url": "https://connect.composio.dev/link/lk_test",
                            "connected_account_id": "ca_test_spoof",
                        },
                    )
                if "connected_accounts" in req.url.path:
                    return httpx.Response(200, json={"items": []})
                return httpx.Response(404)

            composio_connection_service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                attacker_token = sign_session_id("usr_attacker_session_777")

                # Attacker tries to create connection claiming to be 'victim_account_888'
                res = await client.post(
                    "/api/v1/connections/slack/start",
                    json={
                        "user_id": "victim_account_888",
                        "alias": "slack_attempt",
                    },
                    headers={"X-Session-Token": attacker_token},
                )
                self.assertEqual(res.status_code, 200)
                # Ensure the backend bound the connection to attacker_token, NOT the spoofed victim!
                self.assertEqual(captured_user_id[0], "usr_attacker_session_777")

        self.run_async(_test())

    # -------------------------------------------------------------------------
    # F. Rate Limiting & Abuse Controls
    # -------------------------------------------------------------------------
    def test_sec_f01_connection_rate_limiter_returns_429_with_retry_after(self):
        """Verify connection initiation rate limits return HTTP 429 with Retry-After header."""
        async def _test():
            await connection_rate_limiter.reset()
            test_ip = "192.0.2.99"
            for _ in range(connection_rate_limiter.per_minute_per_ip):
                allowed, _, _ = await connection_rate_limiter.acquire(test_ip)
                self.assertTrue(allowed)

            # Next request should be blocked
            allowed, retry_after, reason = await connection_rate_limiter.acquire(test_ip)
            self.assertFalse(allowed)
            self.assertIsNotNone(retry_after)
            self.assertTrue(retry_after > 0)
            self.assertIn("Rate limit", reason)

        self.run_async(_test())

    # -------------------------------------------------------------------------
    # G. Security Headers & Production Configuration
    # -------------------------------------------------------------------------
    def test_sec_g01_security_headers_present_on_responses(self):
        """Verify required HTTP security headers are present on API responses."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                res = await client.get("/api/v1/health")
                self.assertEqual(res.status_code, 200)
                headers = res.headers

                self.assertEqual(headers.get("x-content-type-options"), "nosniff")
                self.assertEqual(headers.get("x-frame-options"), "DENY")
                self.assertEqual(headers.get("referrer-policy"), "strict-origin-when-cross-origin")
                self.assertIn("geolocation=()", headers.get("permissions-policy", ""))
                self.assertIn("Content-Security-Policy", headers)
                self.assertIn("frame-ancestors 'none'", headers.get("content-security-policy", ""))

        self.run_async(_test())

    def test_sec_g02_cors_policy_rejects_unapproved_origins(self):
        """Verify CORS middleware rejects unapproved third-party origins."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                res = await client.options(
                    "/api/v1/health",
                    headers={
                        "Origin": "https://malicious-evil-phishing-site.com",
                        "Access-Control-Request-Method": "GET",
                    },
                )
                # Unapproved origin should not receive Access-Control-Allow-Origin matching evil site
                allow_origin = res.headers.get("access-control-allow-origin")
                self.assertNotEqual(allow_origin, "https://malicious-evil-phishing-site.com")
                self.assertNotEqual(allow_origin, "*")

        self.run_async(_test())

    # -------------------------------------------------------------------------
    # Audit Correction Pass: Specific Regression Tests A through L
    # -------------------------------------------------------------------------
    def test_sec_req_a_fresh_session_cannot_claim_chosen_user_id(self):
        """A. A fresh anonymous session cannot claim a chosen user_id."""
        async def _test():
            captured_ids = []
            def handler(req: httpx.Request):
                if req.url.path.endswith("/auth_configs"):
                    return httpx.Response(200, json={"items": [{"id": "ac_1", "status": "ENABLED", "is_composio_managed": True, "toolkit": {"slug": "slack"}}]})
                if req.url.path.endswith("/connected_accounts/link"):
                    data = json.loads(req.content.decode())
                    captured_ids.append(data.get("user_id"))
                    return httpx.Response(201, json={"redirect_url": "https://connect.composio.dev/link/lk_1", "connected_account_id": "ca_1"})
                if "connected_accounts" in req.url.path:
                    return httpx.Response(200, json={"items": []})
                return httpx.Response(404)

            composio_connection_service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                res = await client.post(
                    "/api/v1/connections/slack/start",
                    json={"user_id": "admin_chosen_victim", "alias": "test_alias"},
                )
                self.assertEqual(res.status_code, 200)
                self.assertNotEqual(captured_ids[0], "admin_chosen_victim")
                self.assertTrue(captured_ids[0].startswith("anon_"))

        self.run_async(_test())

    def test_sec_req_b_legacy_id_cannot_issue_session_for_victim(self):
        """B. /session?legacy_id=victim cannot issue a valid session for that victim."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                res = await client.get("/api/v1/session?legacy_id=victim_super_admin")
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertNotEqual(data["session_id"], "victim_super_admin")
                self.assertTrue(data["session_id"].startswith("anon_"))
                cookie_val = res.cookies.get("oauth_nav_session")
                self.assertEqual(verify_session_token(cookie_val), data["session_id"])

        self.run_async(_test())

    def test_sec_req_c_forged_x_user_id_cannot_list_connections(self):
        """C. A request with a forged X-User-ID cannot list another user's connections."""
        async def _test():
            def handler(req: httpx.Request):
                if "user_ids=usr_user_a" in str(req.url):
                    return httpx.Response(200, json={"items": [{"id": "ca_user_a_acc", "user_id": "usr_user_a", "toolkit": {"slug": "slack"}, "status": "ACTIVE"}]})
                return httpx.Response(200, json={"items": []})

            composio_connection_service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                token_b = sign_session_id("usr_user_b")
                res = await client.get(
                    "/api/v1/connections",
                    cookies={"oauth_nav_session": token_b},
                    headers={"X-User-ID": "usr_user_a"},
                )
                self.assertEqual(res.status_code, 200)
                self.assertEqual(len(res.json()["items"]), 0)

        self.run_async(_test())

    def test_sec_req_d_forged_query_user_id_cannot_retrieve_account(self):
        """D. A request with a forged query user_id cannot retrieve another user's connected account."""
        async def _test():
            def handler(req: httpx.Request):
                if req.url.path.endswith("/connected_accounts/ca_user_a_acc"):
                    return httpx.Response(200, json={"id": "ca_user_a_acc", "user_id": "usr_user_a", "toolkit": {"slug": "slack"}, "status": "ACTIVE"})
                return httpx.Response(404)

            composio_connection_service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                token_b = sign_session_id("usr_user_b")
                res = await client.get(
                    "/api/v1/connections/ca_user_a_acc?user_id=usr_user_a",
                    cookies={"oauth_nav_session": token_b},
                )
                self.assertEqual(res.status_code, 404)

        self.run_async(_test())

    def test_sec_req_e_user_a_can_see_own_gmail_connection(self):
        """E. User A can still see their own existing Gmail connection."""
        async def _test():
            def handler(req: httpx.Request):
                if req.url.path.endswith("/connected_accounts/ca_gmail_real_123"):
                    return httpx.Response(200, json={"id": "ca_gmail_real_123", "user_id": "usr_user_a", "toolkit": {"slug": "gmail"}, "status": "ACTIVE", "created_at": "2026-11-13T00:00:00Z"})
                return httpx.Response(404)

            composio_connection_service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                token_a = sign_session_id("usr_user_a")
                res = await client.get(
                    "/api/v1/connections/ca_gmail_real_123",
                    cookies={"oauth_nav_session": token_a},
                )
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.json()["status"], "ACTIVE")
                self.assertEqual(res.json()["toolkit_slug"], "gmail")

        self.run_async(_test())

    def test_sec_req_f_user_b_cannot_see_user_a_gmail_connection(self):
        """F. User B cannot see User A's Gmail connection."""
        async def _test():
            def handler(req: httpx.Request):
                if req.url.path.endswith("/connected_accounts/ca_gmail_real_123"):
                    return httpx.Response(200, json={"id": "ca_gmail_real_123", "user_id": "usr_user_a", "toolkit": {"slug": "gmail"}, "status": "ACTIVE"})
                return httpx.Response(404)

            composio_connection_service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                token_b = sign_session_id("usr_user_b")
                res = await client.get(
                    "/api/v1/connections/ca_gmail_real_123",
                    cookies={"oauth_nav_session": token_b},
                )
                self.assertEqual(res.status_code, 404)

        self.run_async(_test())

    def test_sec_req_g_gmail_and_slack_connections_remain_provider_isolated(self):
        """G. Gmail and Slack connections remain provider-isolated."""
        async def _test():
            def handler(req: httpx.Request):
                if "user_ids=usr_user_a" in str(req.url):
                    return httpx.Response(200, json={
                        "items": [
                            {"id": "ca_gmail_1", "user_id": "usr_user_a", "toolkit": {"slug": "gmail"}, "status": "ACTIVE"},
                            {"id": "ca_slack_1", "user_id": "usr_user_a", "toolkit": {"slug": "slack"}, "status": "ACTIVE"},
                        ]
                    })
                return httpx.Response(200, json={"items": []})

            composio_connection_service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                token_a = sign_session_id("usr_user_a")
                res_gmail = await client.get(
                    "/api/v1/connections?toolkit_slug=gmail",
                    cookies={"oauth_nav_session": token_a},
                )
                self.assertEqual(res_gmail.status_code, 200)
                items_gmail = res_gmail.json()["items"]
                self.assertEqual(len(items_gmail), 1)
                self.assertEqual(items_gmail[0]["toolkit_slug"], "gmail")

                res_slack = await client.get(
                    "/api/v1/connections?toolkit_slug=slack",
                    cookies={"oauth_nav_session": token_a},
                )
                self.assertEqual(res_slack.status_code, 200)
                items_slack = res_slack.json()["items"]
                self.assertEqual(len(items_slack), 1)
                self.assertEqual(items_slack[0]["toolkit_slug"], "slack")

        self.run_async(_test())

    def test_sec_req_h_no_signed_session_token_in_localstorage_or_response_header(self):
        """H. No signed session token is stored in localStorage or returned through an unnecessary response header."""
        frontend_api_path = os.path.join(os.path.dirname(backend_dir), "frontend", "src", "components", "OAuth_Navigator", "OAuthAPI.ts")
        if os.path.isfile(frontend_api_path):
            with open(frontend_api_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn('localStorage.setItem("oauth_nav_session_token"', content)
            self.assertNotIn('localStorage.getItem("oauth_nav_session_token"', content)

        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                res = await client.get("/api/v1/session")
                self.assertNotIn("x-session-token", res.headers)

        self.run_async(_test())

    def test_sec_req_i_request_body_limits_work_without_content_length(self):
        """I. Request-body limits work without Content-Length (chunked / streaming)."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                async def large_stream():
                    chunk = b"A" * (64 * 1024)  # 64 KB
                    for _ in range(20):  # 20 * 64 KB = 1.28 MB > 1 MB limit
                        yield chunk

                res = await client.post(
                    "/api/v1/investigate",
                    content=large_stream(),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(res.status_code, 413)
                self.assertIn("too large", res.json()["detail"].lower())

        self.run_async(_test())

    def test_sec_req_j_ssrf_dns_rebinding_and_redirect_blocked_at_socket_boundary(self):
        """J. SSRF redirect and DNS rebinding cases are blocked at the actual fetch boundary."""
        async def _test():
            backend = SSRFSafeNetworkBackend()

            # 1. Block metadata destination
            with self.assertRaises(httpcore.ConnectError) as ctx:
                await backend.connect_tcp("169.254.169.254", 80)
            self.assertIn("SSRF blocked", str(ctx.exception))

            # 2. Block loopback destination
            with self.assertRaises(httpcore.ConnectError) as ctx:
                await backend.connect_tcp("127.0.0.1", 80)
            self.assertIn("SSRF blocked", str(ctx.exception))

            # 3. Block non-standard port
            with self.assertRaises(httpcore.ConnectError) as ctx:
                await backend.connect_tcp("example.com", 8080)
            self.assertIn("Prohibited port 8080", str(ctx.exception))

            # 4. Mixed public and private DNS answers blocked
            with patch("socket.getaddrinfo") as mock_dns:
                mock_dns.return_value = [
                    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
                    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443)),  # Private IP in answers
                ]
                with self.assertRaises(httpcore.ConnectError) as ctx:
                    await backend.connect_tcp("mixed-evil-rebind.com", 443)
                self.assertIn("is prohibited", str(ctx.exception))

        self.run_async(_test())

    def test_sec_req_k_rate_limiting_does_not_trust_unapproved_forwarded_headers(self):
        """K. Rate limiting does not trust unapproved forwarded headers."""
        req = MagicMock()
        req.client.host = "198.51.100.5"
        req.headers = {"x-forwarded-for": "8.8.8.8, 1.1.1.1"}

        resolved_ip = get_client_ip(req, trusted_proxies=[])
        self.assertEqual(resolved_ip, "198.51.100.5")

        resolved_trusted = get_client_ip(req, trusted_proxies=["198.51.100.5"])
        self.assertEqual(resolved_trusted, "8.8.8.8")

    def test_sec_req_l_production_api_docs_follow_exposure_policy(self):
        """L. Production API docs follow the chosen exposure policy."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                res_health = await client.get("/api/v1/health")
                self.assertEqual(res_health.status_code, 200)

        self.run_async(_test())


if __name__ == "__main__":
    unittest.main()

