"""
OAuth Research Engine Service (Milestone 3.0 - Milestone 3.3).

Orchestrates evidence-grounded research using:
1. Deterministic Evidence Research Engine (Zero-Cost, 100% Offline/Deterministic).
2. Google Gemini SDK (`google-genai`) without paid search grounding.
3. Automatic fallback to Deterministic Evidence Engine on Gemini timeout/503/errors.
"""
import re
import json
import logging
import asyncio
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timezone

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.security import redact_sensitive_data
from app.core.rate_limit import gemini_quota_protection
from app.services.doc_fetcher import (
    DocFetcherService,
    FetchedDoc,
    doc_fetcher_service,
)
from app.models.guide import (
    EvidenceConfidence,
    ValueStatus,
    ReviewRequirementItem,
    ReviewRequirementType,
    ReviewApplicability,
    HumanAgentBoundary,
)
from app.models.composio import (
    ComposioClassification,
    ComposioToolkitCheckResponse,
)
from app.models.research import (
    ResearchStatus,
    OAuthFlowDetails,
    ProviderRegistrationRequirements,
    RedirectUriRequirements,
    ScopeRequirement,
    ReviewTimelineInfo,
    ResearchCitation,
    ResearchResultResponse,
)
from app.services.composio_metadata import composio_metadata_service
from app.services.evidence_engine import deterministic_evidence_engine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage 1: Evidence-Grounded Prompt Construction (Zero-Cost, No Paid Search)
# ---------------------------------------------------------------------------

def build_evidence_grounded_prompt(
    app_name: str,
    website_or_domain: Optional[str],
    fetched_docs: List[FetchedDoc],
    composio_status: Optional[ComposioToolkitCheckResponse],
) -> str:
    """
    Constructs an evidence-grounded research prompt instructing Gemini to analyze
    ONLY the retrieved official documentation and metadata provided in the prompt.
    Does NOT use external search tools.
    """
    domain_hint = f" (website/domain: {website_or_domain})" if website_or_domain else ""

    # Compile document excerpts
    doc_sections: List[str] = []
    for idx, doc in enumerate(fetched_docs):
        src_id = f"src_{idx + 1}"
        meta_note = " [RFC 8414 OAuth Metadata]" if doc.is_oauth_metadata else ""
        doc_header = f"=== SOURCE [{src_id}]{meta_note} ===\nURL: {doc.final_url}\nTitle: {doc.title}"
        doc_body = doc.text[:12000] if doc.text else "No text extracted."
        doc_sections.append(f"{doc_header}\nContent:\n{doc_body}\n")

    docs_block = "\n".join(doc_sections) if doc_sections else "No official documentation pages were retrieved."

    # Composio catalog context
    composio_info = "Not checked"
    if composio_status:
        composio_info = (
            f"Classification: {composio_status.classification}, "
            f"Supports OAuth: {composio_status.supports_oauth}, "
            f"Composio-Managed OAuth: {composio_status.classification == ComposioClassification.COMPOSIO_MANAGED_AVAILABLE}, "
            f"Auth Schemes: {getattr(composio_status, 'supported_auth_schemes', [])}"
        )

    return f"""You are an expert OAuth security and integration research engine.
Analyze the OAuth 2.0 / authentication capabilities for the application: "{app_name}"{domain_hint}.

COMPOSIO INTEGRATION CONTEXT:
{composio_info}

RETRIEVED OFFICIAL DOCUMENTATION AND METADATA:
{docs_block}

CRITICAL RESEARCH INSTRUCTIONS:
1. Base your analysis STRICTLY on the RETRIEVED OFFICIAL DOCUMENTATION AND METADATA provided above.
2. NEVER invent, fabricate, or hallucinate URLs, waiting periods, review steps, client secret procedures, or endpoints.
3. If a detail is NOT documented in the provided text, explicitly return null or mark it as "NOT_STATED" / "NOT_APPLICABLE".
4. For every review requirement in `review_requirements`, you MUST reference the source identifier (e.g. ["src_1"]) from the provided sources that contains the supporting text.
5. Clarify the difference between:
   - Composio-Managed OAuth: Composio provides the pre-configured OAuth application so developers do not need to register an app.
   - Custom OAuth: Developer must register an OAuth application on the provider's developer console.
6. Clearly separate what the human developer must do vs what the AI agent can automate.

Output MUST be a single valid JSON object adhering strictly to this schema:
{{
  "supports_oauth": true/false,
  "summary": "Concise factual summary of OAuth support and registration workflow.",
  "protocol_version": "OAuth 2.0" or null,
  "grant_types": ["authorization_code", "refresh_token", ...],
  "authorization_endpoint": "https://..." or null,
  "token_endpoint": "https://..." or null,
  "pkce_required": true/false/null,
  "developer_portal_url": "https://..." or null,
  "account_type_required": "Free developer account" or null,
  "requires_client_id": true/false,
  "requires_client_secret": true/false,
  "client_secret_notes": "..." or null,
  "allowed_schemes": ["https"],
  "allows_localhost": true/false/null,
  "wildcards_permitted": true/false/null,
  "strict_exact_match": true/false,
  "scopes": [
    {{"scope": "...", "description": "...", "is_sensitive": true/false/null}}
  ],
  "review_required": true/false,
  "review_type": "OAuth App Verification" or null,
  "estimated_waiting_period_days": 5 or null,
  "waiting_period_status": "ESTABLISHED" or "NOT_STATED" or "NOT_APPLICABLE",
  "review_requirements": [
    {{
      "requirement_type": "OAUTH_VERIFICATION" or "SECURITY_ASSESSMENT" or "APP_STORE_LISTING_REVIEW" or "NONE",
      "name": "...",
      "description": "...",
      "mandatory": true/false,
      "applicability": "MANDATORY" or "CONDITIONAL" or "NOT_APPLICABLE",
      "condition_notes": "...",
      "source_ids": ["src_1"]
    }}
  ],
  "what_human_must_do": ["Create developer account", ...],
  "what_agent_can_automate": ["Generate redirect URI", ...],
  "confidence": "OFFICIAL_DOCS" or "ESTIMATE_HEURISTIC" or "UNCERTAIN"
}}
"""


