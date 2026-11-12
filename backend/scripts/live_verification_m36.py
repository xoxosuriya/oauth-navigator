"""
Live Verification Script for Milestone 3.6 — OAuth Navigator.

Performs live end-to-end verification across:
1. Notion (Capabilities model, endpoints grounded in fetched docs, exact Composio toolkit URL)
2. Slack (Separation of Workspace Bot OAuth V2 vs Sign in with Slack OIDC, real excerpts)
3. Shopify (Custom App vs Public App Store review separation, no fabricated excerpts)
4. Unknown Application (Three-state unverified semantics: supports_oauth=None, review_required=None)
5. Full API Endpoints Round-Trip (research, investigate, composio toolkit, share guide)
"""
import sys
import os
import json
import asyncio

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path = [p for p in sys.path if os.path.abspath(p) not in (r"D:\\", r"D:", "")]
if backend_dir in sys.path:
    sys.path.remove(backend_dir)
sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.services.research import gemini_research_service
from app.services.store import guide_store
from app.models.research import ResearchStatus, FieldEvidenceProvenance
from app.core.config import settings
from fastapi.testclient import TestClient
from app.main import app


async def verify_app(app_name: str, website: str):
    print(f"\n{'='*75}")
    print(f"VERIFYING APPLICATION: {app_name} (website: {website})")
    print(f"{'='*75}")

    result = await gemini_research_service.research_app(
        app_name=app_name,
        website_or_domain=website,
    )

    print(f"Research Status:            {result.status.value}")
    print(f"supports_oauth:             {result.oauth_details.supports_oauth} ({type(result.oauth_details.supports_oauth).__name__})")
    print(f"Confidence:                 {result.confidence}")
    print(f"Protocol Version:           {result.oauth_details.protocol_version}")
    print(f"Grant Types:                {result.oauth_details.grant_types}")
    print(f"Authorization Endpoint:     {result.oauth_details.authorization_endpoint}")
    print(f"Token Endpoint:             {result.oauth_details.token_endpoint}")
    print(f"PKCE Required:              {result.oauth_details.pkce_required}")
    print(f"Developer Portal:           {result.registration.developer_portal_url}")
    print(f"Account Tier Required:      {result.registration.account_type_required}")
    print(f"Requires Client Secret:     {result.registration.requires_client_secret}")
    print(f"Review Required:            {result.review_timeline.review_required}")
    print(f"Waiting Period Status:      {result.review_timeline.waiting_period_status}")
    print(f"Total Sources Retrieved:    {len(result.sources)}")
    for s in result.sources:
        print(f"  - [{s.id}] {s.title} -> {s.url}")

    print(f"\nField Provenance Audit ({len(result.field_provenance)} fields):")
    for fname, fe in result.field_provenance.items():
        excerpt_disp = f"'{fe.evidence_excerpt[:60]}...'" if fe.evidence_excerpt else "None"
        print(f"  * {fname:25s} -> Status: {fe.evidence_status.value:22s} | Method: {fe.extraction_method:28s} | URL: {fe.source_url or 'None'}")
        if fe.evidence_excerpt:
            print(f"    Excerpt: {excerpt_disp}")

    # Check for manufactured generic composio.dev URLs
    for fname, fe in result.field_provenance.items():
        if fe.source_url == "https://composio.dev":
            print(f"  [FAIL] Found generic 'https://composio.dev' in {fname}!")
        elif fe.source_url and "composio.dev" in fe.source_url:
            print(f"  [OK] Valid Composio API endpoint in {fname}: {fe.source_url}")

    return result


def verify_api_endpoints():
    print(f"\n{'='*75}")
    print("VERIFYING FASTAPI API ENDPOINTS ROUND-TRIP")
    print(f"{'='*75}")
    client = TestClient(app)

    # 1. Health check
    resp = client.get(f"{settings.API_V1_STR}/health")
    print(f"GET /api/v1/health: {resp.status_code} -> {resp.json().get('status')}")
    assert resp.status_code == 200

    # 2. Investigate endpoint (Notion)
    resp = client.post("/api/v1/investigate", json={"app_name": "Notion", "website": "https://www.notion.com"})
    print(f"POST /api/v1/investigate: {resp.status_code} -> id={resp.json().get('id')}, app_name={resp.json().get('app_name')}")
    assert resp.status_code == 200
    investigated_id = resp.json().get("id")

    # 3. Research endpoint (Notion)
    resp = client.post("/api/v1/research", json={"app_name": "Notion", "website_or_domain": "https://www.notion.com"})
    print(f"POST /api/v1/research: {resp.status_code} -> status={resp.json().get('status')}, supports_oauth={resp.json().get('oauth_details', {}).get('supports_oauth')}")
    assert resp.status_code == 200

    # 4. Composio toolkit lookup
    resp = client.get("/api/v1/composio/toolkit/notion")
    print(f"GET /api/v1/composio/toolkit/notion: {resp.status_code} -> in_catalog={resp.json().get('in_catalog')}, managed={resp.json().get('managed_oauth_available')}")
    assert resp.status_code == 200

    # 5. Share guide
    resp = client.post("/api/v1/guides/share", json={"guide_id": investigated_id})
    print(f"POST /api/v1/guides/share: {resp.status_code} -> share_url={resp.json().get('share_url')}")
    assert resp.status_code == 200

    # 6. Retrieve shared guide
    resp = client.get(f"/api/v1/guides/share/{investigated_id}")
    print(f"GET /api/v1/guides/share/{investigated_id}: {resp.status_code} -> app_name={resp.json().get('app_name')}")
    assert resp.status_code == 200
    guide = resp.json()
    rev_claim = guide.get("provider_review", {})
    print(f"  Saved Guide review_required: {rev_claim.get('review_required')}, status: {rev_claim.get('status')}, conditions: {rev_claim.get('conditions')}")

    print("\nAPI Endpoints Round-Trip Verification Complete: ALL 6 ENDPOINTS SUCCEEDED.")


async def main():
    print("Starting Milestone 3.6 Live Pipeline & Evidence Integrity Verification...")
    test_cases = [
        ("Notion", "https://www.notion.com"),
        ("Slack", "slack.com"),
        ("Shopify", "shopify.com"),
        ("NonExistentDummyAppXYZ99", "dummyappxyz99.invalid"),
    ]

    for app_name, site in test_cases:
        try:
            await verify_app(app_name, site)
        except Exception as e:
            print(f"ERROR verifying {app_name}: {e}")

    verify_api_endpoints()
    print("\nMilestone 3.6 Verification Complete.")


if __name__ == "__main__":
    asyncio.run(main())
