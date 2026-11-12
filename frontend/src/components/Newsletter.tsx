// SECUVANTA Newsletter: a sticker email card with an abstract signal icon, headline, body and an inline email form.
// Validates the address, shows loading / success / error states and, when "Form endpoint" is set, POSTs
// { email } as JSON to it (e.g. a Formspree, ConvertKit or Zapier webhook URL). With no endpoint the form shows the
// success state locally so the template can be previewed. Connect a real service before going live.
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import {
    Section,
    Title,
    Reveal,
    Icon,
    Sparkle,
    Planet,
    toneControl,
    decorControl,
    T,
} from "./Kit.tsx"

const CSS = `
.sv-nl .card{position:relative;display:grid;grid-template-columns:auto minmax(0,1fr);gap:32px;align-items:center;max-width:1040px;margin:0 auto;padding:48px 52px;border-radius:32px;background:${T.white};border:1.5px solid ${T.ink};box-shadow:7px 8px 0 0 ${T.ink}}
.sv-nl .sig{display:grid;place-items:center;width:120px;height:120px;border-radius:50%;background:${T.butter};border:1.5px solid ${T.ink};box-shadow:4px 4px 0 0 ${T.ink}}
.sv-nl .copy{display:grid;gap:14px}
.sv-nl .copy .sv-h2{color:${T.ink};font-size:clamp(26px,2.8cqw,40px)}
.sv-nl .copy p.lead{font-size:16.5px;line-height:1.5;color:${T.body}}
.sv-nl form{display:flex;gap:10px;margin-top:8px}
.sv-nl input{flex:1;min-width:0;height:56px;padding:0 22px;border-radius:999px;border:1.5px solid ${T.ink};background:${T.cream};font-family:var(--sans);font-size:16px;color:${T.ink};outline:none;transition:box-shadow .2s var(--pop)}
.sv-nl input:focus{box-shadow:3px 3px 0 0 ${T.ink};background:${T.white}}
.sv-nl input[aria-invalid="true"]{border-color:${T.critical}}
.sv-nl button.sv-btn{--btn-bg:${T.ink};--btn-fg:${T.white}}
.sv-nl .msg{font-size:13.5px;font-weight:500;min-height:20px}
.sv-nl .msg.err{color:${T.critical}}
.sv-nl .msg.ok{display:inline-flex;align-items:center;gap:8px;color:${T.ink}}
.sv-nl .msg.ok i{display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:${T.lime};border:1px solid ${T.ink}}
.sv-nl .fine{font-size:12.5px;color:${T.mute}}
@container (max-width:800px){.sv-nl .card{grid-template-columns:1fr;padding:36px 24px;justify-items:start}.sv-nl .sig{width:84px;height:84px}}
@container (max-width:520px){.sv-nl form{flex-direction:column}.sv-nl form .sv-btn{width:100%}}
`

