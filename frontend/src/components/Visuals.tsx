// SECUVANTA Visuals: the illustration library used by the inner-page sections (PageHero, Split). Every visual is a
// sticker-style product fragment in the Pluto look (white cards, ink outlines, hard shadows, pastel fills) drawn on a
// fixed design canvas that scales to the available width. All numbers and names are fictional demo content and the
// whole illustration is aria-hidden; sections pick one with the "Visual" control.
// This file is a helper module. It is not meant to be placed on the canvas.
import * as React from "react"
import { OAuthDiagram } from "./OAuth_Navigator/OAuthDiagram.tsx"
import {
    Icon,
    IconTile,
    Pop,
    Packet,
    Stage,
    Sparkle,
    Planet,
    Orbit,
    useTicker,
    T,
} from "./Kit.tsx"

export const VIS_CSS = `
.vz{position:absolute;inset:0;font-family:var(--sans);color:${T.ink}}
.vz-p{position:absolute;background:${T.white};border:1.5px solid ${T.ink};border-radius:18px;box-shadow:4px 4px 0 0 ${T.ink};overflow:hidden}
.vz-h{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:10px 14px;border-bottom:1.5px solid ${T.ink};background:var(--c,${T.cream});font-family:var(--display);font-weight:600;font-size:13px;white-space:nowrap}
.vz-r{display:flex;align-items:center;gap:8px;padding:0 14px;height:38px;border-top:1px solid rgba(0,0,0,.08);font-size:12.5px;white-space:nowrap}
.vz-r:first-of-type{border-top:0}
.vz-r b{font-weight:600}
.vz-r .end{margin-left:auto}
.vz-pill{display:inline-flex;align-items:center;gap:5px;height:22px;padding:0 9px;border-radius:999px;border:1px solid ${T.ink};font-size:11px;font-weight:600;background:var(--c,${T.white});white-space:nowrap}
.vz-ic{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;border:1px solid ${T.ink};background:var(--c,${T.cream});flex-shrink:0}
.vz-bar{height:10px;border-radius:999px;border:1px solid ${T.ink};background:${T.cream};overflow:hidden}
.vz-bar i{display:block;height:100%;background:var(--c,${T.lime});border-right:1px solid ${T.ink}}
.vz-av{display:grid;place-items:center;width:24px;height:24px;border-radius:50%;border:1px solid ${T.ink};background:var(--c,${T.peach});font-size:9.5px;font-weight:700;flex-shrink:0}
.vz-node{position:absolute;translate:-50% -50%;display:flex;align-items:center;gap:8px;height:44px;padding:0 14px 0 5px;border-radius:999px;background:${T.white};border:1.5px solid ${T.ink};box-shadow:3px 3px 0 0 ${T.ink};font-weight:600;font-size:13px;white-space:nowrap;z-index:2}
.vz-node .sv-ico{border-radius:50%!important}
.vz-dot{position:absolute;translate:-50% -50%;display:grid;place-items:center;width:54px;height:54px;border-radius:50%;background:${T.white};border:1.5px solid ${T.ink};box-shadow:2.5px 2.5px 0 0 ${T.ink};z-index:2}
.vz-ok{position:absolute;right:-6px;top:-6px;display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:${T.lime};border:1.2px solid ${T.ink}}
.vz-cap{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:${T.mute}}
.vz-big{font-family:var(--display);font-weight:800;line-height:1}
.vz-arrow{position:absolute;display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:${T.butter};border:1.5px solid ${T.ink};z-index:3}
.vz-chk{display:flex;align-items:center;gap:8px;font-size:12.5px;padding:6px 0}
.vz-chk i{display:grid;place-items:center;width:18px;height:18px;border-radius:5px;border:1.2px solid ${T.ink};background:var(--c,${T.white})}
`

const SEV: Record<string, string> = {
    Critical: T.critical,
    High: T.risk,
    Medium: T.butter,
    Low: T.lime,
}
const sev = (s: string) => (
    <span className="vz-pill">
        <i
            className="sv-dot"
            style={{ color: SEV[s] || T.lime, width: 7, height: 7 }}
        />
        {s}
    </span>
)
const Panel = ({
    x,
    y,
    w,
    h,
    title,
    c,
    icon,
    children,
    delay = 0,
    rot = 0,
    right,
}: {
    x: number
    y: number
    w: number
    h?: number
    title?: string
    c?: string
    icon?: string
    children?: React.ReactNode
    delay?: number
    rot?: number
    right?: React.ReactNode
}) => (
    <Pop
        delay={delay}
        rotate={rot ? rot * 2 : -4}
        style={{ position: "absolute", left: x, top: y, width: w, zIndex: 2 }}
    >
        <div
            className="vz-p"
            style={{
                position: "relative",
                height: h,
                rotate: rot ? `${rot}deg` : undefined,
            }}
        >
            {title && (
                <div className="vz-h" style={{ ["--c" as any]: c || T.cream }}>
                    <span
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                        }}
                    >
                        {icon && <Icon name={icon} size={15} stroke={2} />}
                        {title}
                    </span>
                    {right}
                </div>
            )}
            {children}
        </div>
    </Pop>
)

/* ---------------------------------------------------------------- hero visuals (1040 × 400) */
function Pipeline() {
    const steps: [string, string, string][] = [
        ["Discovery", "search", T.butter],
        ["Assessment", "gauge", T.peach],
        ["Protection", "shield-check", T.lime],
        ["Governance", "scale", T.pink],
    ]
    const [ref, on] = useTicker(4, 1600)
    return (
        <div ref={ref} className="vz">
            <svg
                width="1040"
                height="400"
                style={{ position: "absolute", inset: 0, overflow: "visible" }}
                aria-hidden="true"
            >
                <path
                    d="M120 200 H920"
                    stroke={T.ink}
                    strokeWidth="1.5"
                    strokeDasharray="6 8"
                    className="sv-flow"
                />
                <Packet d="M120 200 H920" dur={4} color={T.orange} r={6} />
            </svg>
            {steps.map(([t, ic, c], i) => (
                <Panel
                    key={t}
                    x={i * 262}
                    y={i % 2 ? 110 : 60}
                    w={232}
                    title={t}
                    icon={ic}
                    c={c}
                    delay={0.1 + i * 0.12}
                    rot={i % 2 ? 1.5 : -1.5}
                    right={
                        <span
                            className="vz-pill"
                            style={{
                                ["--c" as any]: i <= on ? T.lime : T.white,
                            }}
                        >
                            {i <= on ? "Done" : "Next"}
                        </span>
                    }
                >
                    {i === 0 && (
                        <>
                            <div className="vz-r">
                                <Icon name="cpu" size={14} />
                                Support model
                                <span
                                    className="end vz-pill"
                                    style={{ ["--c" as any]: T.lime }}
                                >
                                    New
                                </span>
                            </div>
                            <div className="vz-r">
                                <Icon name="bot" size={14} />
                                Sales agent
                            </div>
                            <div className="vz-r">
                                <Icon name="plug" size={14} />
                                CRM connector
                            </div>
                        </>
                    )}
                    {i === 1 && (
                        <div style={{ padding: 14, display: "grid", gap: 10 }}>
                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "flex-end",
                                    gap: 8,
                                }}
                            >
                                <span
                                    className="vz-big"
                                    style={{ fontSize: 34 }}
                                >
                                    72
                                </span>
                                <span className="vz-cap">risk score</span>
                            </div>
                            <div
                                style={{
                                    display: "flex",
                                    gap: 6,
                                    flexWrap: "wrap",
                                }}
                            >
                                {sev("High")}
                                {sev("Medium")}
                            </div>
                        </div>
                    )}
                    {i === 2 && (
                        <>
                            <div className="vz-r">
                                Mask PII
                                <span
                                    className="end vz-pill"
                                    style={{ ["--c" as any]: T.lime }}
                                >
                                    On
                                </span>
                            </div>
                            <div className="vz-r">
                                Agent write access
                                <span
                                    className="end vz-pill"
                                    style={{ ["--c" as any]: T.blush }}
                                >
                                    Blocked
                                </span>
                            </div>
                            <div className="vz-r">
                                Model allow-list
                                <span
                                    className="end vz-pill"
                                    style={{ ["--c" as any]: T.lime }}
                                >
                                    On
                                </span>
                            </div>
                        </>
                    )}
                    {i === 3 && (
                        <div style={{ padding: 14, display: "grid", gap: 10 }}>
                            <div className="vz-cap">Policy coverage</div>
                            <div className="vz-bar">
                                <i style={{ width: "92%" }} />
                            </div>
                            <div style={{ display: "flex", gap: 6 }}>
                                <span className="vz-pill">Audit log on</span>
                                <span className="vz-pill">36 policies</span>
                            </div>
                        </div>
                    )}
                </Panel>
            ))}
        </div>
    )
}

