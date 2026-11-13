import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.routes import api_router

logger = logging.getLogger(__name__)

is_production = settings.ENV == "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API providing actionable OAuth app setup guidance, provider review timelines, evidence traceability, and Composio integration blueprints.",
    docs_url="/docs" if not is_production else "/docs",  # Keep docs accessible for reviewers
    redoc_url="/redoc" if not is_production else "/redoc",
    openapi_url="/openapi.json",
)

# 1. Security Headers & Protocol Enforcement Middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)

    # Core Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()"

    # HSTS in production or over HTTPS
    if is_production or request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

    # Tested Content-Security-Policy allowing Google Fonts and required API endpoints
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://oauth-navigator-api.onrender.com http://127.0.0.1:8000 https://backend.composio.dev; "
        "frame-ancestors 'none';"
    )
    response.headers["Content-Security-Policy"] = csp_policy

    return response

# 2. Request Payload Size Limit Middleware (Abuse & DoS protection)
@app.middleware("http")
async def limit_request_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit():
        if int(content_length) > settings.MAX_REQUEST_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request payload too large. Maximum allowed is {settings.MAX_REQUEST_BODY_BYTES} bytes."},
            )
    return await call_next(request)

# 3. Global Exception Handler: Suppress stack traces in production
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception processing {request.method} {request.url.path}: {exc}", exc_info=True)
    if is_production:
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please contact support or retry later."},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# 4. Explicit CORS Origins (strictly enforced, no wildcard '*')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Session-Token", "Retry-After"],
)

# 5. Register API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# 6. Minimal static-file mount for temporary demo frontend (isolated in demo_frontend/)
_workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_demo_dir = os.path.join(_workspace_root, "demo_frontend")
if os.path.isdir(_demo_dir):
    app.mount("/demo", StaticFiles(directory=_demo_dir, html=True), name="demo")

@app.get("/", tags=["System"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }
