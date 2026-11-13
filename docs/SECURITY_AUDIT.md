# OAuth Navigator — Production Security Audit & Hardening Report (Correction Pass)

**Application:** OAuth Navigator (Full-Stack OAuth Architecture Explorer & Connection Manager)  
**Workspace:** `D:\Composio`  
**Frontend Deployment:** `https://oauthnavigator.vercel.app` (Vercel Free)  
**Backend Deployment:** `https://oauth-navigator-api.onrender.com` (Render Free)  
**Repository:** `https://github.com/xoxosuriya/oauth-navigator` (`main`)  
**Audit Pass:** Security Audit Correction Pass (Milestone 4.1)  
**Auditor / Security Reviewer:** Application Security & Integration Engineering  

---

## 1. Executive Summary & Security Architecture

OAuth Navigator is a developer portal and OAuth integration engine designed to investigate third-party OAuth 2.0 implementations, generate RFC-compliant implementation guides, and execute live Composio-managed OAuth connection handshakes (e.g., Slack, Gmail) and custom OAuth blueprints (e.g., Shopify).

Following a rigorous security audit correction pass against commit `1489c34`, all identified security gaps in anonymous session claiming, body-size enforcement, SSRF connection pinning, rate limiting, and client token storage have been remediated, verified locally across 171 automated tests, and validated in production.

### Core Architecture & Boundaries
```
+-----------------------------------------------------------------------------------------+
|                                    CLIENT TIER                                          |
|  React 18 + Vite SPA (Hosted on Vercel)                                                |
|  - Frame-accurate Neo-Brutalist UI                                                      |
|  - Zero token storage in localStorage (HttpOnly Cookie primary transport)               |
|  - Safe External Scheme Validation & OAuth Query Parameter Purging                     |
+-----------------------------------------------------------------------------------------+
                                          │
                  HTTPS / CORS (Strict Whitelist + Credentials: Include)
                                          ▼
+-----------------------------------------------------------------------------------------+
|                                    BACKEND TIER                                         |
|  FastAPI + Uvicorn ASGI (Hosted on Render)                                              |
|  - Security Middleware: HSTS, CSP, nosniff, DENY, Referrer-Policy, Permissions-Policy   |
|  - Streaming ASGI Request Body Limit (1 MB max; chunked & content-length enforcement)   |
|  - Server-Generated HMAC-SHA256 Anonymous Session Engine (HttpOnly, Secure, SameSite)   |
|  - Strict Multi-Tenant Isolation: Caller session strictly bound to Composio user_id     |
|  - Process-Local Sliding-Window Rate Limiters (429 + Retry-After)                       |
|  - DocFetcher SSRF Safe Transport: Socket IP Pinning, DNS Rebinding & Redirect Defense  |
|  - Path Traversal & Schema Sanitizers                                                   |
+-----------------------------------------------------------------------------------------+
                                          │
                  Server-to-Server HTTPS (Protected API Key)
                                          ▼
+-----------------------------------------------------------------------------------------+
|                                 THIRD-PARTY SERVICES                                    |
|  - Composio API v3.1 (https://backend.composio.dev) — Server-side COMPOSIO_API_KEY      |
|  - Google Gemini API (Structured OAuth Research & Synthesis)                           |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Threat Model & Trust Boundaries

| Boundary | Components Involved | Primary Threats | Mitigations |
| :--- | :--- | :--- | :--- |
| **B1: Client to Backend** | Browser ↔ FastAPI | Session impersonation, Account enumeration, BOLA/IDOR, CSRF, XSS, Parameter tampering | Server-only anonymous session minting, HMAC-SHA256 signature verification, SameSite=None Secure HttpOnly cookies, CSP, Strict Input Bounds |
| **B2: Backend to External Docs** | Backend DocFetcher ↔ Third-Party Web | SSRF, Localhost probe, Cloud metadata exfiltration (AWS/GCP/Azure), DNS rebinding (TOCTOU) | `SSRFSafeNetworkBackend` with pre-flight DNS resolution, IP range filtering, socket IP pinning, and per-hop redirect re-validation |
| **B3: Backend to Composio** | Backend ↔ Composio API v3.1 | Secret leakage, Cross-tenant data leakage, Duplicate connection collisions | Secret redaction regexes, Server-only `COMPOSIO_API_KEY`, Per-session unique aliases, Multi-tenant user_id validation |
| **B4: Third-Party Redirects** | Browser ↔ Identity Providers (Google, Slack) | Open redirects, Phishing via dangerous schemes (`javascript:`, `data:`) | Scheme whitelisting (`http://`, `https://`), Strict URL parsing via `urllib.parse` |

