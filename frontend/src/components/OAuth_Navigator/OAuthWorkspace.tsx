import * as React from "react"

import { addPropertyControls, ControlType } from "framer"

import { Section, Icon, IconTile, Reveal, T } from "../Kit.tsx"

import { OAuthDiagram } from "./OAuthDiagram.tsx"

import { service, resolveBase, getSessionUserId, isSafeExternalUrl } from "./OAuthAPI.ts"

interface Props {

    apiBase?: string

    embedded?: boolean

    mode?: string

    style?: React.CSSProperties

}

const css = `

.on-work{padding:0;min-height:760px}.on-embedded .grid>.panel:nth-child(n+4){display:none}.on-embedded .grid>.panel:nth-child(3) .sv-root{display:none}.on-embedded .grid>.panel:nth-child(3){display:none}.on-embedded .shell{min-height:650px}.on-work .shell{display:grid;grid-template-columns:180px minmax(0,1fr);max-width:1440px;margin:auto;min-height:760px}

.on-work .rail{padding:28px 18px;border-right:1.5px solid black;background:${T.cream};display:flex;flex-direction:column;gap:14px}

.on-work .rail button,.on-work .rail a{display:flex;align-items:center;gap:9px;text-align:left;padding:12px;border:1px solid transparent;border-radius:14px;font-size:13px;font-weight:600}

.on-work .rail .selected{background:${T.butter};border-color:black;box-shadow:2px 2px 0 black}

.on-work .content{padding:28px 32px 64px;min-width:0;background:${T.cream}}

.on-work .top{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;border-bottom:1px solid black;padding-bottom:20px;margin-bottom:26px}

.on-work h1{font-family:var(--display);font-size:clamp(25px,3cqw,42px);line-height:1.2;letter-spacing:-.03em}

.on-work h2{font-family:var(--display);font-size:18px;line-height:1.3;margin-bottom:16px}.on-work h3{font-size:15px;font-weight:600;margin:16px 0 8px}

.on-work .intro{position:relative;background:${T.peach};border:1.5px solid black;box-shadow:4px 4px 0 black;border-radius:24px;padding:28px;margin-bottom:28px;overflow:hidden}

.on-work .intro p{max-width:650px;margin:14px 0 22px;font-size:14px}

.on-work form{display:flex;gap:12px;flex-wrap:wrap}.on-work input,.on-work select{font:inherit;background:white;border:1.5px solid black;border-radius:14px;padding:13px 15px;min-width:0;max-width:100%}

.on-work input{flex:1;min-width:140px}.on-work label{font-size:12px;display:grid;gap:8px}

.on-work .action{display:inline-flex;align-items:center;justify-content:center;gap:8px;background:black;color:white;border:1.5px solid black;border-radius:999px;padding:12px 20px;font-size:12px;font-weight:600;transition:transform .2s,box-shadow .2s;white-space:normal}

.on-work .action:hover{transform:translate(-2px,-2px);box-shadow:3px 3px 0 ${T.orange}}.on-work .action.secondary{background:white;color:black}.on-work button:disabled{opacity:.5;cursor:wait}

.on-work .quick{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:14px;font-size:12px}.on-work .quick button,.on-work .tag{border:1px solid black;background:${T.cream};padding:5px 11px;border-radius:999px;font-size:11px;display:inline-block;max-width:100%;overflow-wrap:anywhere}

.on-work .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}.on-work .panel{padding:24px;background:white;border:1.5px solid black;border-radius:20px;box-shadow:3px 3px 0 black;min-width:0;overflow-wrap:anywhere}

.on-work .panel.warm{background:${T.butter}}.on-work .wide{grid-column:1/-1}

.on-work .kv{display:grid;grid-template-columns:minmax(110px,1fr) minmax(0,1.5fr);gap:12px;padding:11px 0;border-top:1px solid rgba(0,0,0,.12);font-size:12px}.on-work .kv>span{color:${T.mute}}.on-work .kv>b{font-weight:500;overflow-wrap:anywhere}

.on-work .muted{font-size:12px;color:${T.mute};line-height:1.6}.on-work .message{border:1px dashed black;border-radius:14px;padding:16px;background:${T.cream};font-size:13px;margin:18px 0}

.on-work .list{display:grid;gap:12px;font-size:13px}.on-work .list li{padding-left:16px;position:relative}.on-work .list li:before{content:"";position:absolute;left:0;top:7px;width:5px;height:5px;background:black;border-radius:50%}

.on-work details{border-top:1px solid rgba(0,0,0,.2);padding:14px 0;font-size:13px}.on-work summary{font-weight:600;cursor:pointer}.on-work details p{margin-top:12px}.on-work details a{display:inline-block;text-decoration:underline;margin:10px 0;overflow-wrap:anywhere}

.on-work pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;border:1px solid black;border-radius:12px;background:${T.cream};padding:16px;max-width:100%}

.on-work .catalog{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px;margin-top:22px}.on-work .app{display:flex;flex-direction:column;gap:12px}.on-work .app .action{margin-top:auto;align-self:flex-start}

.on-work .flow{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:20px 0}.on-work .flow span{padding:8px 12px;border:1px solid black;border-radius:999px;background:${T.butter};font-size:11px;font-weight:600}

.on-work .tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:22px}.on-work .tabs button{padding:9px 15px;border:1px solid black;border-radius:999px;background:white;font-size:12px}.on-work .tabs button[aria-selected=true]{background:${T.butter};box-shadow:2px 2px 0 black}

@container(max-width:900px){.on-work .shell{grid-template-columns:1fr}.on-work .rail{flex-direction:row;flex-wrap:wrap;border-right:0;border-bottom:1.5px solid black;padding:12px 16px}.on-work .rail .aside-note{display:none}.on-work .content{padding:24px 20px 48px}}

@container(max-width:600px){.on-work .grid{grid-template-columns:1fr}.on-work .content{padding:20px 16px 40px}.on-work .intro,.on-work .panel{padding:20px}.on-work form{flex-direction:column}.on-work .kv{grid-template-columns:1fr;gap:5px}.on-work .rail button,.on-work .rail a{padding:8px;font-size:11px}.on-work .top .tag{font-size:10px}.on-work .catalog{grid-template-columns:1fr}}

`

const human = (v: any) =>

    v === null || v === undefined

        ? "Unverified"

        : typeof v === "boolean"

          ? v

              ? "Yes"

              : "No"

          : typeof v === "object"

            ? JSON.stringify(v)

            : String(v).replace(/_/g, " ")

const safe = (u: any) =>

    typeof u === "string" && /^https?:\/\//i.test(u) ? u : undefined

function Rows({ data }: { data: Record<string, any> }) {

    return (

        <>

            {Object.entries(data).map(([k, v]) => (

                <div className="kv" key={k}>

                    <span>{k}</span>

                    <b>

                        {Array.isArray(v)

                            ? v.length

                                ? v.map(human).join(", ")

                                : "Not documented"

                            : human(v)}

                    </b>

                </div>

            ))}

        </>

    )

}