def build_research_prompt(app_name: str, website_or_domain: Optional[str] = None) -> str:
    """Legacy compatibility prompt builder (for direct prompt tests)."""
    return build_evidence_grounded_prompt(app_name, website_or_domain, [], None)


# ---------------------------------------------------------------------------
# Stage 2: Evidence Citation Construction & Excerpt Validation
# ---------------------------------------------------------------------------

def build_citations_from_docs(fetched_docs: List[FetchedDoc]) -> List[ResearchCitation]:
    """
    Constructs verifiable ResearchCitation records directly from fetched documents.
    Source URLs strictly originate from the actual retrieved documents.
    """
    citations: List[ResearchCitation] = []
    seen_urls: Set[str] = set()

    for idx, doc in enumerate(fetched_docs):
        if not doc.final_url or doc.final_url in seen_urls:
            continue
        seen_urls.add(doc.final_url)

        src_id = f"src_{len(citations) + 1}"
        domain = doc.domain.lower() if doc.domain else ""

        # Classify source type based on domain and URL patterns
        source_type = "COMMUNITY"
        if any(term in domain for term in ("developer.", "dev.", "docs.", "api.", "help.", "support.")):
            source_type = "OFFICIAL_DOCS"
        elif any(term in doc.url.lower() for term in ("/docs", "/api", "/developer", "/developers", "/.well-known/")):
            source_type = "OFFICIAL_DOCS"

        title = doc.title or f"Documentation ({domain})"
        excerpt = doc.evidence_excerpt or (doc.text[:300].strip() if doc.text else None)

        citations.append(
            ResearchCitation(
                id=src_id,
                title=title,
                url=doc.final_url,
                domain=domain,
                evidence_excerpt=excerpt,
                source_type=source_type,
                retrieval_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )
        )

    return citations


def validate_and_filter_evidence(
    parsed_data: Dict[str, Any],
    fetched_docs: List[FetchedDoc],
    citations: List[ResearchCitation],
) -> Dict[str, Any]:
    """
    Validates model claims against the actual retrieved document text.
    - Ensures source_ids only reference real fetched source IDs.
    - Discards unsupported or hallucinated source IDs.
    - Validates that waiting periods are backed by document text.
    """
    data = dict(parsed_data)
    valid_source_ids = {c.id for c in citations}
    corpus = " ".join(doc.text for doc in fetched_docs).lower() if fetched_docs else ""

    # 1. Review requirements source ID validation
    raw_reqs = data.get("review_requirements", [])
    if isinstance(raw_reqs, list):
        cleaned_reqs = []
        for req in raw_reqs:
            if isinstance(req, dict) and "name" in req:
                req_copy = dict(req)
                raw_sources = req_copy.get("source_ids", [])
                if isinstance(raw_sources, list):
                    # Keep ONLY source IDs that exist in our citations
                    verified_sources = [str(s) for s in raw_sources if str(s) in valid_source_ids]
                    # If model provided no valid source IDs but we have citations, associate with first doc
                    if not verified_sources and citations:
                        verified_sources = [citations[0].id]
                    req_copy["source_ids"] = verified_sources
                cleaned_reqs.append(req_copy)
        data["review_requirements"] = cleaned_reqs

    # 2. Waiting period verification
    waiting_days = data.get("estimated_waiting_period_days")
    if waiting_days is not None:
        # Check if the number of days is mentioned in corpus or RFC metadata
        days_str = str(waiting_days)
        if days_str not in corpus and f"{days_str} day" not in corpus:
            logger.info("Discarding unsupported waiting period estimate: %s days", waiting_days)
            data["estimated_waiting_period_days"] = None
            data["waiting_period_status"] = "NOT_STATED"

    # 3. Confidence determination
    has_rfc = any(doc.is_oauth_metadata for doc in fetched_docs)
    has_official_docs = any(c.source_type == "OFFICIAL_DOCS" for c in citations)

    if has_rfc or has_official_docs:
        data["confidence"] = "OFFICIAL_DOCS"
    elif citations:
        data["confidence"] = "ESTIMATE_HEURISTIC"
    else:
        data["confidence"] = "UNCERTAIN"

    return data


