// SECUVANTA Platform layers: "One platform. Four layers of AI protection." A horizontal pipeline of four sticker
// cards joined by connectors. Each card has a step number, icon, title, one-liner and a tiny live UI preview:
// Discover = assets popping into an inventory list, Assess = risk badges + score, Protect = allow/block rule,
// Govern = activity sparkline. Packets run along the connectors; cards lift with Pluto's springy hover.
// Cards are lines: "Title | Description | icon".
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import { motion } from "framer-motion"
import {
    Section,
    Head,
    Reveal,
    Btn,
    Icon,
    IconTile,
    Sparkle,
    useTicker,
    useStill,
    lines,
    cells,
    headControls,
    toneControl,
    decorControl,
    T,
    ICON_NAMES,
} from "./Kit.tsx"

const CSS = `
.sv-layers .track{position:relative;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:28px;margin-top:72px}
.sv-layers .wire{position:absolute;left:6%;right:6%;top:64px;height:2px;background:repeating-linear-gradient(90deg,var(--line) 0 8px,transparent 8px 16px);z-index:0}
.sv-layers .wire i{position:absolute;top:50%;width:12px;height:12px;margin-top:-6px;border-radius:50%;background:${T.orange};border:1.2px solid ${T.ink};animation:sv-run 4.5s linear infinite}
@keyframes sv-run{from{left:0}to{left:100%}}
.sv-layers .card{position:relative;z-index:1;display:flex;flex-direction:column;gap:14px;height:100%;padding:22px}
.sv-layers .top{display:flex;align-items:center;justify-content:space-between}
.sv-layers .no{font-family:var(--display);font-weight:700;font-size:13px;letter-spacing:.06em;color:${T.mute}}
.sv-layers .card p{font-size:15px;line-height:1.45;color:var(--body)}
.sv-layers .ui{margin-top:auto;min-height:150px;padding:12px;border-radius:14px;border:1px solid ${T.ink};background:var(--tile);font-size:12px;color:${T.ink};overflow:hidden}
.sv-layers .li{display:flex;align-items:center;gap:8px;height:30px;padding:0 10px;border-radius:9px;background:${T.white};border:1px solid ${T.ink};margin-top:6px;font-weight:600}
.sv-layers .li:first-child{margin-top:0}
.sv-layers .li em{margin-left:auto;font-style:normal;font-size:10.5px;font-weight:600;padding:2px 7px;border-radius:999px;border:1px solid ${T.ink};background:${T.lime}}
.sv-layers .sc{display:flex;align-items:flex-end;gap:10px;margin-bottom:10px}
.sv-layers .sc b{font-family:var(--display);font-weight:800;font-size:34px;line-height:1}
.sv-layers .sc span{font-size:11px;font-weight:600;color:${T.mute};padding-bottom:4px}
.sv-layers .bd{display:flex;flex-wrap:wrap;gap:6px}
.sv-layers .bd span{display:inline-flex;align-items:center;gap:5px;height:24px;padding:0 9px;border-radius:999px;border:1px solid ${T.ink};background:${T.white};font-size:11px;font-weight:600}
.sv-layers .rule{display:grid;gap:6px}
.sv-layers .rule div{display:flex;align-items:center;justify-content:space-between;gap:8px;height:32px;padding:0 10px;border-radius:9px;background:${T.white};border:1px solid ${T.ink};font-weight:600}
.sv-layers .tg{width:34px;height:20px;border-radius:999px;border:1px solid ${T.ink};background:${T.lime};position:relative;flex-shrink:0;transition:background-color .3s}
.sv-layers .tg::after{content:"";position:absolute;top:2px;left:16px;width:14px;height:14px;border-radius:50%;background:${T.white};border:1px solid ${T.ink};transition:left .3s var(--pop)}
.sv-layers .tg.off{background:${T.blush}}
.sv-layers .tg.off::after{left:2px}
.sv-layers .spark{display:block;width:100%;height:70px}
.sv-layers .cta{display:flex;justify-content:center;margin-top:56px}
@container (max-width:1100px){.sv-layers .track{grid-template-columns:repeat(2,minmax(0,1fr))}.sv-layers .wire{display:none}}
@container (max-width:600px){.sv-layers .track{grid-template-columns:1fr;gap:18px;margin-top:48px}}
`
const TILES = [T.butter, T.peach, T.lime, T.pink]

