// SECUVANTA Product preview: "See your AI security posture at a glance." A big dashboard mockup in a sticker browser
// frame: sidebar, four metric cards, a risk-distribution chart, an AI assets table and a recent-activity panel.
// All numbers are fictional and the frame carries a visible "Demo data" tag. Metrics count up, bars grow and the
// activity feed highlights a new event every few seconds. Rows/metrics are edited as lines.
import * as React from "react"
import OAuthWorkspace from "./OAuth_Navigator/OAuthWorkspace.tsx"
import { addPropertyControls, ControlType } from "framer"
import { motion } from "framer-motion"
import {
    Section,
    Head,
    Reveal,
    Icon,
    CountUp,
    DemoTag,
    Sparkle,
    Planet,
    Stage,
    useTicker,
    useStill,
    lines,
    cells,
    headControls,
    toneControl,
    decorControl,
    T,
} from "./Kit.tsx"

const CSS = `
@container(max-width:1000px){.sv-pp .sv-dec{display:none}}
.sv-pp .frame{margin-top:64px;border-radius:26px;background:${T.white};border:1.5px solid ${T.ink};box-shadow:7px 8px 0 0 ${T.ink};overflow:hidden}
.sv-pp .chrome{display:flex;align-items:center;gap:8px;height:48px;padding:0 18px;border-bottom:1.5px solid ${T.ink};background:${T.cream}}
.sv-pp .chrome i{width:13px;height:13px;border-radius:50%;border:1.2px solid ${T.ink}}
.sv-pp .chrome .url{margin:0 auto;display:flex;align-items:center;gap:8px;height:28px;padding:0 14px;border-radius:999px;border:1px solid ${T.ink};background:${T.white};font-size:12px;font-weight:500;color:${T.body}}
/* dashboard canvas 1240 × 736 (phone: 640 × 1010) */
.sv-db{position:absolute;inset:0;display:grid;grid-template-columns:76px 1fr;font-family:var(--sans);color:${T.ink}}
.sv-db .side{display:flex;flex-direction:column;align-items:center;gap:10px;padding:18px 0;border-right:1.5px solid ${T.ink};background:${T.white}}
.sv-db .side span{display:grid;place-items:center;width:42px;height:42px;border-radius:13px;border:1px solid transparent}
.sv-db .side span.on{background:${T.butter};border-color:${T.ink};box-shadow:2px 2px 0 0 ${T.ink}}
.sv-db .main{display:grid;grid-template-rows:auto auto 1fr;gap:18px;padding:22px 24px;background:#FFFCF3;min-width:0}
.sv-db .bar{display:flex;align-items:center;justify-content:space-between}
.sv-db .bar h4{font-family:var(--display);font-weight:700;font-size:20px}
.sv-db .bar .r{display:flex;align-items:center;gap:10px}
.sv-db .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.sv-db .kpi{padding:16px 18px;border-radius:18px;border:1.5px solid ${T.ink};background:var(--c);box-shadow:3px 3px 0 0 ${T.ink}}
.sv-db .kpi small{display:block;font-size:12.5px;font-weight:600;color:${T.body}}
.sv-db .kpi b{display:block;margin-top:8px;font-family:var(--display);font-weight:800;font-size:38px;line-height:1}
.sv-db .kpi em{display:inline-flex;margin-top:10px;font-style:normal;font-size:11px;font-weight:600;padding:3px 8px;border-radius:999px;border:1px solid ${T.ink};background:${T.white}}
.sv-db .low{display:grid;grid-template-columns:270px minmax(0,1fr) 262px;gap:16px;min-height:0}
.sv-db .pn{display:flex;flex-direction:column;border-radius:18px;border:1.5px solid ${T.ink};background:${T.white};overflow:hidden;min-height:0}
.sv-db .pn .ph{display:flex;align-items:center;justify-content:space-between;padding:13px 16px;border-bottom:1.5px solid ${T.ink}}
.sv-db .pn .ph b{font-family:var(--display);font-weight:600;font-size:14px}
.sv-db .bars{display:grid;gap:14px;padding:18px 16px}
.sv-db .bars .lb{display:flex;justify-content:space-between;font-size:12.5px;font-weight:600;margin-bottom:6px}
.sv-db .bars .tr{height:14px;border-radius:999px;border:1px solid ${T.ink};background:${T.cream};overflow:hidden}
.sv-db .bars .tr i{display:block;height:100%;border-right:1px solid ${T.ink};transform-origin:0 50%}
.sv-db table{width:100%;border-collapse:collapse;font-size:12.5px}
.sv-db th{text-align:left;padding:10px 10px;font-size:10.5px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:${T.mute};border-bottom:1px solid rgba(0,0,0,.12)}
.sv-db td{padding:0 10px;height:44px;border-bottom:1px solid rgba(0,0,0,.08);white-space:nowrap}
.sv-db td.nm{font-weight:600}
.sv-db .pill{display:inline-flex;align-items:center;gap:5px;height:22px;padding:0 9px;border-radius:999px;border:1px solid ${T.ink};font-size:11px;font-weight:600;background:var(--c)}
.sv-db .act{display:grid;gap:8px;padding:12px}
.sv-db .ev{display:flex;gap:10px;padding:8px 10px;border-radius:12px;border:1px solid transparent;font-size:12px;line-height:1.35;transition:background-color .4s,border-color .4s}
.sv-db .ev.on{background:${T.butter};border-color:${T.ink}}
.sv-db .ev i{display:grid;place-items:center;width:26px;height:26px;border-radius:50%;border:1px solid ${T.ink};background:${T.white};flex-shrink:0}
.sv-db .ev small{display:block;color:${T.mute};font-size:11px;margin-top:2px}
.sv-db.cmp{grid-template-columns:1fr}
.sv-db.cmp .side{display:none}
.sv-db.cmp .main{grid-template-rows:auto auto auto auto}
.sv-db.cmp .kpis{grid-template-columns:repeat(2,1fr)}
.sv-db.cmp .low{grid-template-columns:1fr}
.sv-db.cmp .tbl{display:none}
.sv-db.cmp .bar .sv-chip{display:none}
.sv-pp .note{display:flex;justify-content:center;margin-top:22px}
.sv-pp .note p{font-size:13px;color:var(--mute);text-align:center}
`
const KPI_C = [T.butter, T.blush, T.lime, T.mint]
const RISK_C: Record<string, string> = {
    critical: T.critical,
    high: T.risk,
    medium: T.butter,
    low: T.lime,
}
const STATUS_C: Record<string, string> = {
    reviewed: T.lime,
    review: "#FFE1A6",
    blocked: T.blush,
    new: T.mint,
}
const ACT_IC = ["search", "alert", "shield-check", "check", "users"]