---

## 3. Vulnerability Findings & Corrections

### SEC-01 (High): Insecure Anonymous Session Identity Claiming & BOLA / IDOR
- **Original Gap in Commit `1489c34`:**
  - `/session?legacy_id=...` allowed callers to pass an arbitrary identifier which was then signed.
  - `/connections/{toolkit_slug}/start` contained fallback logic adopting `payload.user_id` whenever `session_user_id.startswith("anon_")`.
  - Frontend stored tokens in `localStorage` and sent client-generated `user_id` values on connection requests.
- **Correction Implemented:**
  1. Only the backend generates anonymous identities (`anon_{secrets.token_urlsafe(18)}`). Removed `legacy_id` parameter from `/api/v1/session`.
  2. Removed `anon_` adoption fallback in `start_connection`. Connections are strictly bound to `session_user_id`. Any client-supplied `user_id` is ignored and logged.
  3. `get_connection_status` and `list_user_connections` strictly use `session_user_id`. Query parameters or `X-User-ID` headers attempting to access another user's account are ignored.
  4. Returns **HTTP 404 Not Found** when querying an account ID owned by another session (prevents account enumeration).
  5. Frontend removes all token storage from `localStorage` and sends requests with `credentials: "include"`.

### SEC-02 (Medium): Request-Body Size Enforcement Bypass on Chunked / Streaming Requests
- **Original Gap:** The previous middleware inspected only the `Content-Length` header. Requests with missing, misleading, or chunked transfer encoding (`Transfer-Encoding: chunked`) bypassed the size ceiling.
- **Correction Implemented:**
  1. Built pure ASGI `BodySizeLimitMiddleware` in `backend/app/main.py`.
  2. Intercepts incoming ASGI `http.request` stream messages and counts cumulative body bytes.
  3. Raises `PayloadTooLargeError(BaseException)` immediately upon exceeding `MAX_REQUEST_BODY_BYTES` (1 MB / 1,048,576 bytes) without buffering unlimited payloads in memory.
  4. Subclasses `BaseException` to bypass Starlette's internal `except Exception:` JSON parsing traps, guaranteeing a clean HTTP 413 response.

### SEC-03 (Medium): SSRF Time-of-Check to Time-of-Use (TOCTOU) DNS Rebinding Risk
- **Original Gap:** DNS resolution occurred before making HTTP requests, but the underlying HTTP client (`httpx` / `httpcore`) resolved the hostname again when opening the network socket, leaving a window for DNS rebinding attacks.
- **Correction Implemented:**
  1. Implemented `SSRFSafeNetworkBackend(AutoBackend)` in `backend/app/services/doc_fetcher.py`.
  2. In `connect_tcp()`, resolves the target hostname and checks all resolved IP answers. If ANY resolved IP is prohibited (loopback, RFC 1918 private, link-local, multicast, cloud metadata `169.254.169.254`, `100.100.100.200`, `fd00:ec2::254`, reserved, CGNAT), or if mixed public/private answers exist, it raises `ConnectError`.
  3. Pins the TCP socket connection directly to the validated IP literal (`super().connect_tcp(validated_ip, port)`), guaranteeing that the OS socket layer cannot re-resolve the domain.
  4. Preserves TLS SNI and certificate verification through `httpcore`'s `start_tls(server_hostname=host)`.
  5. Re-validates every redirect hop before following.

### SEC-04 (Low): In-Memory Rate Limiter Resource Bounds & IP Spoofing
- **Original Gap:** Unbounded dictionaries in memory could grow indefinitely under high unique IP volume; unapproved `X-Forwarded-For` headers could be spoofed.
- **Correction Implemented:**
  1. Added dictionary pruning in `ResearchRateLimiter` and `EndpointRateLimiter` (`_cleanup_dictionary`), capping tracking maps at 5,000 entries.
  2. `get_client_ip()` strictly uses `direct_ip` unless the direct connection arrives from an explicitly trusted reverse proxy listed in `settings.TRUSTED_PROXY_IPS`.
  3. Explicitly documented that rate limiting is **process-local** in memory and resets upon container restart (not distributed).

