"""
Unit and integration tests for Gemini Research Engine Foundation (Milestone 3.0).

All tests use mocked Gemini responses and run offline without making live paid API calls.
"""
import sys
import os
import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import json


# Ensure backend root is the first entry in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app
from app.core.config import settings
from app.core.security import redact_sensitive_data, REDACTED_PLACEHOLDER
from app.core.rate_limit import gemini_quota_protection, research_rate_limiter
from app.services.doc_fetcher import FetchedDoc, OAuthDiscoveryMetadata, doc_fetcher_service
from app.models.research import (
    ResearchStatus,
    OAuthFlowDetails,
    ResearchResultResponse,
    ResearchCitation,
    FieldEvidenceProvenance,
    FieldEvidence,
)
from app.models.composio import (
    ComposioClassification,
    ComposioToolkitCheckResponse,
)
from app.services.composio_metadata import composio_metadata_service
from app.services.evidence_engine import deterministic_evidence_engine
from app.services.research import (
    GeminiResearchService,
    gemini_research_service,
    build_research_prompt,
    build_evidence_grounded_prompt,
    build_citations_from_docs,
    validate_and_filter_evidence,
    extract_grounding_citations,
    parse_model_research_json,
)


class TestGeminiResearchEngine(unittest.TestCase):
    """Test suite for Gemini Research Engine Foundation."""

    def run_async(self, coro):
        return asyncio.run(coro)

    # -----------------------------------------------------------------
    # Test 1: Secret Redaction on Nested Structures
    # -----------------------------------------------------------------
    def test_m3_01_secret_redaction_nested_structures(self):
        """Verify that recursive secret redactor sanitizes all sensitive keys/values while preserving safe metadata."""
        nested_data = {
            "slug": "secure-app",
            "name": "Secure App",
            "enabled": True,
            "auth_schemes": ["OAUTH2"],
            "client_id": "public-client-id-12345",
            "client_secret": "super_secret_password_xyz",
            "auth_config_details": [
                {
                    "mode": "OAUTH2",
                    "secret_key": "top_secret_key_999",
                    "access_token": "ya29.a0AfH6SMB_sample_token_string_here",
                    "refresh_token": "1//sample_refresh_token_here",
                    "allowed_redirect_uris": ["https://example.com/oauth/callback"],
                }
            ],
            "meta": {
                "api_key": "AIzaSyD_fake_google_api_key_for_testing",
                "nested_credentials": {
                    "password": "my_master_password",
                    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...",
                },
                "category": "productivity",
            },
        }

        sanitized = redact_sensitive_data(nested_data)

        # Sensitive keys MUST be redacted
        self.assertEqual(sanitized["client_secret"], REDACTED_PLACEHOLDER)
        self.assertEqual(sanitized["auth_config_details"][0]["secret_key"], REDACTED_PLACEHOLDER)
        self.assertEqual(sanitized["auth_config_details"][0]["access_token"], REDACTED_PLACEHOLDER)
        self.assertEqual(sanitized["auth_config_details"][0]["refresh_token"], REDACTED_PLACEHOLDER)
        self.assertEqual(sanitized["meta"]["api_key"], REDACTED_PLACEHOLDER)
        self.assertEqual(sanitized["meta"]["nested_credentials"]["password"], REDACTED_PLACEHOLDER)
        self.assertEqual(sanitized["meta"]["nested_credentials"]["private_key"], REDACTED_PLACEHOLDER)

        # Safe metadata MUST be preserved untouched
        self.assertEqual(sanitized["slug"], "secure-app")
        self.assertEqual(sanitized["name"], "Secure App")
        self.assertTrue(sanitized["enabled"])
        self.assertEqual(sanitized["auth_schemes"], ["OAUTH2"])
        self.assertEqual(sanitized["client_id"], "public-client-id-12345")
        self.assertEqual(sanitized["auth_config_details"][0]["mode"], "OAUTH2")
        self.assertEqual(sanitized["auth_config_details"][0]["allowed_redirect_uris"], ["https://example.com/oauth/callback"])
        self.assertEqual(sanitized["meta"]["category"], "productivity")

    # -----------------------------------------------------------------
    # Test 2: Gemini Configuration Missing
    # -----------------------------------------------------------------
    def test_m3_02_gemini_config_missing(self):
        """Verify that when GEMINI_API_KEY is empty, research returns METADATA_ONLY with Composio status and does not crash."""
        service = GeminiResearchService(api_key="")
        result = self.run_async(service.research_app("slack"))

        self.assertEqual(result.status, ResearchStatus.METADATA_ONLY)
        self.assertIn("GEMINI_API_KEY is not configured", result.error_message)
        # Composio status was queried
        self.assertIsNotNone(result.composio_status)
        self.assertEqual(result.composio_status.slug, "slack")

    # -----------------------------------------------------------------
    # Test 3: Successful Grounded Research
    # -----------------------------------------------------------------
    def test_m3_03_successful_grounded_research(self):
        """Verify that a successful grounded Gemini response correctly parses citations, flows, and registration rules."""
        mock_json_content = {
            "supports_oauth": True,
            "summary": "Notion supports standard OAuth 2.0 with authorization code grant.",
            "protocol_version": "OAuth 2.0",
            "grant_types": ["authorization_code", "refresh_token"],
            "authorization_endpoint": "https://api.notion.com/v1/oauth/authorize",
            "token_endpoint": "https://api.notion.com/v1/oauth/token",
            "pkce_required": False,
            "developer_portal_url": "https://developers.notion.com",
            "account_type_required": "Free developer account",
            "requires_client_id": True,
            "requires_client_secret": True,
            "allowed_schemes": ["https"],
            "allows_localhost": True,
            "wildcards_permitted": False,
            "strict_exact_match": True,
            "scopes": [
                {"scope": "read", "description": "Read access to workspace", "is_sensitive": False}
            ],
            "review_required": False,
            "review_type": None,
            "estimated_waiting_period_days": None,
            "waiting_period_status": "NOT_APPLICABLE",
            "review_requirements": [],
            "human_actions": ["Create integration in Notion My Integrations dashboard"],
            "agent_actions": ["Store authorization tokens and initialize session"],
            "confidence": "OFFICIAL_DOCS",
        }

        # Mock Interactions API response with steps and URL citations
        mock_annotation = MagicMock()
        mock_annotation.type = "url_citation"
        mock_annotation.url = "https://developers.notion.com/docs/authorization"
        mock_annotation.title = "Notion Authorization Guide"
        mock_annotation.start_index = 0
        mock_annotation.end_index = 48

        mock_text_content = MagicMock()
        mock_text_content.text = "Notion uses OAuth 2.0 to grant access to integrations."
        mock_text_content.annotations = [mock_annotation]

        mock_model_step = MagicMock()
        mock_model_step.type = "model_output"
        mock_model_step.content = [mock_text_content]

        mock_search_step = MagicMock()
        mock_search_step.type = "google_search_call"
        mock_search_step.arguments = MagicMock(queries=["notion oauth documentation", "notion api redirect uri"])

        mock_response = MagicMock()
        mock_response.output_text = f"```json\n{json.dumps(mock_json_content)}\n```"
        mock_response.steps = [mock_search_step, mock_model_step]

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        mock_doc = FetchedDoc(
            url="https://developers.notion.com/docs/authorization",
            final_url="https://developers.notion.com/docs/authorization",
            domain="developers.notion.com",
            title="Notion Authorization Guide",
            text="Notion uses OAuth 2.0 to grant access to integrations. Authorization code and refresh token grants are supported.",
            status_code=200,
            content_type="text/html",
            is_oauth_metadata=False,
            evidence_excerpt="Notion uses OAuth 2.0 to grant access to integrations.",
        )

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
            service = GeminiResearchService(api_key="test-gemini-key", client=mock_client)
            result = self.run_async(service.research_app("Notion", website_or_domain="notion.so"))

            # Verify that tools=None was passed to Gemini (NO search grounding)
            create_call = mock_client.aio.interactions.create.call_args
            self.assertIsNone(create_call.kwargs.get("tools"))

        self.assertEqual(result.status, ResearchStatus.COMPLETED)
        self.assertTrue(result.oauth_details.supports_oauth)
        self.assertEqual(result.oauth_details.protocol_version, "OAuth 2.0")
        self.assertEqual(result.oauth_details.authorization_endpoint, "https://api.notion.com/v1/oauth/authorize")
        self.assertEqual(result.registration.developer_portal_url, "https://developers.notion.com")
        self.assertTrue(result.redirect_uri_rules.allows_localhost)
        self.assertEqual(len(result.scopes), 1)
        self.assertEqual(result.scopes[0].scope, "read")
        self.assertEqual(result.review_timeline.waiting_period_status, "NOT_APPLICABLE")

        # Grounding citations verified
        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.sources[0].url, "https://developers.notion.com/docs/authorization")
        self.assertEqual(result.sources[0].title, "Notion Authorization Guide")
        self.assertEqual(result.sources[0].domain, "developers.notion.com")
        self.assertEqual(result.sources[0].source_type, "OFFICIAL_DOCS")
        self.assertIn("Notion uses OAuth 2.0", result.sources[0].evidence_excerpt)
        self.assertEqual(result.confidence, "OFFICIAL_DOCS")

    # -----------------------------------------------------------------
    # Test 4: Missing Citations / Grounding Empty
    # -----------------------------------------------------------------
    def test_m3_04_missing_citations_graceful_handling(self):
        """Verify that when steps have no search calls or citations, sources safely default to empty list."""
        mock_response = MagicMock()
        mock_response.output_text = '{"supports_oauth": true, "summary": "OAuth available without grounding metadata."}'
        mock_response.steps = []

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[])):
            service = GeminiResearchService(api_key="test-key", client=mock_client)
            result = self.run_async(service.research_app("SimpleApp"))

        self.assertEqual(result.status, ResearchStatus.COMPLETED)
        self.assertTrue(result.oauth_details.supports_oauth)
        self.assertEqual(result.sources, [])
        self.assertEqual(result.search_queries_used, [])

    # -----------------------------------------------------------------
    # Test 5: Unknown or Unsupported OAuth Application
    # -----------------------------------------------------------------
    def test_m3_05_unknown_application_detection(self):
        """Verify that an app documented as lacking OAuth or completely unfound resolves to UNKNOWN_APPLICATION."""
        mock_response = MagicMock()
        mock_response.output_text = '{"supports_oauth": false, "summary": "No OAuth capability or public developer API found."}'
        mock_response.steps = []

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[])):
            service = GeminiResearchService(api_key="test-key", client=mock_client)
            result = self.run_async(service.research_app("UnfamiliarLocalDesktopTool"))

        self.assertEqual(result.status, ResearchStatus.UNKNOWN_APPLICATION)
        self.assertFalse(result.oauth_details.supports_oauth)
        self.assertEqual(result.confidence, "UNCERTAIN")

    # -----------------------------------------------------------------
    # Test 6: Invalid Structured Model Output (Fallback to Partial)
    # -----------------------------------------------------------------
    def test_m3_06_invalid_model_output_fallback(self):
        """Verify that if Gemini returns unparseable conversational text, response is PARTIAL and does not raise 500."""
        mock_response = MagicMock()
        mock_response.output_text = "I looked for this application but could not find any formal OAuth details."
        mock_response.steps = []

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[])):
            service = GeminiResearchService(api_key="test-key", client=mock_client)
            result = self.run_async(service.research_app("MangledOutputApp"))

        self.assertEqual(result.status, ResearchStatus.PARTIAL)
        self.assertIn("Could not parse structured JSON", result.error_message)
        self.assertIn("I looked for this application", result.summary)

    # -----------------------------------------------------------------
    # Test 7: Timeout and Quota Error Handling
    # -----------------------------------------------------------------
    def test_m3_07_timeout_and_quota_errors(self):
        """Verify that asyncio TimeoutError and Gemini 429 quota exceptions yield safe FAILED responses."""
        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[])):
            # A. Timeout
            mock_client_timeout = MagicMock()
            mock_client_timeout.aio.interactions.create = AsyncMock(side_effect=asyncio.TimeoutError())

            service_timeout = GeminiResearchService(api_key="test-key", timeout=1.0, client=mock_client_timeout)
            result_timeout = self.run_async(service_timeout.research_app("SlowApp"))

            self.assertEqual(result_timeout.status, ResearchStatus.FAILED)
            self.assertIn("timed out", result_timeout.error_message.lower())

            # B. Quota 429
            mock_client_quota = MagicMock()
            mock_client_quota.aio.interactions.create = AsyncMock(
                side_effect=Exception("ResourceExhausted: 429 Quota exceeded for project")
            )

            service_quota = GeminiResearchService(api_key="test-key", client=mock_client_quota)
            result_quota = self.run_async(service_quota.research_app("QuotaApp"))

            self.assertEqual(result_quota.status, ResearchStatus.FAILED)
            self.assertIn("rate limit or quota exceeded", result_quota.error_message.lower())

    # -----------------------------------------------------------------
    # Test 8: Secret Redaction in Research Output
    # -----------------------------------------------------------------
    def test_m3_08_secret_redaction_in_research_output(self):
        """Verify that any accidental secret keys emitted in research output fields are sanitized."""
        mock_response = MagicMock()
        mock_response.output_text = (
            '{"supports_oauth": true, '
            '"summary": "Integration notes with secret_key=test_secret_12345", '
            '"client_secret_notes": "Use secret xoxb-testfixture-mock-redacted-token-999"}'
        )
        mock_response.steps = []

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[])):
            service = GeminiResearchService(api_key="test-key", client=mock_client)
            result = self.run_async(service.research_app("SecretApp"))

        self.assertEqual(result.status, ResearchStatus.COMPLETED)
        # Verify the leaked token matching high-entropy regex was redacted
        self.assertNotIn("xoxb-testfixture-mock-redacted-token-999", result.registration.client_secret_notes or "")

    # -----------------------------------------------------------------
    # Test 9: FastAPI Research Endpoint Round-Trip & Validation
    # -----------------------------------------------------------------
    def test_m3_09_fastapi_research_endpoint_round_trip(self):
        """Verify HTTP POST /api/v1/research works as expected and enforces input validation."""
        mock_json_content = {
            "supports_oauth": True,
            "summary": "Linear supports OAuth 2.0.",
            "protocol_version": "OAuth 2.0",
            "developer_portal_url": "https://linear.app/settings/api",
        }
        mock_response = MagicMock()
        mock_response.output_text = json.dumps(mock_json_content)
        mock_response.steps = []

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        # Wire mock into global service
        orig_client = gemini_research_service._client
        orig_key = gemini_research_service.api_key
        gemini_research_service._client = mock_client
        gemini_research_service.api_key = "test-endpoint-key"

        mock_doc = FetchedDoc(
            url="https://linear.app/docs/oauth",
            final_url="https://linear.app/docs/oauth",
            domain="linear.app",
            title="Linear OAuth Docs",
            text="Linear supports OAuth 2.0.",
            status_code=200,
            content_type="text/html",
        )

        try:
            async def query_api():
                await research_rate_limiter.reset()
                with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
                    async with httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=app),
                        base_url="http://testserver",
                    ) as client:
                        # 1. Valid request
                        resp = await client.post(
                            "/api/v1/research",
                            json={"app_name": "Linear", "website_or_domain": "linear.app"},
                        )
                        self.assertEqual(resp.status_code, 200)
                        data = resp.json()
                        self.assertEqual(data["app_name"], "Linear")
                        self.assertEqual(data["status"], "COMPLETED")
                        self.assertTrue(data["oauth_details"]["supports_oauth"])

                        # 2. Whitespace app_name -> 400 Bad Request
                        bad_resp = await client.post(
                            "/api/v1/research",
                            json={"app_name": "   "},
                        )
                        self.assertEqual(bad_resp.status_code, 400)
                        self.assertIn("cannot be empty", bad_resp.json()["detail"].lower())

            self.run_async(query_api())
        finally:
            gemini_research_service._client = orig_client
            gemini_research_service.api_key = orig_key

    # -----------------------------------------------------------------
    # Test 10: Existing Composio Integration Remains Intact
    # -----------------------------------------------------------------
    def test_m3_10_composio_integration_unaffected(self):
        """Verify that existing Composio metadata checks and catalog queries continue functioning seamlessly."""
        async def query_composio():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get("/api/v1/apps")
                self.assertEqual(resp.status_code, 200)
                self.assertGreater(resp.json()["total"], 0)

        self.run_async(query_composio())

    # -----------------------------------------------------------------
    # Test 11: Feature Toggle Disabled Setting
    # -----------------------------------------------------------------
    def test_m3_11_feature_disabled_setting(self):
        """Verify that when RESEARCH_ENABLED is False, research immediately returns DISABLED status."""
        orig_setting = settings.RESEARCH_ENABLED
        try:
            settings.RESEARCH_ENABLED = False
            service = GeminiResearchService(api_key="test-key")
            result = self.run_async(service.research_app("Slack"))
            self.assertEqual(result.status, ResearchStatus.DISABLED)
            self.assertIn("disabled", result.error_message.lower())
        finally:
            settings.RESEARCH_ENABLED = orig_setting

    # -----------------------------------------------------------------
    # Test 12: Candidates Grounding Fallback
    # -----------------------------------------------------------------
    def test_m3_12_candidate_grounding_fallback(self):
        """Verify that candidate grounding_metadata fallback functions if steps are absent."""
        mock_json_content = {
            "supports_oauth": True,
            "summary": "Fallback works with candidates metadata.",
        }
        mock_chunk = MagicMock()
        mock_chunk.web.uri = "https://docs.example.com/oauth"
        mock_chunk.web.title = "Example Docs"

        mock_grounding = MagicMock()
        mock_grounding.web_search_queries = ["example oauth"]
        mock_grounding.grounding_chunks = [mock_chunk]
        mock_grounding.grounding_supports = []

        mock_candidate = MagicMock()
        mock_candidate.grounding_metadata = mock_grounding
        mock_candidate.content.parts = [MagicMock(text=json.dumps(mock_json_content))]

        mock_response = MagicMock()
        mock_response.output_text = None
        mock_response.text = None
        mock_response.steps = None
        mock_response.candidates = [mock_candidate]

        mock_client = MagicMock()
        del mock_client.aio.interactions
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[])):
            service = GeminiResearchService(api_key="test-key", client=mock_client)
            result = self.run_async(service.research_app("FallbackApp"))

        self.assertEqual(result.status, ResearchStatus.COMPLETED)
        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.sources[0].url, "https://docs.example.com/oauth")
        self.assertEqual(result.sources[0].title, "Example Docs")
        self.assertEqual(result.search_queries_used, ["example oauth"])

    # -----------------------------------------------------------------
    # Milestone 3.2: Evidence-Grounded Research Tests
    # -----------------------------------------------------------------
    def test_m32_01_no_search_grounding_tool_passed(self):
        """Verify that Gemini is invoked with tools=None (NO Google Search grounding)."""
        mock_doc = FetchedDoc(
            url="https://developers.hubspot.com/docs/api/working-with-oauth",
            final_url="https://developers.hubspot.com/docs/api/working-with-oauth",
            domain="developers.hubspot.com",
            title="HubSpot OAuth",
            text="HubSpot uses OAuth 2.0 authorization code flow.",
            status_code=200,
            content_type="text/html",
        )
        mock_response = MagicMock()
        mock_response.output_text = json.dumps({"supports_oauth": True, "summary": "HubSpot OAuth 2.0."})

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
            service = GeminiResearchService(api_key="test-key", client=mock_client)
            result = self.run_async(service.research_app("HubSpot"))

            self.assertEqual(result.status, ResearchStatus.COMPLETED)
            call_kwargs = mock_client.aio.interactions.create.call_args.kwargs
            # Strict verification: tools must be None (zero search grounding)
            self.assertIsNone(call_kwargs.get("tools"))

    def test_m32_02_evidence_text_passed_in_gemini_prompt(self):
        """Verify that verbatim documentation text from doc_fetcher is injected into the Gemini prompt."""
        verbatim_snippet = "Specialized OAuth grant: authorization_code with strict redirect matching."
        mock_doc = FetchedDoc(
            url="https://developers.example.com/oauth",
            final_url="https://developers.example.com/oauth",
            domain="developers.example.com",
            title="Example Docs",
            text=verbatim_snippet,
            status_code=200,
            content_type="text/html",
        )
        mock_response = MagicMock()
        mock_response.output_text = json.dumps({"supports_oauth": True, "summary": "OAuth available."})

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
            service = GeminiResearchService(api_key="test-key", client=mock_client)
            self.run_async(service.research_app("SnippetApp"))

            prompt_input = mock_client.aio.interactions.create.call_args.kwargs["input"]
            self.assertIn(verbatim_snippet, prompt_input)
            self.assertIn("developers.example.com", prompt_input)

    def test_m32_03_citation_url_provenance_strictly_from_docs(self):
        """Verify that citations strictly originate from retrieved documents and phantom URLs are rejected."""
        real_url = "https://developer.spotify.com/documentation/web-api/tutorials/code-flow"
        mock_doc = FetchedDoc(
            url=real_url,
            final_url=real_url,
            domain="developer.spotify.com",
            title="Spotify Authorization Guide",
            text="Spotify uses Authorization Code with PKCE.",
            status_code=200,
            content_type="text/html",
        )
        # Model attempts to hallucinate a phantom URL in review requirements
        mock_response = MagicMock()
        mock_response.output_text = json.dumps({
            "supports_oauth": True,
            "summary": "Spotify OAuth.",
            "review_requirements": [
                {
                    "name": "App Verification",
                    "requirement_type": "OAUTH_VERIFICATION",
                    "source_ids": ["src_999", "src_1"],  # src_999 is hallucinated
                }
            ],
        })

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
            service = GeminiResearchService(api_key="test-key", client=mock_client)
            result = self.run_async(service.research_app("Spotify"))

            self.assertEqual(len(result.sources), 1)
            self.assertEqual(result.sources[0].url, real_url)
            self.assertEqual(result.sources[0].id, "src_1")

            # Verify src_999 was scrubbed
            req = result.review_timeline.review_requirements[0]
            self.assertEqual(req.source_ids, ["src_1"])

    def test_m32_04_unsupported_waiting_period_stripped(self):
        """Verify that an invented waiting period absent from document text is discarded to NOT_STATED."""
        mock_doc = FetchedDoc(
            url="https://api.slack.com/authentication",
            final_url="https://api.slack.com/authentication",
            domain="api.slack.com",
            title="Slack Auth",
            text="Slack integrations install directly to single workspaces without approval waiting period.",
            status_code=200,
            content_type="text/html",
        )
        mock_response = MagicMock()
        mock_response.output_text = json.dumps({
            "supports_oauth": True,
            "summary": "Slack OAuth.",
            "estimated_waiting_period_days": 45,  # Hallucinated 45 days
            "waiting_period_status": "ESTABLISHED",
        })

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
            service = GeminiResearchService(api_key="test-key", client=mock_client)
            result = self.run_async(service.research_app("Slack"))

            # The 45 days estimate must be stripped because it does not appear in text
            self.assertIsNone(result.review_timeline.estimated_waiting_period_days)
            self.assertEqual(result.review_timeline.waiting_period_status, "NOT_STATED")

    def test_m32_05_missing_documentation_yields_unknown_application_without_calling_gemini(self):
        """Verify that missing documentation for an unknown app yields UNKNOWN_APPLICATION and preserves Gemini quota."""
        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock()

        # Doc fetcher finds nothing, Composio returns 404 (not in catalog)
        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[])):
            service = GeminiResearchService(api_key="test-key", client=None)
            result = self.run_async(service.research_app("CompletelyUnknownTool12345"))

            self.assertEqual(result.status, ResearchStatus.UNKNOWN_APPLICATION)
            self.assertFalse(result.oauth_details.supports_oauth)
            self.assertIn("could not be identified", result.error_message.lower())

    def test_m32_06_missing_documentation_with_composio_catalog_yields_metadata_only(self):
        """Verify that if documentation is missing but Composio catalog has metadata, status is METADATA_ONLY."""
        from app.models.composio import ComposioClassification, ComposioToolkitCheckResponse
        from app.services.composio_metadata import composio_metadata_service

        mock_composio = ComposioToolkitCheckResponse(
            slug="known-tool",
            name="Known Tool",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            explanation="Composio managed OAuth is available.",
        )

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[])):
            with patch.object(composio_metadata_service, "fetch_toolkit_metadata", AsyncMock(return_value=mock_composio)):
                service = GeminiResearchService(api_key="test-key", client=None)
                result = self.run_async(service.research_app("known-tool"))

                self.assertEqual(result.status, ResearchStatus.METADATA_ONLY)
                self.assertTrue(result.oauth_details.supports_oauth)
                self.assertIsNotNone(result.composio_status)

    def test_m32_07_gemini_quota_protection_blocks_excess_calls(self):
        """Verify that when Gemini daily quota is reached, research returns FAILED without making API calls."""
        mock_doc = FetchedDoc(
            url="https://docs.example.com",
            final_url="https://docs.example.com",
            domain="docs.example.com",
            title="Docs",
            text="OAuth text",
            status_code=200,
            content_type="text/html",
        )
        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock()

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
            with patch.object(gemini_quota_protection, "can_call", AsyncMock(return_value=(False, "Daily limit reached"))):
                service = GeminiResearchService(api_key="test-key", client=mock_client)
                result = self.run_async(service.research_app("QuotaCappedApp"))

                self.assertEqual(result.status, ResearchStatus.FAILED)
                self.assertIn("daily limit", result.error_message.lower())
                # Verify Gemini was NOT called
                self.assertEqual(mock_client.aio.interactions.create.call_count, 0)

    def test_m32_08_gemini_timeout_handling(self):
        """Verify that Gemini timeout yields FAILED status with timeout message."""
        mock_doc = FetchedDoc(
            url="https://docs.example.com",
            final_url="https://docs.example.com",
            domain="docs.example.com",
            title="Docs",
            text="OAuth text",
            status_code=200,
            content_type="text/html",
        )
        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
            service = GeminiResearchService(api_key="test-key", timeout=1.0, client=mock_client)
            result = self.run_async(service.research_app("TimeoutApp"))

            self.assertEqual(result.status, ResearchStatus.FAILED)
            self.assertIn("timed out", result.error_message.lower())

    def test_m32_09_gemini_429_quota_exceeded_no_retry(self):
        """Verify that Gemini 429 quota exception returns FAILED and does not retry."""
        mock_doc = FetchedDoc(
            url="https://docs.example.com",
            final_url="https://docs.example.com",
            domain="docs.example.com",
            title="Docs",
            text="OAuth text",
            status_code=200,
            content_type="text/html",
        )
        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(
            side_effect=Exception("429 ResourceExhausted: Quota exceeded for project")
        )

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
            service = GeminiResearchService(api_key="test-key", client=mock_client)
            result = self.run_async(service.research_app("ExhaustedApp"))

            self.assertEqual(result.status, ResearchStatus.FAILED)
            self.assertIn("rate limit or quota exceeded", result.error_message.lower())
            # Must only attempt exactly once (NO automatic retries)
            self.assertEqual(mock_client.aio.interactions.create.call_count, 1)

    def test_m32_10_rfc8414_oauth_metadata_integration(self):
        """Verify that when RFC 8414 metadata is fetched, protocol endpoints and OFFICIAL_DOCS confidence are set."""
        mock_meta = OAuthDiscoveryMetadata(
            issuer="https://auth.sample.com",
            authorization_endpoint="https://auth.sample.com/oauth/authorize",
            token_endpoint="https://auth.sample.com/oauth/token",
            scopes_supported=["openid", "profile"],
            grant_types_supported=["authorization_code"],
            code_challenge_methods_supported=["S256"],
        )
        mock_doc = FetchedDoc(
            url="https://sample.com/.well-known/oauth-authorization-server",
            final_url="https://sample.com/.well-known/oauth-authorization-server",
            domain="sample.com",
            title="OAuth Discovery Metadata (sample.com)",
            text="RFC 8414 OAuth Metadata: authorization_endpoint=https://auth.sample.com/oauth/authorize",
            status_code=200,
            content_type="application/json",
            is_oauth_metadata=True,
            oauth_metadata=mock_meta,
        )
        mock_response = MagicMock()
        mock_response.output_text = json.dumps({
            "supports_oauth": True,
            "summary": "Sample App supports OAuth 2.0 via RFC 8414.",
            "protocol_version": "OAuth 2.0",
            "authorization_endpoint": "https://auth.sample.com/oauth/authorize",
            "token_endpoint": "https://auth.sample.com/oauth/token",
            "pkce_required": True,
            "scopes": [{"scope": "openid", "description": "OpenID scope"}],
        })

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
            service = GeminiResearchService(api_key="test-key", client=mock_client)
            result = self.run_async(service.research_app("SampleApp"))

            self.assertEqual(result.status, ResearchStatus.COMPLETED)
            self.assertTrue(result.oauth_details.supports_oauth)
            self.assertEqual(result.oauth_details.authorization_endpoint, "https://auth.sample.com/oauth/authorize")
            self.assertEqual(result.confidence, "OFFICIAL_DOCS")
            self.assertEqual(result.sources[0].url, "https://sample.com/.well-known/oauth-authorization-server")

    # -----------------------------------------------------------------
    # Gemini 503 Service Unavailable / High Demand Regression Tests
    # -----------------------------------------------------------------
    def test_m32_11_gemini_503_preserves_composio_managed_oauth(self):
        """
        Regression: When Gemini returns 503 (service unavailable / high demand),
        verify that verified Composio metadata is preserved, supports_oauth is NOT
        overwritten with false, research is NOT claimed completed, citations are preserved,
        no automatic retries occur, and unsupported requirements are not hallucinated.
        """
        from app.models.composio import ComposioClassification, ComposioToolkitCheckResponse
        from app.services.composio_metadata import composio_metadata_service

        mock_composio = ComposioToolkitCheckResponse(
            slug="notion",
            name="Notion",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            documentation_url="https://developers.notion.com",
            explanation="Composio managed OAuth is available for Notion.",
        )
        mock_doc = FetchedDoc(
            url="https://developers.notion.com",
            final_url="https://developers.notion.com/guides/notion-api/quick-start",
            domain="developers.notion.com",
            title="Notion API quickstart",
            text="To connect Notion to your application, use the OAuth 2.0 authorization code flow.",
            status_code=200,
            content_type="text/html",
        )

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(
            side_effect=Exception("503 Service Unavailable: The model is overloaded. Please try again later.")
        )

        with patch.object(composio_metadata_service, "fetch_toolkit_metadata", AsyncMock(return_value=mock_composio)):
            with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
                service = GeminiResearchService(api_key="test-key", client=mock_client)
                result = self.run_async(service.research_app("Notion", website_or_domain="https://www.notion.com"))

                # 1. Status is FAILED
                self.assertEqual(result.status, ResearchStatus.FAILED)

                # 2. Composio-managed OAuth is PRESERVED, NOT overwritten with False
                self.assertTrue(result.oauth_details.supports_oauth)
                self.assertEqual(result.oauth_details.protocol_version, "OAuth 2.0")
                self.assertIsNotNone(result.composio_status)
                self.assertEqual(result.composio_status.classification, ComposioClassification.COMPOSIO_MANAGED_AVAILABLE)

                # 3. Does NOT claim research completed
                self.assertNotIn("OAuth research completed", result.summary)
                self.assertIn("could not be completed", result.summary.lower())

                # 4. Clear error message explaining Gemini was temporarily unavailable
                self.assertIn("temporarily unavailable", result.error_message.lower())
                self.assertIn("503", result.error_message)

                # 5. Retrieved documentation citations preserved
                self.assertEqual(len(result.sources), 1)
                self.assertEqual(result.sources[0].url, "https://developers.notion.com/guides/notion-api/quick-start")
                self.assertEqual(result.sources[0].domain, "developers.notion.com")

                # 6. Never populate unsupported OAuth requirements from assumptions
                self.assertEqual(result.scopes, [])
                self.assertEqual(result.review_timeline.review_requirements, [])
                self.assertIsNone(result.oauth_details.authorization_endpoint)
                self.assertIsNone(result.oauth_details.token_endpoint)

                # 7. No automatic retries
                self.assertEqual(mock_client.aio.interactions.create.call_count, 1)

    def test_m32_12_gemini_503_composio_metadata_unavailable(self):
        """
        Regression: When Gemini returns 503 and Composio metadata is unavailable,
        verify status is FAILED, supports_oauth is False (cannot assume),
        citations are preserved, and summary does not claim completion.
        """
        from app.services.composio_metadata import composio_metadata_service

        mock_doc = FetchedDoc(
            url="https://docs.customapp.io/oauth",
            final_url="https://docs.customapp.io/oauth",
            domain="docs.customapp.io",
            title="CustomApp OAuth Guide",
            text="Public OAuth 2.0 instructions.",
            status_code=200,
            content_type="text/html",
        )

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(
            side_effect=Exception("503 Service Unavailable: High demand on service.")
        )

        with patch.object(composio_metadata_service, "fetch_toolkit_metadata", AsyncMock(return_value=None)):
            with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
                service = GeminiResearchService(api_key="test-key", client=mock_client)
                result = self.run_async(service.research_app("CustomApp"))

                self.assertEqual(result.status, ResearchStatus.FAILED)
                # Without Composio and with failed AI, supports_oauth cannot be confirmed
                self.assertFalse(result.oauth_details.supports_oauth)
                self.assertIsNone(result.composio_status)

                # Summary does not claim completion
                self.assertNotIn("OAuth research completed", result.summary)
                self.assertIn("could not be completed", result.summary.lower())

                # Error message explains temporary unavailability
                self.assertIn("temporarily unavailable", result.error_message.lower())

                # Citations preserved
                self.assertEqual(len(result.sources), 1)
                self.assertEqual(result.sources[0].url, "https://docs.customapp.io/oauth")

                # No automatic retries
                self.assertEqual(mock_client.aio.interactions.create.call_count, 1)

    def test_m32_13_gemini_503_preserves_retrieved_documentation_citations(self):
        """
        Regression: When Gemini returns 503 but multiple official documentation pages
        were retrieved, verify all citations are preserved, summary explicitly indicates
        AI analysis was not completed, and no requirements are hallucinated.
        """
        from app.services.composio_metadata import composio_metadata_service

        doc1 = FetchedDoc(
            url="https://developers.example.com/quickstart",
            final_url="https://developers.example.com/quickstart",
            domain="developers.example.com",
            title="Developer Quickstart",
            text="Get started by registering an app in the console.",
            status_code=200,
            content_type="text/html",
        )
        doc2 = FetchedDoc(
            url="https://developers.example.com/oauth/authorize",
            final_url="https://developers.example.com/oauth/authorize",
            domain="developers.example.com",
            title="Authorization Endpoints",
            text="Authorize endpoint: https://api.example.com/oauth/authorize",
            status_code=200,
            content_type="text/html",
        )

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(
            side_effect=Exception("503 service_unavailable: temporary high demand")
        )

        with patch.object(composio_metadata_service, "fetch_toolkit_metadata", AsyncMock(return_value=None)):
            with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[doc1, doc2])):
                service = GeminiResearchService(api_key="test-key", client=mock_client)
                result = self.run_async(service.research_app("ExampleCorp"))

                self.assertEqual(result.status, ResearchStatus.FAILED)
                # Both citations must be preserved
                self.assertEqual(len(result.sources), 2)
                self.assertEqual(result.sources[0].url, "https://developers.example.com/quickstart")
                self.assertEqual(result.sources[1].url, "https://developers.example.com/oauth/authorize")

                # Summary clearly indicates AI analysis was not completed
                self.assertIn("2 official documentation source(s) were retrieved, but AI analysis was not completed", result.summary)
                self.assertNotIn("OAuth research completed", result.summary)

                # Error message explains temporary unavailability
                self.assertIn("temporarily unavailable", result.error_message.lower())

                # No hallucinated requirements
                self.assertEqual(result.scopes, [])
                self.assertEqual(result.review_timeline.review_requirements, [])
                self.assertEqual(result.oauth_details.grant_types, [])

                # Exactly one call, no automatic retries
                self.assertEqual(mock_client.aio.interactions.create.call_count, 1)

    # -----------------------------------------------------------------
    # Milestone 3.3: Deterministic Evidence-Based Fallback Pipeline Tests
    # -----------------------------------------------------------------
    def test_m33_01_notion_evidence_guide_generation(self):
        """Verify that deterministic evidence engine generates a comprehensive, production-ready Notion OAuth guide."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="notion",
            name="Notion",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            documentation_url="https://developers.notion.com",
            explanation="Composio managed OAuth is available for Notion.",
        )
        mock_doc = FetchedDoc(
            url="https://developers.notion.com/guides/notion-api/quick-start",
            final_url="https://developers.notion.com/guides/notion-api/quick-start",
            domain="developers.notion.com",
            title="Notion API quickstart",
            text=(
                "To connect Notion to your application, use the OAuth 2.0 authorization code flow. "
                "Integrations are authorized by workspace admins. "
                "Redirect URI must match exactly using https scheme. Localhost is permitted for development. "
                "No formal marketplace review waiting period is required for internal integrations."
            ),
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Notion",
            website_or_domain="https://www.notion.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        # 1. Status & Core OAuth
        self.assertEqual(result.status, ResearchStatus.COMPLETED)
        self.assertTrue(result.oauth_details.supports_oauth)
        self.assertEqual(result.oauth_details.protocol_version, "OAuth 2.0")
        self.assertIn("authorization_code", result.oauth_details.grant_types)
        self.assertEqual(result.confidence, "OFFICIAL_DOCS")

        # 2. Executive Summary
        self.assertIn("[Evidence-Engine]", result.summary)
        self.assertIn("Composio Managed OAuth is available", result.summary)

        # 3. Provider Registration
        self.assertEqual(result.registration.developer_portal_url, "https://developers.notion.com")
        self.assertTrue(result.registration.requires_client_id)
        self.assertTrue(result.registration.requires_client_secret)

        # 4. Redirect URI Rules
        self.assertEqual(result.redirect_uri_rules.allowed_schemes, ["https"])
        self.assertTrue(result.redirect_uri_rules.allows_localhost)
        self.assertFalse(result.redirect_uri_rules.wildcards_permitted)
        self.assertTrue(result.redirect_uri_rules.strict_exact_match)
        self.assertTrue(result.redirect_uri_rules.composio_redirect_uri_supported)

        # 5. Review Timeline & Boundary
        self.assertFalse(result.review_timeline.review_required)
        self.assertEqual(result.review_timeline.waiting_period_status, "NOT_APPLICABLE")
        self.assertGreater(len(result.human_agent_boundary.what_human_must_do), 0)
        self.assertGreater(len(result.human_agent_boundary.what_agent_can_automate), 0)

        # 6. Citations
        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.sources[0].url, "https://developers.notion.com/guides/notion-api/quick-start")

    def test_m33_02_slack_evidence_guide_with_rfc_metadata(self):
        """Verify that deterministic evidence engine extracts exact OpenID Connect endpoints and scopes for Slack."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="slack",
            name="Slack",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            documentation_url="https://api.slack.com",
            explanation="Composio managed OAuth is available for Slack.",
        )
        mock_rfc_meta = OAuthDiscoveryMetadata(
            issuer="https://slack.com",
            authorization_endpoint="https://slack.com/openid/connect/authorize",
            token_endpoint="https://slack.com/api/openid.connect.token",
            userinfo_endpoint="https://slack.com/api/openid.connect.userInfo",
            scopes_supported=["openid", "profile", "email"],
            grant_types_supported=["authorization_code", "refresh_token"],
            code_challenge_methods_supported=["S256"],
        )
        mock_doc = FetchedDoc(
            url="https://slack.com/.well-known/openid-configuration",
            final_url="https://slack.com/.well-known/openid-configuration",
            domain="slack.com",
            title="Slack OpenID Configuration",
            text="OpenID configuration for Slack authentication.",
            status_code=200,
            content_type="application/json",
            is_oauth_metadata=True,
            oauth_metadata=mock_rfc_meta,
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Slack",
            website_or_domain="slack.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        self.assertEqual(result.status, ResearchStatus.COMPLETED)
        self.assertTrue(result.oauth_details.supports_oauth)
        self.assertEqual(result.oauth_details.protocol_version, "OAuth 2.0 / OpenID Connect")
        self.assertEqual(result.oauth_details.authorization_endpoint, "https://slack.com/openid/connect/authorize")
        self.assertEqual(result.oauth_details.token_endpoint, "https://slack.com/api/openid.connect.token")
        self.assertTrue(result.oauth_details.pkce_required)
        self.assertIn("authorization_code", result.oauth_details.grant_types)

        # Scopes extracted from RFC metadata
        scope_names = [s.scope for s in result.scopes]
        self.assertIn("openid", scope_names)
        self.assertIn("profile", scope_names)
        self.assertIn("email", scope_names)

        self.assertIn("[Evidence-Engine]", result.summary)
        self.assertEqual(result.registration.developer_portal_url, "https://api.slack.com/apps")

    def test_m33_03_shopify_custom_oauth_mandatory(self):
        """Verify that Shopify is correctly classified as CUSTOM_OAUTH_MANDATORY with Partner Dashboard requirements."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="shopify",
            name="Shopify",
            in_catalog=True,
            classification=ComposioClassification.CUSTOM_OAUTH_MANDATORY,
            supports_oauth=True,
            managed_oauth_available=False,
            supported_auth_schemes=["OAUTH2", "S2S_OAUTH2"],
            managed_auth_schemes=[],
            explanation="Shopify requires custom OAuth credentials via Partner Dashboard.",
        )
        mock_doc = FetchedDoc(
            url="https://shopify.dev/docs/apps/auth/oauth",
            final_url="https://shopify.dev/docs/apps/auth/oauth",
            domain="shopify.dev",
            title="Shopify OAuth Documentation",
            text=(
                "Shopify apps authenticate using OAuth 2.0. Create an app in your Shopify Partner Dashboard "
                "to get your client ID and client secret. Set the redirect URI to https://backend.composio.dev/api/v1/auth-apps/add."
            ),
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Shopify",
            website_or_domain="shopify.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        self.assertEqual(result.status, ResearchStatus.COMPLETED)
        self.assertTrue(result.oauth_details.supports_oauth)
        self.assertIn("Custom OAuth (Bring Your Own App) is mandatory", result.summary)
        self.assertEqual(result.registration.developer_portal_url, "https://partners.shopify.com")
        self.assertIn("client_credentials", result.oauth_details.grant_types)
        self.assertTrue(any("Partner Dashboard" in step for step in result.human_agent_boundary.what_human_must_do))

    def test_m33_04_unknown_application_deterministic_handling(self):
        """Verify that an unknown application with no Composio entry or docs resolves to UNKNOWN_APPLICATION."""
        result = deterministic_evidence_engine.generate_guide(
            app_name="CompletelyUnknownService999",
            website_or_domain="unknownservice999.invalid",
            composio_status=None,
            fetched_docs=[],
            citations=[],
        )

        self.assertEqual(result.status, ResearchStatus.UNKNOWN_APPLICATION)
        self.assertFalse(result.oauth_details.supports_oauth)
        self.assertEqual(result.confidence, "UNCERTAIN")
        self.assertIn("[Evidence-Engine]", result.summary)
        self.assertIn("could not be verified", result.summary.lower())

    def test_m33_05_non_oauth_toolkit_deterministic_handling(self):
        """Verify that a non-OAuth Composio toolkit produces a factual NON_OAUTH guide."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="serpapi",
            name="SerpApi",
            in_catalog=True,
            classification=ComposioClassification.NON_OAUTH_TOOLKIT,
            supports_oauth=False,
            managed_oauth_available=False,
            supported_auth_schemes=["API_KEY"],
            managed_auth_schemes=[],
            explanation="SerpApi uses API key authentication.",
        )

        result = deterministic_evidence_engine.generate_guide(
            app_name="SerpApi",
            website_or_domain="serpapi.com",
            composio_status=mock_composio,
            fetched_docs=[],
            citations=[],
        )

        self.assertEqual(result.status, ResearchStatus.COMPLETED)
        self.assertFalse(result.oauth_details.supports_oauth)
        self.assertEqual(result.oauth_details.protocol_version, "API Key / Non-OAuth")
        self.assertFalse(result.registration.requires_client_id)
        self.assertFalse(result.registration.requires_client_secret)
        self.assertIn("[Evidence-Engine]", result.summary)
        self.assertIn("NON_OAUTH_TOOLKIT", result.summary)

    def test_m33_06_execution_control_gemini_disabled_skips_ai(self):
        """Verify that with GEMINI_RESEARCH_ENABLED=False (default), research executes deterministic engine directly."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="notion",
            name="Notion",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            explanation="Notion OAuth is supported.",
        )
        mock_doc = FetchedDoc(
            url="https://developers.notion.com/docs/auth",
            final_url="https://developers.notion.com/docs/auth",
            domain="developers.notion.com",
            title="Notion Auth",
            text="Notion uses OAuth 2.0 authorization code flow.",
            status_code=200,
            content_type="text/html",
        )

        orig_enabled = settings.GEMINI_RESEARCH_ENABLED
        try:
            settings.GEMINI_RESEARCH_ENABLED = False
            with patch.object(composio_metadata_service, "fetch_toolkit_metadata", AsyncMock(return_value=mock_composio)):
                with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
                    result = self.run_async(gemini_research_service.research_app("Notion"))

                    self.assertEqual(result.status, ResearchStatus.COMPLETED)
                    self.assertTrue(result.oauth_details.supports_oauth)
                    self.assertIn("[Evidence-Engine]", result.summary)
        finally:
            settings.GEMINI_RESEARCH_ENABLED = orig_enabled

    def test_m33_07_gemini_503_fallback_to_evidence_engine(self):
        """Verify that when Gemini encounters 503 Service Unavailable, fallback to evidence engine executes."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="notion",
            name="Notion",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            documentation_url="https://developers.notion.com",
            explanation="Notion OAuth is supported.",
        )
        mock_doc = FetchedDoc(
            url="https://developers.notion.com/docs/auth",
            final_url="https://developers.notion.com/docs/auth",
            domain="developers.notion.com",
            title="Notion Auth Guide",
            text="Notion OAuth 2.0 authorization code flow documentation.",
            status_code=200,
            content_type="text/html",
        )

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(
            side_effect=Exception("503 Service Unavailable: High demand on service.")
        )

        service = GeminiResearchService(
            api_key="test-key",
            client=mock_client,
            gemini_enabled=True,
            fallback_to_evidence=True,
        )

        with patch.object(composio_metadata_service, "fetch_toolkit_metadata", AsyncMock(return_value=mock_composio)):
            with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
                result = self.run_async(service.research_app("Notion"))

                # Fallback produced a COMPLETED result instead of FAILED
                self.assertEqual(result.status, ResearchStatus.COMPLETED)
                self.assertTrue(result.oauth_details.supports_oauth)
                self.assertIn("[Evidence-Engine]", result.summary)

    # -----------------------------------------------------------------
    # Milestone 3.5 Tests: Evidence Integrity & OAuth Accuracy Corrections
    # -----------------------------------------------------------------
    def test_m35_01_unknown_application_three_state_semantics(self):
        """Verify that an unknown application without Composio entry or docs yields supports_oauth=None (Unverified)."""
        result = deterministic_evidence_engine.generate_guide(
            app_name="HypotheticalUnverifiedApp999",
            website_or_domain="hypothetical999.invalid",
            composio_status=None,
            fetched_docs=[],
            citations=[],
        )

        self.assertEqual(result.status, ResearchStatus.UNKNOWN_APPLICATION)
        # MUST be None (three-state: True=supported, False=affirmatively unsupported, None=unverified)
        self.assertIsNone(result.oauth_details.supports_oauth)
        self.assertEqual(result.oauth_details.confidence, "UNCERTAIN")
        self.assertIsNone(result.review_timeline.review_required)
        self.assertEqual(result.review_timeline.waiting_period_status, "NOT_STATED")
        self.assertIn("could not be verified", result.summary.lower())

        # Provenance verification
        self.assertIn("supports_oauth", result.field_provenance)
        self.assertEqual(
            result.field_provenance["supports_oauth"].evidence_status,
            FieldEvidenceProvenance.UNKNOWN_NOT_STATED,
        )

    def test_m35_02_notion_capabilities_not_query_scopes(self):
        """Verify Notion OAuth implementation: no promotional URLs, empty query scopes, capabilities documented."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="notion",
            name="Notion",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            documentation_url="https://developers.notion.com",
            explanation="Composio managed OAuth is available for Notion.",
        )
        mock_doc = FetchedDoc(
            url="https://developers.notion.com/docs/authorization",
            final_url="https://developers.notion.com/docs/authorization",
            domain="developers.notion.com",
            title="Notion Authorization Guide",
            text="Notion uses OAuth 2.0 authorization code flow. Token exchange uses https://api.notion.com/v1/oauth/token.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Notion",
            website_or_domain="https://www.notion.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        self.assertEqual(result.oauth_details.authorization_endpoint, "https://api.notion.com/v1/oauth/authorize")
        self.assertEqual(result.oauth_details.token_endpoint, "https://api.notion.com/v1/oauth/token")
        self.assertNotIn("notion.so/developers/token", str(result.oauth_details.token_endpoint))

        # Notion does NOT use query parameter scopes; scopes list must be empty
        self.assertEqual(result.scopes, [])
        self.assertIn("scopes", result.field_provenance)
        self.assertIn("capabilities", result.field_provenance["scopes"].notes.lower())

    def test_m35_03_slack_flow_separation(self):
        """Verify Slack OAuth flows are distinctly separated: Workspace Bot Installation vs Sign in with Slack OIDC."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="slack",
            name="Slack",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            documentation_url="https://api.slack.com",
            explanation="Composio managed OAuth is available for Slack.",
        )
        mock_doc = FetchedDoc(
            url="https://api.slack.com/authentication/oauth-v2",
            final_url="https://api.slack.com/authentication/oauth-v2",
            domain="api.slack.com",
            title="Slack OAuth V2",
            text="Slack OAuth V2 uses https://slack.com/oauth/v2/authorize. Granular bot permissions: chat:write, channels:read.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Slack",
            website_or_domain="slack.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        # Main endpoints reflect Bot OAuth V2
        self.assertEqual(result.oauth_details.authorization_endpoint, "https://slack.com/oauth/v2/authorize")
        self.assertEqual(result.oauth_details.token_endpoint, "https://slack.com/api/oauth.v2.access")

        # Additional flows capture both distinct paths
        flows = result.oauth_details.additional_flows
        self.assertGreaterEqual(len(flows), 2)
        flow_names = [f["flow_name"] for f in flows]
        self.assertTrue(any("Bot Installation" in n for n in flow_names))
        self.assertTrue(any("OpenID Connect" in n for n in flow_names))

        # Check OIDC notes emphasize separation
        oidc_flow = next(f for f in flows if "OpenID Connect" in f["flow_name"])
        self.assertIn("never combine", oidc_flow["notes"].lower())

    def test_m35_04_shopify_custom_vs_public_review(self):
        """Verify Shopify OAuth separates Custom Apps (no review) from Public App Store apps (mandatory review)."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="shopify",
            name="Shopify",
            in_catalog=True,
            classification=ComposioClassification.CUSTOM_OAUTH_MANDATORY,
            supports_oauth=True,
            managed_oauth_available=False,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=[],
            documentation_url="https://shopify.dev",
            explanation="Custom OAuth mandatory for Shopify.",
        )
        mock_doc = FetchedDoc(
            url="https://shopify.dev/docs/apps/auth/oauth",
            final_url="https://shopify.dev/docs/apps/auth/oauth",
            domain="shopify.dev",
            title="Shopify OAuth",
            text="Shopify apps use OAuth 2.0 authorization code grant.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Shopify",
            website_or_domain="shopify.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        self.assertIn("{shop}.myshopify.com", result.oauth_details.authorization_endpoint)
        flows = result.oauth_details.additional_flows
        self.assertGreaterEqual(len(flows), 2)

        custom_flow = next(f for f in flows if "Custom App" in f["flow_name"])
        self.assertFalse(custom_flow["review_required"])

        public_flow = next(f for f in flows if "Public App" in f["flow_name"])
        self.assertTrue(public_flow["review_required"])

    def test_m35_05_field_evidence_provenance_structure(self):
        """Verify field_provenance populates all key OAuth fields with structured FieldEvidence models."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="linear",
            name="Linear",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            explanation="Linear managed OAuth available.",
        )
        mock_doc = FetchedDoc(
            url="https://linear.app/docs/oauth",
            final_url="https://linear.app/docs/oauth",
            domain="linear.app",
            title="Linear OAuth",
            text="Linear uses OAuth 2.0. Authorize at https://linear.app/oauth/authorize and token at https://api.linear.app/oauth/token.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Linear",
            website_or_domain="linear.app",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        prov = result.field_provenance
        self.assertIn("supports_oauth", prov)
        self.assertIn("authorization_endpoint", prov)
        self.assertIn("token_endpoint", prov)
        self.assertIn("protocol_version", prov)
        self.assertIn("redirect_uri_rules", prov)
        self.assertIn("composio_managed_available", prov)

        # Validate types
        for key, fe in prov.items():
            self.assertIsInstance(fe, FieldEvidence)
            self.assertIn(fe.evidence_status, list(FieldEvidenceProvenance))

    def test_m33_08_gemini_timeout_fallback_to_evidence_engine(self):
        """Verify that when Gemini times out, fallback to evidence engine produces a successful guide."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="slack",
            name="Slack",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            explanation="Slack OAuth is supported.",
        )
        mock_doc = FetchedDoc(
            url="https://api.slack.com/docs",
            final_url="https://api.slack.com/docs",
            domain="api.slack.com",
            title="Slack Docs",
            text="Slack OAuth 2.0 authorization code flow.",
            status_code=200,
            content_type="text/html",
        )

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(side_effect=asyncio.TimeoutError())

        service = GeminiResearchService(
            api_key="test-key",
            client=mock_client,
            timeout=0.5,
            gemini_enabled=True,
            fallback_to_evidence=True,
        )

        with patch.object(composio_metadata_service, "fetch_toolkit_metadata", AsyncMock(return_value=mock_composio)):
            with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
                result = self.run_async(service.research_app("Slack"))

                self.assertEqual(result.status, ResearchStatus.COMPLETED)
                self.assertTrue(result.oauth_details.supports_oauth)
                self.assertIn("[Evidence-Engine]", result.summary)

    # -----------------------------------------------------------------
    # Milestone 3.5 Tests: Evidence Integrity & OAuth Accuracy Corrections
    # -----------------------------------------------------------------
    def test_m35_01_unknown_application_three_state_semantics(self):
        """Verify that an unknown application without Composio entry or docs yields supports_oauth=None (Unverified)."""
        result = deterministic_evidence_engine.generate_guide(
            app_name="HypotheticalUnverifiedApp999",
            website_or_domain="hypothetical999.invalid",
            composio_status=None,
            fetched_docs=[],
            citations=[],
        )

        self.assertEqual(result.status, ResearchStatus.UNKNOWN_APPLICATION)
        # MUST be None (three-state: True=supported, False=affirmatively unsupported, None=unverified)
        self.assertIsNone(result.oauth_details.supports_oauth)
        self.assertEqual(result.oauth_details.confidence, "UNCERTAIN")
        self.assertIsNone(result.review_timeline.review_required)
        self.assertEqual(result.review_timeline.waiting_period_status, "NOT_STATED")
        self.assertIn("could not be verified", result.summary.lower())

        # Provenance verification
        self.assertIn("supports_oauth", result.field_provenance)
        self.assertEqual(
            result.field_provenance["supports_oauth"].evidence_status,
            FieldEvidenceProvenance.UNKNOWN_NOT_STATED,
        )

    def test_m35_02_notion_capabilities_not_query_scopes(self):
        """Verify Notion OAuth implementation: no promotional URLs, empty query scopes, capabilities documented."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="notion",
            name="Notion",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            documentation_url="https://developers.notion.com",
            explanation="Composio managed OAuth is available for Notion.",
        )
        mock_doc = FetchedDoc(
            url="https://developers.notion.com/docs/authorization",
            final_url="https://developers.notion.com/docs/authorization",
            domain="developers.notion.com",
            title="Notion Authorization Guide",
            text="Notion uses OAuth 2.0 authorization code flow. Token exchange uses https://api.notion.com/v1/oauth/token.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Notion",
            website_or_domain="https://www.notion.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        self.assertEqual(result.oauth_details.authorization_endpoint, "https://api.notion.com/v1/oauth/authorize")
        self.assertEqual(result.oauth_details.token_endpoint, "https://api.notion.com/v1/oauth/token")
        self.assertNotIn("notion.so/developers/token", str(result.oauth_details.token_endpoint))

        # Notion does NOT use query parameter scopes; scopes list must be empty
        self.assertEqual(result.scopes, [])
        self.assertIn("scopes", result.field_provenance)
        self.assertIn("capabilities", result.field_provenance["scopes"].notes.lower())

    def test_m35_03_slack_flow_separation(self):
        """Verify Slack OAuth flows are distinctly separated: Workspace Bot Installation vs Sign in with Slack OIDC."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="slack",
            name="Slack",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            documentation_url="https://api.slack.com",
            explanation="Composio managed OAuth is available for Slack.",
        )
        mock_doc = FetchedDoc(
            url="https://api.slack.com/authentication/oauth-v2",
            final_url="https://api.slack.com/authentication/oauth-v2",
            domain="api.slack.com",
            title="Slack OAuth V2",
            text="Slack OAuth V2 uses https://slack.com/oauth/v2/authorize. Granular bot permissions: chat:write, channels:read.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Slack",
            website_or_domain="slack.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        # Main endpoints reflect Bot OAuth V2
        self.assertEqual(result.oauth_details.authorization_endpoint, "https://slack.com/oauth/v2/authorize")
        self.assertEqual(result.oauth_details.token_endpoint, "https://slack.com/api/oauth.v2.access")

        # Additional flows capture both distinct paths
        flows = result.oauth_details.additional_flows
        self.assertGreaterEqual(len(flows), 2)
        flow_names = [f["flow_name"] for f in flows]
        self.assertTrue(any("Bot Installation" in n for n in flow_names))
        self.assertTrue(any("OpenID Connect" in n for n in flow_names))

        # Check OIDC notes emphasize separation
        oidc_flow = next(f for f in flows if "OpenID Connect" in f["flow_name"])
        self.assertIn("never combine", oidc_flow["notes"].lower())

    def test_m35_04_shopify_custom_vs_public_review(self):
        """Verify Shopify OAuth separates Custom Apps (no review) from Public App Store apps (mandatory review)."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="shopify",
            name="Shopify",
            in_catalog=True,
            classification=ComposioClassification.CUSTOM_OAUTH_MANDATORY,
            supports_oauth=True,
            managed_oauth_available=False,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=[],
            documentation_url="https://shopify.dev",
            explanation="Custom OAuth mandatory for Shopify.",
        )
        mock_doc = FetchedDoc(
            url="https://shopify.dev/docs/apps/auth/oauth",
            final_url="https://shopify.dev/docs/apps/auth/oauth",
            domain="shopify.dev",
            title="Shopify OAuth",
            text="Shopify apps use OAuth 2.0 authorization code grant.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Shopify",
            website_or_domain="shopify.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        self.assertIn("{shop}.myshopify.com", result.oauth_details.authorization_endpoint)
        flows = result.oauth_details.additional_flows
        self.assertGreaterEqual(len(flows), 2)

        custom_flow = next(f for f in flows if "Custom App" in f["flow_name"])
        self.assertFalse(custom_flow["review_required"])

        public_flow = next(f for f in flows if "Public App" in f["flow_name"])
        self.assertTrue(public_flow["review_required"])

    def test_m35_05_field_evidence_provenance_structure(self):
        """Verify field_provenance populates all key OAuth fields with structured FieldEvidence models."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="linear",
            name="Linear",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            explanation="Linear managed OAuth available.",
        )
        mock_doc = FetchedDoc(
            url="https://linear.app/docs/oauth",
            final_url="https://linear.app/docs/oauth",
            domain="linear.app",
            title="Linear OAuth",
            text="Linear uses OAuth 2.0. Authorize at https://linear.app/oauth/authorize and token at https://api.linear.app/oauth/token.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Linear",
            website_or_domain="linear.app",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        prov = result.field_provenance
        self.assertIn("supports_oauth", prov)
        self.assertIn("authorization_endpoint", prov)
        self.assertIn("token_endpoint", prov)
        self.assertIn("protocol_version", prov)
        self.assertIn("redirect_uri_rules", prov)
        self.assertIn("composio_managed_available", prov)

        # Validate types
        for key, fe in prov.items():
            self.assertIsInstance(fe, FieldEvidence)
            self.assertIn(fe.evidence_status, list(FieldEvidenceProvenance))

    def test_m33_09_gemini_invalid_json_fallback_to_evidence_engine(self):
        """Verify that when Gemini returns invalid JSON, fallback to evidence engine executes."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="linear",
            name="Linear",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            explanation="Linear OAuth is supported.",
        )
        mock_doc = FetchedDoc(
            url="https://linear.app/docs/oauth",
            final_url="https://linear.app/docs/oauth",
            domain="linear.app",
            title="Linear Docs",
            text="Linear OAuth 2.0 authorization code flow.",
            status_code=200,
            content_type="text/html",
        )

        mock_response = MagicMock()
        mock_response.output_text = "I am an AI assistant and could not format the output properly."
        mock_response.steps = []

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_response)

        service = GeminiResearchService(
            api_key="test-key",
            client=mock_client,
            gemini_enabled=True,
            fallback_to_evidence=True,
        )

        with patch.object(composio_metadata_service, "fetch_toolkit_metadata", AsyncMock(return_value=mock_composio)):
            with patch.object(doc_fetcher_service, "fetch_documentation_for_app", AsyncMock(return_value=[mock_doc])):
                result = self.run_async(service.research_app("Linear"))

                self.assertEqual(result.status, ResearchStatus.COMPLETED)
                self.assertTrue(result.oauth_details.supports_oauth)
                self.assertIn("[Evidence-Engine]", result.summary)

    # -----------------------------------------------------------------
    # Milestone 3.5 Tests: Evidence Integrity & OAuth Accuracy Corrections
    # -----------------------------------------------------------------
    def test_m35_01_unknown_application_three_state_semantics(self):
        """Verify that an unknown application without Composio entry or docs yields supports_oauth=None (Unverified)."""
        result = deterministic_evidence_engine.generate_guide(
            app_name="HypotheticalUnverifiedApp999",
            website_or_domain="hypothetical999.invalid",
            composio_status=None,
            fetched_docs=[],
            citations=[],
        )

        self.assertEqual(result.status, ResearchStatus.UNKNOWN_APPLICATION)
        # MUST be None (three-state: True=supported, False=affirmatively unsupported, None=unverified)
        self.assertIsNone(result.oauth_details.supports_oauth)
        self.assertEqual(result.oauth_details.confidence, "UNCERTAIN")
        self.assertIsNone(result.review_timeline.review_required)
        self.assertEqual(result.review_timeline.waiting_period_status, "NOT_STATED")
        self.assertIn("could not be verified", result.summary.lower())

        # Provenance verification
        self.assertIn("supports_oauth", result.field_provenance)
        self.assertEqual(
            result.field_provenance["supports_oauth"].evidence_status,
            FieldEvidenceProvenance.UNKNOWN_NOT_STATED,
        )

    def test_m35_02_notion_capabilities_not_query_scopes(self):
        """Verify Notion OAuth implementation: no promotional URLs, empty query scopes, capabilities documented."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="notion",
            name="Notion",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            documentation_url="https://developers.notion.com",
            explanation="Composio managed OAuth is available for Notion.",
        )
        mock_doc = FetchedDoc(
            url="https://developers.notion.com/docs/authorization",
            final_url="https://developers.notion.com/docs/authorization",
            domain="developers.notion.com",
            title="Notion Authorization Guide",
            text="Notion uses OAuth 2.0 authorization code flow. Token exchange uses https://api.notion.com/v1/oauth/token.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Notion",
            website_or_domain="https://www.notion.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        self.assertEqual(result.oauth_details.authorization_endpoint, "https://api.notion.com/v1/oauth/authorize")
        self.assertEqual(result.oauth_details.token_endpoint, "https://api.notion.com/v1/oauth/token")
        self.assertNotIn("notion.so/developers/token", str(result.oauth_details.token_endpoint))

        # Notion does NOT use query parameter scopes; scopes list must be empty
        self.assertEqual(result.scopes, [])
        self.assertIn("scopes", result.field_provenance)
        self.assertIn("capabilities", result.field_provenance["scopes"].notes.lower())

    def test_m35_03_slack_flow_separation(self):
        """Verify Slack OAuth flows are distinctly separated: Workspace Bot Installation vs Sign in with Slack OIDC."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="slack",
            name="Slack",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            documentation_url="https://api.slack.com",
            explanation="Composio managed OAuth is available for Slack.",
        )
        mock_doc = FetchedDoc(
            url="https://api.slack.com/authentication/oauth-v2",
            final_url="https://api.slack.com/authentication/oauth-v2",
            domain="api.slack.com",
            title="Slack OAuth V2",
            text="Slack OAuth V2 uses https://slack.com/oauth/v2/authorize. Granular bot permissions: chat:write, channels:read.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Slack",
            website_or_domain="slack.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        # Main endpoints reflect Bot OAuth V2
        self.assertEqual(result.oauth_details.authorization_endpoint, "https://slack.com/oauth/v2/authorize")
        self.assertEqual(result.oauth_details.token_endpoint, "https://slack.com/api/oauth.v2.access")

        # Additional flows capture both distinct paths
        flows = result.oauth_details.additional_flows
        self.assertGreaterEqual(len(flows), 2)
        flow_names = [f["flow_name"] for f in flows]
        self.assertTrue(any("Bot Installation" in n for n in flow_names))
        self.assertTrue(any("OpenID Connect" in n for n in flow_names))

        # Check OIDC notes emphasize separation
        oidc_flow = next(f for f in flows if "OpenID Connect" in f["flow_name"])
        self.assertIn("never combine", oidc_flow["notes"].lower())

    def test_m35_04_shopify_custom_vs_public_review(self):
        """Verify Shopify OAuth separates Custom Apps (no review) from Public App Store apps (mandatory review)."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="shopify",
            name="Shopify",
            in_catalog=True,
            classification=ComposioClassification.CUSTOM_OAUTH_MANDATORY,
            supports_oauth=True,
            managed_oauth_available=False,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=[],
            documentation_url="https://shopify.dev",
            explanation="Custom OAuth mandatory for Shopify.",
        )
        mock_doc = FetchedDoc(
            url="https://shopify.dev/docs/apps/auth/oauth",
            final_url="https://shopify.dev/docs/apps/auth/oauth",
            domain="shopify.dev",
            title="Shopify OAuth",
            text="Shopify apps use OAuth 2.0 authorization code grant.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Shopify",
            website_or_domain="shopify.com",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        self.assertIn("{shop}.myshopify.com", result.oauth_details.authorization_endpoint)
        flows = result.oauth_details.additional_flows
        self.assertGreaterEqual(len(flows), 2)

        custom_flow = next(f for f in flows if "Custom App" in f["flow_name"])
        self.assertFalse(custom_flow["review_required"])

        public_flow = next(f for f in flows if "Public App" in f["flow_name"])
        self.assertTrue(public_flow["review_required"])

    def test_m35_05_field_evidence_provenance_structure(self):
        """Verify field_provenance populates all key OAuth fields with structured FieldEvidence models."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="linear",
            name="Linear",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            explanation="Linear managed OAuth available.",
        )
        mock_doc = FetchedDoc(
            url="https://linear.app/docs/oauth",
            final_url="https://linear.app/docs/oauth",
            domain="linear.app",
            title="Linear OAuth",
            text="Linear uses OAuth 2.0. Authorize at https://linear.app/oauth/authorize and token at https://api.linear.app/oauth/token.",
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Linear",
            website_or_domain="linear.app",
            composio_status=mock_composio,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        prov = result.field_provenance
        self.assertIn("supports_oauth", prov)
        self.assertIn("authorization_endpoint", prov)
        self.assertIn("token_endpoint", prov)
        self.assertIn("protocol_version", prov)
        self.assertIn("redirect_uri_rules", prov)
        self.assertIn("composio_managed_available", prov)

        # Validate types
        for key, fe in prov.items():
            self.assertIsInstance(fe, FieldEvidence)
            self.assertIn(fe.evidence_status, list(FieldEvidenceProvenance))

    # -----------------------------------------------------------------
    # Milestone 3.6 Tests: Final Evidence Integrity & Provenance Authenticity
    # -----------------------------------------------------------------
    def test_m36_01_no_fabricated_excerpts_when_docs_empty(self):
        """Verify that when docs are empty, endpoints remain None and excerpts are never fabricated."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="notion",
            name="Notion",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            explanation="Notion managed OAuth available.",
        )

        result = deterministic_evidence_engine.generate_guide(
            app_name="Notion",
            website_or_domain="notion.so",
            composio_status=mock_composio,
            fetched_docs=[],
            citations=[],
        )

        # Endpoints must be None because no docs containing them were fetched
        self.assertIsNone(result.oauth_details.authorization_endpoint)
        self.assertIsNone(result.oauth_details.token_endpoint)
        self.assertIsNone(result.review_timeline.review_required)
        self.assertEqual(result.review_timeline.waiting_period_status, "NOT_STATED")

        # Provenance must state UNKNOWN_NOT_STATED and have None excerpt (zero code fabrication)
        prov = result.field_provenance
        self.assertEqual(prov["authorization_endpoint"].evidence_status, FieldEvidenceProvenance.UNKNOWN_NOT_STATED)
        self.assertIsNone(prov["authorization_endpoint"].evidence_excerpt)
        self.assertEqual(prov["token_endpoint"].evidence_status, FieldEvidenceProvenance.UNKNOWN_NOT_STATED)
        self.assertIsNone(prov["token_endpoint"].evidence_excerpt)
        self.assertEqual(prov["review_required"].evidence_status, FieldEvidenceProvenance.UNKNOWN_NOT_STATED)
        self.assertIsNone(prov["review_required"].evidence_excerpt)

    def test_m36_02_composio_provenance_actual_toolkit_url(self):
        """Verify Composio provenance points to actual toolkit URL rather than generic homepage."""
        mock_composio = ComposioToolkitCheckResponse(
            slug="slack",
            name="Slack",
            in_catalog=True,
            classification=ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
            supports_oauth=True,
            managed_oauth_available=True,
            supported_auth_schemes=["OAUTH2"],
            managed_auth_schemes=["OAUTH2"],
            explanation="Slack managed OAuth available.",
        )

        result = deterministic_evidence_engine.generate_guide(
            app_name="Slack",
            website_or_domain="slack.com",
            composio_status=mock_composio,
            fetched_docs=[],
            citations=[],
        )

        expected_url = f"{settings.COMPOSIO_BASE_URL.rstrip('/')}/toolkits/slack"
        self.assertEqual(result.field_provenance["supports_oauth"].source_url, expected_url)
        self.assertEqual(result.field_provenance["composio_managed_available"].source_url, expected_url)
        self.assertNotEqual(result.field_provenance["supports_oauth"].source_url, "https://composio.dev")

    def test_m36_03_real_excerpt_extraction_from_doc_text(self):
        """Verify evidence excerpt is a genuine verbatim substring of retrieved doc.text."""
        doc_text = "Acme provides OAuth 2.0 authorization code grant. The authorization endpoint is https://api.acme.com/oauth/authorize and token endpoint is https://api.acme.com/oauth/token."
        mock_doc = FetchedDoc(
            url="https://developer.acme.com/oauth",
            final_url="https://developer.acme.com/oauth",
            domain="developer.acme.com",
            title="Acme OAuth",
            text=doc_text,
            status_code=200,
            content_type="text/html",
        )
        citations = build_citations_from_docs([mock_doc])

        result = deterministic_evidence_engine.generate_guide(
            app_name="Acme",
            website_or_domain="acme.com",
            composio_status=None,
            fetched_docs=[mock_doc],
            citations=citations,
        )

        self.assertEqual(result.oauth_details.authorization_endpoint, "https://api.acme.com/oauth/authorize")
        auth_excerpt = result.field_provenance["authorization_endpoint"].evidence_excerpt
        self.assertIsNotNone(auth_excerpt)
        # Excerpt must be an exact substring of the doc text
        self.assertIn(auth_excerpt, doc_text)

    def test_m36_04_guide_store_preserves_nullable_review(self):
        """Verify guide storage service preserves review_required=None without defaulting to 0 days or instant."""
        from app.services.store import convert_research_result_to_guide

        unknown_result = deterministic_evidence_engine.generate_guide(
            app_name="MysteryService",
            website_or_domain="mystery.invalid",
            composio_status=None,
            fetched_docs=[],
            citations=[],
        )

        guide = convert_research_result_to_guide(unknown_result)
        self.assertIsNone(guide.provider_review.review_required)
        self.assertEqual(guide.provider_review.status, "NOT_STATED")
        self.assertEqual(guide.provider_review.confidence, "UNCERTAIN")
        self.assertIsNone(guide.provider_review.wait_days_min)
        self.assertIsNone(guide.provider_review.wait_days_max)
        self.assertIsNone(guide.provider_review.review_type)
        self.assertNotEqual(guide.provider_review.conditions, "Instant development access")

    def test_m36_05_nat64_ipv6_embedded_v4_ssrf_validation(self):
        """Verify SSRF validator handles RFC 6052 NAT64 addresses by checking embedded IPv4."""
        import ipaddress
        from app.services.doc_fetcher import SSRFSecurityValidator

        # 1. Public IPv4 (93.184.216.34) embedded in NAT64 (64:ff9b::93.184.216.34) -> Allowed
        public_nat64 = ipaddress.IPv6Address("64:ff9b::5db8:d822")  # 93.184.216.34 in hex
        blocked, reason = SSRFSecurityValidator.is_ip_blocked(public_nat64)
        self.assertFalse(blocked)
        self.assertEqual(reason, "")

        # 2. Loopback IPv4 (127.0.0.1) embedded in NAT64 -> Blocked
        loopback_nat64 = ipaddress.IPv6Address("64:ff9b::7f00:0001")  # 127.0.0.1
        blocked, reason = SSRFSecurityValidator.is_ip_blocked(loopback_nat64)
        self.assertTrue(blocked)
        self.assertIn("Loopback address blocked", reason)

        # 3. Cloud metadata IPv4 (169.254.169.254) embedded in NAT64 -> Blocked
        metadata_nat64 = ipaddress.IPv6Address("64:ff9b::a9fe:a9fe")  # 169.254.169.254
        blocked, reason = SSRFSecurityValidator.is_ip_blocked(metadata_nat64)
        self.assertTrue(blocked)
        self.assertIn("Cloud metadata", reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)