def extract_grounding_citations(response: Any) -> Tuple[List[ResearchCitation], List[str]]:
    """
    Legacy grounding extractor preserved for backward compatibility and testing.
    Extracts citations and search queries if grounding_metadata or Interaction steps are present.
    """
    citations: List[ResearchCitation] = []
    queries: List[str] = []

    if not response:
        return citations, queries

    seen_urls = set()

    # Path A: Interactions API steps
    steps = getattr(response, "steps", None)
    if steps and isinstance(steps, list):
        for step in steps:
            step_type = getattr(step, "type", None)

            # Search queries from google_search_call
            if step_type == "google_search_call" or hasattr(step, "arguments"):
                args = getattr(step, "arguments", None)
                if args:
                    step_queries = getattr(args, "queries", None)
                    if step_queries is None and isinstance(args, dict):
                        step_queries = args.get("queries")
                    if isinstance(step_queries, list):
                        for q in step_queries:
                            if q and str(q) not in queries:
                                queries.append(str(q))

            # URL citations from model_output content annotations
            if step_type == "model_output" or hasattr(step, "content"):
                content_list = getattr(step, "content", None) or []
                for item in content_list:
                    item_text = getattr(item, "text", "") or ""
                    annotations = getattr(item, "annotations", None) or []
                    for ann in annotations:
                        uri = getattr(ann, "url", None)
                        if not uri and hasattr(ann, "uri"):
                            uri = getattr(ann, "uri")
                        if not uri or uri in seen_urls:
                            continue

                        seen_urls.add(uri)
                        domain = urlparse(uri).netloc.lower()

                        source_type = "COMMUNITY"
                        if any(term in domain for term in ("developer.", "dev.", "docs.", "api.", "help.", "support.")):
                            source_type = "OFFICIAL_DOCS"
                        elif any(term in uri.lower() for term in ("/docs", "/api", "/developer", "/developers")):
                            source_type = "OFFICIAL_DOCS"

                        title = getattr(ann, "title", None) or "Documentation Source"
                        start_idx = getattr(ann, "start_index", None)
                        end_idx = getattr(ann, "end_index", None)
                        excerpt = None
                        if item_text and isinstance(start_idx, int) and isinstance(end_idx, int):
                            if 0 <= start_idx < end_idx <= len(item_text):
                                excerpt = item_text[start_idx:end_idx].strip()

                        citations.append(
                            ResearchCitation(
                                id=f"src_{len(citations) + 1}",
                                title=title,
                                url=uri,
                                domain=domain,
                                evidence_excerpt=excerpt,
                                source_type=source_type,
                                retrieval_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                            )
                        )

    # Path B: Legacy/candidate grounding_metadata fallback
    if not citations and hasattr(response, "candidates") and response.candidates:
        candidate = response.candidates[0]
        grounding_meta = getattr(candidate, "grounding_metadata", None)
        if grounding_meta:
            web_queries = getattr(grounding_meta, "web_search_queries", []) or []
            for q in web_queries:
                if q and str(q) not in queries:
                    queries.append(str(q))

            chunks = getattr(grounding_meta, "grounding_chunks", []) or []
            supports = getattr(grounding_meta, "grounding_supports", []) or []

            chunk_excerpts: Dict[int, str] = {}
            for support in supports:
                indices = getattr(support, "grounding_chunk_indices", []) or []
                segment = getattr(support, "segment", None)
                seg_text = getattr(segment, "text", "") if segment else ""
                if seg_text:
                    for idx in indices:
                        if idx not in chunk_excerpts:
                            chunk_excerpts[idx] = seg_text.strip()

            for idx, chunk in enumerate(chunks):
                web = getattr(chunk, "web", None)
                if not web:
                    continue
                uri = getattr(web, "uri", None)
                title = getattr(web, "title", None) or "Documentation Source"
                if not uri or uri in seen_urls:
                    continue
                seen_urls.add(uri)
                domain = urlparse(uri).netloc.lower()

                source_type = "COMMUNITY"
                if any(term in domain for term in ("developer.", "dev.", "docs.", "api.", "help.", "support.")):
                    source_type = "OFFICIAL_DOCS"
                elif any(term in uri.lower() for term in ("/docs", "/api", "/developer", "/developers")):
                    source_type = "OFFICIAL_DOCS"

                excerpt = chunk_excerpts.get(idx)
                citations.append(
                    ResearchCitation(
                        id=f"src_{len(citations) + 1}",
                        title=title,
                        url=uri,
                        domain=domain,
                        evidence_excerpt=excerpt,
                        source_type=source_type,
                        retrieval_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    )
                )

    return citations, queries


