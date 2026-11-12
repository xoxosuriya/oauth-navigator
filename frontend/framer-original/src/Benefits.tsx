// SECUVANTA Benefits: "Built for security without slowing teams down." Four sticker cards, each with a pastel icon
// tile, title, one-liner and a tiny UI detail chip at the bottom (the "small UI detail" from the brief). Cards tilt a
// little and straighten with a springy lift on hover. Cards are lines: "Title | Description | UI detail | icon".
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import {
    Section,
    Head,
    Reveal,
    Icon,
    IconTile,
    Sparkle,
    Planet,
    lines,
    cells,
    headControls,
    toneControl,
    decorControl,
    T,
    ICON_NAMES,
} from "./Kit.tsx"

const CSS = `
.sv-ben .grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px;margin-top:64px}
.sv-ben .card{display:flex;flex-direction:column;gap:14px;height:100%;padding:26px 24px 22px;transition:translate .2s var(--pop),box-shadow .2s var(--pop),rotate .25s var(--pop)}
.sv-ben .card:hover{rotate:0deg!important;translate:-3px -4px;box-shadow:7.5px 8px 0 0 var(--sh)}
.sv-ben .card p{font-size:15.5px;line-height:1.5;color:var(--body)}
.sv-ben .det{margin-top:auto;display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:14px;border:1px dashed ${T.ink};background:var(--tile);font-size:12.5px;font-weight:600;color:${T.ink}}
.sv-ben .det i{display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:${T.white};border:1px solid ${T.ink};flex-shrink:0}
@container (max-width:1100px){.sv-ben .grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@container (max-width:600px){.sv-ben .grid{grid-template-columns:1fr;gap:18px;margin-top:44px}.sv-ben .card{rotate:0deg!important}}
`
const TILES = [T.peach, T.lime, T.pink, T.mint]
const TILT = [-1.5, 1.2, -1, 1.5]

export default function Benefits(props: any) {
    const { tone, eyebrow, title, body, cards, decor, sectionId } = props
    const list = lines(cards).map((l) => {
        const [t, d, det, ic] = cells(l)
        return {
            t,
            d: d || "",
            det: det || "",
            ic: ICON_NAMES.includes(ic) ? ic : "sparkles",
        }
    })
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-ben"
            css={CSS}
            label="Benefits"
        >
            {decor && (
                <div className="sv-dec" aria-hidden="true">
                    <Planet
                        size={92}
                        fill={T.pink}
                        style={{ right: "4%", top: 90 }}
                        className="sv-bob"
                    />
                    <Sparkle
                        size={30}
                        fill={T.white}
                        style={{ left: "8%", top: 130 }}
                        delay={0.4}
                    />
                    <Sparkle
                        size={20}
                        fill={T.ink}
                        style={{ left: "14%", top: 190 }}
                        delay={1.5}
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
                <ul className="grid">
                    {list.map((c, i) => (
                        <Reveal as="li" key={i} delay={0.08 * i}>
                            <article
                                className="sv-card card"
                                style={{
                                    rotate: `${TILT[i % TILT.length]}deg`,
                                }}
                            >
                                <IconTile
                                    name={c.ic}
                                    tile={TILES[i % TILES.length]}
                                    size={56}
                                    icon={26}
                                />
                                <h3 className="sv-h4">{c.t}</h3>
                                <p>{c.d}</p>
                                {c.det && (
                                    <div
                                        className="det"
                                        style={{
                                            ["--tile" as any]:
                                                TILES[i % TILES.length],
                                        }}
                                    >
                                        <i>
                                            <Icon
                                                name="check"
                                                size={12}
                                                stroke={2.6}
                                            />
                                        </i>
                                        {c.det}
                                    </div>
                                )}
                            </article>
                        </Reveal>
                    ))}
                </ul>
            </div>
        </Section>
    )
}

addPropertyControls(Benefits, {
    tone: toneControl("butter"),
    ...headControls({
        eyebrow: "Benefits",
        title: "Built for security without\nslowing teams down.",
        body: "",
    }),
    cards: {
        type: ControlType.String,
        title: "Benefits",
        displayTextArea: true,
        description: "One per line: Title | Description | UI detail | icon",
        defaultValue:
            "Greater visibility | Understand where AI is used. | 248 AI assets mapped | eye\nFaster decisions | Prioritize risks with clear context. | 12 findings prioritized | zap\nConsistent controls | Establish organization-wide guardrails. | 36 guardrails active | lock\nConfident adoption | Give teams a clearer path to secure AI. | Clear review path for new tools | sparkles",
    },
    decor: decorControl,
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "benefits",
    },
})

// Shared control types verified.
