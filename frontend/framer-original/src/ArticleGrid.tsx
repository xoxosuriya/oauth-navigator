// SECUVANTA ArticleGrid: editorial card grid for the Resources page. Each card has a generated abstract thumbnail
// (asset map, data bars, orbit, shield grid, flow) in brand pastels, or an uploaded image, plus category chip, title,
// read time and link. The first card can be featured (wide). Articles are lines:
// "Title | Category | Read time | /link | image URL (optional)".
// CMS tip: to let buyers add articles from Framer's CMS, replace this grid with a Collection List styled the same way.
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import {
    Section,
    Head,
    Reveal,
    Icon,
    lines,
    cells,
    headControls,
    toneControl,
    T,
} from "./Kit.tsx"

const CSS = `
.sv-ag .grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px;margin-top:64px}
.sv-ag .grid[data-feat] li:first-child{grid-column:span 2}
.sv-ag .card{display:flex;flex-direction:column;height:100%;overflow:hidden;padding:0}
.sv-ag .thumb{position:relative;aspect-ratio:16/10;border-bottom:1.5px solid ${T.ink};overflow:hidden;background:var(--c)}
.sv-ag .grid[data-feat] li:first-child .thumb{aspect-ratio:16/8}
.sv-ag .thumb img{width:100%;height:100%;object-fit:cover}
.sv-ag .thumb svg{position:absolute;inset:0;width:100%;height:100%}
.sv-ag .body{display:flex;flex-direction:column;gap:12px;padding:20px 22px 22px;flex:1}
.sv-ag .cat{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.sv-ag h3{font-family:var(--display);font-weight:700;font-size:clamp(17px,1.5cqw,21px);line-height:1.22;color:var(--text)}
.sv-ag .grid[data-feat] li:first-child h3{font-size:clamp(20px,2cqw,28px)}
.sv-ag .foot{margin-top:auto;display:flex;align-items:center;justify-content:space-between;font-size:13.5px;color:var(--mute)}
.sv-ag .foot b{display:inline-flex;align-items:center;gap:6px;font-weight:600;color:var(--text)}
.sv-ag a.card:hover .foot svg{translate:3px 0}
.sv-ag .foot svg{transition:translate .2s var(--pop)}
.sv-ag .note{margin-top:22px;text-align:center;font-size:13px;color:var(--mute)}
@container (max-width:1000px){.sv-ag .grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@container (max-width:620px){.sv-ag .grid{grid-template-columns:1fr;gap:18px;margin-top:44px}.sv-ag .grid[data-feat] li:first-child{grid-column:auto}}
`
const FILLS = [T.butter, T.peach, T.lime, T.pink, T.mint, T.coral]

function Thumb({ i }: { i: number }) {
    const k = i % 5
    const s = { stroke: T.ink, strokeWidth: 1.4, fill: "none" } as any
    return (
        <svg
            viewBox="0 0 320 200"
            preserveAspectRatio="xMidYMid slice"
            aria-hidden="true"
        >
            {k === 0 && (
                <g>
                    {[
                        [70, 60],
                        [160, 40],
                        [250, 70],
                        [100, 150],
                        [220, 150],
                    ].map(([x, y], j) => (
                        <g key={j}>
                            <line x1="160" y1="105" x2={x} y2={y} {...s} />
                            <circle
                                cx={x}
                                cy={y}
                                r="13"
                                fill={T.white}
                                stroke={T.ink}
                                strokeWidth="1.4"
                            />
                        </g>
                    ))}
                    <circle cx="160" cy="105" r="24" fill={T.ink} />
                    <circle
                        cx="250"
                        cy="70"
                        r="6"
                        fill={T.orange}
                        stroke={T.ink}
                    />
                </g>
            )}
            {k === 1 && (
                <g>
                    {[40, 90, 60, 120, 80, 140].map((h, j) => (
                        <rect
                            key={j}
                            x={40 + j * 42}
                            y={170 - h}
                            width="28"
                            height={h}
                            rx="7"
                            fill={
                                [
                                    T.white,
                                    T.butter,
                                    T.white,
                                    T.lime,
                                    T.white,
                                    T.orange,
                                ][j]
                            }
                            stroke={T.ink}
                            strokeWidth="1.4"
                        />
                    ))}
                    <path
                        d="M40 60 L120 80 L200 40 L280 50"
                        {...s}
                        strokeDasharray="5 6"
                    />
                </g>
            )}
            {k === 2 && (
                <g>
                    <ellipse
                        cx="160"
                        cy="100"
                        rx="130"
                        ry="50"
                        {...s}
                        transform="rotate(-12 160 100)"
                    />
                    <ellipse
                        cx="160"
                        cy="100"
                        rx="80"
                        ry="30"
                        {...s}
                        strokeDasharray="4 6"
                        transform="rotate(-12 160 100)"
                    />
                    <circle
                        cx="160"
                        cy="100"
                        r="22"
                        fill={T.white}
                        stroke={T.ink}
                        strokeWidth="1.4"
                    />
                    <circle
                        cx="282"
                        cy="74"
                        r="10"
                        fill={T.lime}
                        stroke={T.ink}
                        strokeWidth="1.4"
                    />
                    <circle
                        cx="70"
                        cy="140"
                        r="8"
                        fill={T.pink}
                        stroke={T.ink}
                        strokeWidth="1.4"
                    />
                </g>
            )}
            {k === 3 && (
                <g>
                    {Array.from({ length: 8 }, (_, j) => (
                        <line
                            key={"v" + j}
                            x1={j * 44}
                            y1="0"
                            x2={j * 44}
                            y2="200"
                            stroke={T.ink}
                            strokeOpacity=".15"
                        />
                    ))}
                    {Array.from({ length: 5 }, (_, j) => (
                        <line
                            key={"h" + j}
                            x1="0"
                            y1={j * 44}
                            x2="320"
                            y2={j * 44}
                            stroke={T.ink}
                            strokeOpacity=".15"
                        />
                    ))}
                    <path
                        d="M160 40 c16 12 32 16 46 16 v34 c0 28-20 46-46 56-26-10-46-28-46-56V56c14 0 30-4 46-16Z"
                        fill={T.white}
                        stroke={T.ink}
                        strokeWidth="1.6"
                    />
                    <path
                        d="m142 98 13 13 25-26"
                        stroke={T.ink}
                        strokeWidth="3"
                        fill="none"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                </g>
            )}
            {k === 4 && (
                <g>
                    {[
                        [50, "#fff"],
                        [130, T.butter],
                        [210, "#fff"],
                        [280, T.lime],
                    ].map(([x, c]: any, j) => (
                        <g key={j}>
                            {j > 0 && (
                                <line
                                    x1={x - 58}
                                    y1="100"
                                    x2={x - 22}
                                    y2="100"
                                    {...s}
                                    strokeDasharray="4 5"
                                />
                            )}
                            <rect
                                x={x - 22}
                                y="78"
                                width="44"
                                height="44"
                                rx="12"
                                fill={c}
                                stroke={T.ink}
                                strokeWidth="1.4"
                            />
                        </g>
                    ))}
                    <circle cx="280" cy="100" r="8" fill={T.ink} />
                </g>
            )}
        </svg>
    )
}

