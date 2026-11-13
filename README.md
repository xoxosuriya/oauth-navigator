# OAuth Navigator

> **OAuth Readiness & Integration Intelligence for AI-Agent Developers**  
> A modular full-stack application that transforms third-party OAuth provider specifications and Composio tool configurations into actionable, evidence-backed integration roadmaps with zero credentials stored.

---

## 1. Product Overview & Value Proposition

Connecting autonomous AI agents to third-party tools (such as Slack, GitHub, Gmail, Shopify, Notion, and Linear) requires answering key authentication questions before writing code:
- **Pathway Selection:** Does this provider require custom developer registration, or does Composio offer a managed, pre-registered OAuth app?
- **Review & Security Gates:** Does the integration trigger mandatory partner review, CASA Tier 2 lab assessments, Google OAuth Brand Verification, or public app store listing requirements?
- **Effort vs SLA:** How much active engineering effort (minutes) is estimated compared to the provider's asynchronous review waiting SLA (days)?
- **Responsibility Boundaries:** Which setup steps can an automated script or agent perform, and which steps mandate human intervention?

**OAuth Navigator** addresses this with:
1. **Pre-Audited Guidance for Seed Apps:** Structured integration roadmaps for foundational developer tools (Slack, Shopify, Gmail/Google Workspace).
2. **Live Investigation for Unfamiliar Apps:** Real-time documentation and metadata retrieval that extracts integration requirements for unseeded tools (e.g. Linear, Notion) on demand.
3. **Evidence-First Epistemic Honesty:** Requirements, scope tiers, review gates, and setup steps link directly to official provider documentation. Unverified or undocumented fields are explicitly presented as `null` / `"Unverified"` rather than inferred.
4. **Persistent Shareable Guide Links:** Save and share integration roadmaps across team members via persistent guide links.

---

## 2. Architecture & Scope Boundaries

OAuth Navigator is built as a decoupled, modular full-stack application:

```
┌────────────────────────────────────────────────────────┐
│                   OAuth Navigator                      │
│      React 18 + TypeScript + Vite + Tailwind CSS       │
│           (Preserved Framer Design System)             │
│        Production: https://oauthnavigator.vercel.app    │
│           Local Dev: http://127.0.0.1:3000             │
└──────────────────────────┬─────────────────────────────┘
                           │ 1. First-Party API Proxy (/api/v1)
                           │    HttpOnly Secure SameSite Cookies
                           ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Backend                      │
│            Python 3.12 + Pydantic v2 + Uvicorn         │
│     Production: https://oauth-navigator-api.onrender.com│
│           Local Dev: http://127.0.0.1:8000             │
├──────────────────────────┬─────────────────────────────┤
│   Deterministic Evidence │      Composio Integration   │
│   & Documentation Engine │     Toolkit & OAuth Catalog │
├──────────────────────────┼─────────────────────────────┤
│ Session Integrity (HMAC) │ Real OAuth Connection Engine│
│ Multi-Tenant Isolation   │ Lifecycle State Machine     │
└──────────────────────────┴─────────────────────────────┘
```

- **Frontend (`/frontend`):** Built with React 18, TypeScript, and Vite. A desktop-first reconstruction preserving the original Framer design system (typography: `Unbounded` display headers, `Poppins` body, custom neo-brutalist borders, tactile pill badges, procedural SVGs, and interactive architecture diagrams). Configured with a first-party reverse proxy via Vercel rewrites (`/api/:path*`) to preserve session cookies in Incognito mode.
- **Backend (`/backend`):** FastAPI service utilizing Pydantic v2 schemas, strict type-checking, in-memory repository with thread safety, cryptographic session integrity (HMAC-SHA256), and modular API routes (`/healthz`, `/session`, `/apps`, `/investigate`, `/research`, `/composio`, `/guides`, `/connections`).
- **Composio Integration:** Direct integration with Composio's API v3.1 to inspect toolkit capabilities, authentication schemes, pre-registered managed credentials, and generate live OAuth connect links.

