// Public client configuration. Set VITE_OAUTH_API_BASE_URL in a local Vite host.
// In Framer, use the API Base URL property on the workspace.
declare const process: any
const localDefault = "http://127.0.0.1:8000/api/v1"
export function resolveBase(override?: string) {
    const env = (import.meta as any).env?.VITE_OAUTH_API_BASE_URL
    return (override || env || localDefault).replace(/\/$/, "")
}
export class APIError extends Error {
    constructor(
        public status: number,
        message: string
    ) {
        super(message)
        this.name = "APIError"
    }
}
export function service(base?: string) {
    const root = resolveBase(base)
    async function request(path: string, body?: unknown, signal?: AbortSignal) {
        const controller = new AbortController()
        const abort = () => controller.abort()
        signal?.addEventListener("abort", abort)
        const timer = setTimeout(abort, 120000)
        try {
            const res = await fetch(root + path, {
                method: body === undefined ? "GET" : "POST",
                headers:
                    body === undefined
                        ? { Accept: "application/json" }
                        : {
                              Accept: "application/json",
                              "Content-Type": "application/json",
                          },
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
    }
}

// Verified module path

// Final module verification.