function Roles() {
    const roles: [string, string, string, string][] = [
        ["Security", "shield", T.peach, "12 findings to triage"],
        ["IT Operations", "server", T.butter, "9 tools need an owner"],
        ["AI Engineering", "code", T.lime, "3 releases in review"],
    ]
    return (
        <div className="vz">
            <svg
                width="1040"
                height="400"
                style={{ position: "absolute", inset: 0, overflow: "visible" }}
                aria-hidden="true"
            >
                {[170, 520, 870].map((x, i) => (
                    <g key={x}>
                        <path
                            d={`M${x} 196 V300`}
                            stroke={T.ink}
                            strokeWidth="1.5"
                            strokeDasharray="5 7"
                            className="sv-flow"
                        />
                        <Packet
                            d={`M${x} 196 V300`}
                            dur={2 + i * 0.4}
                            delay={i * 0.5}
                            color={T.lime}
                        />
                    </g>
                ))}
            </svg>
            {roles.map(([t, ic, c, sub], i) => (
                <Panel
                    key={t}
                    x={60 + i * 350}
                    y={20}
                    w={220}
                    title={t}
                    icon={ic}
                    c={c}
                    delay={0.1 + i * 0.12}
                    rot={i === 1 ? 0 : i ? 2 : -2}
                >
                    <div style={{ padding: 14, display: "grid", gap: 10 }}>
                        <div style={{ fontSize: 13, fontWeight: 600 }}>
                            {sub}
                        </div>
                        <div className="vz-bar" style={{ ["--c" as any]: c }}>
                            <i style={{ width: `${60 + i * 12}%` }} />
                        </div>
                        <div style={{ display: "flex", gap: 4 }}>
                            {["AK", "MR", "JS"].map((a, k) => (
                                <span
                                    key={a}
                                    className="vz-av"
                                    style={{
                                        ["--c" as any]: [
                                            T.peach,
                                            T.mint,
                                            T.pink,
                                        ][k],
                                    }}
                                >
                                    {a}
                                </span>
                            ))}
                        </div>
                    </div>
                </Panel>
            ))}
            <Pop
                delay={0.5}
                rotate={0}
                style={{
                    position: "absolute",
                    left: 80,
                    top: 300,
                    width: 880,
                    zIndex: 2,
                }}
            >
                <div
                    className="vz-p"
                    style={{
                        position: "relative",
                        height: 74,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: 14,
                        background: T.ink,
                        color: T.white,
                        boxShadow: `5px 5px 0 0 ${T.orange}`,
                    }}
                >
                    <IconTile
                        name="layers"
                        tile={T.butter}
                        size={42}
                        icon={20}
                    />
                    <span
                        style={{
                            fontFamily: "var(--display)",
                            fontWeight: 700,
                            fontSize: 18,
                        }}
                    >
                        Shared security layer
                    </span>
                    <span
                        className="vz-pill"
                        style={{ ["--c" as any]: T.lime, color: T.ink }}
                    >
                        Risks · Controls · Ownership
                    </span>
                </div>
            </Pop>
        </div>
    )
}

function Editorial() {
    return (
        <div className="vz">
            <Orbit
                w={560}
                h={230}
                style={{ left: 240, top: 90, transform: "rotate(-10deg)" }}
                dashed
            />
            <Pop
                delay={0.1}
                rotate={-8}
                style={{
                    position: "absolute",
                    left: 340,
                    top: 10,
                    width: 300,
                    zIndex: 3,
                }}
            >
                <div
                    className="vz-p"
                    style={{
                        position: "relative",
                        height: 370,
                        rotate: "-3deg",
                        background: T.butter,
                        padding: 26,
                        display: "flex",
                        flexDirection: "column",
                        gap: 14,
                    }}
                >
                    <span
                        className="vz-pill"
                        style={{ alignSelf: "flex-start" }}
                    >
                        Security report
                    </span>
                    <div className="vz-big" style={{ fontSize: 30 }}>
                        The State of AI Security
                    </div>
                    <svg
                        viewBox="0 0 240 140"
                        style={{ width: "100%", marginTop: "auto" }}
                        aria-hidden="true"
                    >
                        {[
                            [40, 40],
                            [120, 24],
                            [200, 50],
                            [70, 110],
                            [170, 112],
                            [120, 74],
                        ].map(([x, y], i) => (
                            <g key={i}>
                                <line
                                    x1="120"
                                    y1="74"
                                    x2={x}
                                    y2={y}
                                    stroke={T.ink}
                                    strokeWidth="1.2"
                                />
                                <circle
                                    cx={x}
                                    cy={y}
                                    r={i === 5 ? 14 : 9}
                                    fill={
                                        i === 5
                                            ? T.white
                                            : [
                                                  T.peach,
                                                  T.lime,
                                                  T.pink,
                                                  T.mint,
                                                  T.coral,
                                              ][i]
                                    }
                                    stroke={T.ink}
                                    strokeWidth="1.2"
                                />
                            </g>
                        ))}
                    </svg>
                </div>
            </Pop>
            <Panel
                x={60}
                y={70}
                w={240}
                title="Exposure by type"
                icon="activity"
                c={T.peach}
                delay={0.25}
                rot={-2}
            >
                <div style={{ padding: 14, display: "grid", gap: 9 }}>
                    {[
                        ["Agents", 78, T.risk],
                        ["Models", 54, T.butter],
                        ["APIs", 36, T.lime],
                    ].map(([l, v, c]: any) => (
                        <div key={l}>
                            <div
                                style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    fontSize: 12,
                                    fontWeight: 600,
                                    marginBottom: 4,
                                }}
                            >
                                <span>{l}</span>
                                <span>{v}%</span>
                            </div>
                            <div
                                className="vz-bar"
                                style={{ ["--c" as any]: c }}
                            >
                                <i style={{ width: `${v}%` }} />
                            </div>
                        </div>
                    ))}
                </div>
            </Panel>
            <Panel
                x={700}
                y={150}
                w={260}
                title="Reading list"
                icon="file"
                c={T.mint}
                delay={0.35}
                rot={2}
            >
                {[
                    "Shadow AI basics",
                    "Agent tool access",
                    "Risk frameworks",
                ].map((t, i) => (
                    <div className="vz-r" key={t}>
                        <span
                            className="vz-ic"
                            style={{
                                ["--c" as any]: [T.peach, T.lime, T.pink][i],
                                width: 22,
                                height: 22,
                            }}
                        >
                            <Icon name="file" size={11} />
                        </span>
                        {t}
                    </div>
                ))}
            </Panel>
            <Sparkle
                size={30}
                fill={T.pink}
                style={{ left: 660, top: 40 }}
                delay={0.6}
            />
        </div>
    )
}