### Comprehensive Implemented & Verified API Endpoints

| Category | Endpoint | HTTP Method | Description |
|---|---|---|---|
| **System** | `/healthz` | `GET` | Root system health and uptime status. |
| **System** | `/api/v1/health` | `GET` | API v1 service health status and timestamp. |
| **Session** | `/api/v1/session` | `GET` | Server-issued, cryptographically signed anonymous session token (`anon_<token>`) via HttpOnly cookie. |
| **Guides** | `/api/v1/apps` | `GET` | Lists curated and investigated OAuth guides with search and difficulty filters. |
| **Guides** | `/api/v1/apps/{id_or_slug}` | `GET` | Retrieves full guide by identifier, slug, or display name (e.g. `gmail`, `slack`, `shopify`). |
| **Research** | `/api/v1/investigate` | `POST` | Live documentation and metadata extraction for unfamiliar applications (e.g. Linear, Notion). |
| **Research** | `/api/v1/research` | `POST` | Deep technical RFC and endpoint research pipeline. |
| **Composio** | `/api/v1/composio/toolkit/{slug}` | `GET` | Live Composio toolkit catalog metadata inspection. |
| **Sharing** | `/api/v1/guides/share` | `POST` | Generates a permanent shareable permalink for an existing guide. |
| **Sharing** | `/api/v1/guides/share/{share_id}` | `GET` | Resolves and retrieves a shared guide by permalink ID. |
| **Connections** | `/api/v1/connections/{slug}/start` | `POST` | Initializes a live Composio Connect Link bound to authenticated session identity. |
| **Connections** | `/api/v1/connections/{id}` | `GET` | Real-time connection status query with strict multi-tenant ownership validation. |
| **Connections** | `/api/v1/connections` | `GET` | Lists all connected accounts owned by the authenticated session. |
| **Connections** | `/api/v1/connections/{id}` | `DELETE` | Disconnects and deletes a connected account with ownership verification. |
| **Connections** | `/api/v1/connections/shopify/status` | `GET` | Returns Shopify Custom OAuth configuration status and setup instructions. |

### Clarification of Responsibilities (OAuth Navigator vs. Downstream Runtime)
- **What OAuth Navigator does:**
  - Evaluates authentication readiness and classifies pathways (`COMPOSIO MANAGED AVAILABLE` vs `COMPOSIO CUSTOM ONLY`).
  - Analyzes review gates, SLAs, CASA tiers, and permission scopes from provider documentation.
  - Defines the operational boundary between human developers and downstream agent automation.
  - Manages the complete, live OAuth connection journey via Composio API v3.1: initiates Connect Links, opens dedicated authorization tabs without popup blocking or main window redirection, validates callbacks via secure postMessage + polling fallback, verifies active connection status, tests active connectivity, and safely disconnects sessions.
  - Enforces multi-tenant session isolation with server-issued, cryptographically signed HttpOnly cookies.
  - Generates code snippets for Composio SDK session initialization (`session create managed`, `session create custom`) and Auth Config JSON payloads.
  - Persists and renders shareable integration guides.
- **What OAuth Navigator does NOT do (Delegated to Downstream Agent / Composio Runtime):**
  - OAuth Navigator is **not** an OAuth authorization server or runtime token broker.
  - It does **not** store raw access tokens, client secrets, or refresh tokens in local keyrings (tokens are managed server-side by Composio).
  - Runtime tool execution and downstream token injection are handled by downstream agent runtimes or the Composio SDK during action execution.

---

## 3. Evidence Engine & Analysis Methodology

