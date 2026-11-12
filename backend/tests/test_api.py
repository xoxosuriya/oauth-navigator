import sys
import os
import unittest
import asyncio
import copy
import tempfile
import httpx
from pydantic import ValidationError

# Ensure backend root is the first entry in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app
from app.api.v1.routes import (
    health_check,
    list_apps,
    get_app_guide,
    share_guide,
    investigate_app
)
from app.models.guide import (
    OAuthGuide,
    SourceItem,
    ShareGuideRequest,
    InvestigateRequest,
)
from app.services.store import GuideStore, guide_store
from app.core.config import Settings, settings, load_backend_env, get_backend_dir
from fastapi import HTTPException

class TestBackendFunctionality(unittest.TestCase):
    def run_async(self, coro):
        return asyncio.run(coro)

    # -------------------------------------------------------------
    # Existing Tests 1-7 (Retained and Verified)
    # -------------------------------------------------------------
    def test_01_health_check(self):
        """Verify health check returns expected status and ISO timestamp."""
        res = self.run_async(health_check())
        self.assertEqual(res["status"], "healthy")
        self.assertIn("timestamp", res)

    def test_02_seed_data_evidence_traceability(self):
        """
        Verify that all curated seed data conforms to strict schema requirements:
        1. Claim-level confidence on active_effort and provider_review.
        2. Supporting page_section and evidence_excerpt on SourceItem.
        3. All source_ids referenced in claims resolve to verified SourceItems.
        4. No illustrative sample values are marked as verified facts.
        """
        guides = guide_store.list_guides()
        self.assertGreaterEqual(len(guides), 3, "Expected at least 3 curated seed guides.")

        for summary in guides:
            guide = guide_store.get_guide(summary.id)
            self.assertIsNotNone(guide)
            self.assertIsInstance(guide, OAuthGuide)

            # Claim-level confidence verification
            self.assertIn(guide.active_effort.confidence, ["VERIFIED_TESTED", "OFFICIAL_DOCS", "ESTIMATE_HEURISTIC", "UNCERTAIN"])
            self.assertIn(guide.provider_review.confidence, ["VERIFIED_TESTED", "OFFICIAL_DOCS", "ESTIMATE_HEURISTIC", "UNCERTAIN"])
            
            # Source registry check
            source_map = {}
            for src in guide.sources:
                self.assertTrue(src.id)
                self.assertTrue(src.url.startswith("http"))
                self.assertIsNotNone(src.page_section, f"Missing page_section on {src.id} in {guide.slug}")
                self.assertIsNotNone(src.evidence_excerpt, f"Missing evidence_excerpt on {src.id} in {guide.slug}")
                self.assertEqual(src.retrieval_status, "CURATED_STATIC")
                # Ensure no fake live HTTP status codes are asserted on static curated docs
                self.assertIsNone(src.http_status_code)
                source_map[src.id] = src

            # All claim source_ids must resolve
            for sid in guide.active_effort.source_ids:
                self.assertIn(sid, source_map, f"active_effort in {guide.slug} references missing {sid}")
            for sid in guide.provider_review.source_ids:
                self.assertIn(sid, source_map, f"provider_review in {guide.slug} references missing {sid}")
            for step in guide.setup_steps:
                for sid in step.source_ids:
                    self.assertIn(sid, source_map, f"Step '{step.title}' in {guide.slug} references missing {sid}")
            for blocker in guide.blockers:
                for sid in blocker.source_ids:
                    self.assertIn(sid, source_map, f"Blocker '{blocker.title}' in {guide.slug} references missing {sid}")

    def test_03_list_apps_and_filters(self):
        """Verify list_apps endpoint filtering logic."""
        # Unfiltered
        all_apps = self.run_async(list_apps())
        self.assertGreaterEqual(all_apps.total, 3)

        # Search filter
        slack_search = self.run_async(list_apps(search="slack"))
        self.assertEqual(slack_search.total, 1)
        self.assertEqual(slack_search.items[0].slug, "slack")

        # Managed only filter (Gmail, Slack)
        managed_apps = self.run_async(list_apps(managed_only=True))
        for item in managed_apps.items:
            self.assertTrue(item.composio_status.managed_oauth_available)

        # Unmanaged / BYO OAuth app filter (Shopify)
        custom_apps = self.run_async(list_apps(managed_only=False))
        self.assertGreaterEqual(custom_apps.total, 1)
        for item in custom_apps.items:
            self.assertFalse(item.composio_status.managed_oauth_available)

    def test_04_get_guide_lookup(self):
        """Verify guide retrieval by slug, by ID, and 404 behavior."""
        # By slug
        slack_guide = self.run_async(get_app_guide("slack"))
        self.assertEqual(slack_guide.app_name, "Slack")
        self.assertEqual(slack_guide.difficulty_rating, "VERY_EASY")
        self.assertTrue(slack_guide.composio_status.managed_oauth_available)

        # By ID
        shopify_guide = self.run_async(get_app_guide("shopify-oauth-guide"))
        self.assertEqual(shopify_guide.slug, "shopify")
        self.assertTrue(shopify_guide.composio_status.custom_oauth_mandatory_for_oauth)

        # Unknown app -> 404 HTTPException
        with self.assertRaises(HTTPException) as ctx:
            self.run_async(get_app_guide("nonexistent-app"))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_05_share_guide(self):
        """Verify permanent share link generation."""
        req = ShareGuideRequest(guide_id="slack-oauth-guide")
        res = self.run_async(share_guide(req))
        self.assertEqual(res.guide_id, "slack-oauth-guide")
        self.assertTrue(res.share_url.startswith("http"))
        self.assertIn("/guide/slack-oauth-guide", res.share_url)

        # Unknown guide -> 404
        with self.assertRaises(HTTPException) as ctx:
            self.run_async(share_guide(ShareGuideRequest(guide_id="invalid-id")))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_05b_get_shared_guide(self):
        """Verify public share retrieval by share_id."""
        from app.api.v1.routes import get_shared_guide
        guide = self.run_async(get_shared_guide("slack-oauth-guide"))
        self.assertEqual(guide.slug, "slack")

        # By slug
        guide_by_slug = self.run_async(get_shared_guide("slack"))
        self.assertEqual(guide_by_slug.id, "slack-oauth-guide")

        with self.assertRaises(HTTPException) as ctx:
            self.run_async(get_shared_guide("invalid-nonexistent-guide"))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_06_investigate_stub_contract(self):
        """Verify investigate endpoint returns cached guide if present or executes research service."""
        # Cached app
        cached_res = self.run_async(investigate_app(InvestigateRequest(app_name="Slack")))
        self.assertEqual(cached_res.slug, "slack")

        # Unknown unverified app -> 404
        with self.assertRaises(HTTPException) as ctx:
            self.run_async(investigate_app(InvestigateRequest(app_name="CompletelyFakeAppXYZ999")))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_07_cors_security(self):
        """Verify CORS settings do not contain wildcard '*'."""
        self.assertNotIn("*", settings.ALLOWED_ORIGINS, "CORS allowed origins must never contain wildcard '*'")
        self.assertIn("http://localhost:3000", settings.ALLOWED_ORIGINS)

    # -------------------------------------------------------------
    # Milestone 1.1 Tests (Retained and Verified)
    # -------------------------------------------------------------
    def test_08_safe_environment_configuration(self):
        """Verify environment flags evaluate safely to booleans without exposing secrets."""
        self.assertIsInstance(settings.is_composio_configured, bool)
        self.assertIsInstance(settings.is_gemini_configured, bool)
        self.assertTrue(isinstance(settings.FRONTEND_BASE_URL, str) and settings.FRONTEND_BASE_URL.startswith("http"))
        self.assertFalse(settings.FRONTEND_BASE_URL.endswith("/"))

    def test_09_model_validation_rejects_dangling_source_ids(self):
        """Verify Pydantic model validator rejects guides containing unregistered source_ids."""
        slack = guide_store.get_guide("slack")
        self.assertIsNotNone(slack)
        
        guide_dict = copy.deepcopy(slack.model_dump())
        guide_dict["active_effort"]["source_ids"] = ["src-ghost-nonexistent"]

        with self.assertRaises(ValidationError) as ctx:
            OAuthGuide.model_validate(guide_dict)
        
        self.assertIn("Dangling source reference", str(ctx.exception))
        self.assertIn("src-ghost-nonexistent", str(ctx.exception))

    def test_10_model_validation_requires_evidence_for_official_docs(self):
        """Verify SourceItem validator enforces non-empty evidence_excerpt and page_section for OFFICIAL_DOCS."""
        # Missing evidence_excerpt
        with self.assertRaises(ValidationError):
            SourceItem(
                id="src-invalid-01",
                title="Test Source",
                url="https://docs.example.com",
                page_section="Section 1",
                evidence_excerpt="",
                confidence="OFFICIAL_DOCS"
            )

        # Missing page_section
        with self.assertRaises(ValidationError):
            SourceItem(
                id="src-invalid-02",
                title="Test Source",
                url="https://docs.example.com",
                page_section=None,
                evidence_excerpt="Valid quote excerpt.",
                confidence="OFFICIAL_DOCS"
            )

    def test_11_persistence_restart_round_trip(self):
        """Verify that newly saved guides persist to disk and reload on a freshly instantiated GuideStore."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store1 = GuideStore(data_dir=temp_dir)
            self.assertEqual(len(store1.list_guides()), 0)

            slack = guide_store.get_guide("slack")
            test_guide = copy.deepcopy(slack)
            test_guide.id = "roundtrip-test-guide"
            test_guide.slug = "roundtrip-test"
            test_guide.app_name = "Roundtrip Test App"
            store1.save_guide(test_guide)

            self.assertEqual(len(store1.list_guides()), 1)
            self.assertIsNotNone(store1.get_guide("roundtrip-test"))

            store2 = GuideStore(data_dir=temp_dir)
            reloaded_guides = store2.list_guides()
            self.assertEqual(len(reloaded_guides), 1)
            reloaded = store2.get_guide("roundtrip-test")
            self.assertIsNotNone(reloaded)
            self.assertEqual(reloaded.id, "roundtrip-test-guide")
            self.assertEqual(reloaded.app_name, "Roundtrip Test App")

    def test_12_http_fastapi_endpoints_round_trip(self):
        """Verify full HTTP round-trip through FastAPI ASGI application using httpx."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                res_root = await client.get("/")
                self.assertEqual(res_root.status_code, 200)
                self.assertIn("docs_url", res_root.json())

                res_health = await client.get("/api/v1/health")
                self.assertEqual(res_health.status_code, 200)
                self.assertEqual(res_health.json()["status"], "healthy")

                res_apps = await client.get("/api/v1/apps")
                self.assertEqual(res_apps.status_code, 200)
                self.assertGreaterEqual(res_apps.json()["total"], 3)

                res_slack = await client.get("/api/v1/apps/slack")
                self.assertEqual(res_slack.status_code, 200)
                slack_json = res_slack.json()
                self.assertEqual(slack_json["slug"], "slack")
                self.assertTrue(slack_json["composio_status"]["managed_oauth_available"])
                
                step_types = [s["path_type"] for s in slack_json["setup_steps"]]
                self.assertIn("MANAGED_OAUTH", step_types)
                self.assertIn("CUSTOM_OAUTH", step_types)

                res_share = await client.post("/api/v1/guides/share", json={"guide_id": "slack-oauth-guide"})
                self.assertEqual(res_share.status_code, 200)
                self.assertIn("/guide/slack-oauth-guide", res_share.json()["share_url"])

                res_get_share = await client.get("/api/v1/guides/share/slack-oauth-guide")
                self.assertEqual(res_get_share.status_code, 200)
                self.assertEqual(res_get_share.json()["slug"], "slack")

                res_inv = await client.post("/api/v1/investigate", json={"app_name": "CompletelyFakeAppXYZ999"})
                self.assertEqual(res_inv.status_code, 404)

        self.run_async(_test())

    # -------------------------------------------------------------
    # Milestone 1.2 Tests (Retained and Verified)
    # -------------------------------------------------------------
    def test_13_env_loading_from_backend_path(self):
        """Verify that backend .env is explicitly resolved and loaded using dummy values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dummy_env_file = os.path.join(temp_dir, ".env")
            with open(dummy_env_file, "w", encoding="utf-8") as f:
                f.write("TEST_DUMMY_VAR=backend_path_verified\n")
            
            # Clean up env before test
            os.environ.pop("TEST_DUMMY_VAR", None)
            
            loaded = load_backend_env(dummy_env_file)
            self.assertTrue(loaded)
            self.assertEqual(os.getenv("TEST_DUMMY_VAR"), "backend_path_verified")
            
            # Cleanup
            os.environ.pop("TEST_DUMMY_VAR", None)

    def test_14_os_environment_variable_precedence(self):
        """
        Verify that an OS environment variable already set takes precedence
        over the value defined in .env (because override=False).
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            dummy_env_file = os.path.join(temp_dir, ".env")
            with open(dummy_env_file, "w", encoding="utf-8") as f:
                f.write("PRECEDENCE_TEST_KEY=from_env_file\n")
            
            # Set the OS variable first
            os.environ["PRECEDENCE_TEST_KEY"] = "from_os_environment"
            
            # Load with override=False
            load_backend_env(dummy_env_file)
            
            # OS value must be preserved
            self.assertEqual(os.getenv("PRECEDENCE_TEST_KEY"), "from_os_environment")
            
            # Cleanup
            os.environ.pop("PRECEDENCE_TEST_KEY", None)

    def test_15_behavior_when_env_file_absent(self):
        """Verify that when the .env file is absent, load_backend_env returns False and Settings uses safe defaults."""
        nonexistent_path = os.path.join(tempfile.gettempdir(), "nonexistent_secret_123.env")
        if os.path.exists(nonexistent_path):
            os.remove(nonexistent_path)
        
        # Must return False and not raise an error
        result = load_backend_env(nonexistent_path)
        self.assertFalse(result)

        # Settings model must initialize with clean defaults without error
        fallback_settings = Settings()
        self.assertEqual(fallback_settings.VERSION, "1.0.0")
        self.assertIsInstance(fallback_settings.ALLOWED_ORIGINS, list)
        self.assertNotIn("*", fallback_settings.ALLOWED_ORIGINS)

    # -------------------------------------------------------------
    # Milestone 1.3 New Tests: Independent OAuth & CASA Classification
    # -------------------------------------------------------------
    def test_16_google_oauth_and_casa_independent_representation(self):
        """Verify that Google OAuth brand verification and CASA security assessment are independently represented."""
        gmail = guide_store.get_guide("gmail")
        self.assertIsNotNone(gmail)
        self.assertGreaterEqual(len(gmail.review_requirements), 2)

        req_types = {r.requirement_type: r for r in gmail.review_requirements}
        self.assertIn("OAUTH_VERIFICATION", req_types, "Gmail guide must specify OAUTH_VERIFICATION independently.")
        self.assertIn("SECURITY_ASSESSMENT", req_types, "Gmail guide must specify SECURITY_ASSESSMENT independently.")

        oauth_req = req_types["OAUTH_VERIFICATION"]
        casa_req = req_types["SECURITY_ASSESSMENT"]

        # Assert independent IDs and titles
        self.assertNotEqual(oauth_req.id, casa_req.id)
        self.assertIn("OAuth", oauth_req.title)
        self.assertIn("CASA", casa_req.title)

        # Assert different scope tiers and conditions
        self.assertEqual(oauth_req.scope_tier, "SENSITIVE")
        self.assertEqual(casa_req.scope_tier, "RESTRICTED")

    def test_17_casa_conditional_applicability(self):
        """Verify that CASA is conditional on data architecture and restricted scopes, not universally required."""
        gmail = guide_store.get_guide("gmail")
        casa_req = next((r for r in gmail.review_requirements if r.requirement_type == "SECURITY_ASSESSMENT"), None)
        self.assertIsNotNone(casa_req)

        # Applicability must be CONDITIONAL, not mandatory for all
        self.assertEqual(casa_req.applicability, "CONDITIONAL")
        self.assertTrue(casa_req.annual_reassessment_required)
        self.assertIn("third-party", casa_req.conditions.lower())
        self.assertIn("server", casa_req.conditions.lower())
        self.assertIn("risk-based assurance", casa_req.assurance_level.lower())

    def test_18_review_requirements_source_references_valid(self):
        """Verify that all review requirements in all seed guides have valid, registered source_ids."""
        for summary in guide_store.list_guides():
            guide = guide_store.get_guide(summary.id)
            registered_source_ids = {s.id for s in guide.sources}
            for req in guide.review_requirements:
                self.assertGreater(len(req.source_ids), 0, f"Requirement '{req.id}' in '{guide.slug}' has empty source_ids.")
                for sid in req.source_ids:
                    self.assertIn(sid, registered_source_ids, f"Requirement '{req.id}' in '{guide.slug}' references unknown source '{sid}'.")

    def test_19_gmail_testing_mode_and_expiration_intact(self):
        """Verify Testing-mode information, 7-day token expiration warning, and sources remain intact."""
        gmail = guide_store.get_guide("gmail")
        
        # Verify 7-day expiration blocker exists
        exp_blocker = next((b for b in gmail.blockers if b.id == "blk-google-02"), None)
        self.assertIsNotNone(exp_blocker)
        self.assertIn("seven days", exp_blocker.description.lower())
        self.assertIn("src-google-02", exp_blocker.source_ids)

        # Verify Google testing expiration source exists
        exp_source = next((s for s in gmail.sources if s.id == "src-google-02"), None)
        self.assertIsNotNone(exp_source)
        self.assertIn("13465431", exp_source.url)
        self.assertIn("expire after seven days", exp_source.evidence_excerpt)

    def test_20_api_serialization_of_review_requirements(self):
        """Verify that API endpoints serialize review_requirements and preserve provider_review."""
        async def _test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                res = await client.get("/api/v1/apps/gmail")
                self.assertEqual(res.status_code, 200)
                data = res.json()

                # High-level summary preserved
                self.assertIn("provider_review", data)
                self.assertEqual(data["provider_review"]["status"], "NOT_STATED")

                # Granular list serialized
                self.assertIn("review_requirements", data)
                self.assertIsInstance(data["review_requirements"], list)
                self.assertGreaterEqual(len(data["review_requirements"]), 2)
                
                # Check fields in serialized item
                oauth_item = next((r for r in data["review_requirements"] if r["requirement_type"] == "OAUTH_VERIFICATION"), None)
                self.assertIsNotNone(oauth_item)
                self.assertEqual(oauth_item["applicability"], "CONDITIONAL")
                self.assertIn("source_ids", oauth_item)

        self.run_async(_test())

if __name__ == "__main__":
    unittest.main()
