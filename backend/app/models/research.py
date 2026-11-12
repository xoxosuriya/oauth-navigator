"""
Pydantic data models for OAuth Research Engine (Milestones 3.0 - 3.5).

Defines structured research requests, flow specifications, evidence citations,
field-level provenance, review timelines, and comprehensive research result contracts.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.models.guide import (
    EvidenceConfidence,
    ValueStatus,
    ReviewRequirementItem,
    HumanAgentBoundary,
)
from app.models.composio import ComposioToolkitCheckResponse


class ResearchStatus(str, Enum):
    """Execution status of the OAuth research engine."""
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    UNKNOWN_APPLICATION = "UNKNOWN_APPLICATION"
    FAILED = "FAILED"
    DISABLED = "DISABLED"
    METADATA_ONLY = "METADATA_ONLY"


class FieldEvidenceProvenance(str, Enum):
    """Provenance classification for individual OAuth facts and configuration values."""
    PROVIDER_CONFIRMED = "PROVIDER_CONFIRMED"         # Cited directly from provider official docs or RFC metadata
    COMPOSIO_CONFIRMED = "COMPOSIO_CONFIRMED"         # Confirmed via Composio live catalog / OpenAPI metadata
    STANDARDS_BASED = "STANDARDS_BASED"               # Derived from published RFC / OIDC specifications (e.g. RFC 6749, RFC 8414)
    DERIVED_RECOMMENDATION = "DERIVED_RECOMMENDATION" # Computed / recommended best practice
    HEURISTIC_ESTIMATE = "HEURISTIC_ESTIMATE"         # Heuristic estimation when docs leave gaps
    UNKNOWN_NOT_STATED = "UNKNOWN_NOT_STATED"         # Not stated or unverified in available evidence


class FieldEvidence(BaseModel):
    """Structured field-level evidence provenance."""
    field_name: str = Field(..., description="Name of the factual property (e.g., 'authorization_endpoint', 'scopes').")
    value: Any = Field(default=None, description="The assigned field value.")
    source_url: Optional[str] = Field(default=None, description="Source URL where evidence was found, if applicable.")
    evidence_excerpt: Optional[str] = Field(default=None, description="Verbatim or cited snippet supporting this value.")
    extraction_method: str = Field(default="UNKNOWN", description="How the value was extracted.")
    evidence_status: FieldEvidenceProvenance = Field(
        default=FieldEvidenceProvenance.UNKNOWN_NOT_STATED,
        description="Provenance classification."
    )
    confidence: EvidenceConfidence = Field(default="UNCERTAIN", description="Confidence rating.")
    is_provider_specific: bool = Field(default=False, description="Whether this rule/value is provider-specific vs RFC general default.")
    notes: Optional[str] = Field(default=None, description="Qualifying context or warnings.")


class OAuthFlowDetails(BaseModel):
    """Documented protocol, grant types, and endpoints for the provider's OAuth implementation."""
    supports_oauth: Optional[bool] = Field(
        default=None,
        description="Whether the provider supports OAuth authentication (True: supported, False: affirmatively unsupported, None: unverified/unknown)."
    )
    confidence: EvidenceConfidence = Field(
        default="UNCERTAIN",
        description="Confidence level of the OAuth support determination."
    )
    protocol_version: Optional[str] = Field(
        default=None,
        description="Documented protocol version (e.g. 'OAuth 2.0', 'OAuth 1.0a', 'OpenID Connect'), or null if unknown."
    )
    grant_types: List[str] = Field(
        default_factory=list,
        description="Documented grant types (e.g. 'authorization_code', 'client_credentials', 'refresh_token', 'pkce')."
    )
    authorization_endpoint: Optional[str] = Field(
        default=None,
        description="Public authorization URL if documented, else null."
    )
    token_endpoint: Optional[str] = Field(
        default=None,
        description="Public token exchange URL if documented, else null."
    )
    pkce_required: Optional[bool] = Field(
        default=None,
        description="True if PKCE is strictly required, False if optional, null if not stated."
    )
    additional_flows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Additional distinct OAuth flows supported by the provider (e.g., OpenID Connect Sign-In vs Bot OAuth V2, Custom App vs Public Marketplace)."
    )


class ProviderRegistrationRequirements(BaseModel):
    """Requirements for creating a developer account and registering an OAuth app."""
    developer_portal_url: Optional[str] = Field(
        default=None,
        description="URL to the provider's developer console or registration portal."
    )
    account_type_required: Optional[str] = Field(
        default=None,
        description="Required developer tier (e.g. 'Free developer account', 'Paid workspace admin', 'Verified partner', or null if not stated)."
    )
    requires_client_id: bool = Field(
        default=True,
        description="Whether an OAuth Client ID is issued/required."
    )
    requires_client_secret: Optional[bool] = Field(
        default=None,
        description="Whether an OAuth Client Secret is issued/required (None if depends on client type / PKCE)."
    )
    client_secret_notes: Optional[str] = Field(
        default=None,
        description="Specific handling notes for secrets (e.g. 'Displayed once upon creation', 'Manual secret rotation required')."
    )


