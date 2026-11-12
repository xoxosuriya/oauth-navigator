// SECUVANTA CTACard: a compact bordered call-to-action card ("Not ready for a demo?") with a small platform diagram
// thumbnail, headline, one line of copy and an arrow link. The whole card is the link and lifts on hover.
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import { Section, Reveal, Icon, toneControl, T } from "./Kit.tsx"

const CSS = `
.sv-cc{padding:96px 0}
.sv-cc a.card{display:grid;grid-template-columns:200px minmax(0,1fr) auto;gap:32px;align-items:center;max-width:1040px;margin:0 auto;padding:28px 32px 28px 28px;border-radius:28px;background:${T.white};border:1.5px solid ${T.ink};box-shadow:5px 6px 0 0 ${T.ink};color:${T.ink};transition:translate .2s var(--pop),box-shadow .2s var(--pop)}
.sv-cc a.card:hover{translate:-3px -3px;box-shadow:8px 9px 0 0 ${T.ink}}
.sv-cc .thumb{height:130px;border-radius:18px;border:1.2px solid ${T.ink};background:${T.cream};overflow:hidden}
.sv-cc .thumb svg{width:100%;height:100%}
.sv-cc h2{font-family:var(--display);font-weight:700;font-size:clamp(22px,2.2cqw,30px);line-height:1.15}
.sv-cc p{margin-top:8px;font-size:16px;line-height:1.5;color:${T.body}}
.sv-cc .go{display:inline-flex;align-items:center;gap:12px;font-weight:700;font-size:14px;letter-spacing:.09em;text-transform:uppercase;white-space:nowrap}
.sv-cc .go i{display:grid;place-items:center;width:52px;height:52px;border-radius:50%;background:${T.butter};border:1.5px solid ${T.ink};transition:translate .2s var(--pop)}
.sv-cc a.card:hover .go i{translate:4px 0}
@container (max-width:820px){.sv-cc a.card{grid-template-columns:1fr;gap:20px;padding:22px}.sv-cc .thumb{height:150px}}
`

export default function CTACard(props: any) {
    const { tone, title, body, linkLabel, link, sectionId } = props
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-cc"
            css={CSS}
            label="Next step"
            pad={false}
        >
            <div className="sv-wrap">
                <Reveal y={30}>
                    <a className="card" href={link || "#"}>
                        <span className="thumb" aria-hidden="true">
                            <svg viewBox="0 0 200 130">
                                {[
                                    [40, 35, T.butter],
                                    [100, 25, T.peach],
                                    [160, 40, T.lime],
                                    [70, 100, T.pink],
                                    [140, 100, T.mint],
                                ].map(([x, y, c]: any, i) => (
                                    <g key={i}>
                                        <line
                                            x1="100"
                                            y1="68"
                                            x2={x}
                                            y2={y}
                                            stroke={T.ink}
                                            strokeWidth="1.2"
                                        />
                                        <rect
                                            x={x - 13}
                                            y={y - 11}
                                            width="26"
                                            height="22"
                                            rx="7"
                                            fill={c}
                                            stroke={T.ink}
                                            strokeWidth="1.2"
                                        />
                                    </g>
                                ))}
                                <circle cx="100" cy="68" r="16" fill={T.ink} />
                                <path
                                    d="m93 68 5 5 9-10"
                                    stroke={T.white}
                                    strokeWidth="2.2"
                                    fill="none"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                            </svg>
                        </span>
                        <span>
                            <h2>{title}</h2>
                            {body && <p>{body}</p>}
                        </span>
                        <span className="go">
                            {linkLabel}
                            <i>
                                <Icon
                                    name="arrow-right"
                                    size={20}
                                    stroke={2.2}
                                />
                            </i>
                        </span>
                    </a>
                </Reveal>
            </div>
        </Section>
    )
}

addPropertyControls(CTACard, {
    tone: toneControl("cream"),
    title: {
        type: ControlType.String,
        title: "Title",
        defaultValue: "Not ready for a demo?",
    },
    body: {
        type: ControlType.String,
        title: "Body",
        displayTextArea: true,
        defaultValue:
            "Explore our platform overview and learn more about the AI security lifecycle.",
    },
    linkLabel: {
        type: ControlType.String,
        title: "Link label",
        defaultValue: "Explore the Platform",
    },
    link: { type: ControlType.Link, title: "Link", defaultValue: "/platform" },
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "explore",
    },
})
