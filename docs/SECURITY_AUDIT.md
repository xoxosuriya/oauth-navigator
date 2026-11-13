# OAuth Navigator — Production Security Audit & Hardening Report

**Application:** OAuth Navigator (Full-Stack OAuth Architecture Explorer & Connection Manager)  
**Workspace:** `D:\Composio`  
**Frontend Deployment:** `https://oauthnavigator.vercel.app` (Vercel Free)  
**Backend Deployment:** `https://oauth-navigator-api.onrender.com` (Render Free)  
**Repository:** `https://github.com/xoxosuriya/oauth-navigator` (`main`)  
**Audit Date:** November 2026  
**Auditor / Security Reviewer:** Application Security & Integration Engineering  

---

## 1. Executive Summary & Security Architecture

OAuth Navigator is a hybrid developer portal and OAuth integration engine designed to investigate third-party OAuth 2.0 implementations, generate RFC-compliant implementation guides, and execute live Composio-managed OAuth connection handshakes (e.g., Slack, Gmail) and custom OAuth blueprints (e.g., Shopify).

### Core Architecture & Boundaries
```
+-----------------------------------------------------------------------------------------+
|                                    CLIENT TIER                                          |
|  React 18 + Vite SPA (Hosted on Vercel)                                                |
|  - Frame-accurate Neo-Brutalist UI                                                      |
|  - Secure Anonymous Session Token Holder (HttpOnly Cookie / X-Session-Token header)      |
|  - URL sanitization (Safe External Schemes) & OAuth Query Param Purging                |
+-----------------------------------------------------------------------------------------+
                                          │
                  HTTPS / CORS (Strict Whitelist + Credentials)
                                          ▼
+-----------------------------------------------------------------------------------------+
|                                    BACKEND TIER                                         |
|  FastAPI + Uvicorn ASGI (Hosted on Render)                                              |
|  - Security Middleware: HSTS, CSP, nosniff, DENY, Referrer-Policy, Permissions-Policy   |
|  - Request Body Ceiling (1MB max payload)                                               |
|  - HMAC-SHA256 Cryptographic Session Signing & Verification Engine                     |
|  - Multi-Tenant Isolation Enforcement: Caller session bound to Composio user_id         |
|  - Sliding-Window Rate Limiters (429 + Retry-After)                                      |
|  - DocFetcher SSRF Security Validator (DNS check, Private IP, Loopback, Cloud Metadata)|
|  - Path Traversal & Schema Sanitizers                                                   |
+-----------------------------------------------------------------------------------------+
                                          │
                  Server-to-Server HTTPS (Protected API Key)
                                          ▼
+-----------------------------------------------------------------------------------------+
|                                 THIRD-PARTY SERVICES                                    |
|  - Composio API v3.1 (https://backend.composio.dev) — Protected by COMPOSIO_API_KEY     |
|  - Google Gemini API (Structured OAuth Research & Synthesis)                           |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Threat Model & Trust Boundaries

| Boundary | Components Involved | Primary Threats | Mitigations |
| :--- | :--- | :--- | :--- |
| **B1: Client to Backend** | Browser ↔ FastAPI | Session impersonation, Account enumeration, CSRF, XSS, Replay attacks, Parameter tampering | HMAC-SHA256 session signature verification, SameSite=None Secure HttpOnly cookies, CSP, Strict Input Bounds |
| **B2: Backend to External Docs** | Backend DocFetcher ↔ Third-Party Web | SSRF, Localhost probe, Cloud metadata exfiltration (AWS/GCP/Azure), DNS rebinding | `SSRFSecurityValidator` with pre-flight DNS resolution, IP range filtering (RFC 1918, RFC 3927, RFC 4193, 169.254.169.254), redirect limits |
| **B3: Backend to Composio** | Backend ↔ Composio API v3.1 | Secret leakage, Cross-tenant data leakage, Duplicate connection collisions | Secret redaction regexes, Server-only `COMPOSIO_API_KEY`, Per-session unique aliases, Multi-tenant user_id validation |
| **B4: Third-Party Redirects** | Browser ↔ Identity Providers (Google, Slack) | Open redirects, Phishing via dangerous schemes (`javascript:`, `data:`) | Scheme whitelisting (`http://`, `https://`), Strict URL parsing via `urllib.parse` |

---

## 3. Pre-Remediation Findings & Vulnerability Assessment

### SEC-01 (High): Insecure Client-Side User Identity & Cross-Tenant Account Enumeration
- **Vulnerability:** The `/api/v1/connections` and `/api/v1/connections/{account_id}` endpoints relied on client-supplied `user_id` query parameters and headers (`X-User-ID`). A malicious user could supply an arbitrary victim's `user_id` (e.g. `usr_victim123`) to list their connected accounts or query connection status.
- **Impact:** Broken Object Level Authorization (BOLA / IDOR) across tenant boundaries.
- **Remediation:** 
  1. Implemented server-issued, cryptographically signed anonymous session tokens (`anon_<urlsafe_rand>.<hmac_sha256>`).
  2. Implemented `get_authenticated_session` dependency that extracts and validates the token from either `oauth_session` cookie or `X-Session-Token` header.
  3. Any client-provided `user_id` that does not match the authenticated session is rejected or overridden with the verified session identity.