function Ecosystem() {
    const C: [number, number] = [520, 205]
    const nodes: [number, number, string][] = [
        [250, 90, "cpu"],
        [790, 90, "bot"],
        [180, 250, "plug"],
        [860, 250, "database"],
        [330, 350, "users"],
        [710, 350, "layers"],
        [520, 30, "code"],
        [960, 170, "server"],
        [80, 150, "key"],
    ]
    return (
        <div className="vz">
            <div
                style={{
                    position: "absolute",
                    left: C[0] - 260,
                    top: C[1] - 200,
                    width: 520,
                    height: 400,
                    borderRadius: "50%",
                    background:
                        "radial-gradient(closest-side, rgba(255,255,120,.9), rgba(255,255,120,0))",
                }}
            />
            <Orbit
                w={640}
                h={260}
                style={{ left: C[0] - 320, top: C[1] - 130 }}
                dashed
            />
            <Orbit
                w={900}
                h={360}
                style={{ left: C[0] - 450, top: C[1] - 180 }}
            />
            <svg
                width="1040"
                height="400"
                style={{ position: "absolute", inset: 0, overflow: "visible" }}
                aria-hidden="true"
            >
                {nodes.map(([x, y], i) => (
                    <g key={i}>
                        <path
                            d={`M${C[0]} ${C[1]} L${x} ${y}`}
                            stroke={T.ink}
                            strokeWidth="1.2"
                            strokeOpacity=".7"
                        />
                        <Packet
                            d={`M${x} ${y} L${C[0]} ${C[1]}`}
                            dur={2.2 + (i % 4) * 0.4}
                            delay={i * 0.3}
                            color={T.lime}
                            r={4}
                        />
                    </g>
                ))}
            </svg>
            <div
                style={{
                    position: "absolute",
                    left: C[0],
                    top: C[1],
                    translate: "-50% -50%",
                    width: 140,
                    height: 140,
                    borderRadius: "50%",
                    background: T.butter,
                    border: `1.5px solid ${T.ink}`,
                    boxShadow: `5px 5px 0 0 ${T.ink}`,
                    display: "grid",
                    placeItems: "center",
                    zIndex: 3,
                }}
            >
                <span
                    style={{
                        display: "grid",
                        placeItems: "center",
                        width: 64,
                        height: 64,
                        borderRadius: "50%",
                        background: T.white,
                        border: `1.5px solid ${T.ink}`,
                    }}
                >
                    <Icon name="shield-check" size={30} />
                </span>
            </div>
            {nodes.map(([x, y, ic], i) => (
                <div
                    key={i}
                    style={{ position: "absolute", left: x, top: y, zIndex: 2 }}
                >
                    <Pop delay={0.05 * i} rotate={0}>
                        <span
                            className="vz-dot sv-bob"
                            style={{
                                left: 0,
                                top: 0,
                                ["--bd" as any]: `${6 + (i % 3)}s`,
                                ["--fr" as any]: "0deg",
                                background: [
                                    T.white,
                                    T.peach,
                                    T.lime,
                                    T.pink,
                                    T.mint,
                                ][i % 5],
                            }}
                        >
                            <Icon name={ic} size={22} />
                        </span>
                    </Pop>
                </div>
            ))}
        </div>
    )
}

function Posture() {
    return (
        <div className="vz">
            <svg
                width="1040"
                height="400"
                style={{ position: "absolute", inset: 0, overflow: "visible" }}
                aria-hidden="true"
            >
                {[
                    [150, 90],
                    [140, 300],
                    [900, 80],
                    [920, 310],
                ].map(([x, y], i) => (
                    <path
                        key={i}
                        d={`M520 200 L${x} ${y}`}
                        stroke={T.ink}
                        strokeWidth="1.2"
                        strokeDasharray="5 7"
                        className="sv-flow"
                    />
                ))}
            </svg>
            {[
                [150, 90, "cpu"],
                [140, 300, "bot"],
                [900, 80, "plug"],
                [920, 310, "database"],
            ].map(([x, y, ic]: any, i) => (
                <div key={i} style={{ position: "absolute", left: x, top: y }}>
                    <Pop delay={0.1 * i} rotate={0}>
                        <span className="vz-dot" style={{ left: 0, top: 0 }}>
                            <Icon name={ic} size={22} />
                            <span className="vz-ok">
                                <Icon name="check" size={11} stroke={2.8} />
                            </span>
                        </span>
                    </Pop>
                </div>
            ))}
            <Panel
                x={300}
                y={40}
                w={440}
                title="AI security posture"
                icon="layers"
                c={T.butter}
                delay={0.2}
                right={<span className="vz-pill">Sample data</span>}
            >
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(3,1fr)",
                        gap: 10,
                        padding: 14,
                    }}
                >
                    {[
                        ["AI assets", "248", T.butter],
                        ["High risk", "12", T.blush],
                        ["Reviewed", "92%", T.lime],
                    ].map(([l, v, c]) => (
                        <div
                            key={l}
                            style={{
                                padding: 12,
                                border: `1.2px solid ${T.ink}`,
                                borderRadius: 14,
                                background: c,
                            }}
                        >
                            <div className="vz-cap" style={{ color: T.body }}>
                                {l}
                            </div>
                            <div
                                className="vz-big"
                                style={{ fontSize: 28, marginTop: 6 }}
                            >
                                {v}
                            </div>
                        </div>
                    ))}
                </div>
                <div
                    className="vz-r"
                    style={{ borderTop: "1px solid rgba(0,0,0,.1)" }}
                >
                    <Icon name="alert" size={14} />
                    Broad CRM access<span className="end">{sev("High")}</span>
                </div>
                <div className="vz-r">
                    <Icon name="check" size={14} />
                    Docs summarizer reviewed
                    <span
                        className="end vz-pill"
                        style={{ ["--c" as any]: T.lime }}
                    >
                        Done
                    </span>
                </div>
            </Panel>
        </div>
    )
}

