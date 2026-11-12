import sys
import os
import unittest
import asyncio
from typing import Dict, Any
import httpx
from fastapi import HTTPException

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app
from app.core.config import settings
from app.models.connection import ConnectionStartRequest
from app.services.composio_connection import (
    ComposioConnectionService,
    composio_connection_service,
)


class TestComposioConnections(unittest.TestCase):
    def run_async(self, coro):
        return asyncio.run(coro)

    def setUp(self):
        self._orig_key = settings.COMPOSIO_API_KEY
        self._orig_shopify_config = settings.COMPOSIO_SHOPIFY_AUTH_CONFIG_ID
        settings.COMPOSIO_API_KEY = "mock_composio_api_key_test_12345"
        settings.COMPOSIO_SHOPIFY_AUTH_CONFIG_ID = None

    def tearDown(self):
        settings.COMPOSIO_API_KEY = self._orig_key
        settings.COMPOSIO_SHOPIFY_AUTH_CONFIG_ID = self._orig_shopify_config
        composio_connection_service._client = None

    # -------------------------------------------------------------------------
    # 1. Managed Auth Config Lookup & Link Creation
    # -------------------------------------------------------------------------
    def test_01_managed_auth_config_lookup_slack(self):
        """Verify managed auth config discovery for Slack."""
        def handler(req: httpx.Request):
            self.assertEqual(req.headers.get("x-api-key"), "mock_composio_api_key_test_12345")
            if "auth_configs" in req.url.path:
                return httpx.Response(
                    200,
                    json={
                        "items": [
                            {
                                "id": "ac_slack_managed_001",
                                "status": "ENABLED",
                                "is_composio_managed": True,
                                "toolkit": {"slug": "slack"},
                            }
                        ]
                    },
                )
            return httpx.Response(404)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        cfg = self.run_async(service.get_or_create_auth_config("slack"))
        self.assertEqual(cfg["id"], "ac_slack_managed_001")
        self.assertFalse(cfg["is_custom_auth"])

    def test_02_slack_connection_link_creation(self):
        """Verify creating an authorization link for Slack."""
        def handler(req: httpx.Request):
            if req.url.path.endswith("/auth_configs"):
                return httpx.Response(
                    200,
                    json={
                        "items": [
                            {
                                "id": "ac_slack_managed_001",
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
                self.assertEqual(body["auth_config_id"], "ac_slack_managed_001")
                self.assertEqual(body["user_id"], "usr_session_123")
                return httpx.Response(
                    201,
                    json={
                        "redirect_url": "https://connect.composio.dev/link/lk_slack_mock",
                        "connected_account_id": "ca_slack_001",
                        "expires_at": "2026-11-13T12:00:00Z",
                    },
                )
            return httpx.Response(404)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        res = self.run_async(
            service.create_connection_link(
                toolkit_slug="slack",
                user_id="usr_session_123",
                alias="My Slack Team",
                callback_url="https://oauthnavigator.vercel.app/workspace",
            )
        )
        self.assertEqual(res.redirect_url, "https://connect.composio.dev/link/lk_slack_mock")
        self.assertEqual(res.connected_account_id, "ca_slack_001")
        self.assertEqual(res.toolkit_slug, "slack")
        self.assertFalse(res.is_custom_auth)

    def test_03_gmail_connection_link_creation(self):
        """Verify creating an authorization link for Gmail."""
        def handler(req: httpx.Request):
            if req.url.path.endswith("/auth_configs"):
                return httpx.Response(
                    200,
                    json={
                        "items": [
                            {
                                "id": "ac_gmail_managed_002",
                                "status": "ENABLED",
                                "is_composio_managed": True,
                                "toolkit": {"slug": "gmail"},
                            }
                        ]
                    },
                )
            if req.url.path.endswith("/connected_accounts/link"):
                return httpx.Response(
                    201,
                    json={
                        "redirect_url": "https://connect.composio.dev/link/lk_gmail_mock",
                        "connected_account_id": "ca_gmail_002",
                        "expires_at": "2026-11-13T12:00:00Z",
                    },
                )
            return httpx.Response(404)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        res = self.run_async(
            service.create_connection_link(
                toolkit_slug="gmail",
                user_id="usr_session_456",
            )
        )
        self.assertEqual(res.redirect_url, "https://connect.composio.dev/link/lk_gmail_mock")
        self.assertEqual(res.connected_account_id, "ca_gmail_002")
        self.assertEqual(res.toolkit_slug, "gmail")

    # -------------------------------------------------------------------------
    # 2. Shopify Custom OAuth Fallback
    # -------------------------------------------------------------------------
    def test_04_shopify_custom_auth_fallback_unconfigured(self):
        """Verify that Shopify rejects start when custom auth config is not provided."""
        settings.COMPOSIO_SHOPIFY_AUTH_CONFIG_ID = None
        service = ComposioConnectionService()
        with self.assertRaises(HTTPException) as ctx:
            self.run_async(
                service.create_connection_link(
                    toolkit_slug="shopify",
                    user_id="usr_session_123",
                )
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Shopify does not provide Composio-managed credentials", ctx.exception.detail)

    def test_05_shopify_custom_auth_configured_success(self):
        """Verify that Shopify succeeds when COMPOSIO_SHOPIFY_AUTH_CONFIG_ID is set."""
        settings.COMPOSIO_SHOPIFY_AUTH_CONFIG_ID = "ac_shopify_custom_999"

        def handler(req: httpx.Request):
            if req.url.path.endswith("/auth_configs/ac_shopify_custom_999"):
                return httpx.Response(
                    200,
                    json={"id": "ac_shopify_custom_999", "toolkit": {"slug": "shopify"}},
                )
            if req.url.path.endswith("/connected_accounts/link"):
                return httpx.Response(
                    201,
                    json={
                        "redirect_url": "https://connect.composio.dev/link/lk_shopify_mock",
                        "connected_account_id": "ca_shopify_003",
                        "expires_at": "2026-11-13T12:00:00Z",
                    },
                )
            return httpx.Response(404)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        res = self.run_async(
            service.create_connection_link(
                toolkit_slug="shopify",
                user_id="usr_session_123",
            )
        )
        self.assertEqual(res.connected_account_id, "ca_shopify_003")
        self.assertTrue(res.is_custom_auth)

    # -------------------------------------------------------------------------
    # 3. Error Handling: Missing Key, Timeouts, 4xx/5xx
    # -------------------------------------------------------------------------
    def test_06_missing_api_key_raises_503(self):
        """Verify that missing API key raises 503 Service Unavailable."""
        settings.COMPOSIO_API_KEY = ""
        service = ComposioConnectionService()
        with self.assertRaises(HTTPException) as ctx:
            self.run_async(service.get_or_create_auth_config("slack"))
        self.assertEqual(ctx.exception.status_code, 503)

    def test_07_invalid_api_key_401_raises_502(self):
        """Verify that 401 from Composio raises 502 with helpful detail."""
        def handler(req: httpx.Request):
            return httpx.Response(401, json={"error": "Unauthorized"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        with self.assertRaises(HTTPException) as ctx:
            self.run_async(service.get_or_create_auth_config("slack"))
        self.assertEqual(ctx.exception.status_code, 502)
        self.assertIn("Composio API authentication failed", ctx.exception.detail)

    def test_08_composio_api_timeout_raises_504(self):
        """Verify timeout contacting Composio raises 504 Gateway Timeout."""
        def handler(req: httpx.Request):
            raise httpx.TimeoutException("Mock upstream timeout")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        with self.assertRaises(HTTPException) as ctx:
            self.run_async(service.get_or_create_auth_config("slack"))
        self.assertEqual(ctx.exception.status_code, 504)

    def test_09_composio_rate_limit_429_raises_429(self):
        """Verify 429 rate limit is propagated to caller."""
        def handler(req: httpx.Request):
            return httpx.Response(429, json={"error": "Rate limit exceeded"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        with self.assertRaises(HTTPException) as ctx:
            self.run_async(service.get_or_create_auth_config("slack"))
        self.assertEqual(ctx.exception.status_code, 429)

    # -------------------------------------------------------------------------
    # 4. Status Lifecycle (ACTIVE, INITIALIZING, FAILED) & Ownership Validation
    # -------------------------------------------------------------------------
    def test_10_connection_status_active(self):
        """Verify retrieving an active connected account."""
        def handler(req: httpx.Request):
            return httpx.Response(
                200,
                json={
                    "id": "ca_active_01",
                    "user_id": "usr_session_123",
                    "toolkit": {"slug": "slack"},
                    "status": "ACTIVE",
                    "status_reason": None,
                    "created_at": "2026-11-12T10:00:00Z",
                    "updated_at": "2026-11-12T10:05:00Z",
                    "secret_token": "SHOULD_BE_REDACTED",
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        account = self.run_async(service.get_connected_account("ca_active_01", "usr_session_123"))
        self.assertEqual(account.id, "ca_active_01")
        self.assertEqual(account.status, "ACTIVE")
        self.assertEqual(account.toolkit_slug, "slack")

    def test_11_connection_status_initializing(self):
        """Verify retrieving an initializing connection awaiting user OAuth."""
        def handler(req: httpx.Request):
            return httpx.Response(
                200,
                json={
                    "id": "ca_init_01",
                    "user_id": "usr_session_123",
                    "toolkit": {"slug": "gmail"},
                    "status": "INITIALIZING",
                    "status_reason": "Awaiting authorization in Google consent screen",
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        account = self.run_async(service.get_connected_account("ca_init_01", "usr_session_123"))
        self.assertEqual(account.status, "INITIALIZING")
        self.assertEqual(account.toolkit_slug, "gmail")

    def test_12_connection_status_failed(self):
        """Verify retrieving a failed connection captures the reason."""
        def handler(req: httpx.Request):
            return httpx.Response(
                200,
                json={
                    "id": "ca_failed_01",
                    "user_id": "usr_session_123",
                    "toolkit": {"slug": "slack"},
                    "status": "FAILED",
                    "status_reason": "User denied requested permissions in Slack dialog",
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        account = self.run_async(service.get_connected_account("ca_failed_01", "usr_session_123"))
        self.assertEqual(account.status, "FAILED")
        self.assertIn("User denied", account.status_reason)

    def test_13_ownership_validation_rejects_cross_tenant_access(self):
        """Verify that retrieving another user's connected account is blocked with 404."""
        def handler(req: httpx.Request):
            return httpx.Response(
                200,
                json={
                    "id": "ca_other_user",
                    "user_id": "different_victim_user_id",
                    "toolkit": {"slug": "slack"},
                    "status": "ACTIVE",
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        with self.assertRaises(HTTPException) as ctx:
            self.run_async(service.get_connected_account("ca_other_user", "attacker_user_session"))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_14_secret_redaction_in_models(self):
        """Verify that credentials and tokens are strictly excluded from response model."""
        def handler(req: httpx.Request):
            return httpx.Response(
                200,
                json={
                    "id": "ca_leak_test",
                    "user_id": "usr_safe_1",
                    "toolkit": {"slug": "slack"},
                    "status": "ACTIVE",
                    "credentials": {"token": "mock-oauth-token-dummy", "client_secret": "sensitive-123"},
                    "state": {"raw_auth": "should-never-leak"},
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        account = self.run_async(service.get_connected_account("ca_leak_test", "usr_safe_1"))
        model_dict = account.model_dump()
        self.assertNotIn("credentials", model_dict)
        self.assertNotIn("state", model_dict)
        self.assertNotIn("token", model_dict)
        self.assertNotIn("client_secret", model_dict)

    # -------------------------------------------------------------------------
    # 5. Full FastAPI ASGI HTTP Integration Test
    # -------------------------------------------------------------------------
    def test_15_fastapi_http_endpoints_round_trip(self):
        """Verify HTTP endpoints using ASGI transport."""
        async def _test():
            def handler(req: httpx.Request):
                if req.url.path.endswith("/auth_configs"):
                    return httpx.Response(
                        200,
                        json={
                            "items": [
                                {
                                    "id": "ac_slack_asgi_1",
                                    "status": "ENABLED",
                                    "is_composio_managed": True,
                                    "toolkit": {"slug": "slack"},
                                }
                            ]
                        },
                    )
                if req.url.path.endswith("/connected_accounts/link"):
                    return httpx.Response(
                        201,
                        json={
                            "redirect_url": "https://connect.composio.dev/link/lk_asgi",
                            "connected_account_id": "ca_asgi_01",
                            "expires_at": "2026-11-13T15:00:00Z",
                        },
                    )
                if req.url.path.endswith("/connected_accounts/ca_asgi_01"):
                    return httpx.Response(
                        200,
                        json={
                            "id": "ca_asgi_01",
                            "user_id": "usr_asgi_test",
                            "toolkit": {"slug": "slack"},
                            "status": "ACTIVE",
                        },
                    )
                if "/connected_accounts?user_ids=usr_asgi_test" in str(req.url):
                    return httpx.Response(
                        200,
                        json={"items": []},
                    )
                return httpx.Response(404)

            composio_connection_service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                # 1. Start connection (new connection created)
                res_start = await client.post(
                    "/api/v1/connections/slack/start",
                    json={"user_id": "usr_asgi_test", "alias": "My Slack"},
                )
                self.assertEqual(res_start.status_code, 200)
                data_start = res_start.json()
                self.assertEqual(data_start["connected_account_id"], "ca_asgi_01")
                self.assertEqual(data_start["redirect_url"], "https://connect.composio.dev/link/lk_asgi")
                self.assertEqual(data_start["status"], "INITIATED")

                # 2. Get connection status
                res_get = await client.get(
                    "/api/v1/connections/ca_asgi_01",
                    headers={"X-User-ID": "usr_asgi_test"},
                )
                self.assertEqual(res_get.status_code, 200)
                data_get = res_get.json()
                self.assertEqual(data_get["status"], "ACTIVE")

                # 3. List connections
                res_list = await client.get(
                    "/api/v1/connections",
                    headers={"X-User-ID": "usr_asgi_test"},
                )
                self.assertEqual(res_list.status_code, 200)
                data_list = res_list.json()
                self.assertIsInstance(data_list["items"], list)

                # 4. Shopify status check
                res_shop = await client.get("/api/v1/connections/shopify/status")
                self.assertEqual(res_shop.status_code, 200)
                data_shop = res_shop.json()
                self.assertIn("Shopify requires Custom OAuth", data_shop["setup_instructions"])

        self.run_async(_test())

    # -------------------------------------------------------------------------
    # 6. Specific OAuth Lifecycle & Duplicate Alias Regression Tests
    # -------------------------------------------------------------------------
    def test_16_regression_connect_gmail_successfully(self):
        """Regression 1: Connect Gmail successfully returns Connect Link."""
        def handler(req: httpx.Request):
            if req.url.path.endswith("/auth_configs"):
                return httpx.Response(200, json={"items": [{"id": "ac_gmail_1", "status": "ENABLED", "is_composio_managed": True, "toolkit": {"slug": "gmail"}}]})
            if req.url.path.endswith("/connected_accounts/link"):
                return httpx.Response(201, json={"redirect_url": "https://connect.composio.dev/link/lk_gmail", "connected_account_id": "ca_gmail_100", "expires_at": "2026-11-13T12:00:00Z"})
            if "connected_accounts" in req.url.path:
                return httpx.Response(200, json={"items": []})
            return httpx.Response(404)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        res = self.run_async(service.create_connection_link(toolkit_slug="gmail", user_id="usr_stable_user_1"))
        self.assertEqual(res.status, "INITIATED")
        self.assertEqual(res.connected_account_id, "ca_gmail_100")
        self.assertEqual(res.redirect_url, "https://connect.composio.dev/link/lk_gmail")
        self.assertFalse(res.already_active)

    def test_17_regression_connect_slack_with_same_user_id_no_alias_collision(self):
        """Regression 2: Connect Slack using the same user ID does not collide with Gmail alias."""
        seen_aliases = []
        def handler(req: httpx.Request):
            import json
            if req.url.path.endswith("/auth_configs"):
                return httpx.Response(200, json={"items": [{"id": "ac_slack_1", "status": "ENABLED", "is_composio_managed": True, "toolkit": {"slug": "slack"}}]})
            if req.url.path.endswith("/connected_accounts/link"):
                body = json.loads(req.content.decode())
                seen_aliases.append(body.get("alias"))
                return httpx.Response(201, json={"redirect_url": "https://connect.composio.dev/link/lk_slack", "connected_account_id": "ca_slack_200", "expires_at": "2026-11-13T12:00:00Z"})
            if "connected_accounts" in req.url.path:
                # Simulates existing Gmail account with older alias
                return httpx.Response(200, json={"items": [{"id": "ca_gmail_100", "toolkit": {"slug": "gmail"}, "status": "ACTIVE", "user_id": "usr_stable_user_1", "alias": "Session usr_stab"}]})
            return httpx.Response(404)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        # Even if frontend sent older "Session ..." alias, service replaces or sanitizes it
        res = self.run_async(service.create_connection_link(toolkit_slug="slack", user_id="usr_stable_user_1", alias="Session usr_stab"))
        self.assertEqual(res.status, "INITIATED")
        self.assertEqual(res.connected_account_id, "ca_slack_200")
        # Ensure alias sent to Composio was unique and NOT "Session usr_stab"
        self.assertEqual(len(seen_aliases), 1)
        self.assertNotEqual(seen_aliases[0], "Session usr_stab")
        self.assertTrue(seen_aliases[0].startswith("slack_"))

    def test_18_regression_connect_gmail_again_detects_existing_active(self):
        """Regression 3: Connecting Gmail again detects existing ACTIVE connection, preventing duplicate."""
        link_called = []
        def handler(req: httpx.Request):
            if req.url.path.endswith("/connected_accounts/link"):
                link_called.append(True)
                return httpx.Response(201, json={})
            if "connected_accounts" in req.url.path:
                return httpx.Response(200, json={"items": [
                    {"id": "ca_gmail_active_99", "toolkit": {"slug": "gmail"}, "status": "ACTIVE", "user_id": "usr_stable_user_1", "alias": "gmail_alias_1"}
                ]})
            return httpx.Response(404)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        res = self.run_async(service.create_connection_link(toolkit_slug="gmail", user_id="usr_stable_user_1", force_new=False))
        self.assertTrue(res.already_active)
        self.assertEqual(res.status, "ACTIVE")
        self.assertEqual(res.connected_account_id, "ca_gmail_active_99")
        self.assertIsNone(res.redirect_url)
        # Link endpoint was NOT called
        self.assertEqual(len(link_called), 0)

    def test_19_regression_reconnect_slack_after_earlier_failure(self):
        """Regression 4: Reconnecting Slack after earlier failure with force_new=True generates fresh link."""
        link_created = []
        def handler(req: httpx.Request):
            if req.url.path.endswith("/auth_configs"):
                return httpx.Response(200, json={"items": [{"id": "ac_slack_1", "status": "ENABLED", "is_composio_managed": True, "toolkit": {"slug": "slack"}}]})
            if req.url.path.endswith("/connected_accounts/link"):
                link_created.append(True)
                return httpx.Response(201, json={"redirect_url": "https://connect.composio.dev/link/lk_fresh_slack", "connected_account_id": "ca_slack_fresh", "expires_at": "2026-11-13T12:00:00Z"})
            if "connected_accounts" in req.url.path:
                return httpx.Response(200, json={"items": [
                    {"id": "ca_slack_failed_old", "toolkit": {"slug": "slack"}, "status": "FAILED", "status_reason": "App unauthorized", "user_id": "usr_stable_user_1"}
                ]})
            return httpx.Response(404)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        res = self.run_async(service.create_connection_link(toolkit_slug="slack", user_id="usr_stable_user_1", force_new=True))
        self.assertEqual(res.status, "INITIATED")
        self.assertEqual(res.connected_account_id, "ca_slack_fresh")
        self.assertEqual(res.redirect_url, "https://connect.composio.dev/link/lk_fresh_slack")
        self.assertTrue(len(link_created) == 1)

    def test_20_regression_retry_after_expired_connect_link(self):
        """Regression 5: Retrying after an expired Connect Link succeeds with new link."""
        def handler(req: httpx.Request):
            if req.url.path.endswith("/auth_configs"):
                return httpx.Response(200, json={"items": [{"id": "ac_slack_1", "status": "ENABLED", "is_composio_managed": True, "toolkit": {"slug": "slack"}}]})
            if req.url.path.endswith("/connected_accounts/link"):
                return httpx.Response(201, json={"redirect_url": "https://connect.composio.dev/link/lk_renewed", "connected_account_id": "ca_slack_renewed", "expires_at": "2026-11-13T12:00:00Z"})
            if "connected_accounts" in req.url.path:
                return httpx.Response(200, json={"items": [
                    {"id": "ca_slack_expired", "toolkit": {"slug": "slack"}, "status": "EXPIRED", "user_id": "usr_stable_user_1"}
                ]})
            return httpx.Response(404)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        res = self.run_async(service.create_connection_link(toolkit_slug="slack", user_id="usr_stable_user_1", force_new=False))
        # Since status was EXPIRED (not ACTIVE), it creates a new link
        self.assertEqual(res.status, "INITIATED")
        self.assertEqual(res.connected_account_id, "ca_slack_renewed")
        self.assertFalse(res.already_active)

    def test_21_regression_provider_isolation_gmail_and_slack_do_not_share_status(self):
        """Regression 6: Verifies provider isolation - Gmail active connection does not bleed into Slack."""
        def handler(req: httpx.Request):
            if "connected_accounts" in req.url.path:
                return httpx.Response(200, json={"items": [
                    {"id": "ca_gmail_act", "toolkit": {"slug": "gmail"}, "status": "ACTIVE", "user_id": "usr_iso_user", "alias": "gmail_alias"},
                    {"id": "ca_slack_exp", "toolkit": {"slug": "slack"}, "status": "EXPIRED", "user_id": "usr_iso_user", "alias": "slack_alias"},
                ]})
            return httpx.Response(404)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)

        # 1. Gmail active lookup
        gmail_active = self.run_async(service.find_active_connection(user_id="usr_iso_user", toolkit_slug="gmail"))
        self.assertIsNotNone(gmail_active)
        self.assertEqual(gmail_active.toolkit_slug, "gmail")
        self.assertEqual(gmail_active.id, "ca_gmail_act")

        # 2. Slack active lookup returns None (even though Gmail is ACTIVE)
        slack_active = self.run_async(service.find_active_connection(user_id="usr_iso_user", toolkit_slug="slack"))
        self.assertIsNone(slack_active)

        # 3. Filtered list by toolkit
        gmail_list = self.run_async(service.list_user_connections(user_id="usr_iso_user", toolkit_slug="gmail"))
        self.assertEqual(gmail_list.total_items, 1)
        self.assertEqual(gmail_list.items[0].toolkit_slug, "gmail")

        slack_list = self.run_async(service.list_user_connections(user_id="usr_iso_user", toolkit_slug="slack"))
        self.assertEqual(slack_list.total_items, 1)
        self.assertEqual(slack_list.items[0].toolkit_slug, "slack")

    def test_22_regression_alias_collision_avoidance(self):
        """Regression 7: Alias collision avoidance appends unique salt when requested alias already exists."""
        requested_alias = "my_custom_alias"
        alias_sent = []
        def handler(req: httpx.Request):
            import json
            if req.url.path.endswith("/auth_configs"):
                return httpx.Response(200, json={"items": [{"id": "ac_slack_1", "status": "ENABLED", "is_composio_managed": True, "toolkit": {"slug": "slack"}}]})
            if req.url.path.endswith("/connected_accounts/link"):
                body = json.loads(req.content.decode())
                alias_sent.append(body.get("alias"))
                return httpx.Response(201, json={"redirect_url": "https://connect.composio.dev/link/lk_test", "connected_account_id": "ca_test", "expires_at": "2026-11-13T12:00:00Z"})
            if "connected_accounts" in req.url.path:
                return httpx.Response(200, json={"items": [
                    {"id": "ca_existing", "toolkit": {"slug": "slack"}, "status": "EXPIRED", "user_id": "usr_alias_user", "alias": "my_custom_alias"}
                ]})
            return httpx.Response(404)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        service = ComposioConnectionService(client=client)
        res = self.run_async(service.create_connection_link(toolkit_slug="slack", user_id="usr_alias_user", alias="my_custom_alias"))
        self.assertEqual(len(alias_sent), 1)
        self.assertNotEqual(alias_sent[0], "my_custom_alias")
        self.assertTrue(alias_sent[0].startswith("my_custom_alias_"))


if __name__ == "__main__":
    unittest.main()