### Deterministic Documentation Retrieval (Active Mode)
The active research engine is a **deterministic documentation and metadata retrieval pipeline**, **NOT** an autonomous trial-and-error agent:
- When an application is investigated, the backend executes targeted lookups against the live Composio toolkit catalog (`/composio/toolkit/{slug}`) and official provider documentation.
- Extracted documentation is parsed using deterministic rules, regex extractors, and schema normalizers.
- **Design Rationale:** Using deterministic parsing significantly reduces unsupported or fabricated claims. However, because external provider documentation may change, update, or reorganize over time, fields that cannot be verified against retrieved text are set to `null` and displayed as `"Unverified"`.

### Optional Gemini Synthesis Mode (Disabled by Default)
The backend architecture includes an optional LLM synthesis engine powered by Google Gemini (`GEMINI_MODEL=gemini-3.8-flash`).
- **Configuration:** `GEMINI_RESEARCH_ENABLED: bool = false` in `backend/app/core/config.py`.
- **Status:** Intentionally kept `false` by default to ensure reproducible findings without ungrounded LLM inference.
- **Enabling:** To enable Gemini mode, set `GEMINI_RESEARCH_ENABLED=true` and provide a valid `GEMINI_API_KEY` in `backend/.env`.

---

## 4. Automation Capabilities vs. Required Human Actions

OAuth Navigator explicitly delineates what software automation can perform versus operations requiring human authorization:

| Category | Downstream Automation / Composio SDK | Mandatory Human Action |
|---|---|---|
| **Identity & Authentication** | • Automating OAuth 2.0 authorization code exchange at runtime.<br>• Managing token refresh cycles in client libraries.<br>• Initializing Composio SDK client sessions with generated configs. | • Logging into provider developer portals (Google Cloud Console, Slack API, Shopify Partners).<br>• Approving one-time OAuth consent screen in a browser. |
| **Configuration & Code** | • Generating Composio session initialization code (`session create managed / custom`).<br>• Drafting Slack App Manifests (YAML/JSON) with exact scopes.<br>• Generating Composio Auth Config definition payloads. | • Copying Client ID and Client Secret into developer dashboards (if custom OAuth is chosen).<br>• Creating new projects in provider developer consoles. |
| **Verification & Compliance** | • Validating requested scopes against specific agent tool actions.<br>• Inspecting API responses for compliance gates. | • Verifying domain ownership via Google Search Console (DNS TXT record).<br>• Submitting credit cards or billing details.<br>• Submitting CASA Tier 2 security questionnaires and recording OAuth demo videos. |

---

## 5. Local Share Links vs. Publicly Accessible Share Links

### Local Share Links (Development Mode)
- When running locally, clicking **"Share guide"** dispatches `POST /api/v1/guides/share`.
- The backend generates a local link:
  - Local Link: `http://localhost:3000/guide/:guideId`
  - Local Workspace URL: `http://127.0.0.1:3000/workspace?share=:guideId`
- These URLs resolve against the local FastAPI backend on `http://127.0.0.1:8000/api/v1/guides/share/:guideId`. They are functional on the host machine but are **not reachable across the public internet**.

### Persistence Architecture: Committed Seed Guides vs. Dynamically Generated Guides
OAuth Navigator strictly distinguishes between two classes of guides:
1. **Committed Seed Guides (`seed_guides.json`):**
   - Pre-audited guides (Slack, Shopify, Gmail/Google Workspace) are committed directly to the repository under `backend/app/data/seed_guides.json`.
   - These guides are loaded on startup and **permanently survive** all server restarts, container rebuilds, and redeployments across all hosting environments (Local, Docker, Render Free).
2. **Dynamically Generated Guides & Runtime Share Links (`guides_store.json`):**
   - Created at runtime when an unfamiliar application is investigated (`POST /api/v1/investigate`) or shared (`POST /api/v1/guides/share`).
   - Stored in-memory and serialized atomically to `backend/app/data/guides_store.json`.
   - **Render Free Persistence Limitation:** On Render's Free tier, container storage is ephemeral. When the service spins down after 15 minutes of inactivity, restarts, or redeploys, the local container filesystem is wiped back to the clean git commit. Consequently, dynamically generated guides and runtime shareable permalinks **do NOT persist across restarts on Render Free**. They persist only during the active container lifecycle. Persistent disk storage on Render requires a paid plan ($7/mo Starter + $0.25/GB disk), which is intentionally avoided to maintain the 100% free hosting constraint.