### SEC-02 (Medium): Denial of Service via Endpoint Flooding on AI & Connection Handshakes
- **Vulnerability:** Heavy endpoints like `/api/v1/investigate` (which calls Google Gemini LLM and runs web fetches), `/api/v1/connections/{slug}/start`, and `/api/v1/guides/share` had no dedicated rate limits. An attacker could rapidly exhaust Gemini free quota limits or spam Composio auth link generation.
- **Impact:** Service denial for legitimate users due to third-party upstream rate limits / quota exhaustion.
- **Remediation:** 
  1. Built sliding-window memory rate limiters (`investigate_rate_limiter`, `share_rate_limiter`, `connection_rate_limiter`, `toolkit_rate_limiter`).
  2. Implemented HTTP 429 status response with RFC-compliant `Retry-After` seconds header and structured JSON error response.

### SEC-03 (Medium): Path Traversal & Unbounded String Inputs
- **Vulnerability:** Endpoints accepting path parameters (`/apps/{id_or_slug}`, `/guides/share/{share_id}`, `/composio/toolkit/{slug}`) lacked explicit directory traversal guards, potentially allowing dot-dot-slash sequences to pass to internal stores or error logs. Additionally, input payloads lacked explicit length ceilings.
- **Impact:** Potential internal file probing or log injection.
- **Remediation:**
  1. Added path sanitization rejecting `..`, `\0`, `\`, and leading `/` with HTTP 400.
  2. Added Pydantic field constraints (`min_length=1`, `max_length=100`, regex patterns `^[a-zA-Z0-9_\-\.\s\(\)\/]+$`) on all request models.

### SEC-04 (Medium): Unsanitized External Callback URLs (Open Redirect Potential)
- **Vulnerability:** `ConnectionStartRequest.callback_url` was accepted without protocol validation, theoretically allowing an attacker to submit `javascript:alert(1)` or `data:text/html` which might be reflected into browser location redirects.
- **Impact:** Client-side XSS or open redirect vulnerability.
- **Remediation:**
  1. Added `@field_validator("callback_url")` requiring `http` or `https` schemes, non-empty hostnames, and rejecting control characters (`\r`, `\n`).
  2. Added frontend client-side validation `isSafeExternalUrl()` before initiating any `window.open` navigation.

### SEC-05 (Low): Missing Production HTTP Security Headers & Large Payload Handling
- **Vulnerability:** The API and frontend lacked essential defensive headers (HSTS, CSP, X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy, Permissions-Policy). Additionally, there was no request body payload size guard.
- **Impact:** Susceptibility to clickjacking, MIME-sniffing, and memory exhaustion via multi-megabyte payloads.
- **Remediation:**
  1. Added security headers middleware to FastAPI in `backend/app/main.py`.
  2. Added 1MB maximum payload check in ASGI middleware returning HTTP 413 `Payload Too Large`.
  3. Added comprehensive security headers in `frontend/vercel.json`.

### SEC-06 (Low): OAuth State & Callback Parameter Leakage in Browser History
- **Vulnerability:** When returning from an OAuth callback (e.g. `?status=success&account_id=ca_123`), sensitive identifiers remain visible in the browser address bar and history.
- **Impact:** Shoulder surfing or token leakage via referral headers or history inspection.
- **Remediation:**
  1. Implemented `window.history.replaceState` in `OAuthWorkspace.tsx` upon receiving connection callback parameters, stripping them immediately after processing.

---

## 4. Technical Remediations Implemented

### A. HMAC-SHA256 Anonymous Session Engine (`backend/app/core/session.py`)
```python
# Format: anon_<24-char-urlsafe-entropy>.<hmac-sha256-signature>
def generate_signed_session_token(user_id: Optional[str] = None) -> str:
    user_id = user_id or f"anon_{secrets.token_urlsafe(18)}"
    sig = hmac.new(_get_signing_key(), user_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{user_id}.{sig}"

def verify_session_token(token: Optional[str]) -> Optional[str]:
    # Validates structure, recomputes signature, and checks via hmac.compare_digest
```
- Issues `oauth_session` cookie with `HttpOnly=True`, `Secure=True`, `SameSite="None"`.
- Returns `X-Session-Token` for non-cookie environments.
- Protects multi-tenant Composio connected account queries: a user can only inspect connected accounts matching their verified session identity.

### B. Rate Limiting System (`backend/app/core/rate_limit.py`)
| Endpoint | Minute Limit | Daily Limit | Action on Breach |
| :--- | :--- | :--- | :--- |
| `POST /api/v1/investigate` | 10 req / min | 60 req / day | HTTP 429 + `Retry-After` |
| `POST /api/v1/guides/share` | 15 req / min | 100 req / day | HTTP 429 + `Retry-After` |
| `POST /api/v1/connections/{slug}/start` | 10 req / min | 50 req / day | HTTP 429 + `Retry-After` |
| `GET /api/v1/composio/toolkit/{slug}` | 30 req / min | 300 req / day | HTTP 429 + `Retry-After` |

### C. Server-Side SSRF Protection (`DocFetcher`)
- Validates every URL before socket opening.
- Prohibits:
  - Loopback (`127.0.0.0/8`, `::1`)
  - Private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  - Link-local (`169.254.0.0/16`, `fe80::/10`)
  - Cloud Metadata endpoints (`169.254.169.254`, `100.100.100.200`, `fd00:ec2::254`)
- Validates intermediate IP on each redirect hop (max 3 redirects).

---

## 5. Verification & Automated Test Results

### Backend Test Suite Execution
```
$ & "D:\Composio\.venv\Scripts\python.exe" -m unittest discover -s backend\tests -p "test_*.py"
Ran 159 tests in 16.841s
OK
```

### Dedicated Security Test Suite (`backend/tests/test_security_audit.py`)
| Test ID | Objective | Status |
| :--- | :--- | :--- |
| `test_sec_a01_secrets_redacted_in_logs_and_errors` | Verifies `ak_`, `xoxb-`, `AIza` secrets are redacted from responses and logs | PASS |
| `test_sec_b01_path_traversal_rejected_in_guides_and_toolkits` | Verifies `..` traversal sequences return HTTP 400 / 404 | PASS |
| `test_sec_b02_invalid_callback_url_scheme_rejected` | Verifies `javascript:` / `data:` callback URLs return HTTP 422 | PASS |
| `test_sec_b03_request_body_size_limit_enforced` | Verifies payloads > 1MB return HTTP 413 Payload Too Large | PASS |
| `test_sec_c01_ssrf_validator_blocks_private_and_metadata_ips` | Verifies SSRF blocks 127.0.0.1, 10.0.0.1, 169.254.169.254 | PASS |
| `test_sec_c02_ssrf_validator_blocks_non_standard_ports` | Verifies ports other than 80 and 443 are blocked | PASS |
| `test_sec_d01_session_token_generation_and_tamper_detection` | Verifies HMAC signature generation and tamper rejection | PASS |
| `test_sec_d02_session_endpoint_sets_secure_cookie` | Verifies `/api/v1/session` sets HttpOnly, Secure, SameSite=None | PASS |
| `test_sec_e01_cross_tenant_connection_isolation` | Verifies User B cannot view User A's connected account | PASS |
| `test_sec_e02_spoofed_user_id_rejected_or_overridden` | Verifies caller cannot claim another user's identity | PASS |
| `test_sec_f01_investigate_rate_limit_429_with_retry_after` | Verifies 429 response and `Retry-After` header when rate exceeded | PASS |
| `test_sec_f02_connection_start_rate_limit` | Verifies connection start rate limiter works as expected | PASS |
| `test_sec_g01_security_headers_present_in_responses` | Verifies HSTS, nosniff, DENY, and CSP headers on all responses | PASS |

---

## 6. Residual Architectural Limitations & Risks

1. **Render Free Tier Ephemeral Storage:**
   - Render's free web service runs on an ephemeral container that resets on redeploy or after 15 minutes of inactivity.
   - Saved custom guides and share links stored in the local JSON cache (`guides_cache.json`) reset to baseline built-in guides upon cold restart.
   - *Production Recommendation for V2:* Mount a PostgreSQL database or Redis instance for permanent guide persistence.
2. **Anonymous Sessions vs. Registered Accounts:**
   - Anonymous session tokens prevent unauthorized cross-tenant eavesdropping and tampering within a browser session. However, if a user clears their browser cookies and storage, their session ID changes and previously established connected accounts will no longer be visible to them in the UI.
   - *Design Decision:* This was an intentional architecture choice to maintain a zero-friction developer experience without forcing email verification or password registration.
3. **Upstream Gemini Quota Exhaustion:**
   - Gemini 2.5 Flash free-tier quotas are subject to global rate limits (15 RPM / 1500 RPD).
   - While client-side rate limiting prevents single-user abuse, high concurrent public traffic could still encounter upstream 429s. The application cleanly falls back to cached knowledge without crashing.

---

## 7. Intentional Architectural Non-Goals

- **Full User Authentication (Passwords / Magic Links / Passkeys):** Deliberately omitted. OAuth Navigator is designed as an interactive exploratory workbench and integration generator. Adding authentication gates would create significant friction and require secure credential storage, recovery flows, and compliance overhead outside take-home scope.
- **Direct Access Token Storage:** The backend never stores or proxies OAuth access tokens or refresh tokens. All token lifecycle, refresh, and revocation operations are delegated strictly to Composio's encrypted credential vault.

---

## 8. Pre-Deployment Checklist

- [x] All 159 tests in test suite pass (`OK`).
- [x] Zero hardcoded secrets, test tokens, or private keys present in git staging.
- [x] Secret scanning executed across all modified files.
- [x] Frontend builds with zero TypeScript and Vite warnings (`dist/assets/index-PjTINsoZ.js`).
- [x] Security headers configured on both FastAPI backend and Vercel edge configuration.
- [x] SameSite=None, Secure, HttpOnly cookie configuration active for cross-origin production API calls.
- [x] All production URLs, free tier configurations, and existing UI aesthetics preserved.