/* ---------------------------------------------------------------- split visuals (600 × 460) */
function Inventory() {
    const [ref, on] = useTicker(3, 1500)
    const rows: [string, string, string, string, string][] = [
        ["Support copilot", "Model", "CX", "Prod", "Reviewed"],
        ["Sales research agent", "Agent", "RevOps", "Prod", "Discovered"],
        ["Docs summarizer", "App", "Legal", "Staging", "Reviewed"],
        ["CRM connector", "Integration", "IT", "Prod", "Discovered"],
        ["Vector store", "Data", "Data", "Dev", "Reviewed"],
    ]
    const filters = ["All", "Models", "Agents", "Integrations"]
    return (
        <div ref={ref} className="vz">
            <Panel
                x={20}
                y={20}
                w={560}
                title="AI asset inventory"
                icon="search"
                c={T.butter}
                delay={0.1}
                right={<span className="vz-pill">248 assets</span>}
            >
                <div
                    style={{
                        display: "flex",
                        gap: 6,
                        padding: "10px 14px",
                        borderBottom: "1px solid rgba(0,0,0,.08)",
                    }}
                >
                    {filters.map((f, i) => (
                        <span
                            key={f}
                            className="vz-pill"
                            style={{
                                ["--c" as any]: i === on ? T.ink : T.white,
                                color: i === on ? T.white : T.ink,
                            }}
                        >
                            {f}
                        </span>
                    ))}
                </div>
                {rows.map(([n, t, o, env, st], i) => (
                    <div
                        className="vz-r"
                        key={n}
                        style={{
                            display: "grid",
                            gridTemplateColumns: "1.6fr .9fr .7fr .7fr 1fr",
                            gap: 8,
                        }}
                    >
                        <b
                            style={{
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                            }}
                        >
                            {n}
                        </b>
                        <span>{t}</span>
                        <span
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 6,
                            }}
                        >
                            <span
                                className="vz-av"
                                style={{
                                    ["--c" as any]: [
                                        T.peach,
                                        T.mint,
                                        T.pink,
                                        T.lime,
                                        T.butter,
                                    ][i],
                                }}
                            >
                                {o.slice(0, 2).toUpperCase()}
                            </span>
                        </span>
                        <span
                            className="vz-pill"
                            style={{ justifySelf: "start" }}
                        >
                            {env}
                        </span>
                        <span
                            className="vz-pill"
                            style={{
                                justifySelf: "start",
                                ["--c" as any]:
                                    st === "Reviewed" ? T.lime : "#FFE1A6",
                            }}
                        >
                            {st}
                        </span>
                    </div>
                ))}
            </Panel>
            <Panel
                x={330}
                y={330}
                w={240}
                title="Environments"
                icon="server"
                c={T.mint}
                delay={0.35}
                rot={2}
            >
                <div
                    style={{
                        display: "flex",
                        gap: 8,
                        padding: 14,
                        alignItems: "center",
                    }}
                >
                    {["Prod", "Staging", "Dev"].map((e, i) => (
                        <React.Fragment key={e}>
                            {i > 0 && (
                                <span
                                    style={{
                                        flex: 1,
                                        height: 1.5,
                                        background: T.ink,
                                    }}
                                />
                            )}
                            <span
                                className="vz-pill"
                                style={{
                                    ["--c" as any]: [T.peach, T.butter, T.lime][
                                        i
                                    ],
                                }}
                            >
                                {e}
                            </span>
                        </React.Fragment>
                    ))}
                </div>
            </Panel>
        </div>
    )
}

function RiskDrawer() {
    return (
        <div className="vz">
            <Panel
                x={20}
                y={40}
                w={250}
                title="Findings"
                icon="alert"
                c={T.peach}
                delay={0.1}
                rot={-1.5}
            >
                {[
                    ["Broad CRM access", "Critical"],
                    ["PII in prompts", "High"],
                    ["Unpinned model", "Medium"],
                    ["Stale API key", "High"],
                ].map(([t, s], i) => (
                    <div
                        className="vz-r"
                        key={t}
                        style={{ background: i === 0 ? T.cream : undefined }}
                    >
                        <b>{t}</b>
                        <span className="end">{sev(s)}</span>
                    </div>
                ))}
            </Panel>
            <Panel
                x={250}
                y={10}
                w={330}
                title="Broad CRM access"
                icon="key"
                c={T.butter}
                delay={0.25}
                right={sev("Critical")}
            >
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 14,
                        padding: 14,
                        borderBottom: "1px solid rgba(0,0,0,.08)",
                    }}
                >
                    <div
                        style={{
                            display: "grid",
                            placeItems: "center",
                            width: 74,
                            height: 74,
                            borderRadius: "50%",
                            border: `1.5px solid ${T.ink}`,
                            background: `conic-gradient(${T.critical} 0 86%, ${T.cream} 86% 100%)`,
                        }}
                    >
                        <span
                            style={{
                                display: "grid",
                                placeItems: "center",
                                width: 54,
                                height: 54,
                                borderRadius: "50%",
                                background: T.white,
                                border: `1.2px solid ${T.ink}`,
                            }}
                            className="vz-big"
                        >
                            86
                        </span>
                    </div>
                    <div style={{ display: "grid", gap: 4, fontSize: 12.5 }}>
                        <span className="vz-cap">Affected asset</span>
                        <b>Sales research agent</b>
                        <span style={{ color: T.mute }}>
                            Write access to all CRM records
                        </span>
                    </div>
                </div>
                <div style={{ padding: "8px 14px 14px" }}>
                    <div className="vz-cap" style={{ marginBottom: 4 }}>
                        Remediation
                    </div>
                    {[
                        ["Scope token to read-only", true],
                        ["Assign an owner", true],
                        ["Apply CRM access policy", false],
                        ["Re-run assessment", false],
                    ].map(([t, d]: any) => (
                        <div className="vz-chk" key={t}>
                            <i style={{ ["--c" as any]: d ? T.lime : T.white }}>
                                {d && (
                                    <Icon name="check" size={11} stroke={3} />
                                )}
                            </i>
                            {t}
                        </div>
                    ))}
                </div>
            </Panel>
        </div>
    )
}

function Policy() {
    const [ref, on] = useTicker(2, 2000)
    return (
        <div ref={ref} className="vz">
            <svg
                width="600"
                height="460"
                style={{ position: "absolute", inset: 0, overflow: "visible" }}
                aria-hidden="true"
            >
                <path
                    d="M200 200 H240 M380 200 H410"
                    stroke={T.ink}
                    strokeWidth="1.5"
                    strokeDasharray="5 6"
                    className="sv-flow"
                />
            </svg>
            <Panel
                x={0}
                y={70}
                w={200}
                title="Conditions"
                icon="search"
                c={T.peach}
                delay={0.1}
            >
                {[
                    "Data contains PII",
                    "Actor is an agent",
                    "Target is CRM",
                ].map((t) => (
                    <div className="vz-r" key={t} style={{ fontSize: 12 }}>
                        <span
                            className="vz-ic"
                            style={{ width: 20, height: 20 }}
                        >
                            <Icon name="plus" size={10} />
                        </span>
                        {t}
                    </div>
                ))}
            </Panel>
            <Panel
                x={235}
                y={110}
                w={150}
                title="Rule"
                icon="route"
                c={T.butter}
                delay={0.2}
            >
                <div
                    style={{
                        padding: 14,
                        display: "grid",
                        gap: 8,
                        fontSize: 12,
                        fontWeight: 600,
                    }}
                >
                    <span
                        className="vz-pill"
                        style={{
                            ["--c" as any]: T.ink,
                            color: T.white,
                            justifySelf: "start",
                        }}
                    >
                        IF all match
                    </span>
                    <span>then mask data</span>
                    <span>and request review</span>
                </div>
            </Panel>
            <Panel
                x={410}
                y={40}
                w={180}
                title="Outcome"
                icon="shield-check"
                c={T.lime}
                delay={0.3}
            >
                <div style={{ padding: 12, display: "grid", gap: 8 }}>
                    <div
                        style={{
                            padding: 10,
                            borderRadius: 12,
                            border: `1.2px solid ${T.ink}`,
                            background: on === 0 ? T.lime : T.white,
                            fontSize: 12,
                            fontWeight: 600,
                            transition: "background-color .4s",
                        }}
                    >
                        ✓ Allowed · masked
                    </div>
                    <div
                        style={{
                            padding: 10,
                            borderRadius: 12,
                            border: `1.2px solid ${T.ink}`,
                            background: on === 1 ? T.blush : T.white,
                            fontSize: 12,
                            fontWeight: 600,
                            transition: "background-color .4s",
                        }}
                    >
                        ✕ Blocked · review
                    </div>
                </div>
            </Panel>
            <Panel
                x={150}
                y={300}
                w={300}
                title="Preview"
                icon="activity"
                c={T.mint}
                delay={0.4}
                rot={1.5}
            >
                <div className="vz-r">
                    Agent → CRM export
                    <span
                        className="end vz-pill"
                        style={{ ["--c" as any]: on ? T.blush : T.lime }}
                    >
                        {on ? "Blocked" : "Allowed"}
                    </span>
                </div>
                <div className="vz-r">
                    Copilot → Docs
                    <span
                        className="end vz-pill"
                        style={{ ["--c" as any]: T.lime }}
                    >
                        Allowed
                    </span>
                </div>
            </Panel>
        </div>
    )
}