function Items({ items }: { items: any[] }) {

    return items?.length ? (

        <ul className="list">

            {items.map((x, i) => (

                <li key={i}>{human(x)}</li>

            ))}

        </ul>

    ) : (

        <p className="muted">

            No documented items returned. This does not confirm that none are

            required.

        </p>

    )

}

function Panel({

    title,

    children,

    warm = false,

    wide = false,

}: {

    title: string

    children: React.ReactNode

    warm?: boolean

    wide?: boolean

}) {

    return (

        <Reveal

            className={"panel" + (warm ? " warm" : "") + (wide ? " wide" : "")}

        >

            <h2>{title}</h2>

            {children}

        </Reveal>

    )

}

export default function OAuthWorkspace({

    apiBase = "",

    embedded = false,

    mode = "investigate",

    style,

}: Props) {

    const client = React.useMemo(() => service(apiBase), [apiBase])

    const [tab, setTab] = React.useState(

        mode === "catalog"

            ? "catalog"

            : mode === "docs"

              ? "docs"

              : "investigate"

    )

    const [name, setName] = React.useState("")

    const [guide, setGuide] = React.useState<any>(null),

        [research, setResearch] = React.useState<any>(null),

        [toolkit, setToolkit] = React.useState<any>(null)

    const [catalog, setCatalog] = React.useState<any[]>([]),

        [catalogState, setCatalogState] = React.useState("idle"),

        [catalogError, setCatalogError] = React.useState("")

    const [error, setError] = React.useState(""),

        [busy, setBusy] = React.useState(""),

        [share, setShare] = React.useState(""),

        [recent, setRecent] = React.useState<any[]>([])

    const [filter, setFilter] = React.useState(""),

        [managed, setManaged] = React.useState(""),

        [difficulty, setDifficulty] = React.useState(""),

        [health, setHealth] = React.useState("checking")

    const catalogRequest = React.useRef<AbortController | null>(null)

    const active = React.useRef<AbortController | null>(null)

    const [connection, setConnection] = React.useState<any>(null),
        [connectionState, setConnectionState] = React.useState<
            | "idle"
            | "initiating"
            | "awaiting_authorization"
            | "active"
            | "failed"
            | "expired"
            | "cancelled"
            | "shopify_custom_required"
        >("idle"),
        [connectionError, setConnectionError] = React.useState<string>(""),
        [connectionRedirectUrl, setConnectionRedirectUrl] = React.useState<string>(""),
        [pendingAccountId, setPendingAccountId] = React.useState<string>(""),
        [shopifyInfo, setShopifyInfo] = React.useState<any>(null),
        [isPopupBlocked, setIsPopupBlocked] = React.useState<boolean>(false),
        [testStatusMessage, setTestStatusMessage] = React.useState<string>("")

    const pollIntervalRef = React.useRef<any>(null)
    const userId = React.useMemo(() => getSessionUserId(), [])

    const cancelPolling = React.useCallback(() => {
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
            pollIntervalRef.current = null
        }
        if (typeof window !== "undefined") {
            sessionStorage.removeItem("oauth_nav_pending_account_id")
            sessionStorage.removeItem("oauth_nav_pending_slug")
        }
        setConnectionState("cancelled")
    }, [])

    const checkExistingConnection = React.useCallback(async (slug: string) => {
        if (!slug) return
        const cleanSlug = slug.toLowerCase().trim()
        try {
            const res = await client.listConnections(userId, cleanSlug)
            if (res && res.items && res.items.length > 0) {
                // Prioritize ACTIVE connection
                const active = res.items.find((it: any) => it.status === "ACTIVE")
                if (active) {
                    setConnection(active)
                    setConnectionState("active")
                    setConnectionError("")
                    return
                }
                // Check if any connection is initiated
                const pending = res.items.find((it: any) => it.status === "INITIATED" || it.status === "INITIALIZING")
                if (pending) {
                    setConnection(pending)
                    setPendingAccountId(pending.id)
                    setConnectionState("awaiting_authorization")
                    setConnectionError("")
                    return
                }
                // Check for expired or failed
                const mostRecent = res.items[0]
                if (mostRecent.status === "EXPIRED") {
                    setConnection(mostRecent)
                    setConnectionState("expired")
                    setConnectionError(mostRecent.status_reason || "Connection link expired.")
                } else if (mostRecent.status === "FAILED") {
                    setConnection(mostRecent)
                    setConnectionState("failed")
                    setConnectionError(mostRecent.status_reason || "Connection attempt failed.")
                } else {
                    setConnection(mostRecent)
                    setConnectionState("idle")
                }
            } else {
                setConnection(null)
                setConnectionState("idle")
                setConnectionError("")
            }
        } catch {
            setConnection(null)
            setConnectionState("idle")
        }
    }, [client, userId])

    const pollStatus = React.useCallback(async (accountId: string) => {
        if (!accountId) return
        try {
            const data = await client.getConnection(accountId, userId)
            if (data) {
                setConnection(data)
                if (data.status === "ACTIVE") {
                    setConnectionState("active")
                    setConnectionError("")
                    setTestStatusMessage("")
                    if (typeof window !== "undefined") {
                        sessionStorage.removeItem("oauth_nav_pending_account_id")
                        sessionStorage.removeItem("oauth_nav_pending_slug")
                    }
                    if (pollIntervalRef.current) {
                        clearInterval(pollIntervalRef.current)
                        pollIntervalRef.current = null
                    }
                } else if (data.status === "FAILED") {
                    setConnectionState("failed")
                    setConnectionError(data.status_reason || "Provider OAuth connection failed.")
                    if (typeof window !== "undefined") {
                        sessionStorage.removeItem("oauth_nav_pending_account_id")
                        sessionStorage.removeItem("oauth_nav_pending_slug")
                    }
                    if (pollIntervalRef.current) {
                        clearInterval(pollIntervalRef.current)
                        pollIntervalRef.current = null
                    }
                } else if (data.status === "EXPIRED") {
                    setConnectionState("expired")
                    setConnectionError(data.status_reason || "Connection link has expired.")
                    if (typeof window !== "undefined") {
                        sessionStorage.removeItem("oauth_nav_pending_account_id")
                        sessionStorage.removeItem("oauth_nav_pending_slug")
                    }
                    if (pollIntervalRef.current) {
                        clearInterval(pollIntervalRef.current)
                        pollIntervalRef.current = null
                    }
                } else {
                    setConnectionState("awaiting_authorization")
                }
            }
        } catch (err: any) {
            if (err?.status === 404) {
                setConnectionState("failed")
                setConnectionError("Connected account not found or expired.")
                if (pollIntervalRef.current) {
                    clearInterval(pollIntervalRef.current)
                    pollIntervalRef.current = null
                }
            }
        }
    }, [client, userId])

    const startPolling = React.useCallback((accountId: string) => {
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
        setPendingAccountId(accountId)
        setConnectionState("awaiting_authorization")
        pollStatus(accountId)
        let count = 0
        pollIntervalRef.current = setInterval(() => {
            count++
            if (count > 30) {
                clearInterval(pollIntervalRef.current)
                pollIntervalRef.current = null
                setConnectionState("expired")
                setConnectionError("Authorization timed out. Click 'Refresh Status' or 'Retry' to try again.")
            } else {
                pollStatus(accountId)
            }
        }, 2500)
    }, [pollStatus])

    React.useEffect(() => {
        return () => {
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
        }
    }, [])

    React.useEffect(() => {
        if (typeof window === "undefined" || embedded) return
        // Initialize or synchronize cryptographically signed session on mount via HttpOnly cookie
        client.session().catch(() => {})

        const params = new URLSearchParams(window.location.search)
        const connParam = params.get("connection_id") || params.get("connected_account_id")
        const statusParam = params.get("status")

        // 1. If inside authorization callback popup with window.opener, notify opener via postMessage
        if ((connParam || statusParam) && window.opener && window.opener !== window) {
            try {
                window.opener.postMessage(
                    {
                        type: "OAUTH_CALLBACK",
                        accountId: connParam || "",
                        status: statusParam || "success",
                    },
                    window.location.origin
                )
            } catch {}
            setTimeout(() => {
                try { window.close() } catch {}
            }, 500)
            return
        }

        const storedPending = sessionStorage.getItem("oauth_nav_pending_account_id")
        const targetId = connParam || storedPending
        if (targetId) {
            startPolling(targetId)
        }
        // Clear sensitive query params from browser URL after reading
        if ((connParam || statusParam) && window.history && window.history.replaceState) {
            const cleanUrl = window.location.origin + window.location.pathname
            window.history.replaceState({}, document.title, cleanUrl)
        }

        // 2. Listen for postMessage from authorization tab (Strict origin validation)
        function handleAuthMessage(event: MessageEvent) {
            if (event.origin !== window.location.origin) return
            const data = event.data
            if (data && data.type === "OAUTH_CALLBACK") {
                const { accountId, status } = data
                if (status === "success" || status === "active" || !status) {
                    if (accountId) {
                        pollStatus(accountId)
                    }
                } else if (status === "failed" || status === "error") {
                    setConnectionState("failed")
                    setConnectionError("Provider authorization was denied or failed.")
                }
            }
        }

        window.addEventListener("message", handleAuthMessage)
        return () => {
            window.removeEventListener("message", handleAuthMessage)
        }
    }, [embedded, startPolling, userId, client, pollStatus])

    // Synchronize connection status whenever active guide changes
    React.useEffect(() => {
        if (!guide?.slug) {
            setConnection(null)
            setConnectionState("idle")
            setConnectionError("")
            return
        }
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
            pollIntervalRef.current = null
        }
        checkExistingConnection(guide.slug)
    }, [guide?.slug, checkExistingConnection])

    async function handleDisconnect(accountId?: string) {
        const id = accountId || connection?.id
        if (!id) {
            setConnection(null)
            setConnectionState("idle")
            return
        }
        try {
            await client.disconnect(id)
        } catch {
            // gracefully clear local state
        }
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
            pollIntervalRef.current = null
        }
        if (typeof window !== "undefined") {
            sessionStorage.removeItem("oauth_nav_pending_account_id")
            sessionStorage.removeItem("oauth_nav_pending_slug")
        }
        setConnection(null)
        setConnectionState("idle")
        setConnectionError("")
        setTestStatusMessage("")
    }

    async function handleTestConnection(accountId?: string) {
        const id = accountId || connection?.id
        if (!id) return
        setTestStatusMessage("Verifying active connection...")
        try {
            const data = await client.getConnection(id, userId)
            if (data && data.status === "ACTIVE") {
                setTestStatusMessage("✓ Verified: Connection is ACTIVE and operational!")
                setConnection(data)
                setConnectionState("active")
            } else {
                setTestStatusMessage(`Status: ${data?.status || "UNKNOWN"} - ${data?.status_reason || "Not active"}`)
            }
        } catch (e: any) {
            setTestStatusMessage(e.message || "Verification failed.")
        }
    }

    async function handleConnect(toolkitSlug: string, forceNew: boolean = false) {
        if (!toolkitSlug) return
        const slug = toolkitSlug.toLowerCase().trim()
        setConnectionError("")
        setTestStatusMessage("")
        setIsPopupBlocked(false)

        if (slug === "shopify") {
            try {
                const sStatus = await client.shopifyStatus()
                if (!sStatus.has_custom_config) {
                    setShopifyInfo(sStatus)
                    setConnectionState("shopify_custom_required")
                    return
                }
            } catch {
                // proceed
            }
        }

        // ISSUE 1 REQUIREMENT:
        // Open the new tab synchronously inside click handler before awaiting async calls to prevent popup blocker.
        let authWindow: Window | null = null
        try {
            authWindow = window.open("about:blank", "_blank")
        } catch {
            authWindow = null
        }

        if (!authWindow || authWindow.closed || typeof authWindow.closed === "undefined") {
            setIsPopupBlocked(true)
        }

        setConnectionState("initiating")
        try {
            const callbackUrl = typeof window !== "undefined"
                ? `${window.location.origin}${window.location.pathname}`
                : undefined

            // Generate unique attempt alias: provider + unique attempt token
            const attemptAlias = `${slug}_${Date.now().toString(36).slice(-5)}`

            const res = await client.startConnection(slug, userId, attemptAlias, callbackUrl, forceNew)

            if (res && res.already_active) {
                if (authWindow && !authWindow.closed) {
                    try { authWindow.close() } catch {}
                }
                setConnection({
                    id: res.connected_account_id,
                    toolkit_slug: res.toolkit_slug,
                    status: "ACTIVE",
                    user_id: userId,
                    alias: res.alias,
                    updated_at: "Just now",
                })
                setConnectionState("active")
                setConnectionError("")
                return
            }

            if (res && res.redirect_url && isSafeExternalUrl(res.redirect_url)) {
                setConnectionRedirectUrl(res.redirect_url)
                setPendingAccountId(res.connected_account_id)
                setConnection({
                    id: res.connected_account_id,
                    toolkit_slug: res.toolkit_slug,
                    status: "INITIATED",
                    user_id: userId,
                    alias: res.alias,
                })
                setConnectionState("awaiting_authorization")

                if (typeof window !== "undefined") {
                    sessionStorage.setItem("oauth_nav_pending_account_id", res.connected_account_id)
                    sessionStorage.setItem("oauth_nav_pending_slug", slug)
                }

                startPolling(res.connected_account_id)

                if (authWindow && !authWindow.closed) {
                    try {
                        authWindow.location.href = res.redirect_url
                    } catch {
                        setIsPopupBlocked(true)
                    }
                } else {
                    setIsPopupBlocked(true)
                }

                // CRITICAL (Issue 1): NEVER set window.location.href in the original tab!
            } else {
                if (authWindow && !authWindow.closed) {
                    try { authWindow.close() } catch {}
                }
                setConnectionState("failed")
                setConnectionError("Failed to generate authorization URL.")
            }
        } catch (err: any) {
            if (authWindow && !authWindow.closed) {
                try { authWindow.close() } catch {}
            }
            setConnectionState("failed")
            setConnectionError(err.message || "Failed to start connection.")
        }
    }

    // FIX 3: Automatic initial health check on component mount (with unmount guard)
    React.useEffect(() => {

        if (embedded || typeof window === "undefined") return

        let mounted = true

        setHealth("checking")

        client.health()

            .then((res: any) => {

                if (mounted) {

                    if (res && res.status === "healthy") {

                        setHealth("healthy")

                    } else {

                        setHealth("unavailable")

                    }

                }

            })

            .catch(() => {

                if (mounted) {

                    setHealth("unavailable")

                }

            })

        return () => {

            mounted = false

        }

    }, [client, embedded])

    React.useEffect(

        () => () => {

            active.current?.abort()

            catalogRequest.current?.abort()

        },

        []

    )

    const remember = (g: any) =>

        setRecent((r) =>

            [

                { id: g.id, name: g.app_name },

                ...r.filter((x) => x.id !== g.id),

            ].slice(0, 8)

        )

    async function run(

        kind: string,

        fn: (signal: AbortSignal) => Promise<any>

    ) {

        active.current?.abort()

        const c = new AbortController()

        active.current = c

        setBusy(kind)

        setError("")

        try {

            const value = await fn(c.signal)

            return c.signal.aborted ? null : value

        } catch (e) {

            if (!c.signal.aborted)

                setError(e instanceof Error ? e.message : "Request failed.")

            return null

        } finally {

            if (active.current === c) setBusy("")

        }

    }

    async function investigate(value: string) {

        const n = value.trim()

        if (!n || n.length > 100) {

            setError("Enter an application name between 1 and 100 characters.")

            return

        }

        setName(n)

        setGuide(null)

        setResearch(null)

        setToolkit(null)

        setShare("")

        setConnection(null)

        setConnectionState("idle")

        setConnectionError("")

        setTab("investigate")

        const g = await run("Investigating", (s) => client.investigate(n, s))

        if (g) {

            setGuide(g)

            remember(g)

        } else {

            setGuide(null)

        }

    }

    async function openGuide(id: string) {

        setTab("investigate")

        setResearch(null)

        setToolkit(null)

        setGuide(null)

        setShare("")

        setConnection(null)

        setConnectionState("idle")

        setConnectionError("")

        const g = await run("Opening guide", (s) => client.guide(id, s))

        if (g) {

            setGuide(g)

            setName(g.app_name)

            remember(g)

        }

    }

    async function loadCatalog() {

        setCatalogState("loading")

        setCatalogError("")

        catalogRequest.current?.abort()

        const c = new AbortController()

        catalogRequest.current = c

        const query = new URLSearchParams()

        if (filter) query.set("search", filter)

        if (managed) query.set("managed_only", managed)

        if (difficulty) query.set("difficulty", difficulty)

        try {

            const d = await client.apps(query.toString(), c.signal)

            if (c.signal.aborted) return

            setCatalog(Array.isArray(d.items) ? d.items : [])

            setCatalogState("ready")

        } catch (e) {

            if (c.signal.aborted) return

            setCatalogError(

                e instanceof Error ? e.message : "Catalogue unavailable"

            )

            setCatalogState("error")

        }

    }

    React.useEffect(() => {

        if (!embedded) loadCatalog()

    }, [client, embedded])

    React.useEffect(() => {

        if (embedded || typeof window === "undefined") return

        const params = new URLSearchParams(window.location.search)

        const requestedTab = params.get("view")

        if (["catalog", "recent", "docs"].includes(requestedTab || ""))

            setTab(requestedTab!)

        const shared = params.get("share")

        const app = params.get("app")

        if (shared) {

            run("Loading shared guide", (s) => client.shared(shared, s)).then(

                (g) => {

                    if (g) {

                        setGuide(g)

                        setName(g.app_name)

                        remember(g)

                    }

                }

            )

        } else if (app) openGuide(app)

    }, [])

    const r = research

    const comp = toolkit || r?.composio_status || guide?.composio_status

    const oauth = r?.oauth_details

    const readiness =

        oauth?.supports_oauth === true

            ? "Supported"

            : oauth?.supports_oauth === false

              ? "Unsupported"

              : "Unverified"

    return (

        <Section

            tone="cream"

            pad={false}

            className={"on-work" + (embedded ? " on-embedded" : "")}

            css={css}

            style={{ ...style, paddingTop: embedded ? 0 : 100 }}

            label="OAuth Navigator application workspace"

        >

            <div className="shell">

                <aside className="rail" aria-label="Workspace navigation">

                    <IconTile

                        name="route"

                        tile={T.butter}

                        size={42}

                        icon={22}

                    />

                    {[

                        ["investigate", "search", "Investigate"],

                        ["catalog", "layers", "Catalogue"],

                        ["recent", "activity", "Recent"],

                        ["docs", "file", "Documentation"],

                    ].map(([id, icon, label]) => (

                        <button

                            key={id}

                            className={tab === id ? "selected" : ""}

                            onClick={() => setTab(id)}

                        >

                            <Icon name={icon} size={16} />

                            {label}

                        </button>

                    ))}

                    <a href="/">Back to home</a>

                    <p

                        className="muted aside-note"

                        style={{ marginTop: "auto" }}

                    >

                        Real evidence.

                        <br />

                        Explicit uncertainty.

                        <br />

                        No stored credentials.

                    </p>

                </aside>

                <main className="content">

                    <header className="top">

                        <b

                            style={{

                                fontFamily: "var(--display)",

                                fontSize: 13,

                            }}

                        >

                            OAUTH NAVIGATOR / WORKSPACE

                        </b>

                        <span className="tag">

                            {embedded

                                ? "Interface preview · no application selected"

                                : health === "checking"

                                  ? "API · Checking"

                                  : health === "healthy"

                                    ? "API · Healthy"

                                    : health === "unavailable"

                                      ? "API · Unavailable"

                                      : "API · " + health}

                        </span>

                    </header>

                    {tab === "investigate" && (

                        <>

                            <section className="intro">

                                <p className="sv-tag">

                                    Authentication, understood.

                                </p>

                                <h1>

                                    {guide

                                        ? guide.app_name

                                        : "Investigate an app."}

                                </h1>

                                <p>

                                    {guide?.summary ||

                                        "Start with a name. Understand the OAuth pathway, provider requirements and the evidence behind every finding."}

                                </p>

                                <form

                                    onSubmit={(e) => {

                                        e.preventDefault()

                                        investigate(name)

                                    }}

                                >

                                    <input

                                        aria-label="Application name"

                                        placeholder="Application name, e.g. Notion"

                                        value={name}

                                        maxLength={100}

                                        onChange={(e) =>

                                            setName(e.target.value)

                                        }

                                        required

                                    />

                                    <button

                                        className="action"

                                        disabled={!!busy}

                                        type="submit"

                                    >

                                        <Icon name="search" size={16} />

                                        {busy || "Investigate an App"}

                                    </button>

                                </form>

                                <div className="quick">

                                    <span>Investigate:</span>

                                    {["Notion", "Slack", "Shopify"].map((n) => (

                                        <button

                                            disabled={!!busy}

                                            key={n}

                                            onClick={() => investigate(n)}

                                        >

                                            {n}

                                        </button>

                                    ))}

                                </div>

                            </section>

                            {error && (

                                <div role="alert" className="message">

                                    <b>Investigation not confirmed.</b>

                                    <p>{error}</p>

                                    <p className="muted">

                                        No application capabilities have been

                                        inferred from this error.

                                    </p>

                                </div>

                            )}

                            {busy && (

                                <p

                                    role="status"

                                    aria-live="polite"

                                    className="message"

                                >

                                    {busy}… Checking the backend.{" "}

                                    <button

                                        onClick={() => {

                                            active.current?.abort()

                                            setBusy("")

                                        }}

                                    >

                                        Cancel request

                                    </button>

                                </p>

                            )}

                            {guide && (

                                <div className="tabs">

                                    <button

                                        disabled={!!busy}

                                        onClick={async () => {

                                            setResearch(null)

                                            const d = await run(

                                                "Researching documentation",

                                                (s) =>

                                                    client.research(

                                                        guide.app_name,

                                                        guide.app_website,

                                                        s

                                                    )

                                            )

                                            if (d) setResearch(d)

                                        }}

                                    >

                                        Research technical details

                                    </button>

                                    <button

                                        disabled={!!busy}

                                        onClick={async () => {

                                            const d = await run(

                                                "Checking Composio",

                                                (s) =>

                                                    client.toolkit(

                                                        guide.slug,

                                                        s

                                                    )

                                            )

                                            if (d) setToolkit(d)

                                        }}

                                    >

                                        Verify Composio

                                    </button>

                                    <button

                                        disabled={!!busy}

                                        onClick={async () => {

                                            const d = await run(

                                                "Creating share link",

                                                (s) => client.share(guide.id, s)

                                            )

                                            if (d) setShare(d.share_url)

                                        }}

                                    >

                                        Share guide

                                    </button>

                                    <button
                                        disabled={!!busy || connectionState === "initiating" || connectionState === "initializing"}
                                        onClick={() => {
                                            if (connectionState === "active") {
                                                handleConnect(guide.slug, true)
                                            } else {
                                                handleConnect(guide.slug, false)
                                            }
                                        }}
                                        style={{
                                            background: connectionState === "active" ? "#D1F4D9" : (guide.slug === "slack" || guide.slug === "gmail") ? T.butter : T.peach,
                                            fontWeight: 700,
                                        }}
                                    >
                                        <Icon name="key" size={16} />
                                        {connectionState === "initiating" || connectionState === "initializing"
                                            ? "Initiating…"
                                            : connectionState === "awaiting_authorization" || connectionState === "initiated"
                                            ? "Authorizing in New Tab…"
                                            : connectionState === "active"
                                            ? `✓ ${guide.app_name} Connected`
                                            : (connectionState === "failed" || connectionState === "expired")
                                            ? `Retry Connect`
                                            : `Connect ${guide.app_name}`}
                                    </button>

                                </div>

                            )}

                            {connectionState !== "idle" && (
                                <div
                                    className="message"
                                    style={{
                                        marginTop: 20,
                                        border: "2px solid black",
                                        background:
                                            connectionState === "active"
                                                ? "#E8F8ED"
                                                : connectionState === "failed"
                                                  ? "#FEECEC"
                                                  : connectionState === "expired"
                                                    ? "#FFF3E0"
                                                    : connectionState === "shopify_custom_required"
                                                      ? T.peach
                                                      : T.butter,
                                        boxShadow: "3px 3px 0 black",
                                        borderRadius: 14,
                                        padding: "16px 20px",
                                    }}
                                >
                                    <div
                                        style={{
                                            display: "flex",
                                            justifyContent: "space-between",
                                            alignItems: "center",
                                            flexWrap: "wrap",
                                            gap: 10,
                                            marginBottom: 10,
                                        }}
                                    >
                                        <b style={{ fontFamily: "var(--display)", fontSize: 14 }}>
                                            {guide ? guide.app_name : "OAuth"} Connection · {
                                                connectionState === "initiating" || connectionState === "initializing" ? "INITIATING"
                                                : connectionState === "awaiting_authorization" || connectionState === "initiated" ? "AWAITING AUTHORIZATION"
                                                : connectionState === "active" ? "ACTIVE"
                                                : connectionState === "expired" ? "EXPIRED"
                                                : connectionState === "cancelled" ? "CANCELLED"
                                                : connectionState === "shopify_custom_required" ? "CUSTOM OAUTH REQUIRED"
                                                : "FAILED"
                                            }
                                        </b>
                                        <span className="tag" style={{ fontSize: 11 }}>
                                            Session: {userId.slice(0, 12)}…
                                        </span>
                                    </div>

                                    {(connectionState === "initiating" || connectionState === "initializing") && (
                                        <p style={{ margin: 0 }}>
                                            Generating secure Composio authorization link and session…
                                        </p>
                                    )}

                                    {(connectionState === "awaiting_authorization" || connectionState === "initiated") && (
                                        <div>
                                            <p style={{ margin: "0 0 10px" }}>
                                                Authorization window opened in a new tab. Complete the consent prompt to activate your connection.
                                            </p>

                                            {isPopupBlocked && (
                                                <div style={{
                                                    margin: "10px 0 14px",
                                                    padding: "10px 14px",
                                                    background: "#FFF8E1",
                                                    border: "1.5px solid #FFA000",
                                                    borderRadius: 8,
                                                    fontSize: 13,
                                                    color: "#5D4037",
                                                    display: "flex",
                                                    alignItems: "center",
                                                    justifyContent: "space-between",
                                                    gap: 10
                                                }}>
                                                    <span>⚠️ Popup tab was blocked by your browser. Please open manually:</span>
                                                    {connectionRedirectUrl && (
                                                        <a
                                                            href={connectionRedirectUrl}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="action"
                                                            style={{ fontSize: 12, padding: "5px 12px", whiteSpace: "nowrap" }}
                                                        >
                                                            Open Authorization Page ↗
                                                        </a>
                                                    )}
                                                </div>
                                            )}

                                            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                                                {connectionRedirectUrl && (
                                                    <a
                                                        href={connectionRedirectUrl}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="action secondary"
                                                        style={{ fontSize: 12, padding: "6px 12px" }}
                                                    >
                                                        Open Authorization Link ↗
                                                    </a>
                                                )}
                                                <button
                                                    className="action secondary"
                                                    onClick={() => pollStatus(connection?.id || pendingAccountId)}
                                                    style={{ fontSize: 12, padding: "6px 12px" }}
                                                >
                                                    Refresh Status
                                                </button>
                                                <button
                                                    className="action secondary"
                                                    onClick={cancelPolling}
                                                    style={{ fontSize: 12, padding: "6px 12px" }}
                                                >
                                                    Cancel
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {connectionState === "active" && (
                                        <div>
                                            <p style={{ margin: "0 0 10px", color: "#1B5E20", fontWeight: 600 }}>
                                                ✓ OAuth connection is active! Tokens are managed securely on the backend.
                                            </p>
                                            <Rows
                                                data={{
                                                    "Account ID": connection?.id,
                                                    "Toolkit": connection?.toolkit_slug || guide?.slug,
                                                    "Status": "ACTIVE",
                                                    "Alias": connection?.alias || "—",
                                                    "Updated": connection?.updated_at || connection?.created_at || "Just now",
                                                }}
                                            />
                                            {testStatusMessage && (
                                                <p style={{ margin: "8px 0 4px", fontSize: 12, color: testStatusMessage.startsWith("✓") ? "#1B5E20" : "#C62828", fontWeight: 600 }}>
                                                    {testStatusMessage}
                                                </p>
                                            )}
                                            <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
                                                <button
                                                    className="action secondary"
                                                    onClick={() => handleTestConnection(connection?.id || pendingAccountId)}
                                                    style={{ fontSize: 12, padding: "6px 12px" }}
                                                >
                                                    Test Connection
                                                </button>
                                                <button
                                                    className="action secondary"
                                                    onClick={() => handleDisconnect(connection?.id || pendingAccountId)}
                                                    style={{ fontSize: 12, padding: "6px 12px", color: "#C62828" }}
                                                >
                                                    Disconnect
                                                </button>
                                                <button
                                                    className="action secondary"
                                                    onClick={() => handleConnect(guide?.slug || "", true)}
                                                    style={{ fontSize: 12, padding: "6px 12px" }}
                                                >
                                                    Reconnect
                                                </button>
                                                <button
                                                    className="action secondary"
                                                    onClick={() => pollStatus(connection?.id || pendingAccountId)}
                                                    style={{ fontSize: 12, padding: "6px 12px" }}
                                                >
                                                    Refresh Status
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {connectionState === "failed" && (
                                        <div>
                                            <p style={{ margin: "0 0 10px", color: "#B71C1C", fontWeight: 600 }}>
                                                {connectionError || connection?.status_reason || "OAuth authorization failed."}
                                            </p>
                                            <button
                                                className="action"
                                                onClick={() => handleConnect(guide?.slug || "", true)}
                                                style={{ fontSize: 12, padding: "6px 12px" }}
                                            >
                                                Retry Connection
                                            </button>
                                        </div>
                                    )}

                                    {connectionState === "expired" && (
                                        <div>
                                            <p style={{ margin: "0 0 10px", color: "#E65100", fontWeight: 600 }}>
                                                {connectionError || "Authorization link or connection has expired. Please initiate a fresh link."}
                                            </p>
                                            <button
                                                className="action"
                                                onClick={() => handleConnect(guide?.slug || "", true)}
                                                style={{ fontSize: 12, padding: "6px 12px" }}
                                            >
                                                Start Fresh Connection
                                            </button>
                                        </div>
                                    )}

                                    {connectionState === "cancelled" && (
                                        <div>
                                            <p style={{ margin: "0 0 10px", color: "#555" }}>
                                                Authorization polling cancelled. You can resume or start fresh anytime.
                                            </p>
                                            <button
                                                className="action secondary"
                                                onClick={() => handleConnect(guide?.slug || "", true)}
                                                style={{ fontSize: 12, padding: "6px 12px" }}
                                            >
                                                Connect {guide?.app_name}
                                            </button>
                                        </div>
                                    )}

                                    {connectionState === "shopify_custom_required" && (
                                        <div>
                                            <p style={{ margin: "0 0 8px", fontWeight: 600 }}>
                                                Custom OAuth Required for Shopify
                                            </p>
                                            <p className="muted" style={{ margin: "0 0 10px", fontSize: 13 }}>
                                                {shopifyInfo?.setup_instructions || "Shopify does not provide Composio-managed credentials. Configure a custom app in Shopify Partners and set COMPOSIO_SHOPIFY_AUTH_CONFIG_ID."}
                                            </p>
                                            <Rows
                                                data={{
                                                    "Composio Managed Auth": "Unavailable",
                                                    "Custom Config ID": shopifyInfo?.auth_config_id || "Not configured",
                                                }}
                                            />
                                        </div>
                                    )}
                                </div>
                            )}

                            {share && (

                                <div className="message">

                                    <b>Backend share permalink</b>

                                    <p>

                                        <a

                                            href={safe(share)}

                                            style={{

                                                textDecoration: "underline",

                                                overflowWrap: "anywhere",

                                            }}

                                        >

                                            {share}

                                        </a>

                                    </p>

                                    <p className="muted">

                                        The returned URL targets the backend’s

                                        configured frontend. Open this guide

                                        here:{" "}

                                        <a

                                            href={

                                                "/workspace?share=" +

                                                encodeURIComponent(guide.id)

                                            }

                                        >

                                            workspace share view

                                        </a>

                                        .

                                    </p>

                                    <button

                                        className="action secondary"

                                        onClick={() =>

                                            navigator.clipboard

                                                ?.writeText(share)

                                                .catch(() =>

                                                    setError(

                                                        "Clipboard access unavailable. Select and copy the link above."

                                                    )

                                                )

                                        }

                                    >

                                        Copy permalink

                                    </button>

                                </div>

                            )}

                            <div className="grid">

                                <Panel title="OAuth readiness" warm>

                                    <span className="tag">{readiness}</span>

                                    <Rows

                                        data={{

                                            "Research status": r?.status,

                                            Protocol: oauth?.protocol_version,

                                            "Grant types": oauth?.grant_types,

                                            Confidence:

                                                oauth?.confidence ||

                                                r?.confidence,

                                        }}

                                    />

                                    {r?.error_message && (

                                        <p className="message">

                                            {r.error_message}

                                        </p>

                                    )}

                                    <p className="muted">

                                        {!r

                                            ? "Technical capabilities remain unverified until detailed research returns evidence."

                                            : r.status === "PARTIAL"

                                              ? "Partial research. Missing fields remain unverified."

                                              : r.status === "METADATA_ONLY"

                                                ? "Metadata only. Provider-specific requirements may be unverified."

                                                : ""}

                                    </p>

                                </Panel>

                                <Panel title="Composio pathways">

                                    <Rows

                                        data={{

                                            "Managed OAuth":

                                                comp?.managed_oauth_available ===

                                                true

                                                    ? "Managed OAuth Available"

                                                    : comp?.managed_oauth_available ===

                                                        false

                                                      ? "Not available"

                                                      : "Unverified",

                                            "Custom OAuth":

                                                comp?.custom_oauth_mandatory_for_oauth ===

                                                    true ||

                                                comp?.classification ===

                                                    "CUSTOM_OAUTH_MANDATORY"

                                                    ? "Custom OAuth Required"

                                                    : comp?.custom_oauth_mandatory_for_oauth ===

                                                        false

                                                      ? "Not mandatory"

                                                      : "Unverified",

                                            Classification:

                                                comp?.classification,

                                            "Authentication schemes":

                                                comp?.supported_auth_schemes,

                                        }}

                                    />

                                    {comp?.explanation && (

                                        <p className="muted">

                                            {comp.explanation}

                                        </p>

                                    )}

                                </Panel>

                                <Panel

                                    title="Application & authentication flow"

                                    wide

                                >

                                    <Rows

                                        data={{

                                            Application: guide?.app_name,

                                            Website: guide?.app_website,

                                            "Setup difficulty":

                                                guide?.difficulty_rating,

                                        }}

                                    />

                                    <div className="flow">

                                        {[

                                            "Application",

                                            "OAuth Provider",

                                            "Composio",

                                            "AI Agent",

                                        ].map((x, i) => (

                                            <React.Fragment key={x}>

                                                {i > 0 && (

                                                    <Icon

                                                        name="arrow-right"

                                                        size={16}

                                                    />

                                                )}

                                                <span>{x}</span>

                                            </React.Fragment>

                                        ))}

                                    </div>

                                    <p className="muted">

                                        Conceptual flow — available pathways

                                        depend on the returned investigation.

                                    </p>

                                    {!guide && <OAuthDiagram compact />}

                                </Panel>

                                <Panel title="OAuth technical details">

                                    <Rows

                                        data={{

                                            "Authorization endpoint":

                                                oauth?.authorization_endpoint,

                                            "Token endpoint":

                                                oauth?.token_endpoint,

                                            "PKCE required":

                                                oauth?.pkce_required,

                                            "Additional flows":

                                                oauth?.additional_flows,

                                        }}

                                    />

                                </Panel>

                                <Panel title="Provider registration">

                                    <Rows

                                        data={{

                                            "Developer portal":

                                                r?.registration

                                                    ?.developer_portal_url ||

                                                guide?.developer_portal_url,

                                            "Account type":

                                                r?.registration

                                                    ?.account_type_required,

                                            "Client ID required":

                                                r?.registration

                                                    ?.requires_client_id,

                                            "Client secret required":

                                                r?.registration

                                                    ?.requires_client_secret,

                                            "Credential notes":

                                                r?.registration

                                                    ?.client_secret_notes,

                                        }}

                                    />

                                </Panel>

                                <Panel title="Redirect URI rules">

                                    <Rows

                                        data={{

                                            "Allowed schemes":

                                                r?.redirect_uri_rules

                                                    ?.allowed_schemes,

                                            "Localhost allowed":

                                                r?.redirect_uri_rules

                                                    ?.allows_localhost,

                                            "Wildcards permitted":

                                                r?.redirect_uri_rules

                                                    ?.wildcards_permitted,

                                            "Exact match":

                                                r?.redirect_uri_rules

                                                    ?.strict_exact_match,

                                            "Composio redirect":

                                                r?.redirect_uri_rules

                                                    ?.composio_redirect_uri_supported,

                                            "Standards notes":

                                                r?.redirect_uri_rules

                                                    ?.standards_notes,

                                        }}

                                    />

                                </Panel>

                                <Panel title="Scopes & permissions">

                                    <Items items={r?.scopes} />

                                </Panel>

                                <Panel title="Provider review & setup effort">

                                    <Rows

                                        data={{

                                            "Review required": r

                                                ? r.review_timeline

                                                      ?.review_required

                                                : guide?.provider_review

                                                      ?.review_required,

                                            "Review type":

                                                r?.review_timeline?.review_type,

                                            "Waiting period status":

                                                r?.review_timeline

                                                    ?.waiting_period_status,

                                            "Research wait estimate":

                                                r?.review_timeline

                                                    ?.estimated_waiting_period_days,

                                            "Guide wait minimum (days)":

                                                guide?.provider_review

                                                    ?.wait_days_min,

                                            "Guide wait maximum (days)":

                                                guide?.provider_review

                                                    ?.wait_days_max,

                                            "Review confidence":

                                                guide?.provider_review

                                                    ?.confidence,

                                            "Active effort minimum (minutes)":

                                                guide?.active_effort

                                                    ?.minutes_min,

                                            "Active effort maximum (minutes)":

                                                guide?.active_effort

                                                    ?.minutes_max,

                                            "Effort confidence":

                                                guide?.active_effort

                                                    ?.confidence,

                                        }}

                                    />

                                    <Items

                                        items={

                                            r?.review_timeline

                                                ?.review_requirements ||

                                            guide?.review_requirements

                                        }

                                    />

                                </Panel>

                                <Panel title="Human vs agent" warm>

                                    <h3>What a human must do</h3>

                                    <Items

                                        items={

                                            (

                                                r?.human_agent_boundary ||

                                                guide?.human_agent_boundary

                                            )?.what_human_must_do

                                        }

                                    />

                                    <h3>What an agent can automate</h3>

                                    <Items

                                        items={

                                            (

                                                r?.human_agent_boundary ||

                                                guide?.human_agent_boundary

                                            )?.what_agent_can_automate

                                        }

                                    />

                                </Panel>

                                <Panel title="Setup guide" wide>

                                    {guide?.setup_steps?.length ? (

                                        guide.setup_steps.map(

                                            (s: any, i: number) => (

                                                <details key={i} open={i === 0}>

                                                    <summary>

                                                        {s.step_number}.{" "}

                                                        {s.title}

                                                    </summary>

                                                    <p>{s.instructions}</p>

                                                    <p className="muted">

                                                        {human(s.path_type)} ·{" "}

                                                        {s.is_automated_by_agent ===

                                                        true

                                                            ? "Agent-automated"

                                                            : s.is_automated_by_agent ===

                                                                false

                                                              ? "Human action"

                                                              : "Responsibility unverified"}

                                                    </p>

                                                    {safe(s.portal_url) && (

                                                        <a

                                                            href={s.portal_url}

                                                            target="_blank"

                                                            rel="noopener noreferrer"

                                                        >

                                                            Open provider portal

                                                        </a>

                                                    )}

                                                    <p className="muted">

                                                        Source references:{" "}

                                                        {s.source_ids?.join(

                                                            ", "

                                                        ) || "Not supplied"}

                                                    </p>

                                                </details>

                                            )

                                        )

                                    ) : (

                                        <p className="muted">

                                            Investigate an application to load

                                            its documented setup steps.

                                        </p>

                                    )}

                                    <h3>Potential blockers</h3>

                                    <Items items={guide?.blockers} />

                                    {guide?.code_snippets &&

                                        Object.entries(guide.code_snippets)

                                            .filter(([, v]) => v)

                                            .map(([key, value]) => (

                                                <details key={key}>

                                                    <summary>

                                                        {human(key)}

                                                    </summary>

                                                    <pre>{String(value)}</pre>

                                                </details>

                                            ))}

                                </Panel>

                                <Panel title="Evidence & official sources" wide>

                                    {[

                                        ...(guide?.sources || []),

                                        ...(r?.sources || []),

                                    ].length ? (

                                        [

                                            ...(guide?.sources || []),

                                            ...(r?.sources || []),

                                        ].map((s: any, i: number) => (

                                            <details key={i}>

                                                <summary>

                                                    {s.title || s.id} ·{" "}

                                                    {human(

                                                        s.confidence ||

                                                            s.source_type

                                                    )}

                                                </summary>

                                                {safe(s.url) && (

                                                    <a

                                                        href={s.url}

                                                        target="_blank"

                                                        rel="noopener noreferrer"

                                                    >

                                                        {s.url}

                                                    </a>

                                                )}

                                                <p>

                                                    {s.evidence_excerpt ||

                                                        "No excerpt returned."}

                                                </p>

                                                <Rows

                                                    data={{

                                                        "Source ID": s.id,

                                                        "Page section":

                                                            s.page_section,

                                                        "Retrieval status":

                                                            s.retrieval_status,

                                                        "Retrieval date":

                                                            s.retrieval_date,

                                                        "HTTP status":

                                                            s.http_status_code,

                                                        Notes: s.notes,

                                                    }}

                                                />

                                            </details>

                                        ))

                                    ) : (

                                        <p className="muted">

                                            No sources loaded. Unknown

                                            information is not treated as

                                            confirmed.

                                        </p>

                                    )}

                                    {r?.field_provenance && (

                                        <details>

                                            <summary>

                                                Field-level provenance

                                            </summary>

                                            {Object.entries(

                                                r.field_provenance

                                            ).map(([k, v]: any) => (

                                                <div key={k}>

                                                    <h3>{human(k)}</h3>

                                                    <Rows data={v} />

                                                </div>

                                            ))}

                                        </details>

                                    )}

                                </Panel>

                            </div>

                        </>

                    )}

                    {tab === "catalog" && (

                        <>

                            <h1>Application catalogue.</h1>

                            <p

                                className="muted"

                                style={{ margin: "14px 0 24px" }}

                            >

                                Guides returned by the backend. No pre-filled

                                application claims.

                            </p>

                            <form

                                onSubmit={(e) => {

                                    e.preventDefault()

                                    loadCatalog()

                                }}

                            >

                                <input

                                    aria-label="Search catalogue"

                                    placeholder="Search applications"

                                    value={filter}

                                    onChange={(e) => setFilter(e.target.value)}

                                />

                                <select

                                    aria-label="Managed OAuth filter"

                                    value={managed}

                                    onChange={(e) => setManaged(e.target.value)}

                                >

                                    <option value="">All OAuth pathways</option>

                                    <option value="true">

                                        Managed available

                                    </option>

                                    <option value="false">

                                        Managed unavailable

                                    </option>

                                </select>

                                <select

                                    aria-label="Difficulty"

                                    value={difficulty}

                                    onChange={(e) =>

                                        setDifficulty(e.target.value)

                                    }

                                >

                                    <option value="">

                                        All difficulty levels

                                    </option>

                                    {[

                                        "VERY_EASY",

                                        "MODERATE",

                                        "COMPLEX",

                                        "ENTERPRISE_GATED",

                                    ].map((x) => (

                                        <option key={x}>{x}</option>

                                    ))}

                                </select>

                                <button

                                    className="action"

                                    disabled={catalogState === "loading"}

                                >

                                    Load catalogue

                                </button>

                            </form>

                            {catalogState === "loading" && (

                                <p role="status" className="message">

                                    Loading catalogue…

                                </p>

                            )}

                            {catalogError && (

                                <p role="alert" className="message">

                                    {catalogError}

                                </p>

                            )}

                            {catalogState === "ready" && !catalog.length && (

                                <p className="message">

                                    No guides match these filters.

                                </p>

                            )}

                            <div className="catalog">

                                {catalog.map((a) => (

                                    <article key={a.id} className="panel app">

                                        <IconTile name="plug" tile={T.peach} />

                                        <h2>{a.app_name}</h2>

                                        <p className="muted">{a.summary}</p>

                                        <span className="tag">

                                            {human(

                                                a.composio_status

                                                    ?.classification

                                            )}

                                        </span>

                                        <Rows

                                            data={{

                                                Difficulty: a.difficulty_rating,

                                                "Managed OAuth":

                                                    a.composio_status

                                                        ?.managed_oauth_available,

                                                Updated: a.updated_at,

                                            }}

                                        />

                                        <button

                                            className="action"

                                            onClick={() =>

                                                openGuide(a.slug || a.id)

                                            }

                                        >

                                            Open guide

                                        </button>

                                    </article>

                                ))}

                            </div>

                        </>

                    )}

                    {tab === "recent" && (

                        <>

                            <h1>Recent investigations.</h1>

                            <p

                                className="muted"

                                style={{ margin: "14px 0 24px" }}

                            >

                                Successful investigations from this session

                                only.

                            </p>

                            {!recent.length ? (

                                <p className="message">

                                    No investigations yet. Start with an

                                    application name.

                                </p>

                            ) : (

                                <div className="catalog">

                                    {recent.map((g) => (

                                        <button

                                            className="panel"

                                            key={g.id}

                                            onClick={() => openGuide(g.id)}

                                        >

                                            {g.name}

                                        </button>

                                    ))}

                                </div>

                            )}

                        </>

                    )}

                    {tab === "docs" && (

                        <>

                            <h1>Build with evidence.</h1>

                            <div className="grid" style={{ marginTop: 28 }}>

                                <Panel title="1. Investigate">

                                    <p className="sv-small">

                                        Enter an application name. An existing

                                        guide or a newly researched guide is

                                        returned by the backend. An unidentified

                                        application stays unverified.

                                    </p>

                                </Panel>

                                <Panel title="2. Research">

                                    <p className="sv-small">

                                        Request technical research to load

                                        endpoints, scopes, registration,

                                        redirect rules and field-level

                                        provenance. Partial and metadata-only

                                        results are shown explicitly.

                                    </p>

                                </Panel>

                                <Panel title="3. Understand uncertainty">

                                    <p className="sv-small">

                                        True confirms a requirement or

                                        capability. False confirms it is

                                        unsupported or not required. Null means

                                        unverified. An empty list is not

                                        evidence of absence.

                                    </p>

                                </Panel>

                                <Panel title="4. Share">

                                    <p className="sv-small">

                                        Create a permalink for a saved guide.

                                        The exact backend link is displayed,

                                        along with a query-based share view for

                                        this workspace.

                                    </p>

                                </Panel>

                                <Panel title="Local API connection" wide>

                                    <p className="sv-small">

                                        The frontend does not collect API

                                        secrets. The backend must run on the

                                        same machine as your local browser host.

                                        The supplied allowlist permits localhost

                                        ports 3000, 5173 and 5500, not Framer

                                        origins. Live workflows must be tested

                                        in an allowed local host.

                                    </p>

                                    <p

                                        className="muted"

                                        style={{ margin: "14px 0" }}

                                    >

                                        Configured API: {resolveBase(apiBase)}

                                    </p>

                                    <button

                                        className="action"

                                        disabled={!!busy}

                                        onClick={async () => {

                                            setHealth("checking")

                                            const d = await run(

                                                "Checking health",

                                                (s) => client.health(s)

                                            )

                                            if (d && d.status === "healthy") {

                                                setHealth("healthy")

                                            } else {

                                                setHealth("unavailable")

                                            }

                                        }}

                                    >

                                        Check API health

                                    </button>

                                    {error && (

                                        <p className="message" role="alert">

                                            {error}

                                        </p>

                                    )}

                                </Panel>

                            </div>

                        </>

                    )}

                </main>

            </div>

        </Section>

    )

}

addPropertyControls(OAuthWorkspace, {

    apiBase: {

        type: ControlType.String,

        title: "API Base URL",

        defaultValue: "",

    },

    embedded: {

        type: ControlType.Boolean,

        title: "Preview",

        defaultValue: false,

    },

    mode: {

        type: ControlType.Enum,

        title: "Initial View",

        options: ["investigate", "catalog", "docs"],

        defaultValue: "investigate",

    },

})



// Verified module path



// OAuth Navigator integration



// Final module verification.