### SEC-05 (Low): Production API Documentation Exposure Policy
- **Original Gap:** Interactive Swagger UI was exposed unconditionally in production.
- **Correction Implemented:**
  1. Configured `docs_enabled = (not is_production) or enable_production_docs`.
  2. When `ENV=production` and `ENABLE_PRODUCTION_DOCS` is unset/false, `/docs`, `/redoc`, and `/openapi.json` are disabled (`None`).
  3. Local development documentation remains fully accessible. Health check and public API routes are unaffected.

---

## 4. Verification Status: Categorized by Evidence Tier

### A. Implemented and Automated Unit/Integration Tested Controls (171 Tests)
These controls are executed and validated locally via `unittest` against the live ASGI app:
- **Session Claiming Defense:** Verified that fresh anonymous sessions and `/session?legacy_id=victim` cannot claim a chosen identity (`test_sec_req_a`, `test_sec_req_b`).
- **Header Forgery Rejection:** Verified that forged `X-User-ID` and query `user_id` cannot list or retrieve another user's accounts (`test_sec_req_c`, `test_sec_req_d`).
- **Multi-Tenant Account Isolation:** Verified that User A can view their own connections, while User B receives HTTP 404 for User A's connections (`test_sec_req_e`, `test_sec_req_f`, `test_sec_e01`).
- **Provider Isolation:** Verified that Gmail and Slack connection queries remain strictly filtered by `toolkit_slug` (`test_sec_req_g`).
- **Token Leakage Prevention:** Verified that no tokens are stored in `localStorage` and `X-Session-Token` headers are omitted from responses (`test_sec_req_h`).
- **Streaming Body Size Limit:** Verified that chunked streaming requests without `Content-Length` exceeding 1 MB are immediately terminated with HTTP 413 (`test_sec_req_i`).
- **SSRF Network Boundary:** Verified that `SSRFSafeNetworkBackend` rejects cloud metadata, loopback, non-standard ports, and mixed public/private DNS answers (`test_sec_req_j`).
- **Forwarded IP Spoofing Defense:** Verified that unapproved `X-Forwarded-For` headers from untrusted direct IPs are ignored (`test_sec_req_k`).
- **Path Traversal & Scheme Rejection:** Verified that traversal patterns return 400/404 and dangerous schemes (`javascript:`, `data:`) return 422 (`test_sec_b01`, `test_sec_b02`).

### B. Production Behavior Verified Live Against Deployed Environments
- **Frontend Deployment (Vercel):** `https://oauthnavigator.vercel.app` loads with HTTP 200, serving the updated bundle without localStorage token storage.
- **Security Headers (Live):** Verified live Vercel response includes:
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Content-Security-Policy: default-src 'self'; ...`
- **CORS & Credentials:** Verified `credentials: "include"` cross-origin cookie policy between Vercel origin and Render backend.

---

## 5. Residual Architectural Limitations & Risks

1. **Render Free Tier Ephemeral Container Storage:**
   - Render's free web tier spins down after 15 minutes of inactivity and resets its ephemeral container filesystem on restart or redeployment.
   - User-generated guide share links stored in the local file cache are ephemeral.
   - *V2 Recommendation:* Connect an external database (PostgreSQL / Supabase) or Redis for permanent multi-process persistence.
2. **Anonymous Sessions vs. Persistent Accounts:**
   - Because user accounts are anonymous session tokens stored in HttpOnly browser cookies, clearing browser cookies resets the user's session ID. Any previously established connected accounts in Composio associated with that session will no longer be visible to that browser.
   - *Design Decision:* Intentional trade-off to provide zero-friction developer exploration without requiring username/password registration.
3. **Process-Local Rate Limiting:**
   - Rate limit counters reside in-memory within the Uvicorn worker process. If multiple workers are deployed or if the container restarts, rate limit counters reset.
   - *V2 Recommendation:* Back rate limiters with Redis for distributed multi-worker enforcement.
4. **Third-Party Upstream Quota Limits:**
   - Google Gemini free-tier quotas and Composio API rate limits are enforced by upstream providers. If global limits are exceeded, the system gracefully returns cached research or fallback blueprints.

---

## 6. Pre-Deployment Verification Summary

- [x] All 171 tests in backend test suite pass (`OK`).
- [x] Zero hardcoded secrets, test keys, or credentials present in git working tree.
- [x] Secret scanning executed across all staged files.
- [x] Frontend builds with zero TypeScript and Vite warnings (`dist/assets/index-D_9nvpw6.js`).
- [x] Cookie transport active (`HttpOnly`, `Secure`, `SameSite=None` for cross-site Vercel-to-Render).
- [x] All existing working workflows (Gmail, Slack, Shopify) preserved.
