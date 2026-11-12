// SECUVANTA Steps: a numbered journey. Big numbered sticker circles on a dashed progress line, each with a title,
// one-liner and a small status chip (the "mini UI state" for that step). A marker travels along the line and the
// active step lights up in turn. Works for 3 to 6 steps; becomes a vertical list on small screens.
// Steps are lines: "Title | Description | status chip".
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import {
    Section,
    Head,
    Reveal,
    Icon,
    useTicker,
    lines,
    cells,
    headControls,
    toneControl,
    T,
} from "./Kit.tsx"

const CSS = `
.sv-steps .track{position:relative;display:grid;grid-template-columns:repeat(var(--n,5),minmax(0,1fr));gap:20px;margin-top:72px}
.sv-steps .line{position:absolute;left:calc(100% / var(--n,5) / 2);right:calc(100% / var(--n,5) / 2);top:36px;height:2px;background:repeating-linear-gradient(90deg,var(--line) 0 8px,transparent 8px 16px)}
.sv-steps .line i{position:absolute;left:0;top:0;height:100%;background:${T.orange};transition:width .6s var(--e)}
.sv-steps .st{position:relative;display:flex;flex-direction:column;align-items:center;text-align:center;gap:14px}
.sv-steps .no{position:relative;z-index:1;display:grid;place-items:center;width:72px;height:72px;border-radius:50%;background:${T.white};border:1.5px solid ${T.ink};box-shadow:3px 3px 0 0 ${T.ink};font-family:var(--display);font-weight:800;font-size:22px;color:${T.ink};transition:background-color .35s,translate .25s var(--pop),box-shadow .25s var(--pop)}
.sv-steps .st[data-on] .no{background:${T.butter};translate:-2px -3px;box-shadow:5px 6px 0 0 ${T.ink}}
.sv-steps .st[data-done] .no{background:${T.lime}}
.sv-steps .st h3{font-family:var(--display);font-weight:700;font-size:clamp(16px,1.35cqw,19px);line-height:1.2;color:var(--text)}
.sv-steps .st p{font-size:14.5px;line-height:1.5;color:var(--body);max-width:260px}
.sv-steps .chip{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 11px;border-radius:999px;border:1px dashed ${T.ink};background:${T.white};font-size:12px;font-weight:600;color:${T.ink};transition:background-color .35s}
.sv-steps .st[data-on] .chip{background:${T.butter};border-style:solid}
@container (max-width:900px){.sv-steps .track{grid-template-columns:1fr;gap:26px;margin-top:48px}.sv-steps .line{left:35px;right:auto;top:36px;bottom:36px;width:2px;height:auto;background:repeating-linear-gradient(180deg,var(--line) 0 8px,transparent 8px 16px)}.sv-steps .line i{display:none}
  .sv-steps .st{display:grid;grid-template-columns:72px 1fr;align-items:start;text-align:left;column-gap:18px;row-gap:6px}.sv-steps .st .no{grid-row:span 3}.sv-steps .st p{max-width:none}.sv-steps .chip{justify-self:start}}
`

export default function Steps(props: any) {
    const { tone, eyebrow, title, body, steps, sectionId } = props
    const list = lines(steps).map((l) => {
        const [t, d, chip] = cells(l)
        return { t, d: d || "", chip: chip || "" }
    })
    const n = Math.max(1, Math.min(6, list.length))
    const [ref, on] = useTicker(n, 1800)
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-steps"
            css={CSS}
            label="Steps"
        >
            <div className="sv-wrap">
                <Head
                    eyebrow={eyebrow}
                    title={title}
                    body={body}
                    align="center"
                />
                <div ref={ref} className="track" style={{ ["--n" as any]: n }}>
                    <span className="line" aria-hidden="true">
                        <i
                            style={{
                                width:
                                    n > 1 ? `${(on / (n - 1)) * 100}%` : "0%",
                            }}
                        />
                    </span>
                    {list.slice(0, n).map((s, i) => (
                        <Reveal key={i} delay={0.08 * i} className="st">
                            <div
                                className="st"
                                data-on={i === on ? "" : undefined}
                                data-done={i < on ? "" : undefined}
                                style={{ display: "contents" }}
                            >
                                <span className="no" aria-hidden="true">
                                    {i < on ? (
                                        <Icon
                                            name="check"
                                            size={26}
                                            stroke={2.6}
                                        />
                                    ) : (
                                        String(i + 1).padStart(2, "0")
                                    )}
                                </span>
                                <h3>
                                    <span className="sv-sr">
                                        Step {i + 1}:{" "}
                                    </span>
                                    {s.t}
                                </h3>
                                {s.d && <p>{s.d}</p>}
                                {s.chip && (
                                    <span className="chip">{s.chip}</span>
                                )}
                            </div>
                        </Reveal>
                    ))}
                </div>
            </div>
        </Section>
    )
}

addPropertyControls(Steps, {
    tone: toneControl("cream"),
    ...headControls({
        eyebrow: "Use-case workflow",
        title: "From discovery to remediation,\nwith *fewer blind spots.*",
        body: "",
    }),
    steps: {
        type: ControlType.String,
        title: "Steps",
        displayTextArea: true,
        description: "3–6 lines: Title | Description | status chip",
        defaultValue:
            "Discover | Discover an unknown AI asset. | 1 new asset found\nAssess | Assess its risk and access. | Risk: High\nAssign | Assign an owner and remediation task. | Owner: IT Ops\nApply | Apply the appropriate policy. | Policy applied\nReview | Review the updated security status. | Status: Secured",
    },
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "workflow",
    },
})