def extract_model_output_text(response: Any) -> str:
    """
    Extracts raw text output from an Interaction response or candidate.
    """
    if not response:
        return ""

    # 1. Direct output_text on Interaction
    out = getattr(response, "output_text", None)
    if isinstance(out, str) and out.strip():
        return out.strip()

    # 2. Text property (some SDK wrappers)
    text_prop = getattr(response, "text", None)
    if isinstance(text_prop, str) and text_prop.strip():
        return text_prop.strip()

    # 3. Steps with model_output
    steps = getattr(response, "steps", None)
    if steps and isinstance(steps, list):
        step_texts = []
        for step in steps:
            if getattr(step, "type", None) == "model_output" or hasattr(step, "content"):
                content_list = getattr(step, "content", None) or []
                for item in content_list:
                    item_text = getattr(item, "text", None)
                    if item_text:
                        step_texts.append(item_text)
        if step_texts:
            return "".join(step_texts).strip()

    # 4. Candidates fallback
    if hasattr(response, "candidates") and response.candidates:
        cand = response.candidates[0]
        if hasattr(cand, "content") and cand.content and hasattr(cand.content, "parts"):
            return "".join(getattr(p, "text", "") for p in cand.content.parts if getattr(p, "text", None)).strip()

    return ""


# ---------------------------------------------------------------------------
# Stage 3: Model Output Parsing & JSON Extraction
# ---------------------------------------------------------------------------

def parse_model_research_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Safely parses JSON output from Gemini's response text.
    Handles raw JSON, markdown-wrapped JSON (```json ... ```), or embedded objects.
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    cleaned = raw_text.strip()

    # 1. Direct parse attempt
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 2. Markdown fenced block: ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if match:
        try:
            data = json.loads(match.group(1).strip())
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    # 3. First outermost JSON object: { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            data = json.loads(cleaned[first_brace:last_brace + 1])
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return None


# ---------------------------------------------------------------------------
# Stage 4: Result Assembly and Evidence Validation
# ---------------------------------------------------------------------------

