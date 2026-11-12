"""
Live Verification Script for Milestone 3.5 — OAuth Navigator.

Performs live end-to-end verification across:
1. Notion (Capabilities model, no promotional URLs, empty query scopes)
2. Slack (Separation of Workspace Bot OAuth V2 vs Sign in with Slack OIDC)
3. Shopify (Custom App vs Public App Store review separation)
4. Unknown Application (Three-state unverified semantics: supports_oauth=None)
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
from app.models.research import ResearchStatus


async def verify_app(app_name: str, website: str):
    print(f"\n{'='*70}")
    print(f"VERIFYING APPLICATION: {app_name} (website: {website})")
    print(f"{'='*70}")

    result = await gemini_research_service.research_app(
        app_name=app_name,
        website_or_domain=website,
    )

    print(f"Research Status:            {result.status.value}")
    print(f"supports_oauth:             {result.oauth_details.supports_oauth} (type: {type(result.oauth_details.supports_oauth).__name__})")
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

    print(f"Scopes Discovered ({len(result.scopes)}):")
    for sc in result.scopes:
        print(f"  - {sc.scope}: {sc.description}")

    print(f"Additional Flows ({len(result.oauth_details.additional_flows)}):")
    for af in result.oauth_details.additional_flows:
        print(f"  - Flow: {af.get('flow_name')}")
        print(f"    Auth: {af.get('authorization_endpoint')}")
        print(f"    Token: {af.get('token_endpoint')}")
        print(f"    Notes: {af.get('notes')}")

    print(f"Field Provenance ({len(result.field_provenance)} fields):")
    for fname, fe in result.field_provenance.items():
        print(f"  - {fname}: {fe.evidence_status.value} (method: {fe.extraction_method}, conf: {fe.confidence})")
        if fe.notes:
            print(f"    Notes: {fe.notes}")

    return result


async def main():
    print("Starting Milestone 3.5 Live Pipeline Verification...")
    test_cases = [
        ("Notion", "https://www.notion.com"),
        ("Slack", "slack.com"),
        ("Shopify", "shopify.com"),
        ("NonExistentDummyAppXYZ99", "dummyappxyz99.invalid"),
    ]

    for app, site in test_cases:
        try:
            await verify_app(app, site)
        except Exception as e:
            print(f"ERROR verifying {app}: {e}")

    print("\nLive Pipeline Verification Complete.")


if __name__ == "__main__":
    asyncio.run(main())
