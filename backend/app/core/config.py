import os
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

def get_backend_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def parse_cors_origins(raw: str) -> List[str]:
    if not raw:
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5500"
        ]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]

def load_backend_env(env_path: Optional[str] = None) -> bool:
    """
    Explicitly loads the backend .env file with override=False so that OS
    environment variables take precedence. Avoids accidentally loading an unrelated
    .env from the current working directory.
    Returns True if an env file was found and loaded, False otherwise.
    """
    target = env_path if env_path is not None else os.path.join(get_backend_dir(), ".env")
    if os.path.isfile(target):
        load_dotenv(dotenv_path=target, override=False)
        return True
    return False

# Initialize on module import
_backend_dir = get_backend_dir()
_env_path = os.path.join(_backend_dir, ".env")
load_backend_env(_env_path)

class Settings(BaseModel):
    PROJECT_NAME: str = "Composio OAuth Guide & Intelligence API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENV: str = Field(default_factory=lambda: os.getenv("ENV", "development"))
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    
    # CORS: Explicit allowed origins (strictly enforced, no wildcard '*')
    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: parse_cors_origins(os.getenv("ALLOWED_ORIGINS", ""))
    )
    
    # Frontend Base URL for shareable permalinks
    FRONTEND_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
    )
    
    # Composio Integration (Kept strictly on backend)
    COMPOSIO_API_KEY: str = Field(default_factory=lambda: os.getenv("COMPOSIO_API_KEY", ""))
    COMPOSIO_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("COMPOSIO_BASE_URL", "https://backend.composio.dev/api/v3.1")
    )
    COMPOSIO_SHOPIFY_AUTH_CONFIG_ID: Optional[str] = Field(
        default_factory=lambda: os.getenv("COMPOSIO_SHOPIFY_AUTH_CONFIG_ID", "").strip() or None
    )
    
    # LLM Settings for Live Research Agent
    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))
    GEMINI_TIMEOUT_SECONDS: float = Field(
        default_factory=lambda: float(os.getenv("GEMINI_TIMEOUT_SECONDS", "45.0"))
    )
    RESEARCH_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("RESEARCH_ENABLED", "true").lower() in ("true", "1", "yes")
    )
    # Milestone 3.3: Temporarily disable Gemini from default path; use deterministic evidence engine
    GEMINI_RESEARCH_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("GEMINI_RESEARCH_ENABLED", "false").lower() in ("true", "1", "yes")
    )

    
    # Data Storage Paths
    BASE_DIR: str = Field(default_factory=get_backend_dir)
    DATA_DIR: str = Field(default_factory=lambda: os.path.join(get_backend_dir(), "app", "data"))

    # API Rate Limiting & Abuse Prevention (Milestone 3.1)
    RATE_LIMIT_PER_MINUTE_PER_IP: int = Field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE_PER_IP", "5"))
    )
    RATE_LIMIT_PER_DAY_PER_IP: int = Field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_DAY_PER_IP", "30"))
    )
    RATE_LIMIT_GLOBAL_PER_DAY: int = Field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_GLOBAL_PER_DAY", "500"))
    )
    MAX_REQUEST_BODY_BYTES: int = Field(
        default_factory=lambda: int(os.getenv("MAX_REQUEST_BODY_BYTES", "10240"))
    )
    TRUSTED_PROXY_IPS: List[str] = Field(
        default_factory=lambda: [ip.strip() for ip in os.getenv("TRUSTED_PROXY_IPS", "").split(",") if ip.strip()]
    )

    # Documentation Retrieval Limits (Milestone 3.1)
    DOC_MAX_PAGES_PER_REQUEST: int = Field(
        default_factory=lambda: int(os.getenv("DOC_MAX_PAGES_PER_REQUEST", "5"))
    )
    DOC_MAX_RESPONSE_BYTES: int = Field(
        default_factory=lambda: int(os.getenv("DOC_MAX_RESPONSE_BYTES", "1048576"))  # 1 MB
    )
    DOC_REQUEST_TIMEOUT_SECONDS: float = Field(
        default_factory=lambda: float(os.getenv("DOC_REQUEST_TIMEOUT_SECONDS", "10.0"))
    )
    DOC_MAX_CONCURRENT_FETCHES: int = Field(
        default_factory=lambda: int(os.getenv("DOC_MAX_CONCURRENT_FETCHES", "3"))
    )
    DOC_CACHE_TTL_SECONDS: int = Field(
        default_factory=lambda: int(os.getenv("DOC_CACHE_TTL_SECONDS", "3600"))
    )

    # Gemini Quota Protection Controls (Milestone 3.1 prepared for 3.2)
    GEMINI_MAX_CALLS_PER_REQUEST: int = Field(
        default_factory=lambda: int(os.getenv("GEMINI_MAX_CALLS_PER_REQUEST", "1"))
    )
    GEMINI_MAX_INPUT_CHARS: int = Field(
        default_factory=lambda: int(os.getenv("GEMINI_MAX_INPUT_CHARS", "60000"))
    )
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(
        default_factory=lambda: int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "4096"))
    )
    GEMINI_MAX_DAILY_REQUESTS: int = Field(
        default_factory=lambda: int(os.getenv("GEMINI_MAX_DAILY_REQUESTS", "500"))
    )
    GEMINI_RETRY_ON_QUOTA: bool = Field(
        default_factory=lambda: os.getenv("GEMINI_RETRY_ON_QUOTA", "false").lower() in ("true", "1", "yes")
    )

    # Safe verification properties (never expose or print secrets)
    @property
    def is_composio_configured(self) -> bool:
        """Returns True if COMPOSIO_API_KEY is non-empty without exposing secret."""
        return bool(self.COMPOSIO_API_KEY and self.COMPOSIO_API_KEY.strip())

    @property
    def is_gemini_configured(self) -> bool:
        """Returns True if GEMINI_API_KEY is non-empty without exposing secret."""
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip())

settings = Settings()
