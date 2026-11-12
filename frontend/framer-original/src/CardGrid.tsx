// SECUVANTA CardGrid: a grid of icon sticker cards for principles, topics or capabilities. Each card has a pastel icon
// tile, title, one-line description and an optional link; cards lift with Pluto's springy hover. Columns follow the
// number of cards (up to 5 across) and collapse on smaller screens.
// Cards are lines: "Title | Description | icon | /link (optional)".
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import {
    Section,
    Head,
    Reveal,
    Icon,
    IconTile,
    lines,
    cells,
    headControls,
    toneControl,
    T,
    ICON_NAMES,
} from "./Kit.tsx"

const CSS = `
.sv-cg .grid{display:grid;grid-template-columns:repeat(var(--cols,4),minmax(0,1fr));gap:22px;margin-top:64px}
.sv-cg .card{display:flex;flex-direction:column;gap:14px;height:100%;padding:24px 22px}
.sv-cg .card h3{font-family:var(--display);font-weight:700;font-size:clamp(17px,1.5cqw,21px);line-height:1.2;color:var(--text)}
.sv-cg .card p{font-size:15px;line-height:1.5;color:var(--body)}
.sv-cg .card .go{margin-top:auto;display:inline-flex;align-items:center;gap:6px;font-weight:600;font-size:14px;color:var(--text)}
.sv-cg a.card .go svg{transition:translate .2s var(--pop)}
.sv-cg a.card:hover .go svg{translate:3px 0}
.sv-cg [data-style="flat"] .card{box-shadow:none;border-radius:20px}
@container (max-width:1100px){.sv-cg .grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@container (max-width:800px){.sv-cg .grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@container (max-width:520px){.sv-cg .grid{grid-template-columns:1fr;gap:16px;margin-top:44px}}
`
const TILES = [T.butter, T.peach, T.lime, T.pink, T.mint, T.coral]

export default function CardGrid(props: any) {
    const {
        tone,
        eyebrow,
        title,
        body,
        items,
        linkText,
        cardStyle,
        sectionId,
    } = props
    const list = lines(items).map((l) => {
        const [t, d, ic, href] = cells(l)
        return {
            t,
            d: d || "",
            ic: ICON_NAMES.includes(ic) ? ic : "sparkles",
            href: href || "",
        }
    })
    const cols = Math.max(1, Math.min(5, list.length))
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-cg"
            css={CSS}
            label="Cards"
        >
            <div className="sv-wrap" data-style={cardStyle}>
                <Head
                    eyebrow={eyebrow}
                    title={title}
                    body={body}
                    align="center"
                />
                <ul className="grid" style={{ ["--cols" as any]: cols }}>
                    {list.map((c, i) => {
                        const inner = (
                            <>
                                <IconTile
                                    name={c.ic}
                                    tile={TILES[i % TILES.length]}
                                    size={52}
                                    icon={24}
                                />
                                <h3>{c.t}</h3>
                                {c.d && <p>{c.d}</p>}
                                {c.href && linkText && (
                                    <span className="go">
                                        {linkText}
                                        <Icon
                                            name="arrow-right"
                                            size={15}
                                            stroke={2}
                                        />
                                    </span>
                                )}
                            </>
                        )
                        return (
                            <Reveal as="li" key={i} delay={0.06 * i}>
                                {c.href ? (
                                    <a
                                        className="sv-card hover card"
                                        href={c.href}
                                    >
                                        {inner}
                                    </a>
                                ) : (
                                    <article className="sv-card hover card">
                                        {inner}
                                    </article>
                                )}
                            </Reveal>
                        )
                    })}
                </ul>
            </div>
        </Section>
    )
}

addPropertyControls(CardGrid, {
    tone: toneControl("white"),
    ...headControls({
        eyebrow: "Principles",
        title: "What guides how we *build.*",
        body: "",
    }),
    items: {
        type: ControlType.String,
        title: "Cards",
        displayTextArea: true,
        description:
            "One per line: Title | Description | icon | /link (optional)",
        defaultValue:
            "Clarity over complexity | Make important security information easier to understand. | eye\nProtection by design | Treat security as part of the AI lifecycle, not an afterthought. | shield-check\nHuman-led decisions | Give teams the context needed to make informed choices. | users\nResponsible innovation | Help organizations pursue AI adoption with stronger oversight. | sparkles",
    },
    linkText: {
        type: ControlType.String,
        title: "Card link text",
        defaultValue: "Explore",
        description: "Shown on cards that have a link.",
    },
    cardStyle: {
        type: ControlType.Enum,
        title: "Card style",
        options: ["sticker", "flat"],
        optionTitles: ["Sticker (shadow)", "Flat"],
        defaultValue: "sticker",
        displaySegmentedControl: true,
    },
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "principles",
    },
})
