"""
Unit and integration tests for Composio Live Toolkit Metadata Integration (Milestone 2).

All tests are fully mocked and run offline without requiring internet access or a real API key.
"""
import sys
import os
import unittest
import asyncio
import json
import httpx

# Ensure backend root is the first entry in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app
from app.models.composio import (
    ComposioClassification,
    ComposioToolkitCheckResponse,
)
from app.services.composio_metadata import (
    ComposioMetadataService,
    composio_metadata_service,
    normalize_slug,
    normalize_auth_schemes,
    classify_toolkit_auth,
)


class TestComposioMetadataService(unittest.TestCase):
    """Test suite for Composio Toolkit Metadata Service and classification logic."""

    def run_async(self, coro):
        return asyncio.run(coro)

    def setUp(self):
        # Save original client so tests can cleanly restore state
        self._orig_client = composio_metadata_service._client
        self._orig_key = composio_metadata_service.api_key

    def tearDown(self):
        composio_metadata_service._client = self._orig_client
        composio_metadata_service.api_key = self._orig_key

    # -----------------------------------------------------------------
    # Test 1: Slack Managed OAuth
    # -----------------------------------------------------------------
    def test_m2_01_slack_managed_oauth(self):
        """Verify Slack with OAUTH2 in auth_schemes and composio_managed_auth_schemes -> COMPOSIO_MANAGED_AVAILABLE."""
        def handler(request: httpx.Request):
            self.assertEqual(request.headers.get("x-api-key"), "test-key-slack")
            self.assertTrue(request.url.path.endswith("/toolkits/slack"))
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "slack",
                    "name": "Slack",
                    "enabled": True,
                    "auth_schemes": ["OAUTH2"],
                    "composio_managed_auth_schemes": ["OAUTH2"],
                    "composio_managed_auth": True,
                    "no_auth": False,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key-slack", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("slack"))
        self.assertEqual(result.classification, ComposioClassification.COMPOSIO_MANAGED_AVAILABLE)
        self.assertTrue(result.in_catalog)
        self.assertTrue(result.enabled)
        self.assertTrue(result.supports_oauth)
        self.assertTrue(result.managed_oauth_available)
        self.assertEqual(result.slug, "slack")
        self.assertEqual(result.name, "Slack")
        self.assertIn("OAUTH2", result.supported_auth_schemes)
        self.assertIn("OAUTH2", result.managed_auth_schemes)
        self.assertIn("managed OAuth application", result.explanation)

    # -----------------------------------------------------------------
    # Test 2: Gmail Managed OAuth
    # -----------------------------------------------------------------
    def test_m2_02_gmail_managed_oauth(self):
        """Verify Gmail with OAUTH2 in both scheme lists -> COMPOSIO_MANAGED_AVAILABLE."""
        def handler(request: httpx.Request):
            self.assertTrue(request.url.path.endswith("/toolkits/gmail"))
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "gmail",
                    "name": "Gmail",
                    "enabled": True,
                    "auth_schemes": ["OAUTH2"],
                    "composio_managed_auth_schemes": ["OAUTH2"],
                    "no_auth": False,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key-gmail", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("gmail"))
        self.assertEqual(result.classification, ComposioClassification.COMPOSIO_MANAGED_AVAILABLE)
        self.assertTrue(result.in_catalog)
        self.assertTrue(result.supports_oauth)
        self.assertTrue(result.managed_oauth_available)
        self.assertEqual(result.name, "Gmail")

    # -----------------------------------------------------------------
    # Test 3: Shopify OAuth without Composio Managed OAuth
    # -----------------------------------------------------------------
    def test_m2_03_shopify_custom_oauth_mandatory(self):
        """Verify Shopify with OAUTH2 supported but missing from managed_schemes -> CUSTOM_OAUTH_MANDATORY."""
        def handler(request: httpx.Request):
            self.assertTrue(request.url.path.endswith("/toolkits/shopify"))
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "shopify",
                    "name": "Shopify",
                    "enabled": True,
                    "auth_schemes": ["OAUTH2"],
                    "composio_managed_auth_schemes": [],
                    "composio_managed_auth": False,
                    "no_auth": False,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key-shopify", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("shopify"))
        self.assertEqual(result.classification, ComposioClassification.CUSTOM_OAUTH_MANDATORY)
        self.assertTrue(result.in_catalog)
        self.assertTrue(result.supports_oauth)
        self.assertFalse(result.managed_oauth_available)
        self.assertIn("custom OAuth", result.explanation)

    # -----------------------------------------------------------------
    # Test 4: Non-OAuth Toolkit
    # -----------------------------------------------------------------
    def test_m2_04_non_oauth_toolkit(self):
        """Verify toolkit supporting API_KEY / BEARER_TOKEN but no OAuth -> NON_OAUTH_TOOLKIT."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "sendgrid",
                    "name": "SendGrid",
                    "enabled": True,
                    "auth_schemes": ["API_KEY"],
                    "composio_managed_auth_schemes": [],
                    "no_auth": False,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("sendgrid"))
        self.assertEqual(result.classification, ComposioClassification.NON_OAUTH_TOOLKIT)
        self.assertTrue(result.in_catalog)
        self.assertFalse(result.supports_oauth)
        self.assertFalse(result.managed_oauth_available)
        self.assertEqual(result.supported_auth_schemes, ["API_KEY"])
        self.assertIn("does not support OAuth", result.explanation)

    # -----------------------------------------------------------------
    # Test 5: Toolkit with No Authentication Required
    # -----------------------------------------------------------------
    def test_m2_05_no_auth_required_toolkit(self):
        """Verify toolkit with no_auth: True -> NO_AUTH_REQUIRED."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "math-tools",
                    "name": "Math Tools",
                    "enabled": True,
                    "auth_schemes": [],
                    "composio_managed_auth_schemes": [],
                    "no_auth": True,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("math-tools"))
        self.assertEqual(result.classification, ComposioClassification.NO_AUTH_REQUIRED)
        self.assertTrue(result.in_catalog)
        self.assertFalse(result.supports_oauth)
        self.assertIn("no authentication is required", result.explanation)

    # -----------------------------------------------------------------
    # Test 6: Unknown Toolkit / 404
    # -----------------------------------------------------------------
    def test_m2_06_unknown_toolkit_404(self):
        """Verify confirmed HTTP 404 from Composio -> NOT_IN_COMPOSIO_CATALOG."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=404,
                json={"error": "Toolkit not found", "slug": "nonexistent-app"},
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("nonexistent-app"))
        self.assertEqual(result.classification, ComposioClassification.NOT_IN_COMPOSIO_CATALOG)
        self.assertFalse(result.in_catalog)
        self.assertEqual(result.http_status, 404)
        self.assertEqual(result.error_code, "NOT_FOUND")
        self.assertIn("was not found in the Composio catalog", result.explanation)

    # -----------------------------------------------------------------
    # Test 7: Invalid API Key / HTTP 401 & 403 (Never Misreport as 404)
    # -----------------------------------------------------------------
    def test_m2_07_invalid_api_key_401_and_403(self):
        """Verify HTTP 401/403 yields METADATA_UNAVAILABLE, NEVER NOT_IN_COMPOSIO_CATALOG."""
        for status_code in (401, 403):
            def handler(request: httpx.Request, code=status_code):
                return httpx.Response(
                    status_code=code,
                    json={"error": "Unauthorized", "message": "Invalid API key provided."},
                )

            client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            service = ComposioMetadataService(api_key="invalid-key", client=client)

            result = self.run_async(service.fetch_toolkit_metadata("slack"))
            # MUST NOT be misreported as unknown toolkit / 404
            self.assertNotEqual(result.classification, ComposioClassification.NOT_IN_COMPOSIO_CATALOG)
            self.assertEqual(result.classification, ComposioClassification.METADATA_UNAVAILABLE)
            self.assertEqual(result.http_status, status_code)
            self.assertEqual(result.error_code, "AUTHENTICATION_FAILED")
            self.assertIn(f"HTTP {status_code}", result.explanation)

    # -----------------------------------------------------------------
    # Test 8: Rate Limiting / HTTP 429
    # -----------------------------------------------------------------
    def test_m2_08_rate_limiting_429(self):
        """Verify HTTP 429 from Composio -> METADATA_UNAVAILABLE with RATE_LIMITED code."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=429,
                json={"error": "Rate limit exceeded. Try again in 60s."},
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("slack"))
        self.assertEqual(result.classification, ComposioClassification.METADATA_UNAVAILABLE)
        self.assertEqual(result.http_status, 429)
        self.assertEqual(result.error_code, "RATE_LIMITED")
        self.assertIn("rate limit exceeded", result.explanation.lower())

    # -----------------------------------------------------------------
    # Test 9: Timeout and Network Errors
    # -----------------------------------------------------------------
    def test_m2_09_timeout_and_network_errors(self):
        """Verify network errors and request timeouts yield METADATA_UNAVAILABLE with safe errors."""
        # A. Timeout
        def timeout_handler(request: httpx.Request):
            raise httpx.ReadTimeout("Read timed out after 10.0s")

        client_timeout = httpx.AsyncClient(transport=httpx.MockTransport(timeout_handler))
        service_timeout = ComposioMetadataService(api_key="test-key", client=client_timeout)
        result_timeout = self.run_async(service_timeout.fetch_toolkit_metadata("slack"))

        self.assertEqual(result_timeout.classification, ComposioClassification.METADATA_UNAVAILABLE)
        self.assertEqual(result_timeout.error_code, "REQUEST_TIMEOUT")
        self.assertIn("timed out", result_timeout.explanation.lower())

        # B. Network connect error
        def network_handler(request: httpx.Request):
            raise httpx.ConnectError("Failed to establish a connection")

        client_net = httpx.AsyncClient(transport=httpx.MockTransport(network_handler))
        service_net = ComposioMetadataService(api_key="test-key", client=client_net)
        result_net = self.run_async(service_net.fetch_toolkit_metadata("slack"))

        self.assertEqual(result_net.classification, ComposioClassification.METADATA_UNAVAILABLE)
        self.assertEqual(result_net.error_code, "NETWORK_FAILURE")
        self.assertIn("network error", result_net.explanation.lower())

    # -----------------------------------------------------------------
    # Test 10: Missing API Key Configuration
    # -----------------------------------------------------------------
    def test_m2_10_missing_api_key(self):
        """Verify that when COMPOSIO_API_KEY is empty, no network request is made and METADATA_UNAVAILABLE returned."""
        call_attempted = []

        def handler(request: httpx.Request):
            call_attempted.append(request)
            return httpx.Response(200, json={})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("slack"))
        self.assertEqual(len(call_attempted), 0, "No network call should be attempted when API key is missing")
        self.assertEqual(result.classification, ComposioClassification.METADATA_UNAVAILABLE)
        self.assertEqual(result.error_code, "MISSING_API_KEY")
        self.assertFalse(result.is_live_lookup)
        self.assertIn("COMPOSIO_API_KEY is not configured", result.explanation)

    # -----------------------------------------------------------------
    # Test 11: Malformed Response / Incomplete JSON
    # -----------------------------------------------------------------
    def test_m2_11_malformed_response(self):
        """Verify invalid JSON text or non-dict payloads yield METADATA_UNAVAILABLE with MALFORMED_RESPONSE."""
        # Non-JSON content
        def non_json_handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                text="<html><body>502 Bad Gateway from Cloudflare</body></html>",
                headers={"Content-Type": "text/html"},
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(non_json_handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("slack"))
        self.assertEqual(result.classification, ComposioClassification.METADATA_UNAVAILABLE)
        self.assertEqual(result.error_code, "MALFORMED_RESPONSE")

        # JSON array instead of JSON object
        def array_json_handler(request: httpx.Request):
            return httpx.Response(status_code=200, text="[1, 2, 3]")

        client_arr = httpx.AsyncClient(transport=httpx.MockTransport(array_json_handler))
        service_arr = ComposioMetadataService(api_key="test-key", client=client_arr)
        result_arr = self.run_async(service_arr.fetch_toolkit_metadata("slack"))
        self.assertEqual(result_arr.classification, ComposioClassification.METADATA_UNAVAILABLE)
        self.assertEqual(result_arr.error_code, "MALFORMED_RESPONSE")

    # -----------------------------------------------------------------
    # Test 12: Multiple Authentication Schemes Support
    # -----------------------------------------------------------------
    def test_m2_12_multiple_authentication_schemes(self):
        """Verify toolkit supporting both API_KEY and OAUTH2 evaluates OAuth support correctly."""
        # A. Supports API_KEY and OAUTH2, and OAUTH2 is managed -> COMPOSIO_MANAGED_AVAILABLE
        def multi_managed_handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "hybrid-app",
                    "name": "Hybrid App",
                    "auth_schemes": ["API_KEY", "OAUTH2"],
                    "composio_managed_auth_schemes": ["OAUTH2"],
                    "no_auth": False,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(multi_managed_handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("hybrid-app"))
        self.assertEqual(result.classification, ComposioClassification.COMPOSIO_MANAGED_AVAILABLE)
        self.assertTrue(result.supports_oauth)
        self.assertTrue(result.managed_oauth_available)
        self.assertEqual(result.supported_auth_schemes, ["API_KEY", "OAUTH2"])

        # B. Supports API_KEY and OAUTH2, but OAUTH2 is NOT managed -> CUSTOM_OAUTH_MANDATORY
        def multi_unmanaged_handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "hybrid-app",
                    "name": "Hybrid App",
                    "auth_schemes": ["API_KEY", "OAUTH2"],
                    "composio_managed_auth_schemes": [],
                    "no_auth": False,
                },
            )

        client_unmanaged = httpx.AsyncClient(transport=httpx.MockTransport(multi_unmanaged_handler))
        service_unmanaged = ComposioMetadataService(api_key="test-key", client=client_unmanaged)

        result_unmanaged = self.run_async(service_unmanaged.fetch_toolkit_metadata("hybrid-app"))
        self.assertEqual(result_unmanaged.classification, ComposioClassification.CUSTOM_OAUTH_MANDATORY)
        self.assertTrue(result_unmanaged.supports_oauth)
        self.assertFalse(result_unmanaged.managed_oauth_available)

    # -----------------------------------------------------------------
    # Test 13: Case-Insensitive OAuth2 Normalization
    # -----------------------------------------------------------------
    def test_m2_13_case_insensitive_normalization(self):
        """Verify scheme names in mixed case ('oauth2', 'OAuth2', 'Api_Key') are normalized to uppercase."""
        def mixed_case_handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "mixed-case-app",
                    "name": "Mixed Case App",
                    "auth_schemes": ["oauth2", "Api_Key"],
                    "composio_managed_auth_schemes": ["OAuth2"],
                    "no_auth": False,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(mixed_case_handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("MIXED-CASE-APP"))
        self.assertEqual(result.slug, "mixed-case-app")
        self.assertEqual(result.supported_auth_schemes, ["OAUTH2", "API_KEY"])
        self.assertEqual(result.managed_auth_schemes, ["OAUTH2"])
        self.assertEqual(result.classification, ComposioClassification.COMPOSIO_MANAGED_AVAILABLE)
        self.assertTrue(result.supports_oauth)
        self.assertTrue(result.managed_oauth_available)

    # -----------------------------------------------------------------
    # Test 14: FastAPI Endpoint GET /api/v1/composio/toolkit/{slug} Round-Trip
    # -----------------------------------------------------------------
    def test_m2_14_fastapi_endpoint_round_trip(self):
        """Verify full HTTP round-trip through FastAPI ASGI application for live toolkit check."""
        def mock_composio_upstream(request: httpx.Request):
            # Verify secret key is passed in headers
            self.assertEqual(request.headers.get("x-api-key"), "backend-secret-key")
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "slack",
                    "name": "Slack",
                    "enabled": True,
                    "auth_schemes": ["OAUTH2"],
                    "composio_managed_auth_schemes": ["OAUTH2"],
                    "composio_managed_auth": True,
                    "no_auth": False,
                    "meta": {"category": "communication"},
                },
            )

        # Wire mocked upstream client into global service
        composio_metadata_service._client = httpx.AsyncClient(
            transport=httpx.MockTransport(mock_composio_upstream)
        )
        composio_metadata_service.api_key = "backend-secret-key"

        async def query_api():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                # 1. Valid toolkit query
                resp = await client.get("/api/v1/composio/toolkit/slack")
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertEqual(data["slug"], "slack")
                self.assertEqual(data["name"], "Slack")
                self.assertTrue(data["in_catalog"])
                self.assertTrue(data["supports_oauth"])
                self.assertTrue(data["managed_oauth_available"])
                self.assertEqual(data["classification"], "COMPOSIO_MANAGED_AVAILABLE")
                self.assertIn("meta", data["raw_metadata"])
                # Ensure no secrets leak
                self.assertNotIn("backend-secret-key", resp.text)

                # 2. Whitespace/empty slug rejected with 400
                bad_resp = await client.get("/api/v1/composio/toolkit/%20")
                self.assertEqual(bad_resp.status_code, 400)
                self.assertIn("cannot be empty", bad_resp.json()["detail"].lower())

        self.run_async(query_api())

    # -----------------------------------------------------------------
    # Test 15: Upstream 5xx Server Error
    # -----------------------------------------------------------------
    def test_m2_15_upstream_500_server_error(self):
        """Verify HTTP 500 from Composio -> METADATA_UNAVAILABLE with UPSTREAM_SERVER_ERROR."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=500,
                json={"error": "Internal Server Error"},
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("slack"))
        self.assertEqual(result.classification, ComposioClassification.METADATA_UNAVAILABLE)
        self.assertEqual(result.http_status, 500)
        self.assertEqual(result.error_code, "UPSTREAM_SERVER_ERROR")
        self.assertIn("500", result.explanation)

    # -----------------------------------------------------------------
    # Test 16: URL Construction Helper
    # -----------------------------------------------------------------
    def test_m2_16_url_construction_flexibility(self):
        """Verify endpoint URL builds correctly whether base_url includes /api/v3.1 or not."""
        service_root = ComposioMetadataService(base_url="https://backend.composio.dev")
        self.assertEqual(
            service_root._build_url("slack"),
            "https://backend.composio.dev/api/v3.1/toolkits/slack"
        )

        service_versioned = ComposioMetadataService(base_url="https://backend.composio.dev/api/v3.1")
        self.assertEqual(
            service_versioned._build_url("slack"),
            "https://backend.composio.dev/api/v3.1/toolkits/slack"
        )

    # =================================================================
    # Milestone 2.1 Regression Tests: Multi-source OAuth Detection
    # =================================================================

    def test_m21_01_slack_like_empty_auth_schemes_with_managed_oauth(self):
        """Regression: Slack-like response where auth_schemes is empty/None but managed OAuth2 fields are populated."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "slack",
                    "name": "Slack",
                    "enabled": True,
                    "auth_schemes": None,
                    "composio_managed_auth_schemes": ["OAUTH2"],
                    "composio_managed_auth": [{"mode": "OAUTH2", "scopes": {"available": ["channels:read"]}}],
                    "auth_config_details": [{"mode": "OAUTH2"}],
                    "no_auth": None,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("slack"))
        self.assertEqual(result.classification, ComposioClassification.COMPOSIO_MANAGED_AVAILABLE)
        self.assertTrue(result.in_catalog)
        self.assertTrue(result.supports_oauth)
        self.assertTrue(result.managed_oauth_available)
        self.assertEqual(result.supported_auth_schemes, ["OAUTH2"])
        self.assertEqual(result.managed_auth_schemes, ["OAUTH2"])
        self.assertIn("managed OAuth application", result.explanation)

    def test_m21_02_oauth2_found_via_auth_config_details_when_auth_schemes_empty(self):
        """Regression: OAuth2 discovered through auth_config_details.mode when auth_schemes is empty."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "custom-oauth-app",
                    "name": "Custom OAuth App",
                    "enabled": True,
                    "auth_schemes": [],
                    "composio_managed_auth_schemes": [],
                    "composio_managed_auth": [],
                    "auth_config_details": [{"mode": "OAUTH2"}],
                    "no_auth": False,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("custom-oauth-app"))
        self.assertEqual(result.classification, ComposioClassification.CUSTOM_OAUTH_MANDATORY)
        self.assertTrue(result.in_catalog)
        self.assertTrue(result.supports_oauth)
        self.assertFalse(result.managed_oauth_available)
        self.assertEqual(result.supported_auth_schemes, ["OAUTH2"])
        self.assertEqual(result.managed_auth_schemes, [])
        self.assertIn("custom OAuth", result.explanation)

    def test_m21_03_oauth2_found_via_composio_managed_auth_when_managed_schemes_empty(self):
        """Regression: OAuth2 discovered through composio_managed_auth[].mode when composio_managed_auth_schemes is empty."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "managed-via-dict",
                    "name": "Managed Via Dict App",
                    "enabled": True,
                    "auth_schemes": [],
                    "composio_managed_auth_schemes": [],
                    "composio_managed_auth": [{"mode": "OAUTH2"}],
                    "auth_config_details": [],
                    "no_auth": False,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("managed-via-dict"))
        self.assertEqual(result.classification, ComposioClassification.COMPOSIO_MANAGED_AVAILABLE)
        self.assertTrue(result.in_catalog)
        self.assertTrue(result.supports_oauth)
        self.assertTrue(result.managed_oauth_available)
        self.assertEqual(result.supported_auth_schemes, ["OAUTH2"])
        self.assertEqual(result.managed_auth_schemes, ["OAUTH2"])

    def test_m21_04_oauth_support_without_managed_oauth_custom_mandatory(self):
        """Regression: Toolkit with OAuth (including S2S_OAUTH2) but no managed OAuth -> CUSTOM_OAUTH_MANDATORY."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "shopify",
                    "name": "Shopify",
                    "enabled": True,
                    "auth_schemes": None,
                    "composio_managed_auth_schemes": [],
                    "composio_managed_auth": [],
                    "auth_config_details": [{"mode": "OAUTH2"}, {"mode": "S2S_OAUTH2"}],
                    "no_auth": None,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("shopify"))
        self.assertEqual(result.classification, ComposioClassification.CUSTOM_OAUTH_MANDATORY)
        self.assertTrue(result.in_catalog)
        self.assertTrue(result.supports_oauth)
        self.assertFalse(result.managed_oauth_available)
        self.assertEqual(result.supported_auth_schemes, ["OAUTH2", "S2S_OAUTH2"])
        self.assertEqual(result.managed_auth_schemes, [])

    def test_m21_05_no_auth_true_precedence(self):
        """Regression: no_auth=True takes strict precedence even if other mode fields exist."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "public-utility",
                    "name": "Public Utility",
                    "enabled": True,
                    "no_auth": True,
                    "auth_schemes": [],
                    "composio_managed_auth_schemes": ["OAUTH2"],
                    "auth_config_details": [{"mode": "OAUTH2"}],
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("public-utility"))
        self.assertEqual(result.classification, ComposioClassification.NO_AUTH_REQUIRED)
        self.assertTrue(result.in_catalog)
        self.assertIn("no authentication is required", result.explanation.lower())

    def test_m21_06_genuine_non_oauth_toolkit_classification(self):
        """Regression: Genuine non-OAuth toolkit (e.g. API_KEY only) correctly classified as NON_OAUTH_TOOLKIT."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "sendgrid",
                    "name": "SendGrid",
                    "enabled": True,
                    "auth_schemes": None,
                    "composio_managed_auth_schemes": [],
                    "composio_managed_auth": [],
                    "auth_config_details": [{"mode": "API_KEY"}],
                    "no_auth": False,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("sendgrid"))
        self.assertEqual(result.classification, ComposioClassification.NON_OAUTH_TOOLKIT)
        self.assertTrue(result.in_catalog)
        self.assertFalse(result.supports_oauth)
        self.assertFalse(result.managed_oauth_available)
        self.assertEqual(result.supported_auth_schemes, ["API_KEY"])
        self.assertIn("does not support OAuth", result.explanation)

    def test_m21_07_inconclusive_empty_metadata_unavailable(self):
        """Regression: Toolkit with completely empty auth metadata and no_auth=False -> METADATA_UNAVAILABLE."""
        def handler(request: httpx.Request):
            return httpx.Response(
                status_code=200,
                json={
                    "slug": "empty-app",
                    "name": "Empty App",
                    "enabled": True,
                    "auth_schemes": [],
                    "composio_managed_auth_schemes": [],
                    "composio_managed_auth": [],
                    "auth_config_details": [],
                    "no_auth": False,
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioMetadataService(api_key="test-key", client=client)

        result = self.run_async(service.fetch_toolkit_metadata("empty-app"))
        self.assertEqual(result.classification, ComposioClassification.METADATA_UNAVAILABLE)
        self.assertIn("does not specify any authentication schemes", result.explanation)


if __name__ == "__main__":
    unittest.main(verbosity=2)