function Dashboard({
    title,
    kpis,
    risk,
    assets,
    activity,
    demoLabel,
    compact,
}: {
    compact?: boolean
    title: string
    kpis: string[][]
    risk: string[][]
    assets: string[][]
    activity: string[][]
    demoLabel: string
}) {
    const still = useStill()
    const [ref, on] = useTicker(Math.max(activity.length, 1), 2200)
    const max = Math.max(1, ...risk.map((r) => parseFloat(r[1]) || 0))
    return (
        <Stage w={compact ? 640 : 1240} h={compact ? 1010 : 736}>
            <div className={`sv-db${compact ? " cmp" : ""}`} aria-hidden="true">
                <div className="side">
                    {[
                        "layers",
                        "search",
                        "gauge",
                        "shield-check",
                        "activity",
                        "file",
                    ].map((ic, i) => (
                        <span key={ic} className={i === 0 ? "on" : undefined}>
                            <Icon name={ic} size={20} />
                        </span>
                    ))}
                </div>
                <div className="main">
                    <div className="bar">
                        <h4>{title}</h4>
                        <div className="r">
                            <DemoTag text={demoLabel} />
                            <span className="sv-chip white">Last 30 days</span>
                        </div>
                    </div>
                    <div className="kpis">
                        {kpis.slice(0, 4).map(([label, value, delta], i) => (
                            <div
                                className="kpi"
                                key={i}
                                style={{ ["--c" as any]: KPI_C[i] }}
                            >
                                <small>{label}</small>
                                <b>
                                    <CountUp value={value} />
                                </b>
                                {delta && <em>{delta}</em>}
                            </div>
                        ))}
                    </div>
                    <div className="low">
                        <div className="pn">
                            <div className="ph">
                                <b>Risk distribution</b>
                                <Icon name="gauge" size={16} />
                            </div>
                            <div className="bars">
                                {risk.map(([label, n, level], i) => {
                                    const w = `${((parseFloat(n) || 0) / max) * 100}%`
                                    const c =
                                        RISK_C[
                                            (level || label || "").toLowerCase()
                                        ] || T.peach
                                    return (
                                        <div key={i}>
                                            <div className="lb">
                                                <span>{label}</span>
                                                <span>{n}</span>
                                            </div>
                                            <div className="tr">
                                                {still ? (
                                                    <i
                                                        style={{
                                                            width: w,
                                                            background: c,
                                                        }}
                                                    />
                                                ) : (
                                                    <motion.i
                                                        style={{
                                                            width: w,
                                                            background: c,
                                                        }}
                                                        initial={{ scaleX: 0 }}
                                                        whileInView={{
                                                            scaleX: 1,
                                                        }}
                                                        viewport={{
                                                            once: true,
                                                        }}
                                                        transition={{
                                                            duration: 1,
                                                            delay:
                                                                0.2 + i * 0.12,
                                                            ease: [
                                                                0.22, 0.8, 0.3,
                                                                1,
                                                            ],
                                                        }}
                                                    />
                                                )}
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                        <div className="pn tbl">
                            <div className="ph">
                                <b>AI assets</b>
                                <span
                                    className="sv-chip white"
                                    style={{ height: 24 }}
                                >
                                    <Icon name="search" size={12} stroke={2} />{" "}
                                    Filter
                                </span>
                            </div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Asset</th>
                                        <th>Type</th>
                                        <th>Owner</th>
                                        <th>Risk</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {assets
                                        .slice(0, 7)
                                        .map(
                                            (
                                                [name, type, owner, rk, status],
                                                i
                                            ) => (
                                                <tr key={i}>
                                                    <td className="nm">
                                                        {name}
                                                    </td>
                                                    <td>{type}</td>
                                                    <td>{owner}</td>
                                                    <td>
                                                        <span
                                                            className="pill"
                                                            style={{
                                                                ["--c" as any]:
                                                                    T.white,
                                                            }}
                                                        >
                                                            <i
                                                                className="sv-dot"
                                                                style={{
                                                                    color:
                                                                        RISK_C[
                                                                            (
                                                                                rk ||
                                                                                ""
                                                                            ).toLowerCase()
                                                                        ] ||
                                                                        T.lime,
                                                                    width: 7,
                                                                    height: 7,
                                                                }}
                                                            />
                                                            {rk}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <span
                                                            className="pill"
                                                            style={{
                                                                ["--c" as any]:
                                                                    STATUS_C[
                                                                        (
                                                                            status ||
                                                                            ""
                                                                        )
                                                                            .toLowerCase()
                                                                            .split(
                                                                                " "
                                                                            )[0]
                                                                    ] ||
                                                                    T.cream,
                                                            }}
                                                        >
                                                            {status}
                                                        </span>
                                                    </td>
                                                </tr>
                                            )
                                        )}
                                </tbody>
                            </table>
                        </div>
                        <div className="pn" ref={ref as any}>
                            <div className="ph">
                                <b>Recent activity</b>
                                <i
                                    className="sv-dot live"
                                    style={{ color: T.verified }}
                                />
                            </div>
                            <div className="act">
                                {activity.slice(0, 5).map(([text, time], i) => (
                                    <div
                                        key={i}
                                        className={`ev${i === on ? " on" : ""}`}
                                    >
                                        <i>
                                            <Icon
                                                name={ACT_IC[i % ACT_IC.length]}
                                                size={13}
                                                stroke={2}
                                            />
                                        </i>
                                        <span>
                                            {text}
                                            <small>{time}</small>
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </Stage>
    )
}

export default function ProductPreview(props: any) {
    const {
        tone,
        eyebrow,
        title,
        body,
        dashTitle,
        url,
        kpis,
        risk,
        assets,
        activity,
        demoLabel,
        note,
        decor,
        sectionId,
    } = props
    const frameRef = React.useRef<HTMLDivElement>(null)
    const [compact, setCompact] = React.useState(false)
    React.useEffect(() => {
        const el = frameRef.current
        if (!el) return
        const fit = (w: number) => setCompact(w < 720)
        fit(el.getBoundingClientRect().width)
        if (typeof ResizeObserver === "undefined") return
        const ro = new ResizeObserver(([e]) => fit(e.contentRect.width))
        ro.observe(el)
        return () => ro.disconnect()
    }, [])
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-pp"
            css={CSS}
            label="Product preview"
        >
            {decor && (
                <div className="sv-dec" aria-hidden="true">
                    <div className="sv-plusfield" />
                    <Planet
                        size={110}
                        fill={T.butter}
                        style={{ left: "3%", top: 140 }}
                        className="sv-bob"
                    />
                    <Planet
                        size={80}
                        fill={T.teal}
                        ring={false}
                        style={{ right: "5%", top: 210 }}
                        className="sv-bob"
                    />
                    <Sparkle
                        size={30}
                        fill={T.white}
                        style={{ right: "16%", top: 96 }}
                        delay={0.7}
                    />
                </div>
            )}
            <div className="sv-wrap">
                <Head
                    eyebrow={eyebrow}
                    title={title}
                    body={body}
                    align="center"
                />
                <Reveal delay={0.1} y={40}>
                    <div className="frame" ref={frameRef}>
                        <div className="chrome" aria-hidden="true">
                            <i style={{ background: T.orange }} />
                            <i style={{ background: T.butter }} />
                            <i style={{ background: T.lime }} />
                            <span className="url">
                                <Icon name="lock" size={12} stroke={2} />
                                {url}
                            </span>
                        </div>
                        <div style={{ padding: 24, background: T.cream }}>
                            <OAuthWorkspace embedded />
                        </div>
                    </div>
                </Reveal>
                {note && (
                    <div className="note">
                        <p>{note}</p>
                    </div>
                )}
            </div>
        </Section>
    )
}

addPropertyControls(ProductPreview, {
    tone: toneControl("peach"),
    ...headControls({
        eyebrow: "Product preview",
        title: "See your AI security posture *at a glance.*",
        body: "Bring asset discovery, risk findings, and policy status into one clear operational view. Help teams focus on the issues that matter most.",
    }),
    dashTitle: {
        type: ControlType.String,
        title: "Dashboard title",
        defaultValue: "AI security posture",
    },
    url: {
        type: ControlType.String,
        title: "Browser URL",
        defaultValue: "app.secuvanta.example/overview",
    },
    kpis: {
        type: ControlType.String,
        title: "Metrics",
        displayTextArea: true,
        description: "4 lines: Label | value | small note",
        defaultValue:
            "AI Assets | 248 | +18 this month\nHigh-Risk Findings | 12 | 3 new\nPolicies Active | 36 | 4 drafts\nAssets Reviewed | 92% | +6 pts",
    },
    risk: {
        type: ControlType.String,
        title: "Risk distribution",
        displayTextArea: true,
        description:
            "One per line: Label | count | critical, high, medium or low",
        defaultValue:
            "Critical | 2 | critical\nHigh | 10 | high\nMedium | 27 | medium\nLow | 64 | low",
    },
    assets: {
        type: ControlType.String,
        title: "Assets table",
        displayTextArea: true,
        description:
            "Up to 7, one per line: Asset | Type | Owner | Risk | Status (Reviewed, Review, Blocked, New)",
        defaultValue:
            "Support copilot | Model | CX team | Low | Reviewed\nSales research agent | Agent | RevOps | High | Review\nDocs summarizer | App | Legal | Medium | Reviewed\nCRM connector | Integration | IT | Critical | Blocked\nCode assistant | Model | Platform | Low | Reviewed\nVector store | Data | Data eng | Medium | New",
    },
    activity: {
        type: ControlType.String,
        title: "Activity feed",
        displayTextArea: true,
        description: "Up to 5, one per line: Event | time",
        defaultValue:
            "New agent discovered in Sales workspace | 2 min ago\nHigh-risk finding: broad CRM access | 14 min ago\nPolicy “Mask PII in prompts” applied | 1 h ago\nDocs summarizer marked as reviewed | 3 h ago\nOwner assigned to Vector store | Yesterday",
    },
    demoLabel: {
        type: ControlType.String,
        title: "Demo data tag",
        defaultValue: "Demo data",
        description: "Keep this visible: the numbers are illustrative.",
    },
    note: {
        type: ControlType.String,
        title: "Footnote",
        defaultValue: "Illustrative interface with fictional demo data.",
    },
    decor: decorControl,
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "preview",
    },
})

// OAuth Navigator integration

// Shared control types verified.