function Timeline() {
    const [ref, on] = useTicker(4, 1700)
    const ev: [string, string, string][] = [
        ["New agent connected", "09:12", "bot"],
        ["Policy blocked export", "09:20", "shield"],
        ["Owner assigned", "09:41", "users"],
        ["Finding resolved", "10:05", "check"],
    ]
    return (
        <div ref={ref} className="vz">
            <Panel
                x={10}
                y={20}
                w={270}
                title="Live events"
                icon="activity"
                c={T.butter}
                delay={0.1}
                right={
                    <i className="sv-dot live" style={{ color: T.verified }} />
                }
            >
                <div
                    style={{
                        position: "relative",
                        padding: "10px 14px 14px 40px",
                    }}
                >
                    <span
                        style={{
                            position: "absolute",
                            left: 24,
                            top: 18,
                            bottom: 22,
                            width: 1.5,
                            background: T.ink,
                        }}
                    />
                    {ev.map(([t, time, ic], i) => (
                        <div
                            key={t}
                            style={{
                                position: "relative",
                                padding: "8px 10px",
                                marginBottom: 6,
                                borderRadius: 12,
                                border: `1px solid ${i === on ? T.ink : "transparent"}`,
                                background: i === on ? T.cream : undefined,
                                fontSize: 12.5,
                                transition: "background-color .4s",
                            }}
                        >
                            <span
                                className="vz-ic"
                                style={{
                                    position: "absolute",
                                    left: -30,
                                    top: 6,
                                    width: 22,
                                    height: 22,
                                    ["--c" as any]: i === on ? T.lime : T.white,
                                }}
                            >
                                <Icon name={ic} size={11} />
                            </span>
                            <b style={{ fontWeight: 600 }}>{t}</b>
                            <div style={{ fontSize: 11, color: T.mute }}>
                                {time}
                            </div>
                        </div>
                    ))}
                </div>
            </Panel>
            <Panel
                x={300}
                y={0}
                w={290}
                title="Event log"
                icon="file"
                c={T.mint}
                delay={0.2}
                right={<span className="vz-pill">Filter</span>}
            >
                {[
                    ["agent.connect", "Info"],
                    ["policy.block", "High"],
                    ["owner.assign", "Info"],
                    ["finding.close", "Low"],
                ].map(([t, s]) => (
                    <div
                        className="vz-r"
                        key={t}
                        style={{
                            fontFamily: "ui-monospace, Menlo, monospace",
                            fontSize: 11.5,
                        }}
                    >
                        {t}
                        <span
                            className="end vz-pill"
                            style={{
                                fontFamily: "var(--sans)",
                                ["--c" as any]:
                                    s === "High" ? "#FFE1A6" : T.white,
                            }}
                        >
                            {s}
                        </span>
                    </div>
                ))}
            </Panel>
            <Panel
                x={320}
                y={230}
                w={270}
                title="Incident #204"
                icon="alert"
                c={T.peach}
                delay={0.3}
                rot={1.5}
            >
                <div
                    style={{
                        padding: 14,
                        display: "grid",
                        gap: 8,
                        fontSize: 12.5,
                    }}
                >
                    <b>Blocked CRM export by agent</b>
                    <div style={{ display: "flex", gap: 6 }}>
                        {sev("High")}
                        <span className="vz-pill">Investigating</span>
                    </div>
                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 6,
                        }}
                    >
                        <span className="vz-av">MR</span>Assigned to security
                        on-call
                    </div>
                </div>
            </Panel>
        </div>
    )
}

function Hub() {
    const C: [number, number] = [300, 230]
    const g: [number, number, string, string, string][] = [
        [110, 90, "Cloud infrastructure", "server", T.peach],
        [490, 90, "CI/CD", "git", T.butter],
        [110, 370, "SIEM / SOAR", "activity", T.lime],
        [490, 370, "AI platforms", "cpu", T.pink],
    ]
    return (
        <div className="vz">
            <svg
                width="600"
                height="460"
                style={{ position: "absolute", inset: 0, overflow: "visible" }}
                aria-hidden="true"
            >
                {g.map(([x, y], i) => (
                    <g key={i}>
                        <path
                            d={`M${C[0]} ${C[1]} L${x} ${y}`}
                            stroke={T.ink}
                            strokeWidth="1.5"
                            strokeDasharray="5 7"
                            className="sv-flow"
                        />
                        <Packet
                            d={`M${x} ${y} L${C[0]} ${C[1]}`}
                            dur={2.2 + i * 0.3}
                            delay={i * 0.4}
                            color={T.orange}
                        />
                    </g>
                ))}
            </svg>
            <div
                style={{
                    position: "absolute",
                    left: C[0],
                    top: C[1],
                    translate: "-50% -50%",
                    display: "grid",
                    placeItems: "center",
                    gap: 4,
                    width: 130,
                    height: 130,
                    borderRadius: "50%",
                    background: T.ink,
                    color: T.white,
                    border: `1.5px solid ${T.ink}`,
                    boxShadow: `5px 5px 0 0 ${T.orange}`,
                    zIndex: 3,
                    fontFamily: "var(--display)",
                    fontWeight: 700,
                    fontSize: 13,
                    textAlign: "center",
                }}
            >
                <span style={{ display: "grid", placeItems: "center", gap: 6 }}>
                    <span
                        style={{
                            display: "grid",
                            placeItems: "center",
                            width: 46,
                            height: 46,
                            borderRadius: "50%",
                            background: T.butter,
                            color: T.ink,
                            border: `1.2px solid ${T.white}`,
                        }}
                    >
                        <Icon name="shield-check" size={22} />
                    </span>
                    HUB
                </span>
            </div>
            {g.map(([x, y, t, ic, c], i) => (
                <div key={t} style={{ position: "absolute", left: x, top: y }}>
                    <Pop delay={0.1 + i * 0.1} rotate={i % 2 ? 6 : -6}>
                        <div className="vz-node" style={{ left: 0, top: 0 }}>
                            <IconTile
                                name={ic === "git" ? "route" : ic}
                                tile={c}
                                size={34}
                                icon={16}
                            />
                            {t}
                        </div>
                    </Pop>
                </div>
            ))}
        </div>
    )
}

