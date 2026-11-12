import sys
import os
import unittest
import asyncio

# Ensure backend root is the first entry in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.api.v1.routes import (
    health_check,
    get_app_guide,
    investigate_app,
)
from app.models.guide import InvestigateRequest
from app.services.store import guide_store, KNOWN_ALIASES
from app.services.doc_fetcher import DocFetcherService, KNOWN_APP_DOMAINS


class TestProductionFixes(unittest.TestCase):
    """Regression tests for targeted production bug fixes."""

    def run_async(self, coro):
        return asyncio.run(coro)

    # -------------------------------------------------------------------------
    # FIX 1: Gmail display-name and alias lookup
    # -------------------------------------------------------------------------
    def test_fix1_store_gmail_aliases_and_display_name(self):
        """Verify that get_guide correctly resolves Gmail by slug, title, and aliases."""
        test_inputs = [
            "gmail",
            "Gmail",
            "GMAIL",
            "Gmail / Google Workspace",
            "gmail / google workspace",
            "Google Workspace",
            "google workspace",
            "google-workspace",
            "gsuite",
            "g suite",
            "G Suite",
        ]
        for name in test_inputs:
            guide = guide_store.get_guide(name)
            self.assertIsNotNone(guide, f"Failed to resolve Gmail guide for query: {name}")
            self.assertEqual(guide.id, "gmail-oauth-guide", f"Resolved wrong guide for: {name}")
            self.assertEqual(guide.slug, "gmail")

    def test_fix1_store_slack_and_shopify_remain_functional(self):
        """Verify that existing Slack and Shopify guides continue resolving accurately."""
        for query in ["slack", "Slack", "SLACK"]:
            guide = guide_store.get_guide(query)
            self.assertIsNotNone(guide, f"Failed to resolve Slack guide for: {query}")
            self.assertEqual(guide.id, "slack-oauth-guide")

        for query in ["shopify", "Shopify", "SHOPIFY"]:
            guide = guide_store.get_guide(query)
            self.assertIsNotNone(guide, f"Failed to resolve Shopify guide for: {query}")
            self.assertEqual(guide.id, "shopify-oauth-guide")

    def test_fix1_unrelated_apps_do_not_falsely_match_aliases(self):
        """Verify that unrelated app names do not match Gmail aliases."""
        unrelated = ["linear", "notion", "github", "random_nonexistent_service_xyz"]
        for query in unrelated:
            guide = guide_store.get_guide(query)
            self.assertIsNone(guide, f"Unrelated app '{query}' unexpectedly resolved a guide")

    def test_fix1_api_get_guide_and_investigate_with_display_name(self):
        """Verify that GET /apps/{id_or_slug} and POST /investigate succeed with Gmail display name."""
        # 1. API GET guide
        guide = self.run_async(get_app_guide("Gmail / Google Workspace"))
        self.assertEqual(guide.id, "gmail-oauth-guide")

        guide_workspace = self.run_async(get_app_guide("Google Workspace"))
        self.assertEqual(guide_workspace.id, "gmail-oauth-guide")

        # 2. API POST investigate returns cached seed guide without triggering research error
        inv_res = self.run_async(investigate_app(InvestigateRequest(app_name="Gmail / Google Workspace")))
        self.assertEqual(inv_res.id, "gmail-oauth-guide")

        inv_res_gw = self.run_async(investigate_app(InvestigateRequest(app_name="Google Workspace")))
        self.assertEqual(inv_res_gw.id, "gmail-oauth-guide")

    # -------------------------------------------------------------------------
    # FIX 4: Safer unfamiliar application domain discovery
    # -------------------------------------------------------------------------
    def test_fix4_linear_resolves_to_linear_app_not_linear_com(self):
        """Verify that Linear uses linear.app instead of fabricating linear.com."""
        fetcher = DocFetcherService()
        candidates = fetcher.discover_candidate_urls("Linear")
        self.assertTrue(len(candidates) > 0, "No candidate URLs generated for Linear")

        # Ensure linear.app is present
        has_linear_app = any("linear.app" in url for url in candidates)
        self.assertTrue(has_linear_app, f"Expected linear.app in candidates, got: {candidates}")

        # Ensure linear.com is NOT present
        has_linear_com = any("linear.com" in url for url in candidates)
        self.assertFalse(has_linear_com, f"linear.com was unexpectedly generated: {candidates}")

    def test_fix4_notion_resolves_to_notion_com(self):
        """Verify that Notion maps to notion.com developer endpoints."""
        fetcher = DocFetcherService()
        candidates = fetcher.discover_candidate_urls("Notion")
        self.assertTrue(len(candidates) > 0, "No candidate URLs generated for Notion")
        has_notion_com = any("notion.com" in url for url in candidates)
        self.assertTrue(has_notion_com, f"Expected notion.com in candidates, got: {candidates}")

    def test_fix4_user_supplied_website_takes_precedence(self):
        """Verify that user-supplied website or domain overrides default heuristic."""
        fetcher = DocFetcherService()
        candidates = fetcher.discover_candidate_urls(
            app_name="Linear",
            website_or_domain="https://custom-linear-portal.example.org"
        )
        self.assertTrue(any("custom-linear-portal.example.org" in url for url in candidates))

    def test_fix4_known_app_domains_coverage(self):
        """Verify known developer platform domains exist in registry."""
        self.assertEqual(KNOWN_APP_DOMAINS.get("linear"), "linear.app")
        self.assertEqual(KNOWN_APP_DOMAINS.get("notion"), "notion.com")
        self.assertEqual(KNOWN_APP_DOMAINS.get("slack"), "slack.com")
        self.assertEqual(KNOWN_APP_DOMAINS.get("shopify"), "shopify.com")
        self.assertEqual(KNOWN_APP_DOMAINS.get("zoom"), "zoom.us")

    # -------------------------------------------------------------------------
    # FIX 3: Health check endpoint contract
    # -------------------------------------------------------------------------
    def test_fix3_health_check_contract(self):
        """Verify health check returns status 'healthy' for frontend UI matching."""
        res = self.run_async(health_check())
        self.assertEqual(res.get("status"), "healthy")


if __name__ == "__main__":
    unittest.main()