function Discover() {
    const [ref, i] = useTicker(4, 1400)
    const rows = [
        ["cpu", "Support model"],
        ["bot", "Sales agent"],
        ["plug", "CRM connector"],
        ["database", "Vector store"],
    ]
    return (
        <div ref={ref}>
            {rows.slice(0, i + 1).map(([ic, t], k) => (
                <motion.div
                    className="li"
                    key={t}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ type: "spring", stiffness: 420, damping: 20 }}
                >
                    <Icon name={ic} size={14} stroke={2} />
                    {t}
                    {k === i && <em>New</em>}
                </motion.div>
            ))}
        </div>
    )
}
function Assess() {
    return (
        <div>
            <div className="sc">
                <b>72</b>
                <span>risk score</span>
            </div>
            <div className="bd">
                <span>
                    <i className="sv-dot" style={{ color: T.critical }} />
                    Critical 1
                </span>
                <span>
                    <i className="sv-dot" style={{ color: T.risk }} />
                    High 3
                </span>
                <span>
                    <i className="sv-dot" style={{ color: T.butter }} />
                    Medium 8
                </span>
            </div>
        </div>
    )
}
function Protect() {
    const [ref, i] = useTicker(2, 1800)
    return (
        <div ref={ref} className="rule">
            <div>
                PII in prompts{" "}
                <span
                    className={`tg${i === 0 ? " off" : ""}`}
                    aria-hidden="true"
                />
            </div>
            <div>
                Agent write access{" "}
                <span className="tg off" aria-hidden="true" />
            </div>
            <div style={{ background: i === 0 ? T.blush : T.lime }}>
                {i === 0 ? "Blocked · review" : "Allowed · masked"}
            </div>
        </div>
    )
}
function Govern() {
    const still = useStill()
    const d =
        "M0 52 L22 44 L44 48 L66 30 L88 36 L110 22 L132 26 L154 12 L176 18 L200 8"
    return (
        <div>
            <svg
                className="spark"
                viewBox="0 0 200 64"
                preserveAspectRatio="none"
                aria-hidden="true"
            >
                <path d={`${d} L200 64 L0 64Z`} fill={T.white} stroke="none" />
                {still ? (
                    <path d={d} fill="none" stroke={T.ink} strokeWidth="2" />
                ) : (
                    <motion.path
                        d={d}
                        fill="none"
                        stroke={T.ink}
                        strokeWidth="2"
                        initial={{ pathLength: 0 }}
                        whileInView={{ pathLength: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 1.6, ease: "easeInOut" }}
                    />
                )}
            </svg>
            <div className="bd" style={{ marginTop: 8 }}>
                <span>
                    <Icon name="check" size={11} stroke={2.6} />
                    Audit log on
                </span>
                <span>36 policies</span>
            </div>
        </div>
    )
}
const UIS = [Discover, Assess, Protect, Govern]

export default function PlatformLayers(props: any) {
    const {
        tone,
        eyebrow,
        title,
        body,
        cards,
        showPreviews,
        ctaLabel,
        ctaLink,
        decor,
        sectionId,
    } = props
    const list = lines(cards).map((l) => {
        const [t, d, ic] = cells(l)
        return { t, d: d || "", ic: ICON_NAMES.includes(ic) ? ic : "sparkles" }
    })
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-layers"
            css={CSS}
            label="Platform overview"
        >
            {decor && (
                <Sparkle
                    size={34}
                    fill={T.butter}
                    style={{ right: "8%", top: 120 }}
                    delay={0.5}
                />
            )}
            {decor && (
                <Sparkle
                    size={22}
                    fill={T.pink}
                    style={{ left: "7%", top: 220 }}
                    delay={1.4}
                />
            )}
            <div className="sv-wrap">
                <Head
                    eyebrow={eyebrow}
                    title={title}
                    body={body}
                    align="center"
                />
                <div className="track">
                    <div className="wire" aria-hidden="true">
                        <i />
                        <i style={{ animationDelay: "-2.2s" }} />
                    </div>
                    {list.map((c, i) => {
                        const UI = UIS[i % UIS.length]
                        return (
                            <Reveal key={i} delay={0.1 * i}>
                                <article className="sv-card hover card">
                                    <div className="top">
                                        <IconTile
                                            name={c.ic}
                                            tile={TILES[i % TILES.length]}
                                        />
                                        <span className="no">
                                            {String(i + 1).padStart(2, "0")}
                                        </span>
                                    </div>
                                    <h3 className="sv-h4">{c.t}</h3>
                                    <p>{c.d}</p>
                                    {showPreviews && (
                                        <div
                                            className="ui"
                                            style={{
                                                ["--tile" as any]:
                                                    TILES[i % TILES.length],
                                            }}
                                            aria-hidden="true"
                                        >
                                            <UI />
                                        </div>
                                    )}
                                </article>
                            </Reveal>
                        )
                    })}
                </div>
                {ctaLabel && (
                    <Reveal className="cta">
                        <Btn
                            label={ctaLabel}
                            href={ctaLink}
                            variant="secondary"
                            arrow
                        />
                    </Reveal>
                )}
            </div>
        </Section>
    )
}

addPropertyControls(PlatformLayers, {
    tone: toneControl("white"),
    ...headControls({
        eyebrow: "Platform overview",
        title: "One platform.\nFour layers of *AI protection.*",
        body: "",
    }),
    cards: {
        type: ControlType.String,
        title: "Layers",
        displayTextArea: true,
        description:
            "One per line: Title | Description | icon. The mini previews follow the order Discover, Assess, Protect, Govern.",
        defaultValue:
            "Discover | Find AI assets across your environment. | search\nAssess | Understand risks and prioritize action. | gauge\nProtect | Apply security controls to AI workflows. | shield-check\nGovern | Monitor activity and maintain oversight. | scale",
    },
    showPreviews: {
        type: ControlType.Boolean,
        title: "Mini previews",
        defaultValue: true,
        enabledTitle: "Show",
        disabledTitle: "Hide",
    },
    ctaLabel: {
        type: ControlType.String,
        title: "CTA label",
        defaultValue: "Explore All Capabilities",
    },
    ctaLink: {
        type: ControlType.Link,
        title: "CTA link",
        defaultValue: "/platform",
    },
    decor: decorControl,
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "platform",
    },
})

// Shared control types verified.