function RiskDashboard() {
    const bars = [
        ["Crit", 2, T.critical],
        ["High", 10, T.risk],
        ["Med", 27, T.butter],
        ["Low", 64, T.lime],
    ] as [string, number, string][]
    return (
        <div className="vz">
            <Panel
                x={10}
                y={10}
                w={300}
                title="Severity"
                icon="gauge"
                c={T.peach}
                delay={0.1}
            >
                <div
                    style={{
                        display: "flex",
                        alignItems: "flex-end",
                        gap: 18,
                        height: 150,
                        padding: "14px 22px",
                    }}
                >
                    {bars.map(([l, v, c]) => (
                        <div
                            key={l}
                            style={{
                                flex: 1,
                                display: "grid",
                                justifyItems: "center",
                                gap: 6,
                            }}
                        >
                            <span style={{ fontSize: 11, fontWeight: 700 }}>
                                {v}
                            </span>
                            <span
                                style={{
                                    width: "100%",
                                    height: Math.max(10, v * 1.5),
                                    background: c,
                                    border: `1.2px solid ${T.ink}`,
                                    borderRadius: 8,
                                }}
                            />
                            <span className="vz-cap">{l}</span>
                        </div>
                    ))}
                </div>
            </Panel>
            <Panel
                x={330}
                y={30}
                w={260}
                title="Investigation queue"
                icon="search"
                c={T.butter}
                delay={0.2}
            >
                {[
                    ["Broad CRM access", "Critical"],
                    ["PII in prompts", "High"],
                    ["Unknown plugin", "High"],
                    ["Unpinned model", "Medium"],
                ].map(([t, s]) => (
                    <div className="vz-r" key={t}>
                        <b>{t}</b>
                        <span className="end">{sev(s)}</span>
                    </div>
                ))}
            </Panel>
            <Panel
                x={60}
                y={280}
                w={330}
                title="Policy status"
                icon="shield-check"
                c={T.lime}
                delay={0.3}
                rot={-1.5}
            >
                <div style={{ padding: 14, display: "grid", gap: 10 }}>
                    {[
                        ["Enforced", 72, T.lime],
                        ["Monitoring", 20, T.butter],
                        ["Draft", 8, T.cream],
                    ].map(([l, v, c]: any) => (
                        <div
                            key={l}
                            style={{
                                display: "grid",
                                gridTemplateColumns: "90px 1fr 40px",
                                alignItems: "center",
                                gap: 8,
                                fontSize: 12,
                                fontWeight: 600,
                            }}
                        >
                            <span>{l}</span>
                            <div
                                className="vz-bar"
                                style={{ ["--c" as any]: c }}
                            >
                                <i style={{ width: `${v}%` }} />
                            </div>
                            <span>{v}%</span>
                        </div>
                    ))}
                </div>
            </Panel>
        </div>
    )
}

function AssetTable() {
    const [ref, on] = useTicker(4, 1500)
    const deps = ["All", "Sales", "Marketing", "Finance"]
    const rows: [string, string, string, boolean][] = [
        ["Meeting notes AI", "Sales", "AK", false],
        ["Ad copy generator", "Marketing", "JS", false],
        ["Forecast assistant", "Finance", "MR", true],
        ["Email drafter", "Sales", "LT", true],
        ["Image studio", "Marketing", "", false],
    ]
    return (
        <div ref={ref} className="vz">
            <Panel
                x={20}
                y={30}
                w={560}
                title="Unmanaged AI tools"
                icon="eye"
                c={T.butter}
                delay={0.1}
                right={
                    <span
                        className="vz-pill"
                        style={{ ["--c" as any]: "#FFE1A6" }}
                    >
                        3 unreviewed
                    </span>
                }
            >
                <div
                    style={{
                        display: "flex",
                        gap: 6,
                        padding: "10px 14px",
                        borderBottom: "1px solid rgba(0,0,0,.08)",
                    }}
                >
                    {deps.map((d, i) => (
                        <span
                            key={d}
                            className="vz-pill"
                            style={{
                                ["--c" as any]: i === on ? T.ink : T.white,
                                color: i === on ? T.white : T.ink,
                            }}
                        >
                            {d}
                        </span>
                    ))}
                </div>
                {rows.map(([n, d, o, ok], i) => (
                    <div
                        className="vz-r"
                        key={n}
                        style={{
                            display: "grid",
                            gridTemplateColumns: "1.6fr 1fr .8fr 1fr",
                            gap: 8,
                            height: 44,
                        }}
                    >
                        <b>{n}</b>
                        <span>{d}</span>
                        {o ? (
                            <span
                                className="vz-av"
                                style={{
                                    ["--c" as any]: [
                                        T.peach,
                                        T.mint,
                                        T.pink,
                                        T.lime,
                                    ][i % 4],
                                }}
                            >
                                {o}
                            </span>
                        ) : (
                            <span
                                className="vz-pill"
                                style={{ justifySelf: "start" }}
                            >
                                No owner
                            </span>
                        )}
                        <span
                            className="vz-pill"
                            style={{
                                justifySelf: "start",
                                ["--c" as any]: ok ? T.lime : "#FFE1A6",
                            }}
                        >
                            <i
                                className="sv-dot"
                                style={{
                                    color: ok ? T.verified : T.risk,
                                    width: 7,
                                    height: 7,
                                }}
                            />
                            {ok ? "Reviewed" : "Unreviewed"}
                        </span>
                    </div>
                ))}
            </Panel>
        </div>
    )
}

function Workflow() {
    const nodes: [number, number, string, string, string][] = [
        [80, 120, "Model", "cpu", T.peach],
        [300, 120, "Agent", "bot", T.butter],
        [520, 120, "API", "plug", T.lime],
        [300, 340, "Database", "database", T.pink],
    ]
    const checks: [number, number][] = [
        [190, 120],
        [410, 120],
        [300, 230],
    ]
    return (
        <div className="vz">
            <svg
                width="600"
                height="460"
                style={{ position: "absolute", inset: 0, overflow: "visible" }}
                aria-hidden="true"
            >
                <path
                    d="M80 120 H520 M300 120 V340"
                    stroke={T.ink}
                    strokeWidth="1.5"
                    strokeDasharray="5 7"
                    className="sv-flow"
                />
                <Packet d="M80 120 H520" dur={3} color={T.orange} r={5} />
                <Packet
                    d="M300 120 V340"
                    dur={2.4}
                    delay={0.8}
                    color={T.lime}
                    r={5}
                />
            </svg>
            {nodes.map(([x, y, t, ic, c], i) => (
                <div key={t} style={{ position: "absolute", left: x, top: y }}>
                    <Pop delay={0.1 * i} rotate={0}>
                        <div
                            className="vz-node"
                            style={{
                                left: 0,
                                top: 0,
                                flexDirection: "column",
                                height: "auto",
                                padding: "10px 14px",
                                borderRadius: 18,
                                gap: 6,
                            }}
                        >
                            <IconTile name={ic} tile={c} size={40} icon={19} />
                            {t}
                        </div>
                    </Pop>
                </div>
            ))}
            {checks.map(([x, y], i) => (
                <div
                    key={i}
                    style={{
                        position: "absolute",
                        left: x,
                        top: y,
                        translate: "-50% -50%",
                        zIndex: 3,
                    }}
                >
                    <Pop delay={0.5 + i * 0.12} rotate={0}>
                        <span
                            className="vz-pill"
                            style={{
                                ["--c" as any]: T.ink,
                                color: T.white,
                                height: 26,
                                boxShadow: `2px 2px 0 0 ${T.orange}`,
                            }}
                        >
                            <Icon name="shield-check" size={12} stroke={2} />
                            Policy check
                        </span>
                    </Pop>
                </div>
            ))}
        </div>
    )
}

