"""
Composio Toolkit Metadata Service.

Provides live verification and OAuth classification of toolkits by querying
the official Composio API (GET /api/v3.1/toolkits/{slug}).
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.core.config import settings
from app.core.security import redact_sensitive_data
from app.models.composio import (
    ComposioClassification,
    ComposioToolkitCheckResponse,
)

logger = logging.getLogger(__name__)


def normalize_slug(slug: str) -> str:
    """Normalize a toolkit slug by stripping whitespace and converting to lowercase."""
    if not slug:
        return ""
    return slug.strip().lower()


def extract_modes_from_source(source: Any) -> List[str]:
    """
    Extract authentication scheme / mode names case-insensitively from diverse formats:
    - Lists of strings (e.g. ['OAUTH2', 'api_key'])
    - Lists of dicts (e.g. [{'mode': 'OAUTH2'}, {'auth_mode': 'API_KEY'}, {'scheme': 'BASIC'}])
    - Single strings (e.g. 'OAUTH2')
    - Single dicts (e.g. {'mode': 'OAUTH2'})
    - Nested iterables

    Deduplicates schemes while preserving order and normalizing to uppercase.
    """
    if not source:
        return []

    modes: List[str] = []

    def _add_mode(val: str):
        cleaned = val.strip().upper()
        if cleaned and cleaned not in modes:
            modes.append(cleaned)

    def _inspect_item(item: Any):
        if isinstance(item, str):
            _add_mode(item)
        elif isinstance(item, dict):
            for key in ("mode", "auth_mode", "scheme", "name", "type"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    _add_mode(val)
                    break
        elif isinstance(item, (list, tuple, set)):
            for sub in item:
                _inspect_item(sub)

    _inspect_item(source)
    return modes


def normalize_auth_schemes(schemes_raw: Any) -> List[str]:
    """Backward-compatible wrapper for extracting auth schemes from raw payloads."""
    return extract_modes_from_source(schemes_raw)


def is_oauth_scheme(scheme: str) -> bool:
    """Check whether a normalized scheme/mode represents an OAuth protocol (e.g. OAUTH2, S2S_OAUTH2)."""
    s = scheme.upper()
    return "OAUTH" in s


def classify_toolkit_auth(
    slug: str,
    supported_schemes: List[str],
    managed_schemes: List[str],
    no_auth: bool = False,
) -> Tuple[ComposioClassification, bool, bool, str]:
    """
    Evaluate authentication support according to strict classification rules:

    1. Explicitly requires no authentication (no_auth is True) -> NO_AUTH_REQUIRED (takes precedence)
    2. Supports OAuth and Composio provides managed app -> COMPOSIO_MANAGED_AVAILABLE
    3. Supports OAuth but Composio does NOT provide managed app -> CUSTOM_OAUTH_MANDATORY
    4. Requires auth but does not support OAuth -> NON_OAUTH_TOOLKIT
    5. Inconclusive metadata (no schemes found and no_auth is False) -> METADATA_UNAVAILABLE

    Returns:
        (classification, supports_oauth, managed_oauth_available, explanation)
    """
    supports_oauth = any(is_oauth_scheme(s) for s in supported_schemes)
    managed_oauth_available = any(is_oauth_scheme(s) for s in managed_schemes)

    # 1. no_auth takes precedence
    if no_auth or ("NO_AUTH" in supported_schemes) or ("NONE" in supported_schemes):
        classification = ComposioClassification.NO_AUTH_REQUIRED
        explanation = (
            f"Toolkit '{slug}' explicitly indicates that no authentication is required to execute tools."
        )
    # 2. OAuth supported and Composio managed OAuth available
    elif supports_oauth and managed_oauth_available:
        classification = ComposioClassification.COMPOSIO_MANAGED_AVAILABLE
        explanation = (
            f"Toolkit '{slug}' supports OAuth2 and Composio provides a managed OAuth application. "
            "Users can connect accounts immediately using Composio's pre-registered credentials."
        )
    # 3. OAuth supported but Composio managed OAuth unavailable
    elif supports_oauth and not managed_oauth_available:
        classification = ComposioClassification.CUSTOM_OAUTH_MANDATORY
        explanation = (
            f"Toolkit '{slug}' supports OAuth2, but Composio does not provide a managed OAuth application. "
            "Developers must create and register a custom OAuth application with the provider."
        )
    # 4. Non-OAuth authentication required
    elif supported_schemes:
        classification = ComposioClassification.NON_OAUTH_TOOLKIT
        schemes_str = ", ".join(supported_schemes)
        explanation = (
            f"Toolkit '{slug}' requires authentication ({schemes_str}) but does not support OAuth."
        )
    # 5. Inconclusive metadata
    else:
        classification = ComposioClassification.METADATA_UNAVAILABLE
        explanation = (
            f"Toolkit '{slug}' metadata does not specify any authentication schemes or no_auth status."
        )

    return classification, supports_oauth, managed_oauth_available, explanation


class ComposioMetadataService:
    """
    Client service for querying Composio toolkit metadata and classifying auth schemes.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 10.0,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.base_url = (base_url or settings.COMPOSIO_BASE_URL).rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = client

    def _build_url(self, slug: str) -> str:
        """Construct the official endpoint URL safely."""
        cleaned_base = self.base_url
        if cleaned_base.endswith("/api/v3.1"):
            return f"{cleaned_base}/toolkits/{slug}"
        return f"{cleaned_base}/api/v3.1/toolkits/{slug}"

    def _get_effective_api_key(self) -> str:
        """Return the current API key, checking settings dynamically if not passed at init."""
        if self.api_key is not None:
            return self.api_key.strip()
        return settings.COMPOSIO_API_KEY.strip()

    async def fetch_toolkit_metadata(
        self,
        slug: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> ComposioToolkitCheckResponse:
        """
        Query Composio GET /api/v3.1/toolkits/{slug} and return a structured
        ComposioToolkitCheckResponse.
        
        Guarantees:
        - Never logs or exposes API keys.
        - Never misreports 401/403 or network errors as 404 (not in catalog).
        - Correctly normalizes slugs and authentication scheme names across all metadata fields:
          auth_schemes, auth_config_details[].mode, composio_managed_auth_schemes,
          and composio_managed_auth[].mode.
        """
        normalized = normalize_slug(slug)
        if not normalized:
            return ComposioToolkitCheckResponse(
                slug=slug,
                name=None,
                in_catalog=False,
                enabled=False,
                supported_auth_schemes=[],
                managed_auth_schemes=[],
                supports_oauth=False,
                managed_oauth_available=False,
                classification=ComposioClassification.METADATA_UNAVAILABLE,
                is_live_lookup=False,
                explanation="Toolkit slug cannot be empty.",
                error_code="INVALID_SLUG",
                http_status=None,
                raw_metadata=None,
            )

        effective_key = self._get_effective_api_key()
        if not effective_key:
            logger.warning("COMPOSIO_API_KEY is not configured. Live toolkit lookup aborted.")
            return ComposioToolkitCheckResponse(
                slug=normalized,
                name=None,
                in_catalog=False,
                enabled=False,
                supported_auth_schemes=[],
                managed_auth_schemes=[],
                supports_oauth=False,
                managed_oauth_available=False,
                classification=ComposioClassification.METADATA_UNAVAILABLE,
                is_live_lookup=False,
                explanation="COMPOSIO_API_KEY is not configured on the backend. Live toolkit metadata could not be fetched.",
                error_code="MISSING_API_KEY",
                http_status=None,
                raw_metadata=None,
            )

        url = self._build_url(normalized)
        headers = {
            "x-api-key": effective_key,
            "Accept": "application/json",
            "User-Agent": "ComposioOAuthGuideBackend/1.0",
        }

        # Use injected client, instance client, or ephemeral client
        active_client = client or self._client
        owns_client = False
        if active_client is None:
            active_client = httpx.AsyncClient(timeout=self.timeout)
            owns_client = True

        try:
            resp = await active_client.get(url, headers=headers)
        except httpx.TimeoutException:
            logger.warning("Request to Composio API timed out for toolkit slug: %s", normalized)
            return ComposioToolkitCheckResponse(
                slug=normalized,
                name=None,
                in_catalog=False,
                enabled=False,
                supported_auth_schemes=[],
                managed_auth_schemes=[],
                supports_oauth=False,
                managed_oauth_available=False,
                classification=ComposioClassification.METADATA_UNAVAILABLE,
                is_live_lookup=True,
                explanation="Connection to Composio API timed out. Live toolkit metadata could not be retrieved.",
                error_code="REQUEST_TIMEOUT",
                http_status=None,
                raw_metadata=None,
            )
        except httpx.RequestError as exc:
            logger.warning("Network failure connecting to Composio API for toolkit slug: %s: %s", normalized, str(exc))
            return ComposioToolkitCheckResponse(
                slug=normalized,
                name=None,
                in_catalog=False,
                enabled=False,
                supported_auth_schemes=[],
                managed_auth_schemes=[],
                supports_oauth=False,
                managed_oauth_available=False,
                classification=ComposioClassification.METADATA_UNAVAILABLE,
                is_live_lookup=True,
                explanation="Network error occurred while connecting to Composio API. Live toolkit metadata could not be retrieved.",
                error_code="NETWORK_FAILURE",
                http_status=None,
                raw_metadata=None,
            )
        finally:
            if owns_client:
                await active_client.aclose()

        # Handle HTTP status codes distinctly
        status = resp.status_code

        # 1. 404 Not Found -> Confirmed not in catalog
        if status == 404:
            return ComposioToolkitCheckResponse(
                slug=normalized,
                name=None,
                in_catalog=False,
                enabled=False,
                supported_auth_schemes=[],
                managed_auth_schemes=[],
                supports_oauth=False,
                managed_oauth_available=False,
                classification=ComposioClassification.NOT_IN_COMPOSIO_CATALOG,
                is_live_lookup=True,
                explanation=f"Toolkit '{normalized}' was not found in the Composio catalog (HTTP 404).",
                error_code="NOT_FOUND",
                http_status=404,
                raw_metadata=None,
            )

        # 2. 401 or 403 -> Authentication failure (Never report as 404)
        if status in (401, 403):
            logger.warning("Composio API authentication failed with HTTP %d for slug %s", status, normalized)
            return ComposioToolkitCheckResponse(
                slug=normalized,
                name=None,
                in_catalog=False,
                enabled=False,
                supported_auth_schemes=[],
                managed_auth_schemes=[],
                supports_oauth=False,
                managed_oauth_available=False,
                classification=ComposioClassification.METADATA_UNAVAILABLE,
                is_live_lookup=True,
                explanation=f"Authentication to Composio API failed (HTTP {status}). Please check COMPOSIO_API_KEY.",
                error_code="AUTHENTICATION_FAILED",
                http_status=status,
                raw_metadata=None,
            )

        # 3. 429 -> Rate limited
        if status == 429:
            logger.warning("Composio API rate limit exceeded (HTTP 429) for slug %s", normalized)
            return ComposioToolkitCheckResponse(
                slug=normalized,
                name=None,
                in_catalog=False,
                enabled=False,
                supported_auth_schemes=[],
                managed_auth_schemes=[],
                supports_oauth=False,
                managed_oauth_available=False,
                classification=ComposioClassification.METADATA_UNAVAILABLE,
                is_live_lookup=True,
                explanation="Composio API rate limit exceeded (HTTP 429). Please retry after a brief delay.",
                error_code="RATE_LIMITED",
                http_status=429,
                raw_metadata=None,
            )

        # 4. 5xx -> Upstream server error
        if status >= 500:
            logger.warning("Composio API upstream server error (HTTP %d) for slug %s", status, normalized)
            return ComposioToolkitCheckResponse(
                slug=normalized,
                name=None,
                in_catalog=False,
                enabled=False,
                supported_auth_schemes=[],
                managed_auth_schemes=[],
                supports_oauth=False,
                managed_oauth_available=False,
                classification=ComposioClassification.METADATA_UNAVAILABLE,
                is_live_lookup=True,
                explanation=f"Composio upstream service error (HTTP {status}). Live toolkit metadata could not be retrieved.",
                error_code="UPSTREAM_SERVER_ERROR",
                http_status=status,
                raw_metadata=None,
            )

        # 5. Non-200 unexpected status
        if status != 200:
            logger.warning("Unexpected HTTP %d from Composio API for slug %s", status, normalized)
            return ComposioToolkitCheckResponse(
                slug=normalized,
                name=None,
                in_catalog=False,
                enabled=False,
                supported_auth_schemes=[],
                managed_auth_schemes=[],
                supports_oauth=False,
                managed_oauth_available=False,
                classification=ComposioClassification.METADATA_UNAVAILABLE,
                is_live_lookup=True,
                explanation=f"Composio API returned an unexpected HTTP status code {status}.",
                error_code="UNEXPECTED_STATUS",
                http_status=status,
                raw_metadata=None,
            )

        # 6. Parse JSON payload
        try:
            raw_body = resp.json()
        except Exception as exc:
            logger.warning("Failed to decode JSON from Composio API response: %s", str(exc))
            return ComposioToolkitCheckResponse(
                slug=normalized,
                name=None,
                in_catalog=False,
                enabled=False,
                supported_auth_schemes=[],
                managed_auth_schemes=[],
                supports_oauth=False,
                managed_oauth_available=False,
                classification=ComposioClassification.METADATA_UNAVAILABLE,
                is_live_lookup=True,
                explanation="Composio API returned an invalid or unparseable response JSON.",
                error_code="MALFORMED_RESPONSE",
                http_status=200,
                raw_metadata=None,
            )

        if not isinstance(raw_body, dict):
            return ComposioToolkitCheckResponse(
                slug=normalized,
                name=None,
                in_catalog=False,
                enabled=False,
                supported_auth_schemes=[],
                managed_auth_schemes=[],
                supports_oauth=False,
                managed_oauth_available=False,
                classification=ComposioClassification.METADATA_UNAVAILABLE,
                is_live_lookup=True,
                explanation="Composio API response structure was not a JSON object.",
                error_code="MALFORMED_RESPONSE",
                http_status=200,
                raw_metadata=None,
            )

        # Handle envelope wrappers if present (e.g. {"data": {...}} or {"toolkit": {...}})
        payload = raw_body
        if "data" in raw_body and isinstance(raw_body["data"], dict) and ("slug" in raw_body["data"] or "auth_config_details" in raw_body["data"]):
            payload = raw_body["data"]
        elif "toolkit" in raw_body and isinstance(raw_body["toolkit"], dict) and ("slug" in raw_body["toolkit"] or "auth_config_details" in raw_body["toolkit"]):
            payload = raw_body["toolkit"]

        # Extract fields
        extracted_slug = str(payload.get("slug") or normalized).lower()
        extracted_name = payload.get("name")
        if extracted_name is not None:
            extracted_name = str(extracted_name)

        enabled = bool(payload.get("enabled", True))
        no_auth = bool(payload.get("no_auth", False))

        # 1. Determine all supported authentication schemes across ALL available metadata sources:
        #    - auth_schemes
        #    - auth_config_details[].mode
        #    - composio_managed_auth_schemes
        #    - composio_managed_auth[].mode
        supported_schemes: List[str] = []
        for src in (
            payload.get("auth_schemes"),
            payload.get("auth_config_details"),
            payload.get("composio_managed_auth_schemes"),
            payload.get("composio_managed_auth"),
        ):
            for mode in extract_modes_from_source(src):
                if mode not in supported_schemes:
                    supported_schemes.append(mode)

        # 2. Determine Composio-managed authentication schemes across:
        #    - composio_managed_auth_schemes
        #    - composio_managed_auth[].mode
        managed_schemes: List[str] = []
        for src in (
            payload.get("composio_managed_auth_schemes"),
            payload.get("composio_managed_auth"),
        ):
            for mode in extract_modes_from_source(src):
                if mode not in managed_schemes:
                    managed_schemes.append(mode)

        # Run strict classification engine
        classification, supports_oauth, managed_oauth_available, explanation = classify_toolkit_auth(
            slug=extracted_slug,
            supported_schemes=supported_schemes,
            managed_schemes=managed_schemes,
            no_auth=no_auth,
        )

        # Build sanitized raw_metadata subset for downstream consumption
        raw_metadata: Dict[str, Any] = {
            "slug": extracted_slug,
            "name": extracted_name,
            "enabled": enabled,
            "auth_schemes": supported_schemes,
            "composio_managed_auth_schemes": managed_schemes,
            "no_auth": no_auth,
        }
        if "composio_managed_auth" in payload:
            raw_metadata["composio_managed_auth"] = payload.get("composio_managed_auth")
        if "auth_config_details" in payload:
            raw_metadata["auth_config_details"] = payload.get("auth_config_details")
        if "meta" in payload and isinstance(payload.get("meta"), dict):
            raw_metadata["meta"] = payload.get("meta")

        # Security hardening: Redact any sensitive nested fields from upstream metadata
        raw_metadata = redact_sensitive_data(raw_metadata)

        return ComposioToolkitCheckResponse(
            slug=extracted_slug,
            name=extracted_name,
            in_catalog=True,
            enabled=enabled,
            supported_auth_schemes=supported_schemes,
            managed_auth_schemes=managed_schemes,
            supports_oauth=supports_oauth,
            managed_oauth_available=managed_oauth_available,
            classification=classification,
            is_live_lookup=True,
            explanation=explanation,
            error_code=None,
            http_status=200,
            raw_metadata=raw_metadata,
        )


# Global service instance
composio_metadata_service = ComposioMetadataService()