export default function Newsletter(props: any) {
    const {
        tone,
        title,
        body,
        placeholder,
        buttonLabel,
        successText,
        errorText,
        invalidText,
        endpoint,
        fineprint,
        decor,
        sectionId,
    } = props
    const [email, setEmail] = React.useState("")
    const [state, setState] = React.useState<
        "idle" | "loading" | "ok" | "error" | "invalid"
    >("idle")
    const id = React.useId ? React.useId() : "sv-nl-email"
    const submit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()))
            return setState("invalid")
        setState("loading")
        try {
            if (endpoint) {
                const r = await fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Accept: "application/json",
                    },
                    body: JSON.stringify({ email: email.trim() }),
                })
                if (!r.ok) throw new Error(String(r.status))
            } else await new Promise((r) => setTimeout(r, 700))
            setState("ok")
            setEmail("")
        } catch {
            setState("error")
        }
    }
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-nl"
            css={CSS}
            label="Newsletter"
        >
            {decor && (
                <div className="sv-dec" aria-hidden="true">
                    <Planet
                        size={84}
                        fill={T.lime}
                        style={{ left: "6%", top: 80 }}
                        className="sv-bob"
                    />
                    <Sparkle
                        size={28}
                        fill={T.pink}
                        style={{ right: "8%", top: 90 }}
                        delay={0.5}
                    />
                </div>
            )}
            <div className="sv-wrap">
                <Reveal y={36}>
                    <div className="card">
                        <span className="sig" aria-hidden="true">
                            <svg
                                width="58"
                                height="58"
                                viewBox="0 0 58 58"
                                fill="none"
                                stroke={T.ink}
                                strokeWidth="2.4"
                                strokeLinecap="round"
                            >
                                <circle cx="29" cy="37" r="4.5" fill={T.ink} />
                                <path d="M19 27a14 14 0 0 1 20 0" />
                                <path d="M12 20a24 24 0 0 1 34 0" />
                                <path d="M5 13a34 34 0 0 1 48 0" />
                            </svg>
                        </span>
                        <div className="copy">
                            <Title text={title} className="sv-h2" />
                            {body && <p className="lead">{body}</p>}
                            <form onSubmit={submit} noValidate>
                                <label htmlFor={id} className="sv-sr">
                                    {placeholder}
                                </label>
                                <input
                                    id={id}
                                    type="email"
                                    autoComplete="email"
                                    placeholder={placeholder}
                                    value={email}
                                    onChange={(e) => (
                                        setEmail(e.target.value),
                                        state !== "idle" &&
                                            state !== "loading" &&
                                            setState("idle")
                                    )}
                                    aria-invalid={state === "invalid"}
                                    aria-describedby={`${id}-msg`}
                                />
                                <button
                                    type="submit"
                                    className="sv-btn sv-btn-primary"
                                    disabled={state === "loading"}
                                >
                                    {state === "loading" ? (
                                        <Icon
                                            name="activity"
                                            size={16}
                                            stroke={2.2}
                                        />
                                    ) : null}
                                    <span>
                                        {state === "loading"
                                            ? "…"
                                            : buttonLabel}
                                    </span>
                                </button>
                            </form>
                            <div
                                id={`${id}-msg`}
                                role="status"
                                aria-live="polite"
                            >
                                {state === "ok" && (
                                    <span className="msg ok">
                                        <i>
                                            <Icon
                                                name="check"
                                                size={12}
                                                stroke={2.8}
                                            />
                                        </i>
                                        {successText}
                                    </span>
                                )}
                                {state === "error" && (
                                    <span className="msg err">{errorText}</span>
                                )}
                                {state === "invalid" && (
                                    <span className="msg err">
                                        {invalidText}
                                    </span>
                                )}
                                {(state === "idle" || state === "loading") &&
                                    fineprint && (
                                        <span className="fine">
                                            {fineprint}
                                        </span>
                                    )}
                            </div>
                        </div>
                    </div>
                </Reveal>
            </div>
        </Section>
    )
}

addPropertyControls(Newsletter, {
    tone: toneControl("butter"),
    title: {
        type: ControlType.String,
        title: "Title",
        displayTextArea: true,
        defaultValue: "Stay ahead of emerging *AI risks.*",
    },
    body: {
        type: ControlType.String,
        title: "Body",
        displayTextArea: true,
        defaultValue:
            "Get thoughtful updates on AI security, governance, and emerging threats.",
    },
    placeholder: {
        type: ControlType.String,
        title: "Placeholder",
        defaultValue: "Work email address",
    },
    buttonLabel: {
        type: ControlType.String,
        title: "Button",
        defaultValue: "Subscribe",
    },
    successText: {
        type: ControlType.String,
        title: "Success text",
        defaultValue: "Thanks! Please check your inbox to confirm.",
    },
    errorText: {
        type: ControlType.String,
        title: "Error text",
        defaultValue: "Something went wrong. Please try again.",
    },
    invalidText: {
        type: ControlType.String,
        title: "Invalid email text",
        defaultValue: "Please enter a valid work email.",
    },
    endpoint: {
        type: ControlType.String,
        title: "Form endpoint",
        defaultValue: "",
        description:
            "POST URL that receives { email } as JSON. Leave empty to preview the success state only.",
    },
    fineprint: {
        type: ControlType.String,
        title: "Fine print",
        defaultValue: "No spam. Unsubscribe anytime.",
    },
    decor: decorControl,
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "newsletter",
    },
})