function Compliance() {
    const rows: [string, string, string, string][] = [
        ["Acceptable AI use", "AK", "Mar 12", "On track"],
        ["Model access", "MR", "Apr 02", "Review due"],
        ["Data retention", "JS", "Feb 20", "On track"],
        ["Vendor AI review", "LT", "Jan 30", "Overdue"],
    ]
    const c = (s: string) =>
        s === "On track" ? T.lime : s === "Overdue" ? T.blush : "#FFE1A6"
    return (
        <div className="vz">
            <Panel
                x={10}
                y={20}
                w={470}
                title="Governance matrix"
                icon="clipboard"
                c={T.butter}
                delay={0.1}
            >
                <div
                    className="vz-r"
                    style={{
                        display: "grid",
                        gridTemplateColumns: "1.6fr .6fr .8fr 1fr",
                        gap: 8,
                        height: 32,
                    }}
                >
                    {["Policy", "Owner", "Review", "Status"].map((h) => (
                        <span key={h} className="vz-cap">
                            {h}
                        </span>
                    ))}
                </div>
                {rows.map(([p, o, d, s], i) => (
                    <div
                        className="vz-r"
                        key={p}
                        style={{
                            display: "grid",
                            gridTemplateColumns: "1.6fr .6fr .8fr 1fr",
                            gap: 8,
                            height: 42,
                        }}
                    >
                        <b>{p}</b>
                        <span
                            className="vz-av"
                            style={{
                                ["--c" as any]: [
                                    T.peach,
                                    T.mint,
                                    T.pink,
                                    T.lime,
                                ][i],
                            }}
                        >
                            {o}
                        </span>
                        <span>{d}</span>
                        <span
                            className="vz-pill"
                            style={{
                                justifySelf: "start",
                                ["--c" as any]: c(s),
                            }}
                        >
                            {s}
                        </span>
                    </div>
                ))}
            </Panel>
            <Pop
                delay={0.35}
                rotate={8}
                style={{
                    position: "absolute",
                    left: 380,
                    top: 230,
                    width: 200,
                    zIndex: 3,
                }}
            >
                <div
                    className="vz-p"
                    style={{
                        position: "relative",
                        rotate: "3deg",
                        padding: 16,
                        display: "grid",
                        gap: 10,
                        background: T.cream,
                    }}
                >
                    <span className="vz-pill" style={{ justifySelf: "start" }}>
                        <Icon name="file" size={11} />
                        PDF export
                    </span>
                    <b style={{ fontFamily: "var(--display)", fontSize: 15 }}>
                        Quarterly AI governance report
                    </b>
                    <div className="vz-bar">
                        <i style={{ width: "75%" }} />
                    </div>
                    <div className="vz-bar" style={{ ["--c" as any]: T.peach }}>
                        <i style={{ width: "48%" }} />
                    </div>
                </div>
            </Pop>
        </div>
    )
}

function LayersVenn() {
    const L: [number, number, string, string][] = [
        [220, 170, "Visibility", T.peach],
        [380, 170, "Intelligence", T.lime],
        [300, 300, "Control", T.butter],
    ]
    return (
        <div className="vz">
            {L.map(([x, y, t, c], i) => (
                <div
                    key={t}
                    style={{
                        position: "absolute",
                        left: x,
                        top: y,
                        translate: "-50% -50%",
                        width: 250,
                        height: 250,
                        borderRadius: "50%",
                        background: c,
                        opacity: 0.85,
                        border: `1.5px solid ${T.ink}`,
                        mixBlendMode: "multiply" as any,
                    }}
                >
                    <span
                        style={{
                            position: "absolute",
                            left: "50%",
                            top: i === 2 ? "72%" : "30%",
                            translate:
                                i === 2 ? "-50% 0" : i ? "-10% 0" : "-90% 0",
                            fontFamily: "var(--display)",
                            fontWeight: 700,
                            fontSize: 16,
                        }}
                    >
                        {t}
                    </span>
                </div>
            ))}
            <div
                style={{
                    position: "absolute",
                    left: 300,
                    top: 220,
                    translate: "-50% -50%",
                    display: "grid",
                    placeItems: "center",
                    width: 84,
                    height: 84,
                    borderRadius: "50%",
                    background: T.white,
                    border: `1.5px solid ${T.ink}`,
                    boxShadow: `4px 4px 0 0 ${T.ink}`,
                    zIndex: 3,
                }}
            >
                <Icon name="shield-check" size={34} />
            </div>
            <Sparkle
                size={28}
                fill={T.pink}
                style={{ left: 500, top: 50 }}
                delay={0.4}
            />
            <Sparkle
                size={18}
                fill={T.white}
                style={{ left: 80, top: 380 }}
                delay={1.4}
            />
        </div>
    )
}

function Report() {
    return (
        <div className="vz">
            <Planet
                size={80}
                fill={T.lime}
                style={{ left: 470, top: 30 }}
                className="sv-bob"
            />
            <Pop
                delay={0.1}
                rotate={-8}
                style={{
                    position: "absolute",
                    left: 140,
                    top: 20,
                    width: 320,
                    zIndex: 2,
                }}
            >
                <div
                    className="vz-p"
                    style={{
                        position: "relative",
                        height: 420,
                        rotate: "-3deg",
                        background: T.peach,
                        padding: 28,
                        display: "flex",
                        flexDirection: "column",
                        gap: 14,
                    }}
                >
                    <span
                        className="vz-pill"
                        style={{ alignSelf: "flex-start" }}
                    >
                        Guide · 8 min
                    </span>
                    <div className="vz-big" style={{ fontSize: 30 }}>
                        The Enterprise Guide to AI Security
                    </div>
                    <div
                        style={{
                            position: "relative",
                            marginTop: "auto",
                            height: 170,
                            borderRadius: 14,
                            border: `1.2px solid ${T.ink}`,
                            background: T.cream,
                            overflow: "hidden",
                        }}
                    >
                        <div
                            style={{
                                position: "absolute",
                                inset: 0,
                                backgroundImage: `linear-gradient(rgba(0,0,0,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.12) 1px,transparent 1px)`,
                                backgroundSize: "22px 22px",
                            }}
                        />
                        <svg
                            viewBox="0 0 260 170"
                            style={{
                                position: "absolute",
                                inset: 0,
                                width: "100%",
                                height: "100%",
                            }}
                            aria-hidden="true"
                        >
                            {[
                                [50, 50],
                                [130, 30],
                                [210, 60],
                                [80, 130],
                                [190, 125],
                            ].map(([x, y], i) => (
                                <g key={i}>
                                    <line
                                        x1="130"
                                        y1="88"
                                        x2={x}
                                        y2={y}
                                        stroke={T.ink}
                                        strokeWidth="1.2"
                                    />
                                    <circle
                                        cx={x}
                                        cy={y}
                                        r="9"
                                        fill={
                                            [
                                                T.butter,
                                                T.lime,
                                                T.pink,
                                                T.mint,
                                                T.white,
                                            ][i]
                                        }
                                        stroke={T.ink}
                                        strokeWidth="1.2"
                                    />
                                </g>
                            ))}
                            <path
                                d="M130 64 c9 7 18 9 26 9 v18 c0 15-11 25-26 30-15-5-26-15-26-30V73c8 0 17-2 26-9Z"
                                fill={T.white}
                                stroke={T.ink}
                                strokeWidth="1.4"
                            />
                        </svg>
                    </div>
                </div>
            </Pop>
            <Sparkle
                size={30}
                fill={T.butter}
                style={{ left: 90, top: 330 }}
                delay={0.8}
            />
        </div>
    )
}