### Publicly Accessible Share Links (Production Deployment)
To support public sharing across external users:
1. **Backend Configuration (`backend/.env`):**
   ```env
   FRONTEND_BASE_URL=https://oauth-navigator.yourdomain.com
   ALLOWED_ORIGINS=https://oauth-navigator.yourdomain.com
   HOST=0.0.0.0
   PORT=8000
   ```
2. **Frontend Configuration (`frontend/.env`):**
   ```env
   VITE_OAUTH_API_BASE_URL=https://api.oauth-navigator.yourdomain.com/api/v1
   ```
3. **CORS Security:**
   - The backend enforces explicit origin validation (`ALLOWED_ORIGINS`).
   - Wildcards (`*`) are disallowed by design to prevent cross-origin credential leaking.

---

## 6. Clean Machine Setup Instructions

### Backend Setup (FastAPI)

1. **Navigate to the backend directory:**
   ```powershell
   cd backend
   ```

2. **Create a virtual environment:**
   ```powershell
   python -m venv .venv
   ```

3. **Activate virtual environment:**
   ```powershell
   # Standard Windows PowerShell:
   .\.venv\Scripts\Activate.ps1

   # On macOS / Linux:
   # source .venv/bin/activate
   ```
   *Alternative:* If Windows PowerShell execution policy prevents running scripts (`PSSecurityException`), run commands directly with the virtual environment interpreter:
   ```powershell
   & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   & .\.venv\Scripts\python.exe run.py
   ```

4. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Initialize environment file from example:**
   ```powershell
   Copy-Item .env.example .env
   ```
   *(The default `.env.example` runs with the deterministic evidence engine enabled and requires 0 API keys for seed app inspection).*

6. **Start the backend server:**
   ```powershell
   python run.py
   ```

7. **Verify health endpoint:**
   ```powershell
   curl http://127.0.0.1:8000/api/v1/health
   # Expected output: {"status": "healthy", "service": "oauth-navigator-backend", "version": "1.0.0"}
   ```

### Frontend Setup (React + Vite)

1. **Navigate to the frontend directory:**
   ```powershell
   cd frontend
   ```

2. **Install dependencies:**
   ```powershell
   npm install
   ```

3. **Initialize environment file:**
   ```powershell
   Copy-Item .env.example .env
   ```
   *(Ensure `VITE_OAUTH_API_BASE_URL=http://127.0.0.1:8000/api/v1`)*.

4. **Run in Development Mode:**
   ```powershell
   npm run dev
   # Serves on http://127.0.0.1:3000
   ```

5. **Run in Production Mode (Build & Preview):**
   ```powershell
   npm run build
   npm run preview -- --port 3000 --host 127.0.0.1
   # Compiles bundle and serves on http://127.0.0.1:3000
   ```

---

## 7. Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Type | Default | Description |
|---|---|---|---|
| `ENV` | string | `development` | Environment mode (`development` or `production`). |
| `HOST` | string | `127.0.0.1` | Host interface to bind server. |
| `PORT` | integer | `8000` | Port for the FastAPI server. |
| `ALLOWED_ORIGINS` | string | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated CORS allowed origins (strictly no wildcard `*`). |
| `FRONTEND_BASE_URL` | string | `http://localhost:3000` | Base URL used when generating shareable guide links. |
| `COMPOSIO_API_KEY` | string | `""` | Composio API key (kept strictly on backend; never exposed to frontend). |
| `COMPOSIO_BASE_URL` | string | `https://backend.composio.dev/api/v3.1` | Base URL for Composio API v3.1 endpoints. |
| `RESEARCH_ENABLED` | boolean | `true` | Enables evidence-based documentation retrieval. |
| `GEMINI_RESEARCH_ENABLED` | boolean | `false` | When `false`, uses the deterministic evidence engine; when `true`, enables Gemini LLM synthesis. |

