// SECUVANTA Trust strip: Pluto's "Trusted by" band, but with industry labels instead of invented customer logos.
// Each label sits in a tilted oval sticker with a minimal line icon, threaded on one orbit line. Pops in with a
// spring and wobbles on hover. Items are lines: "Label | icon".
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import {
    Section,
    Reveal,
    Pop,
    Icon,
    Sparkle,
    lines,
    cells,
    toneControl,
    decorControl,
    T,
    ICON_NAMES,
} from "./Kit.tsx"

const CSS = `
.sv-trust{padding:24px 0 112px}
.sv-trust .hd{font-family:var(--display);font-weight:600;font-size:clamp(18px,1.7cqw,24px);line-height:1.2;text-align:center;color:var(--text);text-wrap:balance}
.sv-trust .row{position:relative;display:grid;grid-template-columns:repeat(var(--n,4),minmax(0,1fr));gap:24px;margin-top:48px}
.sv-trust .orbit{position:absolute;left:-4%;right:-4%;top:50%;height:120px;translate:0 -50%;border:1px solid var(--line);border-radius:50%;pointer-events:none;opacity:.9}
.sv-trust .ov{position:relative;display:flex;align-items:center;justify-content:center;gap:12px;min-height:92px;padding:16px 26px;border-radius:50%;background:${T.white};border:1.5px solid ${T.ink};box-shadow:3px 3px 0 0 ${T.ink};
  font-family:var(--display);font-weight:600;font-size:clamp(14px,1.25cqw,17px);line-height:1.2;color:${T.ink};text-align:left;transition:translate .2s var(--pop),box-shadow .2s var(--pop),rotate .2s var(--pop)}
.sv-trust .ov:hover{translate:-2px -3px;box-shadow:6px 6px 0 0 ${T.ink};rotate:0deg!important}
.sv-trust .ov i{display:grid;place-items:center;width:42px;height:42px;border-radius:50%;border:1.2px solid ${T.ink};background:var(--c);flex-shrink:0}
@container (max-width:1000px){.sv-trust .row{grid-template-columns:repeat(2,minmax(0,1fr))}.sv-trust .orbit{display:none}}
@container (max-width:520px){.sv-trust .row{grid-template-columns:1fr;gap:14px}.sv-trust .ov{rotate:0deg!important;border-radius:999px;min-height:72px;justify-content:flex-start}}
`
const FILL = [T.peach, T.lime, T.pink, T.mint, T.cream, T.coral]
const TILT = [-4, 3, -2, 4, -3, 2]

export default function TrustStrip(props: any) {
    const { tone, title, items, decor, sectionId } = props
    const list = lines(items).map((l) => {
        const [label, icon] = cells(l)
        return { label, icon: ICON_NAMES.includes(icon) ? icon : "sparkles" }
    })
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-trust"
            css={CSS}
            label="Who it is for"
        >
            <div className="sv-wrap">
                {title && (
                    <Reveal>
                        <h2 className="hd">{title}</h2>
                    </Reveal>
                )}
                <ul
                    className="row"
                    style={{ ["--n" as any]: Math.min(list.length || 1, 6) }}
                >
                    <span className="orbit" aria-hidden="true" />
                    {decor && (
                        <>
                            <Sparkle
                                size={22}
                                fill={T.white}
                                style={{ left: "24.5%", top: -28 }}
                                delay={0.6}
                            />
                            <Sparkle
                                size={18}
                                fill={T.pink}
                                style={{ left: "74%", bottom: -26 }}
                                delay={1.8}
                            />
                        </>
                    )}
                    {list.map((it, i) => (
                        <li key={i}>
                            <Pop
                                delay={0.08 * i}
                                rotate={TILT[i % TILT.length] * 2}
                            >
                                <div
                                    className="ov"
                                    style={{
                                        rotate: `${TILT[i % TILT.length]}deg`,
                                    }}
                                >
                                    <i
                                        style={{
                                            ["--c" as any]:
                                                FILL[i % FILL.length],
                                        }}
                                    >
                                        <Icon name={it.icon} size={20} />
                                    </i>
                                    {it.label}
                                </div>
                            </Pop>
                        </li>
                    ))}
                </ul>
            </div>
        </Section>
    )
}

addPropertyControls(TrustStrip, {
    tone: toneControl("butter"),
    title: {
        type: ControlType.String,
        title: "Title",
        defaultValue: "Built for teams securing the next era of AI",
    },
    items: {
        type: ControlType.String,
        title: "Labels",
        displayTextArea: true,
        description:
            "Up to 6, one per line: Label | icon (shield, code, server, scale, building, users…). Use industry or team labels, not customer logos you don't have permission for.",
        defaultValue:
            "Enterprise Security | shield\nAI Engineering | code\nIT Operations | server\nRisk & Compliance | scale",
    },
    decor: decorControl,
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "teams",
    },
})

// Shared control types verified.