function Lifecycle({
    steps = ["Discover", "Understand", "Protect", "Improve"],
}: {
    steps?: string[]
}) {
    const ic = ["search", "eye", "shield-check", "sparkles", "zap", "layers"]
    const tiles = [T.butter, T.peach, T.lime, T.pink, T.mint, T.coral]
    const n = Math.max(3, Math.min(6, steps.length))
    const R = 170
    return (
        <div className="vz">
            <svg
                width="600"
                height="460"
                style={{ position: "absolute", inset: 0, overflow: "visible" }}
                aria-hidden="true"
            >
                <circle
                    cx="300"
                    cy="230"
                    r={R}
                    fill="none"
                    stroke={T.ink}
                    strokeWidth="1.5"
                    strokeDasharray="6 8"
                    className="sv-flow"
                />
                <Packet
                    d={`M300 ${230 - R} a${R} ${R} 0 1 1 -0.1 0`}
                    dur={6}
                    color={T.orange}
                    r={6}
                />
            </svg>
            <div
                style={{
                    position: "absolute",
                    left: 300,
                    top: 230,
                    translate: "-50% -50%",
                    display: "grid",
                    placeItems: "center",
                    width: 120,
                    height: 120,
                    borderRadius: "50%",
                    background: T.ink,
                    color: T.white,
                    fontFamily: "var(--display)",
                    fontWeight: 700,
                    fontSize: 13,
                    letterSpacing: ".06em",
                    textTransform: "uppercase",
                    boxShadow: `4px 4px 0 0 ${T.orange}`,
                }}
            >
                Lifecycle
            </div>
            {steps.slice(0, n).map((s, i) => {
                const a = -Math.PI / 2 + (i / n) * Math.PI * 2
                return (
                    <div
                        key={i}
                        style={{
                            position: "absolute",
                            left: 300 + Math.cos(a) * R,
                            top: 230 + Math.sin(a) * R,
                        }}
                    >
                        <Pop delay={0.1 * i} rotate={0}>
                            <div
                                className="vz-node"
                                style={{ left: 0, top: 0 }}
                            >
                                <IconTile
                                    name={ic[i % ic.length]}
                                    tile={tiles[i % tiles.length]}
                                    size={32}
                                    icon={15}
                                />
                                {s}
                            </div>
                        </Pop>
                    </div>
                )
            })}
        </div>
    )
}

function BrokenNode() {
    return (
        <div className="vz">
            <Orbit w={480} h={200} style={{ left: 60, top: 120 }} dashed />
            <svg
                width="600"
                height="440"
                style={{ position: "absolute", inset: 0, overflow: "visible" }}
                aria-hidden="true"
            >
                <path d="M120 120 L230 190" stroke={T.ink} strokeWidth="1.5" />
                <path d="M480 120 L370 190" stroke={T.ink} strokeWidth="1.5" />
                <path d="M130 340 L232 262" stroke={T.ink} strokeWidth="1.5" />
                <path
                    d="M470 330 L410 290"
                    stroke={T.ink}
                    strokeWidth="1.5"
                    strokeDasharray="4 6"
                />
                <path
                    d="M402 284 l-12 -4 l6 -6 l-12 -5"
                    stroke={T.orange}
                    strokeWidth="2.5"
                    fill="none"
                    strokeLinecap="round"
                />
            </svg>
            {[
                [120, 120, "cpu"],
                [480, 120, "bot"],
                [130, 340, "plug"],
            ].map(([x, y, ic]: any, i) => (
                <div key={i} style={{ position: "absolute", left: x, top: y }}>
                    <span className="vz-dot" style={{ left: 0, top: 0 }}>
                        <Icon name={ic} size={22} />
                    </span>
                </div>
            ))}
            <div style={{ position: "absolute", left: 470, top: 330 }}>
                <span
                    className="vz-dot sv-bob"
                    style={{
                        left: 0,
                        top: 0,
                        background: T.cream,
                        borderStyle: "dashed",
                        ["--fr" as any]: "8deg",
                    }}
                >
                    <Icon name="help" size={22} />
                </span>
            </div>
            <div
                style={{
                    position: "absolute",
                    left: 300,
                    top: 225,
                    translate: "-50% -50%",
                    display: "grid",
                    placeItems: "center",
                    width: 150,
                    height: 150,
                    borderRadius: "50%",
                    background: T.butter,
                    border: `1.5px solid ${T.ink}`,
                    boxShadow: `5px 5px 0 0 ${T.ink}`,
                    fontFamily: "var(--display)",
                    fontWeight: 800,
                    fontSize: 44,
                }}
            >
                404
            </div>
        </div>
    )
}

/* ---------------------------------------------------------------- registry */
type Def = { w: number; h: number; C: (p: any) => JSX.Element }
const REG: Record<string, Def> = {
    pipeline: { w: 1040, h: 400, C: Pipeline },
    roles: { w: 1040, h: 400, C: Roles },
    editorial: { w: 1040, h: 400, C: Editorial },
    ecosystem: { w: 1040, h: 400, C: Ecosystem },
    posture: { w: 1040, h: 400, C: Posture },
    inventory: { w: 600, h: 460, C: Inventory },
    riskDrawer: { w: 600, h: 460, C: RiskDrawer },
    policy: { w: 600, h: 460, C: Policy },
    timeline: { w: 600, h: 460, C: Timeline },
    hub: { w: 600, h: 460, C: Hub },
    riskDashboard: { w: 600, h: 460, C: RiskDashboard },
    assetTable: { w: 600, h: 460, C: AssetTable },
    workflow: { w: 600, h: 460, C: Workflow },
    compliance: { w: 600, h: 460, C: Compliance },
    layers: { w: 600, h: 460, C: LayersVenn },
    report: { w: 600, h: 460, C: Report },
    lifecycle: { w: 600, h: 460, C: Lifecycle },
    broken: { w: 600, h: 440, C: BrokenNode },
}
export const HERO_VISUALS = {
    options: ["pipeline", "roles", "editorial", "ecosystem", "posture", "none"],
    optionTitles: [
        "Pipeline (Platform)",
        "Role panels (Solutions)",
        "Editorial (Resources)",
        "Ecosystem (About)",
        "Posture dashboard (Contact)",
        "None",
    ],
}
export const SPLIT_VISUALS = {
    options: [
        "inventory",
        "riskDrawer",
        "policy",
        "timeline",
        "hub",
        "riskDashboard",
        "assetTable",
        "workflow",
        "compliance",
        "layers",
        "report",
        "lifecycle",
    ],
    optionTitles: [
        "Asset inventory",
        "Risk drawer",
        "Policy builder",
        "Event timeline",
        "Integrations hub",
        "Risk dashboard",
        "Unmanaged tools table",
        "AI workflow",
        "Compliance matrix",
        "Three layers",
        "Report cover",
        "Lifecycle circle",
    ],
}

export function Visual({
    kind,
    max = 1,
    props,
}: {
    kind: string
    max?: number
    props?: any
}) {
    return (
        <div style={{ position: "relative", width: "100%" }}>
            <OAuthDiagram />
        </div>
    )
}

export default function Visuals() {
    return null
}