export default function ArticleGrid(props: any) {
    const {
        tone,
        eyebrow,
        title,
        body,
        articles,
        featureFirst,
        readLabel,
        note,
        sectionId,
    } = props
    const list = lines(articles).map((l) => {
        const [t, cat, time, href, img] = cells(l)
        return {
            t,
            cat: cat || "",
            time: time || "",
            href: href || "",
            img: img || "",
        }
    })
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-ag"
            css={CSS}
            label="Articles"
        >
            <div className="sv-wrap">
                <Head
                    eyebrow={eyebrow}
                    title={title}
                    body={body}
                    align="center"
                />
                <ul className="grid" data-feat={featureFirst ? "" : undefined}>
                    {list.map((a, i) => {
                        const inner = (
                            <>
                                <div
                                    className="thumb"
                                    style={{
                                        ["--c" as any]: FILLS[i % FILLS.length],
                                    }}
                                >
                                    {a.img ? (
                                        <img
                                            src={a.img}
                                            alt=""
                                            loading="lazy"
                                        />
                                    ) : (
                                        <Thumb i={i} />
                                    )}
                                </div>
                                <div className="body">
                                    {a.cat && (
                                        <div className="cat">
                                            <span className="sv-chip white">
                                                {a.cat}
                                            </span>
                                        </div>
                                    )}
                                    <h3>{a.t}</h3>
                                    <div className="foot">
                                        <span>{a.time}</span>
                                        {a.href && readLabel && (
                                            <b>
                                                {readLabel}
                                                <Icon
                                                    name="arrow-right"
                                                    size={15}
                                                    stroke={2}
                                                />
                                            </b>
                                        )}
                                    </div>
                                </div>
                            </>
                        )
                        return (
                            <Reveal as="li" key={i} delay={0.06 * i}>
                                {a.href ? (
                                    <a
                                        className="sv-card hover card"
                                        href={a.href}
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
                {note && <p className="note">{note}</p>}
            </div>
        </Section>
    )
}

addPropertyControls(ArticleGrid, {
    tone: toneControl("white"),
    ...headControls({
        eyebrow: "Latest insights",
        title: "Ideas for a more secure *AI ecosystem.*",
        body: "",
    }),
    articles: {
        type: ControlType.String,
        title: "Articles",
        displayTextArea: true,
        description:
            "One per line: Title | Category | Read time | /link | image URL (optional)",
        defaultValue:
            "Understanding Shadow AI in the Enterprise | AI Security Fundamentals | 6 min read | #\nA Practical Framework for AI Risk Assessment | Risk Assessment | 9 min read | #\nSecuring AI Agents and Connected Tools | AI Agents & Tool Access | 7 min read | #\nBuilding an Effective AI Governance Program | Governance & Compliance | 8 min read | #\nFrom Security Findings to Remediation | Security Operations | 5 min read | #",
    },
    featureFirst: {
        type: ControlType.Boolean,
        title: "Feature first",
        defaultValue: true,
        enabledTitle: "Wide",
        disabledTitle: "Normal",
    },
    readLabel: {
        type: ControlType.String,
        title: "Read label",
        defaultValue: "Read",
    },
    note: {
        type: ControlType.String,
        title: "Footnote",
        defaultValue:
            "Sample articles for demonstration. Replace with your own content.",
    },
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "insights",
    },
})