### Frontend (`frontend/.env`)

| Variable | Type | Default | Description |
|---|---|---|---|
| `VITE_OAUTH_API_BASE_URL` | string | `http://127.0.0.1:8000/api/v1` | URL of the running FastAPI backend API. |

---

## 8. Demo Applications Walkthrough

### 1. Slack (`VERY EASY`)
- **Pathway:** Composio Managed OAuth Available (`COMPOSIO MANAGED AVAILABLE`). Developers do not need to register an app on `api.slack.com` or manage redirect URIs.
- **Active Effort:** 15–30 minutes (2–5 minutes with managed auth). Confidence: `ESTIMATE HEURISTIC`.
- **Review Requirement:** `No` (0 days SLA). Single-workspace installations and unlisted direct install links install immediately. App Directory listing review is conditional only for public marketplace listings.
- **Human vs Downstream Automation:** Human authorizes the workspace installation; downstream automation initializes the Composio session.

### 2. Shopify (`MODERATE`)
- **Pathway:** Custom OAuth Required (`COMPOSIO CUSTOM ONLY`). Shopify does not provide a universal managed multi-tenant app.
- **Active Effort:** 20–45 minutes.
- **Review Requirement:** `No` for API-only custom apps in a merchant test store. Conditional automated security and staff review if publishing to the public Shopify App Store.
- **Setup Steps:** Access dev dashboard, create API-only app, register redirect URIs in Composio.

### 3. Gmail / Google Workspace (`COMPLEX`)
- **Pathway:** Managed OAuth Available via Composio for personal or internal connections.
- **Security & Review Gates:**
  - *Testing Mode:* Up to 100 users, tokens expire after 7 days, 0 review required.
  - *Google OAuth Brand Verification:* Mandatory for external production apps requesting sensitive/restricted scopes. Internal Google Workspace org users exempt.
  - *CASA Tier 2 Security Assessment:* Conditionally required when restricted scopes (e.g. Gmail read/send) are accessed or stored on third-party application servers.
- **Active Effort:** 45–90 minutes (Confidence: `ESTIMATE HEURISTIC`).

---

## 9. Live Unfamiliar Application Walkthrough (Linear)

To investigate any application not seeded in the database:
1. Open the Workspace at `http://127.0.0.1:3000/workspace`.
2. Type `"Linear"` in the application input and click **INVESTIGATE AN APP**.
3. Frontend triggers `POST /api/v1/investigate`.
4. Backend retrieves Linear's metadata from Composio's live toolkit catalog and official documentation.
5. Guide renders immediately:
   - Identifies that Linear supports Managed OAuth via Composio (`toolkit: "linear"`).
   - Generates code snippets for `session create managed`, `session create custom`, and Auth Config payloads.
   - **Honesty of Uncertainty:** Fields without explicit documentation citations (e.g. PKCE enforcement, Wildcard URIs) render as `"Unverified"` (`null`), never fabricated.

---

## 10. Real Composio OAuth Connection Flow

In addition to pre-flight guidance, OAuth Navigator implements the **live, real-world OAuth connection flow** for developer tools via Composio's API v3.1:

