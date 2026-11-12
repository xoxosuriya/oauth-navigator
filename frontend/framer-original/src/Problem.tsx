// SECUVANTA Problem: Pluto's "CISO's brand new problem" block. Orange eyebrow, chunky headline and lead, then a split:
// three pain-point sticker rows + CTA on the left, and a clean AI asset map on the right (tilted orbits with asset
// stickers, like Pluto's tool galaxy) with three warning callouts. No hacker imagery.
// Motion: orbits drift, assets pop in, callouts swing in one after another and their markers pulse.
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import {
    Section,
    Head,
    Reveal,
    Pop,
    Btn,
    Icon,
    IconTile,
    Stage,
    Sparkle,
    Planet,
    Orbit,
    lines,
    cells,
    headControls,
    toneControl,
    decorControl,
    T,
    ICON_NAMES,
} from "./Kit.tsx"

const CSS = `
.sv-prob .grid{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:64px;align-items:center;margin-top:72px}
.sv-prob .pts{display:grid;gap:16px}
.sv-prob .pt{display:flex;align-items:center;gap:16px;padding:16px 20px 16px 16px}
.sv-prob .pt p{font-weight:500;font-size:17px;line-height:1.4;color:${T.ink}}
.sv-prob .cta{margin-top:28px}
.sv-prob .map{position:relative}
/* asset map canvas 640 × 540 */
.sv-am{position:absolute;inset:0}
.sv-am .as{position:absolute;translate:-50% -50%;display:grid;place-items:center;width:52px;height:52px;border-radius:50%;background:${T.white};border:1.5px solid ${T.ink};box-shadow:2.25px 2.25px 0 0 ${T.ink};color:${T.ink};z-index:1}
.sv-am .as.flag{background:#FFE1A6}
.sv-am .as.flag::after{content:"";position:absolute;inset:-7px;border-radius:50%;border:2px dashed ${T.ink};animation:sv-spin 12s linear infinite}
.sv-am .hub{position:absolute;left:320px;top:270px;translate:-50% -50%;display:flex;align-items:center;gap:8px;height:48px;padding:0 18px;border-radius:999px;background:${T.ink};color:${T.white};font-family:var(--display);font-weight:600;font-size:13px;letter-spacing:.06em;text-transform:uppercase;white-space:nowrap;z-index:2;box-shadow:3px 3px 0 0 ${T.orange}}
.sv-am .co{position:absolute;z-index:3;width:206px}
.sv-am .co .sv-card{padding:12px 14px;display:grid;gap:4px;border-radius:16px}
.sv-am .co b{display:flex;align-items:center;gap:8px;font-family:var(--display);font-weight:700;font-size:14px;color:${T.ink}}
.sv-am .co b i{display:grid;place-items:center;width:24px;height:24px;border-radius:50%;border:1.2px solid ${T.ink};background:var(--c)}
.sv-am .co span{font-size:12.5px;line-height:1.4;color:${T.body}}
@container (max-width:1000px){.sv-prob .grid{grid-template-columns:1fr;gap:48px;margin-top:48px}}
`
const ASSETS: [number, number, string][] = [
    [120, 170, "cpu"],
    [208, 96, "bot"],
    [440, 92, "plug"],
    [540, 190, "database"],
    [560, 330, "code"],
    [430, 452, "server"],
    [196, 440, "key"],
    [92, 330, "users"],
    [318, 160, "file"],
    [322, 384, "layers"],
]
// callout anchors: [asset index, callout left, callout top, color]
const CALLS: [number, number, number, string][] = [
    [1, 0, 0, "#FFE1A6"],
    [3, 432, 214, T.coral],
    [6, 4, 470, T.peach],
]
const ICONS = ["help", "key", "database"]