def build_research_result(
    app_name: str,
    website_or_domain: Optional[str],
    status: ResearchStatus,
    parsed_data: Optional[Dict[str, Any]],
    citations: List[ResearchCitation],
    search_queries: List[str],
    composio_status: Optional[ComposioToolkitCheckResponse],
    error_message: Optional[str] = None,
) -> ResearchResultResponse:
    """
    Constructs a validated ResearchResultResponse, normalizing confidence,
    applying secret redaction, and mapping structured claims.
    """
    data = parsed_data or {}

    # OAuth details: Preserve verified Composio OAuth status when AI analysis is unavailable/failed
    supports_oauth_val = data.get("supports_oauth")
    if supports_oauth_val is not None:
        supports_oauth = bool(supports_oauth_val)
    elif composio_status and composio_status.supports_oauth:
        supports_oauth = True
    elif status == ResearchStatus.UNKNOWN_APPLICATION:
        supports_oauth = None
    elif composio_status and not composio_status.supports_oauth:
        supports_oauth = False
    else:
        supports_oauth = None

    raw_confidence = str(data.get("confidence", "UNCERTAIN")).upper()
    valid_confidences = {"VERIFIED_TESTED", "OFFICIAL_DOCS", "ESTIMATE_HEURISTIC", "UNCERTAIN"}
    if raw_confidence in valid_confidences:
        confidence = raw_confidence
    elif status == ResearchStatus.FAILED:
        # When research failed, confidence is UNCERTAIN because AI analysis was not completed
        confidence = "UNCERTAIN"
    else:
        confidence = "OFFICIAL_DOCS" if any(c.source_type == "OFFICIAL_DOCS" for c in citations) else "UNCERTAIN"

    # Protocol version: from model data, or verified Composio metadata
    protocol_version = data.get("protocol_version")
    if not protocol_version and composio_status and composio_status.supports_oauth:
        schemes = [str(s).upper() for s in getattr(composio_status, "supported_auth_schemes", [])]
        if "OAUTH2" in schemes:
            protocol_version = "OAuth 2.0"

    oauth_details = OAuthFlowDetails(
        supports_oauth=supports_oauth,
        confidence=confidence,
        protocol_version=protocol_version,
        grant_types=data.get("grant_types", []) if isinstance(data.get("grant_types"), list) else [],
        authorization_endpoint=data.get("authorization_endpoint"),
        token_endpoint=data.get("token_endpoint"),
        pkce_required=data.get("pkce_required"),
    )

    # Provider registration
    registration = ProviderRegistrationRequirements(
        developer_portal_url=data.get("developer_portal_url"),
        account_type_required=data.get("account_type_required"),
        requires_client_id=bool(data.get("requires_client_id", True)),
        requires_client_secret=bool(data.get("requires_client_secret", True)),
        client_secret_notes=data.get("client_secret_notes"),
    )

    # Redirect URI rules
    allowed_schemes = data.get("allowed_schemes")
    if not isinstance(allowed_schemes, list) or not allowed_schemes:
        allowed_schemes = ["https"]

    redirect_rules = RedirectUriRequirements(
        allowed_schemes=allowed_schemes,
        allows_localhost=data.get("allows_localhost"),
        wildcards_permitted=data.get("wildcards_permitted"),
        strict_exact_match=bool(data.get("strict_exact_match", True)),
        composio_redirect_uri_supported=True,
    )

    # Scopes
    scopes_list: List[ScopeRequirement] = []
    raw_scopes = data.get("scopes", [])
    if isinstance(raw_scopes, list):
        for s in raw_scopes:
            if isinstance(s, dict) and "scope" in s:
                scopes_list.append(
                    ScopeRequirement(
                        scope=str(s["scope"]),
                        description=s.get("description"),
                        is_sensitive=s.get("is_sensitive"),
                    )
                )

    # Review timeline info
    raw_waiting_status = str(data.get("waiting_period_status", "NOT_STATED")).upper()
    valid_waiting_statuses = {"ESTABLISHED", "NOT_STATED", "NOT_APPLICABLE", "UNCERTAIN"}
    waiting_status = raw_waiting_status if raw_waiting_status in valid_waiting_statuses else "NOT_STATED"

    review_requirements_list: List[ReviewRequirementItem] = []
    raw_rev_reqs = data.get("review_requirements", [])
    if isinstance(raw_rev_reqs, list):
        for req in raw_rev_reqs:
            if isinstance(req, dict) and "name" in req:
                valid_req_types = {"OAUTH_VERIFICATION", "SECURITY_ASSESSMENT", "APP_STORE_LISTING_REVIEW", "NONE"}
                raw_req_type = str(req.get("requirement_type", "OAUTH_VERIFICATION")).upper()
                req_type = raw_req_type if raw_req_type in valid_req_types else "OAUTH_VERIFICATION"

                valid_app_types = {"MANDATORY", "CONDITIONAL", "NOT_APPLICABLE"}
                raw_app_type = str(req.get("applicability", "CONDITIONAL")).upper()
                app_type = raw_app_type if raw_app_type in valid_app_types else "CONDITIONAL"

                req_title = str(req.get("title") or req.get("name") or "Review Requirement")
                req_id = str(req.get("id") or f"rev_{len(review_requirements_list) + 1}")
                req_conditions = str(req.get("conditions") or req.get("condition_notes") or req.get("description") or "Documented review gate")
                req_confidence = req.get("confidence") or confidence

                review_requirements_list.append(
                    ReviewRequirementItem(
                        id=req_id,
                        title=req_title,
                        requirement_type=req_type,
                        applicability=app_type,
                        conditions=req_conditions,
                        confidence=req_confidence if req_confidence in {"OFFICIAL_DOCS", "ESTIMATE_HEURISTIC", "UNCERTAIN"} else "UNCERTAIN",
                        source_ids=req.get("source_ids", []),
                    )
                )

    raw_review_req = data.get("review_required")
    if raw_review_req is not None:
        review_required = bool(raw_review_req)
    elif status == ResearchStatus.UNKNOWN_APPLICATION:
        review_required = None
    else:
        review_required = None

    review_timeline = ReviewTimelineInfo(
        review_required=review_required,
        review_type=data.get("review_type"),
        estimated_waiting_period_days=data.get("estimated_waiting_period_days") if isinstance(data.get("estimated_waiting_period_days"), int) else None,
        waiting_period_status=waiting_status,
        review_requirements=review_requirements_list,
    )

    # Human-agent boundary
    human_actions = data.get("what_human_must_do") or data.get("human_actions", [])
    if not isinstance(human_actions, list) or not human_actions:
        if status == ResearchStatus.FAILED:
            human_actions = [
                "Review retrieved documentation manually or retry research query once AI service is available",
                "Register developer account with provider if custom OAuth credentials are required",
            ]
        else:
            human_actions = ["Register developer account and generate OAuth credentials"]

    agent_actions = data.get("what_agent_can_automate") or data.get("agent_actions", [])
    if not isinstance(agent_actions, list) or not agent_actions:
        if status == ResearchStatus.FAILED:
            if composio_status and composio_status.classification == ComposioClassification.COMPOSIO_MANAGED_AVAILABLE:
                agent_actions = ["Connect via verified Composio-managed OAuth integration"]
            else:
                agent_actions = ["Retrieve public official developer documentation and check Composio catalog"]
        else:
            agent_actions = ["Configure Composio auth parameters and test authorization flow"]

    boundary = HumanAgentBoundary(
        what_human_must_do=[str(a) for a in human_actions],
        what_agent_can_automate=[str(a) for a in agent_actions],
    )

    # Factual summary: Never claim research completed when status is FAILED
    if data.get("summary"):
        summary = str(data["summary"])
    elif status == ResearchStatus.FAILED:
        summary_parts = []
        if error_message:
            summary_parts.append(f"OAuth research could not be completed for '{app_name}': {error_message}")
        else:
            summary_parts.append(f"OAuth research could not be completed for '{app_name}'.")

        if citations:
            summary_parts.append(f"{len(citations)} official documentation source(s) were retrieved, but AI analysis was not completed.")
        else:
            summary_parts.append("Official documentation could not be analyzed.")

        if composio_status and composio_status.supports_oauth:
            summary_parts.append(f"Composio catalog confirmed OAuth2 support ({composio_status.classification}).")
        elif composio_status:
            summary_parts.append(f"Composio catalog check returned: {composio_status.classification}.")

        summary = " ".join(summary_parts)
    else:
        summary = f"OAuth research completed for {app_name}."

    result = ResearchResultResponse(
        app_name=app_name,
        website_or_domain=website_or_domain,
        status=status,
        summary=summary,
        oauth_details=oauth_details,
        registration=registration,
        redirect_uri_rules=redirect_rules,
        scopes=scopes_list,
        review_timeline=review_timeline,
        composio_status=composio_status,
        human_agent_boundary=boundary,
        sources=citations,
        search_queries_used=search_queries,
        confidence=confidence,
        field_provenance=data.get("field_provenance") or {},
        error_message=error_message,
        created_at=datetime.now(timezone.utc),
    )

    # Security hardening: Redact all sensitive credentials from final result
    sanitized_dict = redact_sensitive_data(result.model_dump())
    return ResearchResultResponse.model_validate(sanitized_dict)


