// SECUVANTA Split: the workhorse feature row for inner pages. Copy on one side (optional meta chips, eyebrow,
// headline, body, key-point chips and CTAs), an illustration from the Visuals library on the other. "Visual side"
// swaps sides so stacked rows zig-zag. The illustration sits on a pastel sticker plate that tilts slightly on hover.
// Key points are "Point · Point · Point" (or one per line).
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import {
    Section,
    Title,
    Reveal,
    Btn,
    TextLink,
    Icon,
    lines,
    toneControl,
    T,
} from "./Kit.tsx"
import { Visual, SPLIT_VISUALS } from "./Visuals.tsx"

const CSS = `
.sv-split .grid{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:72px;align-items:center}
.sv-split .grid[data-flip] .copy{order:2}
.sv-split .copy{display:flex;flex-direction:column;align-items:flex-start;gap:20px}
.sv-split .meta{display:flex;flex-wrap:wrap;gap:8px}
.sv-split .pts{display:flex;flex-wrap:wrap;gap:10px;margin-top:4px}
.sv-split .pt{display:inline-flex;align-items:center;gap:8px;height:38px;padding:0 14px 0 6px;border-radius:999px;background:${T.white};border:1px solid ${T.ink};box-shadow:2px 2px 0 0 ${T.ink};font-weight:600;font-size:14px;color:${T.ink}}
.sv-split .pt i{display:grid;place-items:center;width:26px;height:26px;border-radius:50%;background:${T.butter};border:1px solid ${T.ink}}
.sv-split .ctas{display:flex;flex-wrap:wrap;align-items:center;gap:18px;margin-top:8px}
.sv-split .plate{position:relative;padding:28px 22px;border-radius:30px;background:var(--plate);border:1.5px solid ${T.ink};box-shadow:6px 7px 0 0 ${T.ink};transition:rotate .3s var(--pop),translate .3s var(--pop)}
.sv-split .plate:hover{rotate:-.6deg;translate:-2px -3px}
@container (max-width:1000px){.sv-split .grid{grid-template-columns:1fr;gap:48px}.sv-split .grid[data-flip] .copy{order:0}}
@container (max-width:680px){.sv-split .plate{padding:16px 10px;border-radius:22px}}
`
const PLATES: Record<string, string> = {
    white: T.cream,
    cream: T.white,
    peach: T.cream,
    butter: T.white,
    ink: T.cream,
}

export default function Split(props: any) {
    const {
        tone,
        meta,
        eyebrow,
        title,
        body,
        points,
        ctaLabel,
        ctaLink,
        linkLabel,
        linkUrl,
        visual,
        plate,
        flip,
        sectionId,
    } = props
    const pts = String(points || "").includes("·")
        ? String(points)
              .split("·")
              .map((s) => s.trim())
              .filter(Boolean)
        : lines(points)
    const metas = String(meta || "")
        .split("·")
        .map((s) => s.trim())
        .filter(Boolean)
    const plateColor =
        plate === "auto"
            ? PLATES[tone] || T.cream
            : (T as any)[plate] || T.cream
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-split"
            css={CSS}
            label={String(title || "").replace(/[*_]/g, "")}
        >
            <div className="sv-wrap">
                <div className="grid" data-flip={flip ? "" : undefined}>
                    <div className="copy">
                        {metas.length > 0 && (
                            <Reveal className="meta">
                                {metas.map((m, i) => (
                                    <span
                                        key={i}
                                        className="sv-chip"
                                        style={{
                                            background:
                                                i === 0 ? T.butter : T.white,
                                        }}
                                    >
                                        {m}
                                    </span>
                                ))}
                            </Reveal>
                        )}
                        {eyebrow && (
                            <Reveal>
                                <p className="sv-eyebrow">{eyebrow}</p>
                            </Reveal>
                        )}
                        <Title
                            text={title}
                            className="sv-h2"
                            style={{ fontSize: "clamp(28px,3.1cqw,44px)" }}
                        />
                        {body && (
                            <Reveal delay={0.1}>
                                <p
                                    className="sv-lead"
                                    style={{
                                        fontSize: "clamp(17px,1.5cqw,20px)",
                                    }}
                                >
                                    {body}
                                </p>
                            </Reveal>
                        )}
                        {pts.length > 0 && (
                            <Reveal delay={0.18} className="pts">
                                {pts.map((p, i) => (
                                    <span key={i} className="pt">
                                        <i>
                                            <Icon
                                                name="check"
                                                size={13}
                                                stroke={2.6}
                                            />
                                        </i>
                                        {p}
                                    </span>
                                ))}
                            </Reveal>
                        )}
                        {(ctaLabel || linkLabel) && (
                            <Reveal delay={0.24} className="ctas">
                                <Btn label={ctaLabel} href={ctaLink} arrow />
                                <TextLink label={linkLabel} href={linkUrl} />
                            </Reveal>
                        )}
                    </div>
                    <Reveal delay={0.1} y={36}>
                        <div
                            className="plate"
                            style={{ ["--plate" as any]: plateColor }}
                        >
                            <Visual kind={visual} />
                        </div>
                    </Reveal>
                </div>
            </div>
        </Section>
    )
}

addPropertyControls(Split, {
    tone: toneControl("white"),
    meta: {
        type: ControlType.String,
        title: "Meta chips",
        defaultValue: "",
        description:
            "Optional chips above the eyebrow, e.g. AI Security · 8 min read",
    },
    eyebrow: {
        type: ControlType.String,
        title: "Eyebrow",
        defaultValue: "AI discovery",
    },
    title: {
        type: ControlType.String,
        title: "Title",
        displayTextArea: true,
        defaultValue: "Know what AI is running across your *organization.*",
        description:
            "*stars* = yellow marker · _underscores_ = orange · new line = line break.",
    },
    body: {
        type: ControlType.String,
        title: "Body",
        displayTextArea: true,
        defaultValue:
            "Build a centralized inventory of AI models, applications, agents, and integrations to reduce visibility gaps.",
    },
    points: {
        type: ControlType.String,
        title: "Key points",
        displayTextArea: true,
        defaultValue:
            "Asset inventory · Ownership context · Environment mapping",
        description:
            "Separate with · or put one per line. Leave empty to hide.",
    },
    ctaLabel: {
        type: ControlType.String,
        title: "Button label",
        defaultValue: "",
    },
    ctaLink: { type: ControlType.Link, title: "Button link", defaultValue: "" },
    linkLabel: {
        type: ControlType.String,
        title: "Text link label",
        defaultValue: "",
    },
    linkUrl: { type: ControlType.Link, title: "Text link", defaultValue: "" },
    visual: {
        type: ControlType.Enum,
        title: "Visual",
        options: SPLIT_VISUALS.options,
        optionTitles: SPLIT_VISUALS.optionTitles,
        defaultValue: "inventory",
    },
    plate: {
        type: ControlType.Enum,
        title: "Plate color",
        options: ["auto", "cream", "white", "peach", "butter", "mint", "blush"],
        optionTitles: [
            "Auto",
            "Cream",
            "White",
            "Peach",
            "Butter",
            "Mint",
            "Blush",
        ],
        defaultValue: "auto",
    },
    flip: {
        type: ControlType.Boolean,
        title: "Visual side",
        defaultValue: false,
        enabledTitle: "Left",
        disabledTitle: "Right",
    },
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "discovery",
    },
})

// OAuth Navigator integration

// Shared control types verified.
