"""
Automated Regression Tests for OAuth Flow Corrections:
1. Incognito session continuity (first-party session cookie survival across start -> callback -> status).
2. Separate incognito session isolation (two distinct sessions cannot see or manipulate each other's connections).
3. Lifecycle state machine transitions (pending -> active -> delete/idle).
4. Delete connection ownership enforcement (multi-tenant boundary on disconnect).
5. Root /healthz endpoint verification.
"""
import sys
import os
import unittest
from unittest.mock import patch, AsyncMock

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.services.composio_connection import composio_connection_service
from app.core.session import COOKIE_NAME, sign_session_id, generate_new_session_id


class TestOAuthFlowCorrections(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_healthz_endpoint(self):
        """Verifies root /healthz returns 200 OK for uptime checks and proxy verification."""
        res = self.client.get("/healthz")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "healthy")

    def test_02_incognito_session_continuity(self):
        """
        Simulates an Incognito window: starts with empty cookie jar.
        Initial call to /session establishes first-party HttpOnly cookie.
        Subsequent connection start and status checks retain the exact session identity.
        """
        incognito_client = TestClient(app)

        # 1. First visit in Incognito: GET /api/v1/session
        res_session = incognito_client.get("/api/v1/session")
        self.assertEqual(res_session.status_code, 200)
        session_data = res_session.json()
        session_id = session_data["session_id"]
        self.assertTrue(session_id.startswith("anon_"))

        # Verify HttpOnly cookie was set
        cookie_val = incognito_client.cookies.get(COOKIE_NAME)
        self.assertIsNotNone(cookie_val)
        self.assertTrue(cookie_val.startswith(session_id))

        # 2. Start connection for Gmail using the same incognito session
        mock_composio_resp = {
            "redirect_url": "https://backend.composio.dev/connect/fake_link_123",
            "connected_account_id": "ca_incognito_gmail_01",
            "expires_at": "2026-11-13T20:00:00Z",
            "toolkit_slug": "gmail",
            "alias": "gmail_incog1",
            "is_custom_auth": False,
            "status": "INITIATED",
            "already_active": False,
            "message": "Authorization link generated",
        }

        with patch("app.services.composio_connection.composio_connection_service.create_connection_link", new_callable=AsyncMock) as mock_link:
            mock_link.return_value = mock_composio_resp
            res_start = incognito_client.post(
                "/api/v1/connections/gmail/start",
                json={"force_new": True},
            )
            self.assertEqual(res_start.status_code, 200)
            start_data = res_start.json()
            self.assertEqual(start_data["status"], "INITIATED")
            self.assertEqual(start_data["connected_account_id"], "ca_incognito_gmail_01")
            # Verify the service was called with the exact incognito session ID
            mock_link.assert_called_once()
            call_kwargs = mock_link.call_args[1]
            self.assertEqual(call_kwargs["user_id"], session_id)

        # 3. Simulate callback / polling verification under the same incognito session
        mock_account_resp = {
            "id": "ca_incognito_gmail_01",
            "toolkit_slug": "gmail",
            "status": "ACTIVE",
            "status_reason": None,
            "created_at": "2026-11-13T10:00:00Z",
            "updated_at": "2026-11-13T10:01:00Z",
            "user_id": session_id,
            "alias": "gmail_incog1",
        }

        with patch("app.services.composio_connection.composio_connection_service.get_connected_account", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_account_resp
            res_status = incognito_client.get("/api/v1/connections/ca_incognito_gmail_01")
            self.assertEqual(res_status.status_code, 200)
            status_data = res_status.json()
            self.assertEqual(status_data["status"], "ACTIVE")
            self.assertEqual(status_data["user_id"], session_id)

    def test_03_separate_incognito_windows_isolated(self):
        """
        Simulates two separate Incognito windows (Window A and Window B).
        Verifies that Window B cannot access or manipulate Window A's connections.
        """
        window_a = TestClient(app)
        window_b = TestClient(app)

        # Establish distinct sessions for each window
        res_a = window_a.get("/api/v1/session")
        res_b = window_b.get("/api/v1/session")
        session_a = res_a.json()["session_id"]
        session_b = res_b.json()["session_id"]
        self.assertNotEqual(session_a, session_b)

        # Window A creates a connection
        conn_a_id = "ca_window_a_slack"
        with patch("app.services.composio_connection.composio_connection_service.create_connection_link", new_callable=AsyncMock) as mock_link:
            mock_link.return_value = {
                "redirect_url": "https://backend.composio.dev/connect/link_a",
                "connected_account_id": conn_a_id,
                "expires_at": "2026-11-13T20:00:00Z",
                "toolkit_slug": "slack",
                "alias": "slack_a",
                "is_custom_auth": False,
                "status": "INITIATED",
                "already_active": False,
                "message": "Auth link",
            }
            res_start = window_a.post("/api/v1/connections/slack/start", json={})
            self.assertEqual(res_start.status_code, 200)

        # Window B attempts to query Window A's connection -> must return 404
        with patch.object(
            composio_connection_service,
            "_request",
            new_callable=AsyncMock,
        ) as mock_req:
            mock_req.return_value = {
                "id": conn_a_id,
                "user_id": session_a,
                "toolkit": {"slug": "slack"},
                "status": "ACTIVE",
            }
            res_b_query = window_b.get(f"/api/v1/connections/{conn_a_id}")
            # Because Window B's session != Window A's session, the ownership check rejects with 404
            self.assertEqual(res_b_query.status_code, 404)

            # Window B attempts to delete Window A's connection -> must return 404
            res_b_delete = window_b.delete(f"/api/v1/connections/{conn_a_id}")
            self.assertEqual(res_b_delete.status_code, 404)

    def test_04_lifecycle_state_machine_transitions(self):
        """
        Verifies lifecycle state machine transitions:
        - Calling start does NOT return ACTIVE unless verified.
        - Polling reflects ACTIVE only once upstream Composio confirms ACTIVE.
        - Disconnect transitions connection cleanly to DELETED.
        """
        client = TestClient(app)
        session_res = client.get("/api/v1/session")
        user_id = session_res.json()["session_id"]

        # Step 1: Start connection -> Status must be INITIATED
        with patch("app.services.composio_connection.composio_connection_service.create_connection_link", new_callable=AsyncMock) as mock_link:
            mock_link.return_value = {
                "redirect_url": "https://backend.composio.dev/connect/oauth_step1",
                "connected_account_id": "ca_test_lifecycle_123",
                "expires_at": "2026-11-13T20:00:00Z",
                "toolkit_slug": "gmail",
                "alias": "gmail_step1",
                "is_custom_auth": False,
                "status": "INITIATED",
                "already_active": False,
                "message": "Link ready",
            }
            start_res = client.post("/api/v1/connections/gmail/start", json={})
            self.assertEqual(start_res.status_code, 200)
            self.assertEqual(start_res.json()["status"], "INITIATED")
            self.assertFalse(start_res.json()["already_active"])

        # Step 2: Query status while authorization is pending -> INITIATED
        with patch("app.services.composio_connection.composio_connection_service.get_connected_account", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "id": "ca_test_lifecycle_123",
                "toolkit_slug": "gmail",
                "status": "INITIATED",
                "status_reason": "Waiting for user consent",
                "created_at": "2026-11-13T10:00:00Z",
                "updated_at": "2026-11-13T10:00:00Z",
                "user_id": user_id,
                "alias": "gmail_step1",
            }
            pending_res = client.get("/api/v1/connections/ca_test_lifecycle_123")
            self.assertEqual(pending_res.status_code, 200)
            self.assertEqual(pending_res.json()["status"], "INITIATED")

        # Step 3: Upstream verifies ACTIVE -> Status becomes ACTIVE
        with patch("app.services.composio_connection.composio_connection_service.get_connected_account", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "id": "ca_test_lifecycle_123",
                "toolkit_slug": "gmail",
                "status": "ACTIVE",
                "status_reason": None,
                "created_at": "2026-11-13T10:00:00Z",
                "updated_at": "2026-11-13T10:02:00Z",
                "user_id": user_id,
                "alias": "gmail_step1",
            }
            active_res = client.get("/api/v1/connections/ca_test_lifecycle_123")
            self.assertEqual(active_res.status_code, 200)
            self.assertEqual(active_res.json()["status"], "ACTIVE")

        # Step 4: Disconnect -> DELETE endpoint removes the connection
        with patch("app.services.composio_connection.composio_connection_service.delete_connected_account", new_callable=AsyncMock) as mock_del:
            mock_del.return_value = {
                "status": "DELETED",
                "connected_account_id": "ca_test_lifecycle_123",
                "message": "Connection disconnected and removed successfully.",
            }
            del_res = client.delete("/api/v1/connections/ca_test_lifecycle_123")
            self.assertEqual(del_res.status_code, 200)
            self.assertEqual(del_res.json()["status"], "DELETED")


if __name__ == "__main__":
    unittest.main()
