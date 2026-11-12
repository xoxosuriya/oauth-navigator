// SECUVANTA ContactForm: "Request a Personalized Demo". Concise explanation + reassurance points on the left, a grouped
// sticker form on the right: full name, work email, company, job role, company size, area of interest and goals.
// Inline validation shows errors under each field; the submit button has loading, success and error states.
// When "Form endpoint" is set the form POSTs the fields as JSON (Formspree, HubSpot forms API, Zapier, your backend).
// With no endpoint it shows the success state locally so the template can be previewed. Connect and test a real
// destination before launch; nothing is sent anywhere by default.
// Dropdown options are lines; the privacy note supports a link via "Privacy link".
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import { Section, Title, Reveal, Icon, lines, toneControl, T } from "./Kit.tsx"

const CSS = `
.sv-cf .grid{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:64px;align-items:start}
.sv-cf .side{display:grid;gap:22px;position:sticky;top:140px}
.sv-cf .side ul{display:grid;gap:14px;margin-top:6px}
.sv-cf .side li{display:flex;gap:12px;align-items:flex-start;font-size:16px;line-height:1.45;color:var(--body)}
.sv-cf .side li i{display:grid;place-items:center;width:26px;height:26px;border-radius:50%;background:${T.butter};border:1px solid ${T.ink};flex-shrink:0;color:${T.ink}}
.sv-cf .side .mail{display:inline-flex;align-items:center;gap:10px;font-weight:600;color:var(--text)}
.sv-cf form{position:relative;display:grid;gap:22px;padding:36px;border-radius:30px;background:${T.white};border:1.5px solid ${T.ink};box-shadow:7px 8px 0 0 ${T.ink};color:${T.ink}}
.sv-cf form h3{font-family:var(--display);font-weight:700;font-size:clamp(21px,2cqw,28px);line-height:1.15}
.sv-cf fieldset{display:grid;grid-template-columns:1fr 1fr;gap:16px 18px;border:0;margin:0;padding:0;min-width:0}
.sv-cf legend{grid-column:1/-1;padding:0;margin-bottom:12px;font-size:11.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:${T.mute}}
.sv-cf .f{display:grid;gap:7px;min-width:0}
.sv-cf .f.full{grid-column:1/-1}
.sv-cf label{font-size:14px;font-weight:600}
.sv-cf label em{font-style:normal;color:${T.orange}}
.sv-cf input,.sv-cf select,.sv-cf textarea{width:100%;height:52px;padding:0 16px;border-radius:14px;border:1.5px solid ${T.ink};background:${T.cream};font-family:var(--sans);font-size:15.5px;color:${T.ink};outline:none;appearance:none;-webkit-appearance:none;transition:box-shadow .2s var(--pop),background-color .2s}
.sv-cf select{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='none' stroke='black' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='m4 6 4 4 4-4'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 14px center;padding-right:40px}
.sv-cf textarea{height:120px;padding:14px 16px;resize:vertical;line-height:1.5}
.sv-cf :is(input,select,textarea):focus{background-color:${T.white};box-shadow:3px 3px 0 0 ${T.ink}}
.sv-cf [aria-invalid="true"]{border-color:${T.critical};background-color:#FFF4F2}
.sv-cf .err{display:flex;align-items:center;gap:6px;font-size:12.5px;font-weight:500;color:${T.critical}}
.sv-cf .actions{display:grid;gap:14px}
.sv-cf button.sv-btn{width:100%;height:60px;--btn-bg:${T.ink};--btn-fg:${T.white}}
.sv-cf button[disabled]{opacity:.75;cursor:progress}
.sv-cf .spin{animation:sv-spin 1s linear infinite}
.sv-cf .priv{font-size:13px;line-height:1.5;color:${T.mute}}
.sv-cf .priv a{color:${T.ink};text-decoration:underline;text-underline-offset:3px}
.sv-cf .banner{display:flex;gap:12px;align-items:flex-start;padding:16px;border-radius:16px;border:1.5px solid ${T.ink};font-size:14.5px;line-height:1.45}
.sv-cf .banner.ok{background:${T.lime}}
.sv-cf .banner.bad{background:${T.blush}}
.sv-cf .banner i{display:grid;place-items:center;width:26px;height:26px;border-radius:50%;background:${T.white};border:1px solid ${T.ink};flex-shrink:0}
.sv-cf .done{display:grid;justify-items:start;gap:16px;padding:12px 0}
.sv-cf .done h3{font-size:clamp(24px,2.4cqw,32px)}
@container (max-width:1000px){.sv-cf .grid{grid-template-columns:1fr;gap:40px}.sv-cf .side{position:static}}
@container (max-width:600px){.sv-cf form{padding:24px 18px;border-radius:22px}.sv-cf fieldset{grid-template-columns:1fr}}
`
type Vals = Record<string, string>
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function ContactForm(props: any) {
    const {
        tone,
        title,
        body,
        points,
        contactEmail,
        formTitle,
        groupAbout,
        groupNeeds,
        nameLabel,
        emailLabel,
        companyLabel,
        roleLabel,
        roleOptions,
        sizeLabel,
        sizeOptions,
        interestLabel,
        interestOptions,
        goalsLabel,
        goalsPlaceholder,
        selectPlaceholder,
        submitLabel,
        loadingLabel,
        privacyText,
        privacyLinkLabel,
        privacyLink,
        successTitle,
        successText,
        againLabel,
        errorText,
        requiredText,
        emailText,
        endpoint,
        sectionId,
    } = props
    const [v, setV] = React.useState<Vals>({
        name: "",
        email: "",
        company: "",
        role: "",
        size: "",
        interest: "",
        goals: "",
    })
    const [errs, setErrs] = React.useState<Vals>({})
    const [state, setState] = React.useState<
        "idle" | "loading" | "ok" | "error"
    >("idle")
    const refs = React.useRef<Record<string, HTMLElement | null>>({})
    const req = ["name", "email", "company", "role", "size", "interest"]
    const validate = (vals: Vals) => {
        const e: Vals = {}
        req.forEach(
            (k) => !String(vals[k] || "").trim() && (e[k] = requiredText)
        )
        if (vals.email && !EMAIL.test(vals.email.trim())) e.email = emailText
        return e
    }
    const set = (k: string) => (ev: any) => {
        const nv = { ...v, [k]: ev.target.value }
        setV(nv)
        if (errs[k]) setErrs(validate(nv))
    }
    const submit = async (ev: React.FormEvent) => {
        ev.preventDefault()
        const e = validate(v)
        setErrs(e)
        const first = req.find((k) => e[k])
        if (first) return refs.current[first]?.focus()
        setState("loading")
        try {
            if (endpoint) {
                const r = await fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Accept: "application/json",
                    },
                    body: JSON.stringify(v),
                })
                if (!r.ok) throw new Error(String(r.status))
            } else await new Promise((r) => setTimeout(r, 900))
            setState("ok")
        } catch {
            setState("error")
        }
    }
    const field = (
        k: string,
        label: string,
        el: React.ReactNode,
        full = false,
        required = true
    ) => (
        <div className={`f${full ? " full" : ""}`}>
            <label htmlFor={`sv-cf-${k}`}>
                {label}
                {required && <em aria-hidden="true"> *</em>}
            </label>
            {el}
            {errs[k] && (
                <span className="err" id={`sv-cf-${k}-err`}>
                    <Icon name="alert" size={13} stroke={2.2} />
                    {errs[k]}
                </span>
            )}
        </div>
    )
    const common = (k: string) => ({
        id: `sv-cf-${k}`,
        name: k,
        value: v[k],
        onChange: set(k),
        "aria-invalid": errs[k] ? true : undefined,
        "aria-describedby": errs[k] ? `sv-cf-${k}-err` : undefined,
        ref: (el: HTMLElement | null) => (refs.current[k] = el),
    })
    const select = (k: string, opts: string) => (
        <select {...(common(k) as any)} required>
            <option value="">{selectPlaceholder}</option>
            {lines(opts).map((o) => (
                <option key={o} value={o}>
                    {o}
                </option>
            ))}
        </select>
    )
    return (
        <Section
            tone={tone}
            id={sectionId}
            className="sv-cf"
            css={CSS}
            label="Request a demo"
        >
            <div className="sv-wrap">
                <div className="grid">
                    <div className="side">
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
                        <Reveal delay={0.16}>
                            <ul>
                                {lines(points).map((p, i) => (
                                    <li key={i}>
                                        <i>
                                            <Icon
                                                name="check"
                                                size={13}
                                                stroke={2.6}
                                            />
                                        </i>
                                        {p}
                                    </li>
                                ))}
                            </ul>
                        </Reveal>
                        {contactEmail && (
                            <Reveal delay={0.2}>
                                <a
                                    className="mail sv-link"
                                    href={`mailto:${contactEmail}`}
                                >
                                    <Icon
                                        name="arrow-up-right"
                                        size={16}
                                        stroke={2}
                                    />
                                    {contactEmail}
                                </a>
                            </Reveal>
                        )}
                    </div>
                    <Reveal delay={0.1} y={36}>
                        {state === "ok" ? (
                            <form
                                aria-live="polite"
                                onSubmit={(e) => e.preventDefault()}
                            >
                                <div className="done">
                                    <span
                                        className="banner ok"
                                        style={{ width: "100%" }}
                                    >
                                        <i>
                                            <Icon
                                                name="check"
                                                size={13}
                                                stroke={2.8}
                                            />
                                        </i>
                                        <span>
                                            <b>{successTitle}</b>
                                            <br />
                                            {successText}
                                        </span>
                                    </span>
                                    <button
                                        type="button"
                                        className="sv-btn sv-btn-secondary"
                                        style={{ width: "auto", height: 48 }}
                                        onClick={() => (
                                            setState("idle"),
                                            setV({
                                                name: "",
                                                email: "",
                                                company: "",
                                                role: "",
                                                size: "",
                                                interest: "",
                                                goals: "",
                                            })
                                        )}
                                    >
                                        {againLabel}
                                    </button>
                                </div>
                            </form>
                        ) : (
                            <form
                                onSubmit={submit}
                                noValidate
                                aria-label={formTitle}
                            >
                                {formTitle && <h3>{formTitle}</h3>}
                                <fieldset>
                                    <legend>{groupAbout}</legend>
                                    {field(
                                        "name",
                                        nameLabel,
                                        <input
                                            type="text"
                                            autoComplete="name"
                                            {...(common("name") as any)}
                                        />
                                    )}
                                    {field(
                                        "email",
                                        emailLabel,
                                        <input
                                            type="email"
                                            autoComplete="email"
                                            inputMode="email"
                                            {...(common("email") as any)}
                                        />
                                    )}
                                    {field(
                                        "company",
                                        companyLabel,
                                        <input
                                            type="text"
                                            autoComplete="organization"
                                            {...(common("company") as any)}
                                        />
                                    )}
                                    {field(
                                        "role",
                                        roleLabel,
                                        select("role", roleOptions)
                                    )}
                                </fieldset>
                                <fieldset>
                                    <legend>{groupNeeds}</legend>
                                    {field(
                                        "size",
                                        sizeLabel,
                                        select("size", sizeOptions)
                                    )}
                                    {field(
                                        "interest",
                                        interestLabel,
                                        select("interest", interestOptions)
                                    )}
                                    {field(
                                        "goals",
                                        goalsLabel,
                                        <textarea
                                            placeholder={goalsPlaceholder}
                                            {...(common("goals") as any)}
                                        />,
                                        true,
                                        false
                                    )}
                                </fieldset>
                                {state === "error" && (
                                    <div className="banner bad" role="alert">
                                        <i>
                                            <Icon
                                                name="alert"
                                                size={13}
                                                stroke={2.4}
                                            />
                                        </i>
                                        {errorText}
                                    </div>
                                )}
                                <div className="actions">
                                    <button
                                        type="submit"
                                        className="sv-btn sv-btn-primary"
                                        disabled={state === "loading"}
                                    >
                                        {state === "loading" && (
                                            <Icon
                                                name="activity"
                                                size={17}
                                                stroke={2.2}
                                                className="spin"
                                            />
                                        )}
                                        <span>
                                            {state === "loading"
                                                ? loadingLabel
                                                : submitLabel}
                                        </span>
                                        {state !== "loading" && (
                                            <Icon
                                                name="arrow-right"
                                                size={16}
                                                stroke={2.2}
                                            />
                                        )}
                                    </button>
                                    <p className="priv">
                                        {privacyText}{" "}
                                        {privacyLinkLabel && (
                                            <a href={privacyLink || "#"}>
                                                {privacyLinkLabel}
                                            </a>
                                        )}
                                    </p>
                                </div>
                            </form>
                        )}
                    </Reveal>
                </div>
            </div>
        </Section>
    )
}

