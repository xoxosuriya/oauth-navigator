from fastapi import APIRouter, HTTPException, Query, Request, Header
from typing import Optional
from datetime import datetime, timezone
from app.models.guide import (
    OAuthGuide,
    AppListResponse,
    ShareGuideRequest,
    ShareGuideResponse,
    InvestigateRequest,
)
from app.models.connection import (
    ConnectionStartRequest,
    ConnectionStartResponse,
    ConnectedAccountResponse,
    ConnectedAccountListResponse,
    ShopifyConfigStatusResponse,
)
from app.models.composio import (
    ComposioClassification,
    ComposioToolkitCheckResponse,
)
from app.models.research import (
    ResearchRequest,
    ResearchResultResponse,
    ResearchStatus,
)
from app.services.store import guide_store, convert_research_result_to_guide
from app.services.composio_metadata import composio_metadata_service
from app.services.composio_connection import composio_connection_service
from app.services.research import gemini_research_service
from app.core.rate_limit import research_rate_limiter, get_client_ip
from app.core.config import settings

api_router = APIRouter()

@api_router.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify backend service status."""
    return {
        "status": "healthy",
        "service": "Composio OAuth Guide & Intelligence API",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/apps", response_model=AppListResponse, tags=["Guides"])
async def list_apps(
    search: Optional[str] = Query(default=None, description="Search apps by name or slug"),
    managed_only: Optional[bool] = Query(default=None, description="Filter by Composio managed OAuth availability"),
    difficulty: Optional[str] = Query(default=None, description="Filter by difficulty: VERY_EASY, MODERATE, COMPLEX, ENTERPRISE_GATED"),
):
    """
    List curated and investigated OAuth setup guides.
    Supports filtering by search keywords, managed OAuth availability, and difficulty rating.
    """
    # Guard against direct python function calls where Query objects may be default values
    search_str = search if isinstance(search, str) else None
    managed_bool = managed_only if isinstance(managed_only, bool) else None
    diff_str = difficulty if isinstance(difficulty, str) else None

    items = guide_store.list_guides(
        search=search_str,
        managed_only=managed_bool,
        difficulty=diff_str,
    )
    return AppListResponse(total=len(items), items=items)

@api_router.get("/apps/{id_or_slug}", response_model=OAuthGuide, tags=["Guides"])
async def get_app_guide(id_or_slug: str):
    """
    Retrieve a comprehensive OAuth setup guide by its unique ID or URL slug.
    Includes claim-level evidence links, timeline breakdowns, blockers, and Composio snippets.
    """
    guide = guide_store.get_guide(id_or_slug)
    if not guide:
        raise HTTPException(
            status_code=404,
            detail=f"OAuth guide for '{id_or_slug}' not found in library."
        )
    return guide

@api_router.post("/guides/share", response_model=ShareGuideResponse, tags=["Guides"])
async def share_guide(request: ShareGuideRequest):
    """
    Generate a permanent public shareable link for an OAuth setup guide.
    """
    guide = guide_store.get_guide(request.guide_id)
    if not guide:
        raise HTTPException(
            status_code=404,
            detail=f"Guide with ID '{request.guide_id}' does not exist."
        )
    share_url = guide_store.create_share_url(guide.id)
    return ShareGuideResponse(
        guide_id=guide.id,
        share_url=share_url,
        created_at=datetime.now(timezone.utc)
    )

@api_router.get("/guides/share/{share_id}", response_model=OAuthGuide, tags=["Guides"])
async def get_shared_guide(share_id: str):
    """
    Public share retrieval endpoint for an OAuth guide by guide ID or share slug.
    """
    guide = guide_store.get_guide(share_id)
    if not guide:
        raise HTTPException(
            status_code=404,
            detail=f"Shared guide '{share_id}' not found."
        )
    return guide

@api_router.post("/investigate", response_model=OAuthGuide, tags=["Investigation"])
async def investigate_app(request: InvestigateRequest):
    """
    Endpoint for live app investigation.
    If the app exists in the cached library, returns the existing grounded guide.
    Otherwise, invokes the live research engine, converts the verified evidence into
    a structured OAuth guide, persists it to the store, and returns it.
    """
    query = request.app_name.lower().strip()
    existing = guide_store.get_guide(query)
    if existing:
        return existing

    # Invoke research engine
    research_result = await gemini_research_service.research_app(
        app_name=request.app_name.strip(),
        website_or_domain=request.website.strip() if request.website else None,
    )

    if research_result.status == ResearchStatus.UNKNOWN_APPLICATION:
        raise HTTPException(
            status_code=404,
            detail=f"Application '{request.app_name}' could not be verified or investigated."
        )

    # Convert to OAuthGuide, persist, and return
    guide = convert_research_result_to_guide(research_result)
    guide_store.save_guide(guide)
    return guide


@api_router.get(
    "/composio/toolkit/{slug}",
    response_model=ComposioToolkitCheckResponse,
    tags=["Composio"],
    summary="Check Composio live toolkit metadata and OAuth classification",
)
async def check_composio_toolkit(slug: str):
    """
    Check whether an application exists in Composio, which authentication schemes
    it supports, and whether Composio manages its OAuth configuration.

    Returns structured OAuth classification:
    - NOT_IN_COMPOSIO_CATALOG (HTTP 404 from Composio)
    - NO_AUTH_REQUIRED (explicitly requires no authentication)
    - NON_OAUTH_TOOLKIT (requires auth such as API_KEY, but no OAuth support)
    - COMPOSIO_MANAGED_AVAILABLE (OAuth2 supported with Composio-managed app)
    - CUSTOM_OAUTH_MANDATORY (OAuth2 supported, but BYO / custom OAuth app required)
    - METADATA_UNAVAILABLE (Composio API unconfigured, 401/403, 429, timeout, network error, or 5xx)
    """
    cleaned_slug = slug.strip().lower()
    if not cleaned_slug:
        raise HTTPException(
            status_code=400,
            detail="Toolkit slug cannot be empty or whitespace."
        )
    return await composio_metadata_service.fetch_toolkit_metadata(cleaned_slug)


@api_router.post(
    "/research",
    response_model=ResearchResultResponse,
    tags=["Research"],
    summary="Research OAuth documentation, requirements, and evidence for an application",
)
async def research_app_endpoint(request: ResearchRequest, http_request: Request):
    """
    Research OAuth requirements, developer portal URLs, client credentials,
    redirect URI constraints, scopes, and review timelines for an application.
    Enforces request-body size limits and multi-tiered rate limiting (per-minute, per-day).
    """
    # 1. Check request body size against max limit if Content-Length header is present
    content_length = http_request.headers.get("content-length")
    if content_length and content_length.isdigit():
        if int(content_length) > settings.MAX_REQUEST_BODY_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Request payload too large. Maximum allowed is {settings.MAX_REQUEST_BODY_BYTES} bytes."
            )

    # 2. Rate limiting check (per-minute, per-day per IP, and global daily cap)
    client_ip = get_client_ip(http_request, settings.TRUSTED_PROXY_IPS)
    allowed, retry_after, reason = await research_rate_limiter.acquire(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=reason or "Research rate limit exceeded. Please retry later.",
            headers={"Retry-After": str(retry_after or 60)},
        )

    # 3. Input validation & normalization
    cleaned_name = request.app_name.strip()
    if not cleaned_name:
        raise HTTPException(
            status_code=400,
            detail="Application name cannot be empty or whitespace."
        )

    return await gemini_research_service.research_app(
        app_name=cleaned_name,
        website_or_domain=request.website_or_domain.strip() if request.website_or_domain else None,
    )


# =============================================================================
# Composio Connection & OAuth Lifecycle Endpoints
# =============================================================================

@api_router.get("/connections/shopify/status", response_model=ShopifyConfigStatusResponse, tags=["Connections"])
async def get_shopify_connection_status():
    """Returns Shopify custom OAuth configuration status and setup instructions."""
    return composio_connection_service.get_shopify_status()


@api_router.post(
    "/connections/{toolkit_slug}/start",
    response_model=ConnectionStartResponse,
    tags=["Connections"],
)
async def start_connection(
    toolkit_slug: str,
    payload: ConnectionStartRequest,
):
    """
    Initializes a real Composio OAuth connection link for a supported toolkit.
    Discovers the Composio-managed auth configuration (or custom config for Shopify)
    and returns the direct authorization URL and connected account identifier.
    """
    clean_slug = toolkit_slug.lower().strip()
    return await composio_connection_service.create_connection_link(
        toolkit_slug=clean_slug,
        user_id=payload.user_id,
        alias=payload.alias,
        callback_url=payload.callback_url,
    )


@api_router.get(
    "/connections/{connected_account_id}",
    response_model=ConnectedAccountResponse,
    tags=["Connections"],
)
async def get_connection_status(
    connected_account_id: str,
    user_id: Optional[str] = Query(default=None, description="Owner user ID for session validation"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-ID", description="Owner user ID header"),
):
    """
    Retrieves the real-time status of a Composio connected account.
    Enforces user session ownership and redacts all secrets/tokens.
    """
    active_user_id = user_id or x_user_id
    if not active_user_id or not active_user_id.strip():
        raise HTTPException(
            status_code=400,
            detail="user_id query parameter or X-User-ID header is required for ownership validation.",
        )
    return await composio_connection_service.get_connected_account(
        connected_account_id=connected_account_id.strip(),
        user_id=active_user_id.strip(),
    )


@api_router.get(
    "/connections",
    response_model=ConnectedAccountListResponse,
    tags=["Connections"],
)
async def list_user_connections(
    user_id: Optional[str] = Query(default=None, description="Owner user ID for session validation"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-ID", description="Owner user ID header"),
):
    """
    Lists all connected accounts owned by the current browser session.
    """
    active_user_id = user_id or x_user_id
    if not active_user_id or not active_user_id.strip():
        raise HTTPException(
            status_code=400,
            detail="user_id query parameter or X-User-ID header is required for ownership validation.",
        )
    return await composio_connection_service.list_user_connections(
        user_id=active_user_id.strip(),
    )


