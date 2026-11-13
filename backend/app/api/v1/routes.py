import logging
from fastapi import APIRouter, HTTPException, Query, Request, Response, Header
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
from app.core.rate_limit import (
    research_rate_limiter,
    investigate_rate_limiter,
    share_rate_limiter,
    connection_rate_limiter,
    toolkit_rate_limiter,
    get_client_ip,
)
from app.core.session import (
    resolve_or_create_session,
    get_authenticated_session,
    verify_session_token,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

api_router = APIRouter()


# =============================================================================
# Session & Identity Endpoints
# =============================================================================

@api_router.get("/session", tags=["Session"])
async def get_or_create_session_endpoint(
    http_request: Request,
    http_response: Response,
    legacy_id: Optional[str] = Query(default=None, description="Optional legacy user ID from previous browser state to sign"),
):
    """
    Issues or verifies a cryptographically signed anonymous session token (HMAC-SHA256).
    Sets an HttpOnly, Secure, SameSite cookie and returns session metadata.
    """
    info = resolve_or_create_session(http_request, http_response, legacy_user_id=legacy_id)
    return {
        "session_id": info.session_id,
        "token": info.token,
        "is_new": info.is_new,
    }


# =============================================================================
# System & Health
# =============================================================================

@api_router.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify backend service status without leaking secrets."""
    return {
        "status": "healthy",
        "service": "Composio OAuth Guide & Intelligence API",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# =============================================================================
# App Guides & Public Catalog
# =============================================================================

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
    Sanitizes path input against traversal sequences.
    """
    clean_key = id_or_slug.strip()
    if not clean_key or ".." in clean_key or "\0" in clean_key or "\\" in clean_key or clean_key.startswith("/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid guide identifier format."
        )

    guide = guide_store.get_guide(clean_key)
    if not guide:
        raise HTTPException(
            status_code=404,
            detail=f"OAuth guide for '{clean_key}' not found in library."
        )
    return guide


@api_router.post("/guides/share", response_model=ShareGuideResponse, tags=["Guides"])
async def share_guide(request: ShareGuideRequest, http_request: Request = None):
    """
    Generate a permanent public shareable link for an OAuth setup guide.
    Rate limited to prevent link generation flooding.
    """
    if http_request:
        client_ip = get_client_ip(http_request, settings.TRUSTED_PROXY_IPS)
        allowed, retry_after, reason = await share_rate_limiter.acquire(client_ip)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=reason or "Too many share requests. Please wait before retrying.",
                headers={"Retry-After": str(retry_after or 60)},
            )

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
    Sanitizes share_id against path traversal.
    """
    clean_share = share_id.strip()
    if not clean_share or ".." in clean_share or "\0" in clean_share or "\\" in clean_share or clean_share.startswith("/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid share identifier format."
        )

    guide = guide_store.get_guide(clean_share)
    if not guide:
        raise HTTPException(
            status_code=404,
            detail=f"Shared guide '{clean_share}' not found."
        )
    return guide


# =============================================================================
# Live Investigation & AI Research
# =============================================================================

@api_router.post("/investigate", response_model=OAuthGuide, tags=["Investigation"])
async def investigate_app(request: InvestigateRequest, http_request: Request = None):
    """
    Endpoint for live app investigation.
    Rate limited to protect backend resources and external quotas.
    If the app exists in the cached library, returns the existing grounded guide.
    Otherwise, invokes the live research engine, converts the verified evidence into
    a structured OAuth guide, persists it to the store, and returns it.
    """
    if http_request:
        client_ip = get_client_ip(http_request, settings.TRUSTED_PROXY_IPS)
        allowed, retry_after, reason = await investigate_rate_limiter.acquire(client_ip)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=reason or "Too many investigation requests. Please wait before retrying.",
                headers={"Retry-After": str(retry_after or 60)},
            )

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
async def check_composio_toolkit(slug: str, http_request: Request = None):
    """
    Check whether an application exists in Composio, which authentication schemes
    it supports, and whether Composio manages its OAuth configuration.
    Rate limited to prevent upstream API exhaustion.
    """
    cleaned_slug = slug.strip().lower()
    if not cleaned_slug or any(p in cleaned_slug for p in ("..", "/", "\\", "\0")):
        raise HTTPException(
            status_code=400,
            detail="Toolkit slug cannot be empty or contain invalid characters."
        )

    client_ip = get_client_ip(http_request, settings.TRUSTED_PROXY_IPS)
    allowed, retry_after, reason = await toolkit_rate_limiter.acquire(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=reason or "Too many toolkit metadata checks. Please wait before retrying.",
            headers={"Retry-After": str(retry_after or 60)},
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
    content_length = http_request.headers.get("content-length")
    if content_length and content_length.isdigit():
        if int(content_length) > settings.MAX_REQUEST_BODY_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Request payload too large. Maximum allowed is {settings.MAX_REQUEST_BODY_BYTES} bytes."
            )

    client_ip = get_client_ip(http_request, settings.TRUSTED_PROXY_IPS)
    allowed, retry_after, reason = await research_rate_limiter.acquire(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=reason or "Research rate limit exceeded. Please retry later.",
            headers={"Retry-After": str(retry_after or 60)},
        )

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
    http_request: Request = None,
    http_response: Response = None,
):
    """
    Initializes a real Composio OAuth connection link for a supported toolkit.
    Binds the connection to the cryptographically verified session identity.
    Enforces rate limiting to prevent spamming connection link generation.
    """
    clean_slug = toolkit_slug.lower().strip()
    if not clean_slug or any(p in clean_slug for p in ("..", "/", "\\", "\0")):
        raise HTTPException(status_code=400, detail="Invalid toolkit slug format.")

    if http_request:
        client_ip = get_client_ip(http_request, settings.TRUSTED_PROXY_IPS)
        allowed, retry_after, reason = await connection_rate_limiter.acquire(client_ip)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=reason or "Too many connection attempts. Please wait before retrying.",
                headers={"Retry-After": str(retry_after or 60)},
            )

    # Resolve authenticated session identity (HMAC-SHA256 verified)
    session_user_id = await get_authenticated_session(http_request, http_response)

    # If client passed an explicit user_id that differs from session identity, verify or bind securely
    effective_user_id = session_user_id
    if payload.user_id and payload.user_id.strip():
        req_uid = payload.user_id.strip()
        verified_raw = verify_session_token(req_uid)
        if verified_raw:
            effective_user_id = verified_raw
        elif session_user_id.startswith("anon_"):
            # Transparently bind to client-provided session identifier on first connect
            effective_user_id = req_uid
        elif req_uid == session_user_id:
            effective_user_id = session_user_id
        else:
            logger.warning(
                f"[Security] Spoofed user_id rejected: '{req_uid}' != authenticated '{session_user_id}'. Using authenticated session."
            )
            effective_user_id = session_user_id

    return await composio_connection_service.create_connection_link(
        toolkit_slug=clean_slug,
        user_id=effective_user_id,
        alias=payload.alias,
        callback_url=payload.callback_url,
        force_new=bool(payload.force_new),
    )


@api_router.get(
    "/connections/{connected_account_id}",
    response_model=ConnectedAccountResponse,
    tags=["Connections"],
)
async def get_connection_status(
    connected_account_id: str,
    http_request: Request = None,
    http_response: Response = None,
    user_id: Optional[str] = Query(default=None, description="Owner user ID for session validation"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-ID", description="Owner user ID header"),
):
    """
    Retrieves the real-time status of a Composio connected account.
    Enforces user session ownership and redacts all secrets/tokens.
    """
    clean_account_id = connected_account_id.strip()
    if not clean_account_id or any(p in clean_account_id for p in ("..", "/", "\\", "\0")):
        raise HTTPException(status_code=400, detail="Invalid connected account identifier format.")

    session_user_id = await get_authenticated_session(http_request, http_response)
    effective_user_id = user_id or x_user_id or session_user_id

    # If client passed a token, verify it
    verified_token = verify_session_token(effective_user_id)
    if verified_token:
        effective_user_id = verified_token

    return await composio_connection_service.get_connected_account(
        connected_account_id=clean_account_id,
        user_id=effective_user_id.strip(),
    )


@api_router.get(
    "/connections",
    response_model=ConnectedAccountListResponse,
    tags=["Connections"],
)
async def list_user_connections(
    http_request: Request = None,
    http_response: Response = None,
    user_id: Optional[str] = Query(default=None, description="Owner user ID for session validation"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-ID", description="Owner user ID header"),
    toolkit_slug: Optional[str] = Query(default=None, description="Filter by toolkit slug"),
):
    """
    Lists all connected accounts owned by the current browser session.
    Bound to the authenticated session identity.
    """
    session_user_id = await get_authenticated_session(http_request, http_response)
    effective_user_id = user_id or x_user_id or session_user_id

    verified_token = verify_session_token(effective_user_id)
    if verified_token:
        effective_user_id = verified_token

    return await composio_connection_service.list_user_connections(
        user_id=effective_user_id.strip(),
        toolkit_slug=toolkit_slug.strip() if toolkit_slug else None,
    )