```
┌────────────────────────────────────────────────────────┐
│                   OAuth Navigator UI                   │
│           (Workspace Guide / Direct Connect)           │
│            User clicks "Connect {AppName}"             │
└──────────────────────────┬─────────────────────────────┘
                           │ 1. Synchronously reserves blank tab: window.open("about:blank", "_blank")
                           │ 2. Dispatches POST /api/v1/connections/{slug}/start (via Vercel proxy)
                           │    Transmits HttpOnly signed session cookie: oauth_nav_session
                           ▼
┌────────────────────────────────────────────────────────┐
│              FastAPI Backend (Render Web API)          │
│            ComposioConnectionService                   │
│  • Authenticates caller via HMAC-SHA256 session cookie │
│  • Resolves managed or custom Auth Config in Composio  │
│  • Generates unique per-attempt alias & Connect Link   │
└──────────────────────────┬─────────────────────────────┘
                           │ 3. POST https://backend.composio.dev/api/v3.1/connected_accounts/link
                           │    Payload: { auth_config_id, user_id: session_id, callback_url }
                           ▼
┌────────────────────────────────────────────────────────┐
│                   Composio v3.1 API                    │
│       Returns: redirect_url, connected_account_id      │
└──────────────────────────┬─────────────────────────────┘
                           │ 4. Return to frontend: { redirect_url, connected_account_id }
                           ▼
┌────────────────────────────────────────────────────────┐
│                    React Frontend                      │
│  • Exclusively navigates reserved tab to redirect_url  │
│  • Original tab NEVER navigates (stays on workspace)   │
│  • Lifecycle: INITIATING → AWAITING_AUTHORIZATION      │
│  • Fallback in-page link if popup blocked by browser   │
│  • Listens for postMessage (strict origin check)       │
│  • Active polling fallback: GET /api/v1/connections/{id│
└──────────────────────────┬─────────────────────────────┘
                           │ 5. Provider consent completed in auth tab:
                           │    Auth tab sends postMessage to opener and closes
                           ▼
┌────────────────────────────────────────────────────────┐
│                 Verified Connection                    │
│  • Lifecycle transitions to ACTIVE                     │
│  • Renders verified Account ID, Toolkit, Alias, Date   │
│  • Action: Test Connection (live verification)         │
│  • Action: Disconnect (DELETE /api/v1/connections/{id})│
│  • Action: Reconnect (force_new attempt with new alias)│
└────────────────────────────────────────────────────────┘
```

### Supported Provider Behaviors
1. **Slack (Composio-Managed OAuth):**
   - Automatically resolves `ac_...` managed auth configuration.
   - Generates a real `https://connect.composio.dev/link/...` authorization URL.
   - User grants permission in Slack workspace; backend reports `ACTIVE`.
2. **Gmail (Composio-Managed OAuth):**
   - Automatically resolves managed Google OAuth configuration.
   - Generates authorization link directing user to Google OAuth consent screen.
3. **Shopify (Custom OAuth Required):**
   - Composio does not provide shared/managed multi-tenant credentials for Shopify.
   - The connection service explicitly detects this and returns `CUSTOM_OAUTH_REQUIRED` with setup instructions.
   - If a custom app is registered in Shopify Partners and configured in Composio Dashboard, setting `COMPOSIO_SHOPIFY_AUTH_CONFIG_ID` on the backend unlocks the live connection flow.
   - No credentials or secrets are ever requested or stored on the frontend.

### Security, Cryptographic Session Integrity & Storage Architecture
- **Server-Issued HttpOnly Session Cookies:** Anonymous user session identities are generated strictly server-side using high-entropy random identifiers (`anon_<token>`). The backend cryptographically signs each session ID using HMAC-SHA256 (`{session_id}.{signature}`) and sets an `HttpOnly`, `Secure`, `SameSite=none/lax` cookie (`oauth_nav_session`).
- **First-Party Reverse Proxy (Incognito Cookie Continuity):** In production on Vercel (`oauthnavigator.vercel.app`), API requests route through the Vercel edge reverse proxy (`/api/:path*` -> Render). As a result, the session cookie is treated as a **100% first-party cookie** on `oauthnavigator.vercel.app`, completely immune to third-party cookie blocking in Chrome Incognito, Safari, and Firefox Private Browsing.
- **Strict Multi-Tenant Session Isolation:** Two separate browser sessions or incognito windows obtain independent session IDs. All connection retrieval, listing, testing, and deletion endpoints enforce strict session ownership checks. Attempts by one session to access another session's connection return `HTTP 404 Not Found` (preventing ID enumeration).
- **Zero Secrets in Browser Storage:** No API keys, client secrets, access tokens, or session identifiers are stored in `localStorage` or `sessionStorage`. All authentication state resides in the server-managed HttpOnly cookie.
- **Tab Preservation & Popup Handling:** The original OAuth Navigator workspace tab never redirects or reloads. The authorization URL opens exclusively in a synchronously reserved tab, with automatic fallback links displayed if a browser blocks popups.