function AssetMap({
    hub,
    callouts,
    decor,
}: {
    hub: string
    callouts: string[][]
    decor: boolean
}) {
    const flagged = new Set(CALLS.slice(0, callouts.length).map((c) => c[0]))
    return (
        <Stage w={640} h={560} className="map">
            <div className="sv-am">
                <div
                    className="sv-spin"
                    style={{
                        position: "absolute",
                        left: 20,
                        top: 120,
                        width: 600,
                        height: 300,
                        ["--sd" as any]: "90s",
                    }}
                >
                    <Orbit
                        w={600}
                        h={300}
                        style={{ left: 0, top: 0, transform: "rotate(-14deg)" }}
                    />
                </div>
                <Orbit
                    w={460}
                    h={230}
                    style={{ left: 90, top: 155, transform: "rotate(-14deg)" }}
                    dashed
                />
                <Orbit
                    w={260}
                    h={130}
                    style={{ left: 190, top: 205, transform: "rotate(-14deg)" }}
                />
                <svg
                    width="640"
                    height="560"
                    style={{
                        position: "absolute",
                        inset: 0,
                        overflow: "visible",
                    }}
                    aria-hidden="true"
                >
                    {CALLS.slice(0, callouts.length).map(([ai, cx, cy], i) => {
                        const a = ASSETS[ai]
                        const tx = cx + 103
                        const ty = cy + (cy > a[1] ? 0 : 60)
                        return (
                            <path
                                key={i}
                                d={`M${a[0]} ${a[1]} L${tx} ${ty}`}
                                stroke={T.ink}
                                strokeWidth="1.4"
                                strokeDasharray="4 5"
                                className="sv-flow"
                            />
                        )
                    })}
                </svg>
                {ASSETS.map(([x, y, ic], i) => (
                    <div
                        key={i}
                        style={{ position: "absolute", left: x, top: y }}
                    >
                        <Pop delay={0.05 * i} rotate={0}>
                            <span
                                className={`as${flagged.has(i) ? " flag" : ""}`}
                                style={{ left: 0, top: 0 }}
                            >
                                <Icon name={ic} size={21} />
                            </span>
                        </Pop>
                    </div>
                ))}
                <div className="hub">
                    <Icon name="radar" size={16} stroke={2} />
                    {hub}
                </div>
                {callouts.slice(0, 3).map(([title, detail], i) => {
                    const [, x, y, c] = CALLS[i]
                    return (
                        <Pop
                            key={i}
                            className="co"
                            style={{ left: x, top: y }}
                            delay={0.5 + i * 0.18}
                            rotate={i % 2 ? 6 : -6}
                        >
                            <div
                                className="sv-card"
                                style={{ rotate: `${i % 2 ? 2 : -2}deg` }}
                            >
                                <b>
                                    <i style={{ ["--c" as any]: c }}>
                                        <Icon
                                            name={ICONS[i]}
                                            size={13}
                                            stroke={2.2}
                                        />
                                    </i>
                                    {title}
                                </b>
                                {detail && <span>{detail}</span>}
                            </div>
                        </Pop>
                    )
                })}
                {decor && (
                    <>
                        <Planet
                            size={70}
                            fill={T.pink}
                            style={{ left: 560, top: 30 }}
                            className="sv-bob"
                        />
                        <Sparkle
                            size={26}
                            fill={T.butter}
                            style={{ left: 300, top: 18 }}
                            delay={0.9}
                        />
                        <Sparkle
                            size={18}
                            fill={T.white}
                            style={{ left: 600, top: 470 }}
                            delay={2.1}
                        />
                    </>
                )}
            </div>
        </Stage>
    )
}

export default function Problem(props: any) {
    const {
        tone,
        eyebrow,
        title,
        body,
        points,
        ctaLabel,
        ctaLink,
        hub,
        callouts,
        decor,
        sectionId,
    } = props
    const pts = lines(points).map((l) => {
        const [text, icon] = cells(l)
        return { text, icon: ICON_NAMES.includes(icon) ? icon : "alert" }
    })
    const calls = lines(callouts).map(cells)
    const tiles = ["#FFE1A6", T.coral, T.peach]
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-prob"
            css={CSS}
            label="The problem"
        >
            <div className="sv-wrap">
                <Head
                    eyebrow={eyebrow}
                    title={title}
                    body={body}
                    align="center"
                />
                <div className="grid">
                    <div>
                        <ul className="pts">
                            {pts.map((p, i) => (
                                <Reveal as="li" key={i} delay={0.08 * i}>
                                    <div className="sv-card sm pt hover">
                                        <IconTile
                                            name={p.icon}
                                            tile={tiles[i % tiles.length]}
                                            size={46}
                                            icon={21}
                                        />
                                        <p>{p.text}</p>
                                    </div>
                                </Reveal>
                            ))}
                        </ul>
                        {ctaLabel && (
                            <Reveal delay={0.3} className="cta">
                                <Btn label={ctaLabel} href={ctaLink} arrow />
                            </Reveal>
                        )}
                    </div>
                    <AssetMap hub={hub} callouts={calls} decor={decor} />
                </div>
            </div>
        </Section>
    )
}

addPropertyControls(Problem, {
    tone: toneControl("cream"),
    ...headControls({
        eyebrow: "The problem",
        title: "AI is moving faster than your _security visibility._",
        body: "New models, agents, and integrations appear every day. Without a unified view, security teams struggle to understand what is running, what is exposed, and what needs attention.",
    }),
    points: {
        type: ControlType.String,
        title: "Pain points",
        displayTextArea: true,
        description: "One per line: Text | icon",
        defaultValue:
            "Unknown AI tools create blind spots. | eye\nUnchecked integrations increase exposure. | plug\nInconsistent policies make governance harder. | scale",
    },
    ctaLabel: {
        type: ControlType.String,
        title: "CTA label",
        defaultValue: "Understand the Risks",
    },
    ctaLink: {
        type: ControlType.Link,
        title: "CTA link",
        defaultValue: "/resources",
    },
    hub: {
        type: ControlType.String,
        title: "Map center label",
        defaultValue: "AI asset map",
    },
    callouts: {
        type: ControlType.String,
        title: "Warning callouts",
        displayTextArea: true,
        description: "Up to 3, one per line: Title | detail",
        defaultValue:
            "Unknown Tool | Agent not in your inventory\nExcessive Access | Write access to production\nSensitive Data | Customer PII in prompts",
    },
    decor: decorControl,
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "problem",
    },
})

// Shared control types verified.
