// SECUVANTA NotFound: custom 404. An isolated network node with a broken connection (minimal, no cartoon alarms),
// "ERROR 404" eyebrow, heading, description, primary + secondary CTAs and optional quick links. Buttons go
// full-width on phones. Pair it with the Navbar and the Footer "Simple" variant.
// Quick links are lines: "Label | /link".
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import {
    Section,
    Title,
    Reveal,
    Btn,
    lines,
    cells,
    toneControl,
    T,
} from "./Kit.tsx"
import { Visual } from "./Visuals.tsx"

const CSS = `
.sv-404{padding:168px 0 120px;min-height:100vh;display:flex;align-items:center}
.sv-404 .grid{display:grid;grid-template-columns:minmax(0,6fr) minmax(0,5fr);gap:56px;align-items:center}
.sv-404 .copy{display:flex;flex-direction:column;align-items:flex-start;gap:22px}
.sv-404 .ctas{display:flex;flex-wrap:wrap;gap:14px;margin-top:6px}
.sv-404 .links{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-top:10px}
.sv-404 .links span{font-size:13px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--mute);margin-right:4px}
.sv-404 .links a{display:inline-flex;align-items:center;height:36px;padding:0 14px;border-radius:999px;border:1px solid var(--line);background:${T.white};font-weight:600;font-size:14px;color:${T.ink};transition:translate .2s var(--pop),box-shadow .2s var(--pop)}
.sv-404 .links a:hover{translate:-2px -2px;box-shadow:3px 3px 0 0 ${T.ink}}
@container (max-width:900px){.sv-404 .grid{grid-template-columns:1fr;gap:32px}.sv-404 .art{order:-1;max-width:440px}}
@container (max-width:600px){.sv-404{padding:128px 0 80px}.sv-404 .ctas{width:100%}.sv-404 .ctas .sv-btn{flex:1 1 100%}}
`

export default function NotFound(props: any) {
    const {
        tone,
        eyebrow,
        title,
        body,
        primaryLabel,
        primaryLink,
        secondaryLabel,
        secondaryLink,
        linksLabel,
        links,
    } = props
    const list = lines(links).map((l) => {
        const [label, href] = cells(l)
        return { label, href: href || "#" }
    })
    return (
        <Section
            tone={tone}
            className="sv-404"
            css={CSS}
            label="Page not found"
        >
            <div className="sv-wrap">
                <div className="grid">
                    <div className="copy">
                        {eyebrow && (
                            <Reveal now>
                                <p className="sv-eyebrow">{eyebrow}</p>
                            </Reveal>
                        )}
                        <Title
                            as="h1"
                            text={title}
                            className="sv-h1"
                            now
                            delay={0.1}
                        />
                        {body && (
                            <Reveal delay={0.2} now>
                                <p className="sv-lead">{body}</p>
                            </Reveal>
                        )}
                        <Reveal delay={0.3} className="ctas" now>
                            <Btn
                                label={primaryLabel}
                                href={primaryLink || "/"}
                                arrow
                            />
                            <Btn
                                label={secondaryLabel}
                                href={secondaryLink}
                                variant="secondary"
                            />
                        </Reveal>
                        {list.length > 0 && (
                            <Reveal delay={0.4} className="links" now>
                                {linksLabel && <span>{linksLabel}</span>}
                                {list.map((l, i) => (
                                    <a key={i} href={l.href}>
                                        {l.label}
                                    </a>
                                ))}
                            </Reveal>
                        )}
                    </div>
                    <Reveal delay={0.2} y={30} className="art" now>
                        <Visual kind="broken" />
                    </Reveal>
                </div>
            </div>
        </Section>
    )
}

addPropertyControls(NotFound, {
    tone: toneControl("cream"),
    eyebrow: {
        type: ControlType.String,
        title: "Eyebrow",
        defaultValue: "Error 404",
    },
    title: {
        type: ControlType.String,
        title: "Title",
        displayTextArea: true,
        defaultValue: "This signal went *missing.*",
    },
    body: {
        type: ControlType.String,
        title: "Body",
        displayTextArea: true,
        defaultValue:
            "The page you're looking for may have moved, expired, or no longer exists. Let's get you back to a secure starting point.",
    },
    primaryLabel: {
        type: ControlType.String,
        title: "Primary CTA",
        defaultValue: "Back to Home",
    },
    primaryLink: {
        type: ControlType.Link,
        title: "Primary link",
        defaultValue: "/",
    },
    secondaryLabel: {
        type: ControlType.String,
        title: "Secondary CTA",
        defaultValue: "Explore Platform",
    },
    secondaryLink: {
        type: ControlType.Link,
        title: "Secondary link",
        defaultValue: "/platform",
    },
    linksLabel: {
        type: ControlType.String,
        title: "Links label",
        defaultValue: "Or try",
    },
    links: {
        type: ControlType.String,
        title: "Quick links",
        displayTextArea: true,
        description: "One per line: Label | /link",
        defaultValue:
            "Platform | /platform\nSolutions | /solutions\nResources | /resources\nContact | /contact",
    },
})