---

## 11. Environment Variables & Setup Guide

### Required Environment Variables

| Variable | Scope | Description |
|---|---|---|
| `COMPOSIO_API_KEY` | Backend | Composio API key (`ak_...`) used server-side for metadata and connection links. |
| `COMPOSIO_BASE_URL` | Backend | Composio API v3.1 root (default: `https://backend.composio.dev/api/v3.1`). |
| `COMPOSIO_SHOPIFY_AUTH_CONFIG_ID` | Backend (Optional) | Custom OAuth config ID for Shopify if registered in Composio. |
| `SESSION_SECRET_KEY` | Backend (Optional) | Custom secret for HMAC-SHA256 session token signing (falls back to app-derived salt). |
| `ALLOWED_ORIGINS` | Backend | Comma-separated CORS origins (e.g. `https://oauthnavigator.vercel.app,http://localhost:3000`). |
| `FRONTEND_BASE_URL` | Backend | Production frontend URL for shareable permalinks (`https://oauthnavigator.vercel.app`). |
| `VITE_OAUTH_API_BASE_URL` | Frontend | Backend API root (`/api/v1` in production via Vercel first-party proxy; `http://localhost:8000/api/v1` in local dev). |

### Local Setup (Development)
```bash
# 1. Backend
cd backend
python -m venv .venv
# Activate virtual environment (.venv\Scripts\activate on Windows)
pip install -r requirements.txt
cp .env.example .env # Add your COMPOSIO_API_KEY
python run.py

# 2. Frontend
cd ../frontend
npm install
npm run dev # Starts Vite on http://localhost:5173 or :3000
```

---

## 12. Honest Limitations & Boundary Conditions

1. **Pre-flight Roadmap vs Connection Scope:**
   - Pre-flight guidance analyzes review policies and generates blueprints. The connection flow initiates real Composio connection links.
2. **Ephemeral Storage on Render Free Tier:**
   - Free instances spin down after 15 minutes of inactivity; `seed_guides.json` persists permanently, while live-generated guides and shared IDs are reset on restart unless committed or backed by persistent storage.
3. **Server-Issued Anonymous Session Identity:**
   - Implements zero-login server-issued anonymous session IDs (`anon_<token>`) cryptographically signed via HMAC-SHA256 (`oauth_nav_session` HttpOnly cookie) with first-party proxying (`/api/v1`) and strict tenant isolation. In enterprise production deployments requiring cross-device persistence or team management, this can seamlessly transition to Auth0, WorkOS, or enterprise OIDC.

---

## 13. Acceptance Report & Submission Inventory

- **Full Acceptance Report:** See [acceptance_report.md](acceptance_report.md) for complete audits.
- **Public GitHub Repository:** [https://github.com/xoxosuriya/oauth-navigator](https://github.com/xoxosuriya/oauth-navigator)
- **Live Deployed Frontend (Vercel):** [https://oauthnavigator.vercel.app](https://oauthnavigator.vercel.app)
- **Live Deployed Backend API (Render):** [https://oauth-navigator-api.onrender.com](https://oauth-navigator-api.onrender.com)
- **Swagger / OpenAPI Documentation:** [https://oauth-navigator-api.onrender.com/docs](https://oauth-navigator-api.onrender.com/docs)