addPropertyControls(ContactForm, {
    tone: toneControl("white"),
    title: {
        type: ControlType.String,
        title: "Title",
        displayTextArea: true,
        defaultValue: "Request a *personalized demo.*",
    },
    body: {
        type: ControlType.String,
        title: "Body",
        displayTextArea: true,
        defaultValue:
            "Share a few details and we'll tailor the walkthrough to your environment. We only ask for what we need.",
    },
    points: {
        type: ControlType.String,
        title: "Points",
        displayTextArea: true,
        defaultValue:
            "A walkthrough focused on your priorities\nTime for your team's questions\nNo commitment required",
        description: "One per line.",
    },
    contactEmail: {
        type: ControlType.String,
        title: "Contact email",
        defaultValue: "",
        description: "Optional mailto link under the points.",
    },
    formTitle: {
        type: ControlType.String,
        title: "Form title",
        defaultValue: "Request a Personalized Demo",
    },
    groupAbout: {
        type: ControlType.String,
        title: "Group 1 label",
        defaultValue: "About you",
    },
    groupNeeds: {
        type: ControlType.String,
        title: "Group 2 label",
        defaultValue: "Your needs",
    },
    nameLabel: {
        type: ControlType.String,
        title: "Name label",
        defaultValue: "Full name",
    },
    emailLabel: {
        type: ControlType.String,
        title: "Email label",
        defaultValue: "Work email",
    },
    companyLabel: {
        type: ControlType.String,
        title: "Company label",
        defaultValue: "Company name",
    },
    roleLabel: {
        type: ControlType.String,
        title: "Role label",
        defaultValue: "Job role",
    },
    roleOptions: {
        type: ControlType.String,
        title: "Role options",
        displayTextArea: true,
        defaultValue: "Security\nIT\nEngineering\nCompliance\nExecutive\nOther",
    },
    sizeLabel: {
        type: ControlType.String,
        title: "Size label",
        defaultValue: "Company size",
    },
    sizeOptions: {
        type: ControlType.String,
        title: "Size options",
        displayTextArea: true,
        defaultValue: "1–50\n51–200\n201–1,000\n1,001–5,000\n5,000+",
    },
    interestLabel: {
        type: ControlType.String,
        title: "Interest label",
        defaultValue: "Primary area of interest",
    },
    interestOptions: {
        type: ControlType.String,
        title: "Interest options",
        displayTextArea: true,
        defaultValue:
            "AI Discovery\nRisk Assessment\nAI Protection\nGovernance\nPlatform Overview",
    },
    goalsLabel: {
        type: ControlType.String,
        title: "Goals label",
        defaultValue: "Tell us about your security goals",
    },
    goalsPlaceholder: {
        type: ControlType.String,
        title: "Goals placeholder",
        defaultValue: "What would you like to see in the demo?",
    },
    selectPlaceholder: {
        type: ControlType.String,
        title: "Select placeholder",
        defaultValue: "Select…",
    },
    submitLabel: {
        type: ControlType.String,
        title: "Submit label",
        defaultValue: "Request My Demo",
    },
    loadingLabel: {
        type: ControlType.String,
        title: "Loading label",
        defaultValue: "Sending…",
    },
    privacyText: {
        type: ControlType.String,
        title: "Privacy note",
        displayTextArea: true,
        defaultValue:
            "By submitting this form, you agree that Secuvanta may use your information to respond to your inquiry. See our",
    },
    privacyLinkLabel: {
        type: ControlType.String,
        title: "Privacy link label",
        defaultValue: "Privacy Policy.",
    },
    privacyLink: {
        type: ControlType.Link,
        title: "Privacy link",
        defaultValue: "/privacy",
    },
    successTitle: {
        type: ControlType.String,
        title: "Success title",
        defaultValue: "Thanks, your request is in.",
    },
    successText: {
        type: ControlType.String,
        title: "Success text",
        displayTextArea: true,
        defaultValue:
            "We'll review your details and reply by email to schedule your walkthrough.",
    },
    againLabel: {
        type: ControlType.String,
        title: "Send another label",
        defaultValue: "Send another request",
    },
    errorText: {
        type: ControlType.String,
        title: "Error text",
        defaultValue:
            "We couldn't send your request. Please try again in a moment.",
    },
    requiredText: {
        type: ControlType.String,
        title: "Required error",
        defaultValue: "This field is required.",
    },
    emailText: {
        type: ControlType.String,
        title: "Email error",
        defaultValue: "Please enter a valid work email.",
    },
    endpoint: {
        type: ControlType.String,
        title: "Form endpoint",
        defaultValue: "",
        description:
            "POST URL that receives the fields as JSON. Leave empty to preview the success state only.",
    },
    sectionId: {
        type: ControlType.String,
        title: "Section ID",
        defaultValue: "demo-form",
    },
})
