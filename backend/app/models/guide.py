from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal, Set
from datetime import datetime

# Evidence confidence ratings for transparency and rigor
EvidenceConfidence = Literal[
    "VERIFIED_TESTED",      # Directly verified via test run or live portal inspection
    "OFFICIAL_DOCS",        # Cited directly from official provider documentation
    "ESTIMATE_HEURISTIC",   # Policy-based estimate derived from published thresholds/rules
    "UNCERTAIN"             # Ambiguous, conflicting, or unverified
]

# State of knowledge for optional/conditional fields
ValueStatus = Literal[
    "ESTABLISHED",          # Firmly established and supported by source
    "NOT_STATED",           # Source makes no mention of this
    "NOT_APPLICABLE",       # Concept does not apply in this mode/context
    "UNCERTAIN"             # Ambiguous, conditional, or dependent on unstated variables
]

# Path type for setup steps
SetupPathType = Literal[
    "MANAGED_OAUTH",        # Steps when using Composio Managed OAuth (zero provider app setup)
    "CUSTOM_OAUTH",         # Steps when bringing custom OAuth app credentials
    "GENERAL"               # General preparation or post-connection step
]

# Evidence provenance / retrieval status
RetrievalStatus = Literal[
    "CURATED_STATIC",       # Curated official documentation citation (not a live automated network fetch)
    "LIVE_RETRIEVED",       # Dynamically fetched over HTTP by the live investigation agent
    "MANUAL_VERIFIED",      # Manually inspected and confirmed directly in provider portal
    "FAILED_HTTP_ERROR",    # Live retrieval attempted but failed with HTTP error code
    "FAILED_TIMEOUT"        # Live retrieval attempted but timed out
]

# Review Requirement Types
ReviewRequirementType = Literal[
    "OAUTH_VERIFICATION",       # Provider OAuth brand / consent screen verification
    "SECURITY_ASSESSMENT",      # Third-party or framework security assessment (e.g. CASA)
    "APP_STORE_LISTING_REVIEW", # Public marketplace / directory listing review
    "NONE"                      # No review required for this distribution tier
]

# Review Applicability Status
ReviewApplicability = Literal[
    "MANDATORY",                # Always required for this provider/tier
    "CONDITIONAL",              # Required only under specific architectural or scope conditions
    "NOT_APPLICABLE"            # Does not apply to this distribution path
]

class SourceItem(BaseModel):
    id: str                                                 # e.g., "src-01"
    title: str
    url: str
    page_section: Optional[str] = None                      # Specific section or header of the page
    evidence_excerpt: Optional[str] = None                  # Verbatim supporting passage from docs
    retrieved_at: Optional[datetime] = None                 # Timestamp of retrieval (if live/verified)
    retrieval_status: RetrievalStatus = "CURATED_STATIC"    # Explicit provenance
    http_status_code: Optional[int] = None                  # Only present if live HTTP fetch occurred
    confidence: EvidenceConfidence
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_official_docs_excerpt(self):
        """Ensure official documentation sources provide an explicit page section and excerpt."""
        if self.confidence == "OFFICIAL_DOCS":
            if not self.evidence_excerpt or not self.evidence_excerpt.strip():
                raise ValueError(
                    f"Source '{self.id}' with confidence 'OFFICIAL_DOCS' must provide a non-empty evidence_excerpt."
                )
            if not self.page_section or not self.page_section.strip():
                raise ValueError(
                    f"Source '{self.id}' with confidence 'OFFICIAL_DOCS' must specify page_section."
                )
        return self

class AuthSchemeDetail(BaseModel):
    scheme: Literal["OAUTH2", "API_KEY", "BEARER_TOKEN", "BASIC", "CUSTOM"]
    is_managed_by_composio: bool
    description: str

class ComposioStatus(BaseModel):
    toolkit_slug: Optional[str] = None
    catalog_status: Literal["IN_CATALOG", "NOT_IN_COMPOSIO_CATALOG"]
    supported_schemes: List[AuthSchemeDetail] = Field(default_factory=list)
    supports_oauth: bool
    managed_oauth_available: bool
    custom_oauth_mandatory_for_oauth: bool                  # True ONLY IF user needs OAuth AND managed_oauth_available is False
    alternative_auth_methods: List[str] = Field(default_factory=list)
    when_to_use_custom_oauth: List[str] = Field(default_factory=list)
    composio_redirect_uri: Optional[str] = None             # Obtained from dashboard flow or null if unconfirmed
    redirect_uri_notes: Optional[str] = None

class ActiveEffortClaim(BaseModel):
    confidence: EvidenceConfidence                          # Claim-level confidence
    status: ValueStatus
    minutes_min: Optional[int] = None
    minutes_max: Optional[int] = None
    basis: Optional[str] = None
    source_ids: List[str] = Field(default_factory=list)

class ProviderReviewClaim(BaseModel):
    confidence: EvidenceConfidence                          # Claim-level confidence
    status: ValueStatus
    review_required: Optional[bool] = None                  # None if conditional or unknown
    wait_days_min: Optional[int] = None
    wait_days_max: Optional[int] = None
    review_type: Optional[Literal[
        "NONE", 
        "SELF_SERVE", 
        "AUTOMATED_SCAN", 
        "HUMAN_APP_REVIEW", 
        "SECURITY_ASSESSMENT"
    ]] = None
    conditions: Optional[str] = None
    basis: Optional[str] = None
    source_ids: List[str] = Field(default_factory=list)