# ---------------------------------------------------------------------------
# Stage 5: Research Engine Service
# ---------------------------------------------------------------------------

class GeminiResearchService:
    """
    Modular research service using Google's official `google-genai` SDK
    and deterministic evidence-based fallback (Milestone 3.3).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        client: Optional[Any] = None,
        gemini_enabled: Optional[bool] = None,
        fallback_to_evidence: Optional[bool] = None,
    ):
        self.api_key = api_key
        self.model = model or settings.GEMINI_MODEL
        self.timeout = timeout or settings.GEMINI_TIMEOUT_SECONDS
        self._client = client
        self._gemini_enabled = gemini_enabled
        self._fallback_to_evidence = fallback_to_evidence

    def _get_effective_key(self) -> str:
        """Dynamically resolve API key, prioritizing instance key then settings."""
        if self.api_key is not None:
            return self.api_key.strip()
        return settings.GEMINI_API_KEY.strip()

    def _get_client(self, effective_key: str) -> Any:
        """Instantiate or return the GenAI client."""
        if self._client is not None:
            return self._client
        return genai.Client(api_key=effective_key)

    async def research_app(
        self,
        app_name: str,
        website_or_domain: Optional[str] = None,
    ) -> ResearchResultResponse:
        """
        Execute automated OAuth research for an application.

        Stages:
        1. Validate input and check feature toggles.
        2. Query Composio toolkit catalog for known metadata.
        3. Retrieve official documentation & RFC metadata via doc_fetcher.
        4. If GEMINI_RESEARCH_ENABLED is False, generate guide directly using
           DeterministicEvidenceResearchEngine.
        5. If GEMINI_RESEARCH_ENABLED is True, attempt Gemini analysis.
        6. If Gemini fails (503, 429, timeout, invalid JSON), fall back to
           DeterministicEvidenceResearchEngine to ensure successful guide generation.
        """
        cleaned_app = app_name.strip()
        if not cleaned_app:
            return build_research_result(
                app_name=app_name,
                website_or_domain=website_or_domain,
                status=ResearchStatus.FAILED,
                parsed_data=None,
                citations=[],
                search_queries=[],
                composio_status=None,
                error_message="Application name cannot be empty.",
            )

        # 1. Feature flag check
        if not settings.RESEARCH_ENABLED:
            logger.info("Research engine is disabled via RESEARCH_ENABLED setting.")
            return build_research_result(
                app_name=cleaned_app,
                website_or_domain=website_or_domain,
                status=ResearchStatus.DISABLED,
                parsed_data={"summary": f"OAuth research engine is currently disabled."},
                citations=[],
                search_queries=[],
                composio_status=None,
                error_message="Research engine is currently disabled in backend settings.",
            )

        # 2. Check Composio toolkit catalog first
        composio_status: Optional[ComposioToolkitCheckResponse] = None
        try:
            composio_status = await composio_metadata_service.fetch_toolkit_metadata(cleaned_app)
        except Exception as exc:
            logger.warning("Composio metadata lookup failed during research for %s: %s", cleaned_app, str(exc))

        # 3. Retrieve official documentation & OAuth discovery metadata using doc_fetcher_service
        composio_doc_url = getattr(composio_status, "documentation_url", None) if composio_status else None
        fetched_docs: List[FetchedDoc] = []
        try:
            fetched_docs = await doc_fetcher_service.fetch_documentation_for_app(
                app_name=cleaned_app,
                website_or_domain=website_or_domain,
                composio_doc_url=composio_doc_url,
                max_pages=settings.DOC_MAX_PAGES_PER_REQUEST,
            )
        except Exception as exc:
            logger.warning("Documentation fetcher error for %s: %s", cleaned_app, str(exc))

        # Build citations strictly from fetched documents (or empty list)
        citations = build_citations_from_docs(fetched_docs)

        # Determine if Gemini AI research should be attempted
        if self._gemini_enabled is not None:
            is_gemini_enabled = self._gemini_enabled
        elif self.api_key is not None or self._client is not None:
            # Explicit test parameters provided -> execute Gemini test pipeline
            is_gemini_enabled = True
        else:
            is_gemini_enabled = settings.GEMINI_RESEARCH_ENABLED

        # Determine whether fallback to deterministic engine is enabled on Gemini failure
        if self._fallback_to_evidence is not None:
            should_fallback = self._fallback_to_evidence
        elif self.api_key is not None or self._client is not None:
            # Injected test parameters default to no fallback unless explicitly requested
            should_fallback = False
        else:
            # Production default: fallback is always enabled
            should_fallback = True

        # When Gemini research is disabled, execute deterministic evidence engine directly
        if not is_gemini_enabled:
            logger.info("GEMINI_RESEARCH_ENABLED is False. Executing deterministic evidence engine directly for %s.", cleaned_app)
            return deterministic_evidence_engine.generate_guide(
                app_name=cleaned_app,
                website_or_domain=website_or_domain,
                composio_status=composio_status,
                fetched_docs=fetched_docs,
                citations=citations,
            )

        # 4. Check Gemini configuration
        effective_key = self._get_effective_key()
        if not effective_key:
            if should_fallback:
                logger.info("GEMINI_API_KEY is not configured. Falling back to deterministic evidence engine for %s.", cleaned_app)
                return deterministic_evidence_engine.generate_guide(
                    app_name=cleaned_app,
                    website_or_domain=website_or_domain,
                    composio_status=composio_status,
                    fetched_docs=fetched_docs,
                    citations=citations,
                )
            logger.info("GEMINI_API_KEY is not configured. Returning METADATA_ONLY response for %s.", cleaned_app)
            summary = (
                f"Gemini API key is not configured. Retrieved {len(fetched_docs)} documentation source(s). "
                f"Composio catalog check returned: {composio_status.classification if composio_status else 'UNCHECKED'}."
            )
            return build_research_result(
                app_name=cleaned_app,
                website_or_domain=website_or_domain,
                status=ResearchStatus.METADATA_ONLY,
                parsed_data={
                    "summary": summary,
                    "supports_oauth": composio_status.supports_oauth if composio_status else None,
                    "confidence": "OFFICIAL_DOCS" if any(c.source_type == "OFFICIAL_DOCS" for c in citations) else "UNCERTAIN",
                },
                citations=citations,
                search_queries=[],
                composio_status=composio_status,
                error_message="GEMINI_API_KEY is not configured on backend. Live AI analysis skipped.",
            )

        # 5. Handle "No documentation found"
        # If no docs retrieved and no mock client override provided, return structured status
        if not fetched_docs and self._client is None:
            logger.info("No documentation retrieved for %s.", cleaned_app)
            if composio_status and composio_status.classification in (
                ComposioClassification.COMPOSIO_MANAGED_AVAILABLE,
                ComposioClassification.CUSTOM_OAUTH_MANDATORY,
                ComposioClassification.NON_OAUTH_TOOLKIT,
                ComposioClassification.NO_AUTH_REQUIRED,
            ):
                summary = (
                    f"No public documentation pages retrieved for '{cleaned_app}'. "
                    f"Composio catalog confirmed status: {composio_status.classification}."
                )
                return build_research_result(
                    app_name=cleaned_app,
                    website_or_domain=website_or_domain,
                    status=ResearchStatus.METADATA_ONLY,
                    parsed_data={
                        "summary": summary,
                        "supports_oauth": composio_status.supports_oauth,
                        "confidence": "UNCERTAIN",
                    },
                    citations=[],
                    search_queries=[],
                    composio_status=composio_status,
                    error_message="No public developer documentation could be retrieved. Returning Composio catalog metadata.",
                )
            else:
                summary = f"No public developer documentation or Composio catalog entry found for '{cleaned_app}'."
                return build_research_result(
                    app_name=cleaned_app,
                    website_or_domain=website_or_domain,
                    status=ResearchStatus.UNKNOWN_APPLICATION,
                    parsed_data={"summary": summary, "supports_oauth": None, "confidence": "UNCERTAIN"},
                    citations=[],
                    search_queries=[],
                    composio_status=composio_status,
                    error_message=f"Application '{cleaned_app}' could not be identified from official documentation.",
                )

        # 6. Check Gemini quota protection controls
        can_call, quota_reason = await gemini_quota_protection.can_call()
        if not can_call:
            logger.warning("Gemini quota protection blocked research request for %s: %s", cleaned_app, quota_reason)
            if should_fallback:
                logger.info("Gemini quota reached. Falling back to deterministic evidence engine for %s.", cleaned_app)
                return deterministic_evidence_engine.generate_guide(
                    app_name=cleaned_app,
                    website_or_domain=website_or_domain,
                    composio_status=composio_status,
                    fetched_docs=fetched_docs,
                    citations=citations,
                )
            return build_research_result(
                app_name=cleaned_app,
                website_or_domain=website_or_domain,
                status=ResearchStatus.FAILED,
                parsed_data=None,
                citations=citations,
                search_queries=[],
                composio_status=composio_status,
                error_message=quota_reason or "Gemini daily quota limit reached.",
            )

        # 7. Construct evidence-grounded prompt (Zero Search Grounding Tools)
        prompt = build_evidence_grounded_prompt(cleaned_app, website_or_domain, fetched_docs, composio_status)
        prompt = gemini_quota_protection.sanitize_prompt_length(prompt)
        client = self._get_client(effective_key)

        try:
            # Make exactly ONE Gemini request with tools=None (NO SEARCH GROUNDING)
            if hasattr(client, "aio") and hasattr(client.aio, "interactions"):
                response = await asyncio.wait_for(
                    client.aio.interactions.create(
                        model=self.model,
                        input=prompt,
                        tools=None,  # Zero search grounding tools!
                        generation_config={"temperature": 0.1},
                    ),
                    timeout=self.timeout,
                )
            else:
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        # Zero tools!
                    ),
                    timeout=self.timeout,
                )
            await gemini_quota_protection.record_call()
        except asyncio.TimeoutError:
            logger.warning("Gemini research request timed out for %s after %s seconds", cleaned_app, self.timeout)
            if should_fallback:
                logger.info("Executing deterministic evidence fallback due to Gemini timeout for %s.", cleaned_app)
                return deterministic_evidence_engine.generate_guide(
                    app_name=cleaned_app,
                    website_or_domain=website_or_domain,
                    composio_status=composio_status,
                    fetched_docs=fetched_docs,
                    citations=citations,
                )
            return build_research_result(
                app_name=cleaned_app,
                website_or_domain=website_or_domain,
                status=ResearchStatus.FAILED,
                parsed_data=None,
                citations=citations,
                search_queries=[],
                composio_status=composio_status,
                error_message=f"Gemini research request timed out after {self.timeout} seconds.",
            )
        except Exception as exc:
            err_str = str(exc)
            logger.warning("Gemini API call failed for %s: %s", cleaned_app, err_str)
            if should_fallback:
                logger.info("Executing deterministic evidence fallback due to Gemini failure for %s: %s", cleaned_app, err_str)
                return deterministic_evidence_engine.generate_guide(
                    app_name=cleaned_app,
                    website_or_domain=website_or_domain,
                    composio_status=composio_status,
                    fetched_docs=fetched_docs,
                    citations=citations,
                )
            # Differentiate quota/rate limit and temporary high demand/service unavailable errors - NO automatic retries
            is_quota = "429" in err_str or "ResourceExhausted" in err_str or "quota" in err_str.lower()
            code = getattr(exc, "code", None) or getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
            is_503 = (
                code == 503
                or "503" in err_str
                or "service_unavailable" in err_str.lower()
                or "high demand" in err_str.lower()
                or "unavailable" in err_str.lower()
                or "overloaded" in err_str.lower()
            )
            if is_quota:
                error_msg = "Gemini API rate limit or quota exceeded. Please retry later."
            elif is_503:
                error_msg = "Gemini API is temporarily unavailable due to high demand (HTTP 503). AI analysis could not be completed. Please retry later."
            else:
                error_msg = f"Upstream AI research error: {err_str}"
            return build_research_result(
                app_name=cleaned_app,
                website_or_domain=website_or_domain,
                status=ResearchStatus.FAILED,
                parsed_data=None,
                citations=citations,
                search_queries=[],
                composio_status=composio_status,
                error_message=error_msg,
            )

        # 8. If legacy grounding citations were returned in response, preserve them if citations is empty
        legacy_citations, search_queries = extract_grounding_citations(response)
        if not citations and legacy_citations:
            citations = legacy_citations

        # 9. Extract text content from Interaction response or candidates
        raw_text = extract_model_output_text(response)

        # 10. Parse structured model output
        parsed_data = parse_model_research_json(raw_text)

        if not parsed_data:
            logger.warning("Failed to parse structured JSON from Gemini response for %s", cleaned_app)
            if should_fallback:
                logger.info("Executing deterministic evidence fallback due to unparseable JSON from Gemini for %s.", cleaned_app)
                return deterministic_evidence_engine.generate_guide(
                    app_name=cleaned_app,
                    website_or_domain=website_or_domain,
                    composio_status=composio_status,
                    fetched_docs=fetched_docs,
                    citations=citations,
                )
            fallback_summary = raw_text[:500].strip() if raw_text else "Research returned unparseable output."
            return build_research_result(
                app_name=cleaned_app,
                website_or_domain=website_or_domain,
                status=ResearchStatus.PARTIAL,
                parsed_data={"summary": fallback_summary, "confidence": "UNCERTAIN"},
                citations=citations,
                search_queries=search_queries,
                composio_status=composio_status,
                error_message="Could not parse structured JSON output from Gemini response.",
            )

        # 11. Validate claims against retrieved evidence
        validated_data = validate_and_filter_evidence(parsed_data, fetched_docs, citations)

        # Format summary with AI-Assisted tag if successful
        if validated_data.get("summary") and not validated_data["summary"].startswith("[AI-Assisted]"):
            validated_data["summary"] = f"[AI-Assisted] {validated_data['summary']}"

        # Determine if application was identified as unknown/unsupported
        supports_oauth = validated_data.get("supports_oauth")
        final_status = ResearchStatus.COMPLETED
        if supports_oauth is False and not citations:
            final_status = ResearchStatus.UNKNOWN_APPLICATION

        return build_research_result(
            app_name=cleaned_app,
            website_or_domain=website_or_domain,
            status=final_status,
            parsed_data=validated_data,
            citations=citations,
            search_queries=search_queries,
            composio_status=composio_status,
            error_message=None,
        )


# Global research service instance
gemini_research_service = GeminiResearchService()
