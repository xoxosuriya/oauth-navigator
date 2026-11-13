// Public client configuration. Set VITE_OAUTH_API_BASE_URL in a local Vite host.

// In Framer, use the API Base URL property on the workspace.

declare const process: any

const localDefault = "http://127.0.0.1:8000/api/v1"

export function resolveBase(override?: string) {
    if (override && typeof override === "string" && override.trim()) {
        return override.trim().replace(/\/$/, "")
    }

    // In production browser environments (Vercel, custom domain, or any non-localhost host),
    // route through the first-party reverse proxy (/api/v1). This ensures all session cookies
    // are strictly first-party cookies on the frontend origin, preventing Incognito 3P cookie blocks.
    if (typeof window !== "undefined" && window.location && window.location.hostname) {
        const host = window.location.hostname.toLowerCase()
        if (host !== "localhost" && host !== "127.0.0.1" && host !== "0.0.0.0") {
            return "/api/v1"
        }
    }

    const env = (import.meta as any).env?.VITE_OAUTH_API_BASE_URL || (import.meta as any).env?.VITE_API_BASE_URL
    if (env && typeof env === "string" && env.trim()) {
        return env.trim().replace(/\/$/, "")
    }

    return localDefault
}

export class APIError extends Error {
    status: number

    constructor(
        status: number,
        message: string
    ) {
        super(message)
        this.status = status
        this.name = "APIError"
    }
}

export function isSafeExternalUrl(url: string): boolean {
    if (!url || typeof url !== "string") return false
    const trimmed = url.trim().toLowerCase()
    return (trimmed.startsWith("https://") || trimmed.startsWith("http://")) &&
        !trimmed.includes("javascript:") &&
        !trimmed.includes("data:")
}

// In-memory session identifier fallback for display/transient use only.
// NEVER stored in localStorage to preserve zero-storage security requirements and incognito window isolation.
let inMemoryFallbackUserId: string | null = null

export function getSessionUserId(): string {
    if (typeof window === "undefined") return "usr_demo_session"
    // Clear any legacy user_id from localStorage if present
    try {
        if (localStorage.getItem("oauth_nav_session_user_id")) {
            localStorage.removeItem("oauth_nav_session_user_id")
        }
    } catch {}

    if (!inMemoryFallbackUserId) {
        inMemoryFallbackUserId = "usr_" + Math.random().toString(36).substring(2, 10) + Date.now().toString(36).slice(-4)
    }
    return inMemoryFallbackUserId
}

export function service(base?: string) {

    const root = resolveBase(base)

    async function request(path: string, body?: unknown, signal?: AbortSignal, methodOverride?: string) {

        const controller = new AbortController()

        const abort = () => controller.abort()

        signal?.addEventListener("abort", abort)

        const timer = setTimeout(abort, 120000)

        try {

            const method = methodOverride || (body === undefined ? "GET" : "POST")

            const headers: Record<string, string> = {
                Accept: "application/json",
                ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
            }

            const res = await fetch(root + path, {

                method,

                headers,

                credentials: "include",

                body: body === undefined ? undefined : JSON.stringify(body),

                signal: controller.signal,

            })

            const data = await res.json().catch(() => null)

            if (!res.ok)

                throw new APIError(

                    res.status,

                    typeof data?.detail === "string"

                        ? data.detail

                        : res.status === 429

                          ? "Rate limit reached. Please wait before retrying."

                          : "Request failed (" + res.status + ")."

                )

            return data

        } catch (e) {

            if (e instanceof APIError) throw e

            if (signal?.aborted) throw e

            throw new APIError(

                0,

                "Could not reach the local API. Check that the backend is running and this browser origin is allowed. Framer preview is not in the supplied CORS allowlist."

            )

        } finally {

            clearTimeout(timer)

            signal?.removeEventListener("abort", abort)

        }

    }

    return {

        session: (s?: AbortSignal) =>
            request("/session", undefined, s),

        health: (s?: AbortSignal) => request("/health", undefined, s),

        apps: (query: string = "", s?: AbortSignal) =>

            request("/apps" + (query ? "?" + query : ""), undefined, s),

        guide: (id: string, s?: AbortSignal) =>

            request("/apps/" + encodeURIComponent(id), undefined, s),

        investigate: (name: string, s?: AbortSignal) =>

            request("/investigate", { app_name: name }, s),

        research: (name: string, domain?: string, s?: AbortSignal) =>

            request(

                "/research",

                {

                    app_name: name,

                    ...(domain ? { website_or_domain: domain } : {}),

                },

                s

            ),

        toolkit: (slug: string, s?: AbortSignal) =>

            request(

                "/composio/toolkit/" + encodeURIComponent(slug),

                undefined,

                s

            ),

        share: (id: string, s?: AbortSignal) =>

            request("/guides/share", { guide_id: id }, s),

        shared: (id: string, s?: AbortSignal) =>

            request("/guides/share/" + encodeURIComponent(id), undefined, s),

        startConnection: (
            slug: string,
            _userId?: string,
            alias?: string,
            callbackUrl?: string,
            forceNew?: boolean,
            s?: AbortSignal
        ) =>
            request(
                "/connections/" + encodeURIComponent(slug) + "/start",
                {
                    ...(alias ? { alias } : {}),
                    ...(callbackUrl ? { callback_url: callbackUrl } : {}),
                    force_new: !!forceNew,
                },
                s
            ),

        getConnection: (id: string, _userId?: string, s?: AbortSignal) =>
            request(
                "/connections/" + encodeURIComponent(id),
                undefined,
                s
            ),

        listConnections: (_userId?: string, toolkitSlug?: string, s?: AbortSignal) =>
            request(
                "/connections" + (toolkitSlug ? "?toolkit_slug=" + encodeURIComponent(toolkitSlug) : ""),
                undefined,
                s
            ),

        shopifyStatus: (s?: AbortSignal) =>
            request("/connections/shopify/status", undefined, s),

        disconnect: (id: string, s?: AbortSignal) =>
            request("/connections/" + encodeURIComponent(id), undefined, s, "DELETE"),

    }

}



// Verified module path



// Final module verification.