class ReviewRequirementItem(BaseModel):
    """
    Granular review requirement representing an independent review or assessment gate
    (e.g., Google OAuth Verification vs. CASA Security Assessment).
    """
    id: str                                                 # e.g., "rev-google-oauth", "rev-google-casa"
    title: str                                              # Human-readable title
    requirement_type: ReviewRequirementType                 # OAUTH_VERIFICATION, SECURITY_ASSESSMENT, etc.
    applicability: ReviewApplicability                      # MANDATORY, CONDITIONAL, NOT_APPLICABLE
    scope_tier: Optional[Literal[
        "ALL_SCOPES",
        "NON_SENSITIVE",
        "SENSITIVE",
        "RESTRICTED",
        "NOT_APPLICABLE"
    ]] = None
    conditions: str                                         # Circumstances under which this applies or is exempt
    assurance_level: Optional[str] = None                   # Assessment level details (e.g. CASA Tier 2 risk-based)
    annual_reassessment_required: bool = False              # Whether periodic recertification is required
    confidence: EvidenceConfidence
    source_ids: List[str] = Field(default_factory=list)

class SetupStep(BaseModel):
    step_number: int
    title: str
    instructions: str
    portal_url: Optional[str] = None
    is_automated_by_agent: bool
    path_type: SetupPathType = "GENERAL"                    # Distinguishes Managed vs Custom OAuth paths
    source_ids: List[str] = Field(default_factory=list)

class BlockerItem(BaseModel):
    id: str                                                 # e.g., "blk-01"
    title: str
    category: Literal[
        "DOMAIN_VERIFICATION", 
        "PRIVACY_POLICY_AND_TERMS", 
        "VIDEO_DEMO_OR_SCOPES", 
        "PAID_ACCOUNT_OR_TIER", 
        "BUSINESS_OR_LEGAL_ENTITY", 
        "SECURITY_ASSESSMENT",
        "OTHER"
    ]
    description: str
    mitigation_or_workaround: str
    source_ids: List[str] = Field(default_factory=list)

class HumanAgentBoundary(BaseModel):
    what_agent_can_automate: List[str]
    what_human_must_do: List[str]

class ComposioCodeSnippets(BaseModel):
    session_create_managed: Optional[str] = None
    session_create_custom: Optional[str] = None
    auth_config_request_payload: Optional[str] = None

class OAuthGuide(BaseModel):
    id: str
    slug: str
    app_name: str
    app_website: str
    developer_portal_url: Optional[str] = None
    summary: str
    difficulty_rating: Literal["VERY_EASY", "MODERATE", "COMPLEX", "ENTERPRISE_GATED"]
    
    # Composio Integration Metadata
    composio_status: ComposioStatus
    
    # Timelines & Effort with Claim-Level Evidence Links
    active_effort: ActiveEffortClaim
    provider_review: ProviderReviewClaim
    
    # Granular Independent Review Requirements (OAuth Verification, CASA, App Store Review)
    review_requirements: List[ReviewRequirementItem] = Field(default_factory=list)
    
    # Nuances, Blockers, Steps with Evidence Links
    blockers: List[BlockerItem] = Field(default_factory=list)
    setup_steps: List[SetupStep] = Field(default_factory=list)
    human_agent_boundary: HumanAgentBoundary
    
    # Integration Code
    code_snippets: ComposioCodeSnippets
    
    # Source Registry with Exact Excerpts and Provenance
    sources: List[SourceItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_source_references(self):
        """Strict model-level validation: ensures every referenced source_id exists in sources registry."""
        registered_ids: Set[str] = {s.id for s in self.sources}

        def check_ids(source_ids: List[str], claim_name: str):
            for sid in source_ids:
                if sid not in registered_ids:
                    raise ValueError(
                        f"Dangling source reference: '{sid}' is referenced in {claim_name} "
                        f"for guide '{self.slug}', but not registered in sources list."
                    )

        # 1. Check timeline claims
        check_ids(self.active_effort.source_ids, "active_effort")
        check_ids(self.provider_review.source_ids, "provider_review")

        # 2. Check granular review requirements
        for req in self.review_requirements:
            check_ids(req.source_ids, f"review_requirement '{req.id}' ('{req.title}')")

        # 3. Check setup steps
        for step in self.setup_steps:
            check_ids(step.source_ids, f"setup_step #{step.step_number} ('{step.title}')")

        # 4. Check blockers
        for blocker in self.blockers:
            check_ids(blocker.source_ids, f"blocker '{blocker.id}' ('{blocker.title}')")

        return self

class GuideSummary(BaseModel):
    id: str
    slug: str
    app_name: str
    app_website: str
    difficulty_rating: Literal["VERY_EASY", "MODERATE", "COMPLEX", "ENTERPRISE_GATED"]
    composio_status: ComposioStatus
    active_effort: ActiveEffortClaim
    provider_review: ProviderReviewClaim
    review_requirements: List[ReviewRequirementItem] = Field(default_factory=list)

class AppListResponse(BaseModel):
    total: int
    items: List[GuideSummary]

class ShareGuideRequest(BaseModel):
    guide_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_\-\.]{1,100}$",
        description="Target guide identifier or slug to share",
    )

class ShareGuideResponse(BaseModel):
    guide_id: str
    share_url: str
    created_at: datetime

class InvestigateRequest(BaseModel):
    app_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[\w\s\-\.\,\(\)\/\+]{1,100}$",
        description="Name of the application to investigate",
    )
    website: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional website or documentation URL",
    )
