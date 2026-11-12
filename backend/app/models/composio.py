"""
Pydantic data models for Composio Toolkit Metadata and OAuth Classification.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ComposioClassification(str, Enum):
    """
    Standardized classification of an application's OAuth & authentication support
    within the Composio ecosystem.
    """
    NOT_IN_COMPOSIO_CATALOG = "NOT_IN_COMPOSIO_CATALOG"
    NO_AUTH_REQUIRED = "NO_AUTH_REQUIRED"
    NON_OAUTH_TOOLKIT = "NON_OAUTH_TOOLKIT"
    COMPOSIO_MANAGED_AVAILABLE = "COMPOSIO_MANAGED_AVAILABLE"
    CUSTOM_OAUTH_MANDATORY = "CUSTOM_OAUTH_MANDATORY"
    METADATA_UNAVAILABLE = "METADATA_UNAVAILABLE"


class ComposioToolkitCheckResponse(BaseModel):
    """
    Structured response model returned when verifying an application against
    the official Composio Toolkit API (/api/v3.1/toolkits/{slug}).
    """
    slug: str = Field(
        ...,
        description="Normalized lowercase toolkit slug (e.g. 'slack', 'gmail', 'shopify')."
    )
    name: Optional[str] = Field(
        default=None,
        description="Official display name of the toolkit as reported by Composio."
    )
    in_catalog: bool = Field(
        ...,
        description="True if the toolkit exists in the Composio catalog; False if confirmed 404 or unverified."
    )
    enabled: bool = Field(
        default=False,
        description="Whether the toolkit is active and enabled for use within Composio."
    )
    supported_auth_schemes: List[str] = Field(
        default_factory=list,
        description="Normalized uppercase list of authentication schemes supported by the toolkit."
    )
    managed_auth_schemes: List[str] = Field(
        default_factory=list,
        description="Normalized uppercase list of authentication schemes managed directly by Composio."
    )
    supports_oauth: bool = Field(
        default=False,
        description="True if the toolkit supports OAuth (e.g. OAUTH2, OAUTH1)."
    )
    managed_oauth_available: bool = Field(
        default=False,
        description="True if Composio provides a managed OAuth app for this toolkit."
    )
    classification: ComposioClassification = Field(
        ...,
        description="Final OAuth classification category."
    )
    is_live_lookup: bool = Field(
        default=False,
        description="True if metadata was retrieved from a live Composio API call; False if cached, simulated, or unavailable."
    )
    explanation: str = Field(
        ...,
        description="Safe, clear human-readable explanation of the classification."
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Granular error code if metadata retrieval failed (e.g. MISSING_API_KEY, AUTHENTICATION_FAILED, RATE_LIMITED)."
    )
    http_status: Optional[int] = Field(
        default=None,
        description="Upstream HTTP status code returned by Composio API, if an HTTP call was made."
    )
    raw_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Sanitized subset of original toolkit metadata for downstream agent consumption."
    )