class RedirectUriRequirements(BaseModel):
    """Provider restrictions on OAuth redirect URIs."""
    allowed_schemes: List[str] = Field(
        default_factory=lambda: ["https"],
        description="Allowed URI schemes (e.g. ['https'], ['http', 'https'])."
    )
    allows_localhost: Optional[bool] = Field(
        default=None,
        description="Whether http://localhost or http://127.0.0.1 is permitted for development."
    )
    wildcards_permitted: Optional[bool] = Field(
        default=None,
        description="Whether wildcard subdomains or paths are allowed in redirect URIs."
    )
    strict_exact_match: Optional[bool] = Field(
        default=None,
        description="Whether the provider enforces exact string matching on callback URIs."
    )
    composio_redirect_uri_supported: bool = Field(
        default=True,
        description="Whether standard Composio redirect URIs (https://backend.composio.dev/...) satisfy provider requirements."
    )
    standards_notes: Optional[str] = Field(
        default=None,
        description="RFC 6749 baseline standards commentary vs provider-specific constraints."
    )


class ScopeRequirement(BaseModel):
    """Documented permission scope and its sensitivity classification."""
    scope: str = Field(
        ...,
        description="Scope name/identifier (e.g. 'channels:read', 'read_products', 'https://mail.google.com/')."
    )
    description: Optional[str] = Field(
        default=None,
        description="Documented purpose or access level granted by the scope."
    )
    is_sensitive: Optional[bool] = Field(
        default=None,
        description="Whether the provider classifies this as a sensitive or restricted scope."
    )


class ReviewTimelineInfo(BaseModel):
    """Documented provider verification, security assessments, and approval timelines."""
    review_required: Optional[bool] = Field(
        default=None,
        description="Whether formal review/verification is required before public distribution or production use."
    )
    review_type: Optional[str] = Field(
        default=None,
        description="Review category (e.g. 'OAuth App Verification', 'CASA Security Assessment', 'Marketplace Listing Review')."
    )
    estimated_waiting_period_days: Optional[int] = Field(
        default=None,
        description="Documented waiting period in days, or null if not stated."
    )
    waiting_period_status: ValueStatus = Field(
        default="NOT_STATED",
        description="Status of waiting period: ESTABLISHED, NOT_STATED, NOT_APPLICABLE, UNCERTAIN."
    )
    review_requirements: List[ReviewRequirementItem] = Field(
        default_factory=list,
        description="Granular review requirements, triggers, and conditionality."
    )


class ResearchCitation(BaseModel):
    """Grounded evidence citation linking findings to official documentation or source URLs."""
    id: str = Field(
        ...,
        description="Unique reference identifier, e.g. 'src_1'."
    )
    title: str = Field(
        ...,
        description="Page or document title."
    )
    url: str = Field(
        ...,
        description="Publicly accessible URL of the source document."
    )
    domain: Optional[str] = Field(
        default=None,
        description="Host domain of the source (e.g. 'api.slack.com', 'developer.spotify.com')."
    )
    evidence_excerpt: Optional[str] = Field(
        default=None,
        description="Verbatim text passage or citation snippet."
    )
    source_type: str = Field(
        default="OFFICIAL_DOCS",
        description="Source classification: OFFICIAL_DOCS, RFC_STANDARD, COMPOSIO_METADATA, etc."
    )
    retrieval_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        description="ISO date string when the citation was captured."
    )


class ResearchRequest(BaseModel):
    """Input payload for initiating an automated OAuth research query."""
    app_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the application or integration to research (e.g. 'Notion', 'HubSpot', 'Linear')."
    )
    website_or_domain: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional website, developer portal URL, or domain to guide research."
    )


class ResearchResultResponse(BaseModel):
    """Comprehensive structured output returned by the OAuth research engine."""
    app_name: str = Field(
        ...,
        description="Normalized application name."
    )
    website_or_domain: Optional[str] = Field(
        default=None,
        description="Website or domain researched."
    )
    status: ResearchStatus = Field(
        ...,
        description="Status of the research run: COMPLETED, PARTIAL, UNKNOWN_APPLICATION, FAILED, DISABLED, METADATA_ONLY."
    )
    summary: str = Field(
        ...,
        description="Concise factual summary of OAuth support, registration steps, and review requirements."
    )
    oauth_details: OAuthFlowDetails = Field(
        ...,
        description="Detailed protocol and grant specifications."
    )
    registration: ProviderRegistrationRequirements = Field(
        ...,
        description="Developer account and app registration prerequisites."
    )
    redirect_uri_rules: RedirectUriRequirements = Field(
        ...,
        description="Redirect URI syntax, localhost allowances, and matching rules."
    )
    scopes: List[ScopeRequirement] = Field(
        default_factory=list,
        description="Discovered common scopes and permissions."
    )
    review_timeline: ReviewTimelineInfo = Field(
        ...,
        description="Provider review, verification, and waiting period claims."
    )
    composio_status: Optional[ComposioToolkitCheckResponse] = Field(
        default=None,
        description="Composio catalog status and managed OAuth availability, if queried."
    )
    human_agent_boundary: HumanAgentBoundary = Field(
        ...,
        description="Separation of human developer responsibilities vs agent automation."
    )
    sources: List[ResearchCitation] = Field(
        default_factory=list,
        description="Traceable grounded citations supporting the research claims."
    )
    search_queries_used: List[str] = Field(
        default_factory=list,
        description="Grounding search queries executed by the research engine."
    )
    confidence: EvidenceConfidence = Field(
        default="UNCERTAIN",
        description="Overall confidence in the findings."
    )
    field_provenance: Dict[str, FieldEvidence] = Field(
        default_factory=dict,
        description="Structured field-level evidence provenance tracing each fact to its source."
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if research failed or was partially completed."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when research was completed."
    )
