// SECUVANTA PageHero: hero for inner pages. Orange eyebrow, chunky headline that rises in on load, lead copy, up to
// two pill CTAs and a wide illustration from the Visuals library (pipeline, role panels, editorial, ecosystem,
// posture dashboard) sitting on a soft cream "ground" with sparkles. Leaves room for the fixed navbar.
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import {
    Section,
    Title,
    Reveal,
    Btn,
    Sparkle,
    Planet,
    toneControl,
    decorControl,
    T,
} from "./Kit.tsx"
import { Visual, HERO_VISUALS } from "./Visuals.tsx"

const CSS = `
@container(max-width:1000px){.sv-ph .sky{display:none}}
.sv-ph{padding:176px 0 112px;overflow:hidden}
.sv-ph .copy{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;text-align:center;gap:22px;max-width:900px;margin:0 auto}
.sv-ph .copy .sv-lead{max-width:680px}
.sv-ph .ctas{display:flex;flex-wrap:wrap;justify-content:center;gap:14px;margin-top:6px}
.sv-ph .art{position:relative;z-index:1;max-width:1100px;margin:72px auto 0}
.sv-ph .sky{position:absolute;inset:0;pointer-events:none}
@container (max-width:1000px){.sv-ph{padding:150px 0 96px}.sv-ph .art{margin-top:56px}}
@container (max-width:680px){.sv-ph{padding:128px 0 72px}.sv-ph .ctas{width:100%}.sv-ph .ctas .sv-btn{flex:1 1 100%}.sv-ph .art{margin-top:40px}}
`

export default function PageHero(props: any) {
    const {
        tone,
        eyebrow,
        title,
        body,
        primaryLabel,
        primaryLink,
        primaryAnchor,
        secondaryLabel,
        secondaryLink,
        visual,
        decor,
        sectionId,
    } = props
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-ph"
            css={CSS}
            label="Page hero"
        >
            {decor && (
                <div className="sky sv-dec" aria-hidden="true">
                    {tone === "peach" && <div className="sv-plusfield" />}
                    <Planet
                        size={88}
                        fill={T.lime}
                        style={{ left: "5%", top: 190 }}
                        className="sv-bob"
                    />
                    <Planet
                        size={64}
                        fill={T.pink}
                        ring={false}
                        style={{ right: "7%", top: 250 }}
                        className="sv-bob"
                    />
                    <Sparkle
                        size={30}
                        fill={T.ink}
                        style={{ left: "17%", top: 140 }}
                        delay={0.5}
                    />
                    <Sparkle
                        size={22}
                        fill={T.butter}
                        style={{ right: "19%", top: 150 }}
                        delay={1.5}
                    />
                </div>
            )}
            <div className="sv-wrap">
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
                        <Reveal delay={0.25} now>
                            <p className="sv-lead">{body}</p>
                        </Reveal>
                    )}
                    {(primaryLabel || secondaryLabel) && (
                        <Reveal delay={0.35} className="ctas" now>
                            <Btn
                                label={primaryLabel}
                                href={primaryAnchor || primaryLink}
                                arrow
                            />
                            <Btn
                                label={secondaryLabel}
                                href={secondaryLink}
                                variant="secondary"
                            />
                        </Reveal>
                    )}
                </div>
                {visual !== "none" && (
                    <Reveal delay={0.3} y={40} className="art" now>
                        <Visual kind={visual} />
                    </Reveal>
                )}
            </div>
        </Section>
    )
}

addPropertyControls(PageHero, {
    tone: toneControl("cream"),
    eyebrow: {
        type: ControlType.String,
        title: "Eyebrow",
        defaultValue: "Platform",
    },
    title: {
        type: ControlType.String,
        title: "Title",
        displayTextArea: true,
        defaultValue: "Complete visibility across your *AI lifecycle.*",
        description:
            "*stars* = yellow marker · _underscores_ = orange · new line = line break.",
    },
    body: {
        type: ControlType.String,
        title: "Body",
        displayTextArea: true,
        defaultValue:
            "From AI discovery to ongoing protection, Secuvanta helps security teams understand their AI environment and apply controls where they matter.",
    },
    primaryLabel: {
        type: ControlType.String,
        title: "Primary CTA",
        defaultValue: "Request a Platform Demo",
    },
    primaryLink: {
        type: ControlType.Link,
        title: "Primary link",
        defaultValue: "/contact",
    },
    primaryAnchor: {
        type: ControlType.String,
        title: "Primary anchor",
        defaultValue: "",
        description:
            "Optional. Overrides the link, e.g. #security to scroll on the same page.",
    },
    secondaryLabel: {
        type: ControlType.String,
        title: "Secondary CTA",
        defaultValue: "",
    },
    secondaryLink: {
        type: ControlType.Link,
        title: "Secondary link",
        defaultValue: "",
    },
    visual: {
        type: ControlType.Enum,
        title: "Visual",
        options: HERO_VISUALS.options,
        optionTitles: HERO_VISUALS.optionTitles,
        defaultValue: "pipeline",
    },
    decor: decorControl,
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "top",
    },
})

// OAuth Navigator integration

// Shared control types verified.
