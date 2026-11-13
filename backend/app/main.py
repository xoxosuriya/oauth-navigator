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
enable_production_docs = os.getenv("ENABLE_PRODUCTION_DOCS", "false").lower() == "true"
docs_enabled = (not is_production) or enable_production_docs

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API providing actionable OAuth app setup guidance, provider review timelines, evidence traceability, and Composio integration blueprints.",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)


class PayloadTooLargeError(BaseException):
    """Raised when streaming request body exceeds maximum allowed size (subclasses BaseException to bypass Starlette exception traps)."""
    pass


class BodySizeLimitMiddleware:
    """
    ASGI middleware enforcing a strict maximum request-body limit (default 1 MB / 1,048,576 bytes).
    Protects against memory exhaustion and DoS attacks by:
    1. Early rejection when Content-Length exceeds the limit.
    2. Streaming chunk byte counting for chunked requests or missing/misleading Content-Length.
    3. Immediate HTTP 413 termination as soon as accumulated bytes exceed the limit without buffering.
    """
    def __init__(self, app, max_bytes: int = 1048576):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length_header = headers.get(b"content-length")
        if content_length_header:
            try:
                cl_val = int(content_length_header.decode("ascii"))
                if cl_val > self.max_bytes:
                    res = JSONResponse(
                        status_code=413,
                        content={"detail": f"Request payload too large. Maximum allowed is {self.max_bytes} bytes."},
                    )
                    await res(scope, receive, send)
                    return
            except (ValueError, UnicodeDecodeError):
                pass

        total_bytes = 0

        async def limited_receive():
            nonlocal total_bytes
            message = await receive()
            if message.get("type") == "http.request":
                chunk = message.get("body", b"")
                total_bytes += len(chunk)
                if total_bytes > self.max_bytes:
                    raise PayloadTooLargeError()
            return message

        try:
            await self.app(scope, limited_receive, send)
        except PayloadTooLargeError:
            res = JSONResponse(
                status_code=413,
                content={"detail": f"Request payload too large. Maximum allowed is {self.max_bytes} bytes."},
            )
            await res(scope, receive, send)


# Register streaming body size limit middleware
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.MAX_REQUEST_BODY_BYTES)


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


# 2. Global Exception Handler: Suppress stack traces in production
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
    expose_headers=["Retry-After"],
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
        "docs_url": "/docs" if docs_enabled else None,
        "api_v1": settings.API_V1_STR,
    }
