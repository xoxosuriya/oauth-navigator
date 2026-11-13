// SECUVANTA Footer: one reusable footer for every page. Brand block (logo, tagline, description, socials), up to

// three link columns, a giant wordmark with planet doodles (Pluto's oversized footer type) and a bottom bar

// with copyright + legal links. "Simple" variant (for 404 and utility pages) keeps only the logo row and bottom bar.

// Links are lines: "Label | /link". Socials: "linkedin | https://…" (linkedin, x, github, youtube).

import * as React from "react"

import { addPropertyControls, ControlType } from "framer"

import {

    Section,

    Logo,

    Icon,

    Sparkle,

    Planet,

    lines,

    cells,

    toneControl,

    decorControl,

    T,

} from "./Kit.tsx"



const CSS = `

.sv-foot{padding:0;overflow:hidden;border-top:1.5px solid ${T.ink}}

.sv-foot .top{display:grid;grid-template-columns:minmax(0,1.4fr) repeat(var(--cols,2),minmax(0,1fr));gap:48px;padding:88px 0 64px}

.sv-foot .brand{display:grid;gap:18px;align-content:start;max-width:420px}

.sv-foot .brand > a{justify-self:start}

.sv-foot .tag{font-family:var(--display);font-weight:700;font-size:22px;line-height:1.2;color:var(--text)}

.sv-foot .desc{font-size:15px;line-height:1.55;color:var(--body)}

.sv-foot .soc{display:flex;flex-wrap:wrap;gap:14px 16px;margin-top:8px;align-items:flex-start}

.sv-foot .soc a{color:${T.ink};text-decoration:none}

.sv-foot .soc a.soc-item{display:flex;flex-direction:column;align-items:center;gap:6px;text-decoration:none;color:${T.ink};outline:none;transition:transform .2s var(--pop)}

.sv-foot .soc-circle{display:grid;place-items:center;width:42px;height:42px;border-radius:50%;background:${T.white};border:1.4px solid ${T.ink};color:${T.ink};box-shadow:2px 2px 0 0 ${T.ink};transition:translate .2s var(--pop),box-shadow .2s var(--pop),background-color .2s}

.sv-foot .soc a.soc-item:hover .soc-circle{translate:-2px -2px;box-shadow:4px 4px 0 0 ${T.ink};background:${T.butter}}

.sv-foot .soc a.soc-item:focus-visible .soc-circle{outline:2px solid ${T.ink};outline-offset:3px}

.sv-foot .soc-label{font-family:var(--display);font-weight:700;font-size:9.5px;line-height:1;letter-spacing:.05em;text-transform:uppercase;color:var(--text);user-select:none;text-align:center;transition:color .2s}

.sv-foot .soc a.soc-item:hover .soc-label{color:${T.ink};text-decoration:underline}

@keyframes svOrbitPulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.25);opacity:.75}}

.sv-foot-orbit-dot{transform-origin:19.5px 8px;animation:svOrbitPulse 2.4s ease-in-out infinite}

.sv-foot h3{font-family:var(--display);font-weight:600;font-size:15px;letter-spacing:.04em;text-transform:uppercase;color:var(--text);margin-bottom:18px}

.sv-foot ul{display:grid;gap:12px}

.sv-foot ul a{font-weight:500;font-size:15.5px;color:var(--body);transition:color .2s}

.sv-foot ul a:hover{color:var(--accent)}

.sv-foot .big{position:relative;padding:8px 0 0;text-align:center;user-select:none}

.sv-foot .big .wm{display:block;width:100%;height:auto;overflow:visible}

.sv-foot .bot{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px 24px;padding:22px 0 26px;border-top:1px solid var(--line2);font-size:14px;color:var(--body)}

.sv-foot .bot nav{display:flex;flex-wrap:wrap;gap:6px 22px}

.sv-foot .bot a:hover{color:var(--accent)}

.sv-foot .simple{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:16px;padding:32px 0 22px}

@container (max-width:1000px){.sv-foot .top{grid-template-columns:repeat(2,minmax(0,1fr));gap:40px}.sv-foot .brand{grid-column:1/-1}}

@container (max-width:520px){.sv-foot .top{grid-template-columns:1fr;padding:64px 0 40px}.sv-foot .bot{flex-direction:column;align-items:flex-start}}

`

const parse = (s: string) =>

    lines(s).map((l) => {

        const [label, href] = cells(l)

        return { label, href: href || "#" }

    })

export const DEFAULT_SOCIALS = `linkedin | https://www.linkedin.com/in/suriya-prakash-28a5273ba
instagram | https://www.instagram.com/xoxo.suriya/
github | https://github.com/xoxosuriya
portfolio | https://xoxosuriya.github.io/suriya_portfolio/
gmail | https://mail.google.com/mail/?view=cm&fs=1&to=sp2742006@gmail.com`

const SOC: Record<string, string> = {
    linkedin: "linkedin",
    instagram: "instagram",
    github: "github",
    portfolio: "portfolio",
    gmail: "gmail",
    youtube: "youtube",
    x: "x_social",
}

const SOC_META: Record<string, { label: string; title: string }> = {
    linkedin: {
        label: "LINKEDIN",
        title: "LinkedIn — Suriya Prakash (opens in new tab)",
    },
    instagram: {
        label: "INSTAGRAM",
        title: "Instagram — @xoxo.suriya (opens in new tab)",
    },
    github: {
        label: "GITHUB",
        title: "GitHub — xoxosuriya (opens in new tab)",
    },
    portfolio: {
        label: "PORTFOLIO",
        title: "Personal Portfolio — Suriya Prakash (opens in new tab)",
    },
    gmail: {
        label: "GMAIL",
        title: "Gmail — Compose message to sp2742006@gmail.com (opens in new tab)",
    },
}

export function LinkedInLogo({ size = 18 }: { size?: number }) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.8}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            focusable="false"
        >
            <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z" />
            <rect width="4" height="12" x="2" y="9" />
            <circle cx="4" cy="4" r="2" />
        </svg>
    )
}

export function InstagramLogo({ size = 18 }: { size?: number }) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.8}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            focusable="false"
        >
            <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
            <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
            <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
        </svg>
    )
}

export function GitHubLogo({ size = 18 }: { size?: number }) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.8}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            focusable="false"
        >
            <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
            <path d="M9 18c-4.51 2-5-2-7-2" />
        </svg>
    )
}

export function PortfolioLogo({ size = 19 }: { size?: number }) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.75}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            focusable="false"
            className="sv-foot-portfolio-svg"
        >
            <circle cx="12" cy="12" r="5" />
            <ellipse cx="12" cy="12" rx="2.4" ry="5" strokeWidth={1.2} />
            <line x1="7" y1="12" x2="17" y2="12" strokeWidth={1.2} />
            <ellipse
                cx="12"
                cy="12"
                rx="9.5"
                ry="4"
                transform="rotate(-26 12 12)"
                strokeWidth={1.4}
                strokeDasharray="26 3.5"
            />
            <circle
                cx="19.5"
                cy="8"
                r="1.4"
                fill="currentColor"
                stroke="none"
                className="sv-foot-orbit-dot"
            />
        </svg>
    )
}

export function GmailLogo({ size = 19 }: { size?: number }) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
            focusable="false"
            className="sv-foot-gmail-svg"
        >
            <path
                d="M4 18.5V7.5C4 6.67 4.67 6 5.5 6H7v12.5H5.5A1.5 1.5 0 0 1 4 18.5z"
                fill="#4285F4"
            />
            <path
                d="M17 6h1.5A1.5 1.5 0 0 1 20 7.5v11a1.5 1.5 0 0 1-1.5 1.5H17V6z"
                fill="#34A853"
            />
            <path
                d="M17 5.25h1.5A1.5 1.5 0 0 1 20 6.75v1.75l-3-2.25V5.25z"
                fill="#FBBC04"
            />
            <path
                d="M4 6.75A1.5 1.5 0 0 1 5.5 5.25H7v2.75l-3 2.25V6.75z"
                fill="#C5221F"
            />
            <path
                d="M7 6.25L12 10l5-3.75v3.25L12 13.25 7 9.5V6.25z"
                fill="#EA4335"
            />
        </svg>
    )
}

export function renderSocialIcon(key: string, size = 18) {
    const k = key.toLowerCase()
    switch (k) {
        case "linkedin":
            return <LinkedInLogo size={size} />
        case "instagram":
            return <InstagramLogo size={size} />
        case "github":
            return <GitHubLogo size={size} />
        case "portfolio":
            return <PortfolioLogo size={size} />
        case "gmail":
            return <GmailLogo size={size} />
        default:
            return <Icon name={SOC[k] || "zap"} size={size} />
    }
}



export default function Footer(props: any) {

    const {

        tone,

        variant,

        brand,

        logo,

        tagline,

        description,

        col1Title,

        col1Links,

        col2Title,

        col2Links,

        col3Title,

        col3Links,

        socials,

        showWordmark,

        wordmark,

        copyright,

        legalLinks,

        decor,

    } = props

    const cols = [

        [col1Title, parse(col1Links)],

        [col2Title, parse(col2Links)],

        [col3Title, parse(col3Links)],

    ].filter(([t, l]: any) => t && l.length) as [

        string,

        { label: string; href: string }[],

    ][]

    const socialsText =
        typeof socials === "string" && socials.trim() !== ""
            ? socials
            : DEFAULT_SOCIALS

    const soc = parse(socialsText).filter((s) => SOC[s.label.toLowerCase()])

    const legal = parse(legalLinks)

    const bottom = (

        <div className="bot">

            <span>{copyright}</span>

            {legal.length > 0 && (

                <nav aria-label="Legal">

                    {legal.map((l, i) => (

                        <a key={i} href={l.href}>

                            {l.label}

                        </a>

                    ))}

                </nav>

            )}

        </div>

    )

    return (

        <Section

            as="footer"

            tone={tone}

            pad={false}

            className="sv-foot"

            css={CSS}

            label="Site footer"

        >

            <div className="sv-wrap">

                {variant === "simple" ? (

                    <>

                        <div className="simple">

                            <Logo name={brand} image={logo} size={30} />

                            {cols[0] && (

                                <nav

                                    aria-label="Footer"

                                    style={{

                                        display: "flex",

                                        flexWrap: "wrap",

                                        gap: "8px 22px",

                                    }}

                                >

                                    {cols

                                        .flatMap(([, l]) => l)

                                        .slice(0, 5)

                                        .map((l, i) => (

                                            <a

                                                key={i}

                                                href={l.href}

                                                style={{

                                                    fontWeight: 500,

                                                    fontSize: 15,

                                                }}

                                            >

                                                {l.label}

                                            </a>

                                        ))}

                                </nav>

                            )}

                        </div>

                        {bottom}

                    </>

                ) : (

                    <>

                        <div

                            className="top"

                            style={{

                                ["--cols" as any]: Math.max(1, cols.length),

                            }}

                        >

                            <div className="brand">

                                <Logo name={brand} image={logo} size={34} />

                                {tagline && <p className="tag">{tagline}</p>}

                                {description && (

                                    <p className="desc">{description}</p>

                                )}

                                {soc.length > 0 && (

                                    <div className="soc" role="list" aria-label="Social and contact links">

                                        {soc.map((s, i) => {

                                            const key = s.label.toLowerCase()

                                            const meta = SOC_META[key] || {

                                                label: s.label.toUpperCase(),

                                                title: `${s.label} — ${s.href}`,

                                            }

                                            return (

                                                <a

                                                    key={i}

                                                    href={s.href}

                                                    target="_blank"

                                                    rel="noopener noreferrer"

                                                    className="soc-item"

                                                    aria-label={`${meta.label} - ${meta.title} (opens in a new tab)`}

                                                    title={meta.title}

                                                    role="listitem"

                                                >

                                                    <div className="soc-circle">

                                                        {renderSocialIcon(key)}

                                                    </div>

                                                    <span className="soc-label">

                                                        {meta.label}

                                                    </span>

                                                </a>

                                            )

                                        })}

                                    </div>

                                )}

                            </div>

                            {cols.map(([t, l], i) => (

                                <nav key={i} aria-label={t}>

                                    <h3>{t}</h3>

                                    <ul>

                                        {l.map((x, k) => (

                                            <li key={k}>

                                                <a href={x.href}>{x.label}</a>

                                            </li>

                                        ))}

                                    </ul>

                                </nav>

                            ))}

                        </div>

                        {showWordmark && (wordmark || brand) && (

                            <div className="big" aria-hidden="true">

                                {decor && (

                                    <>

                                        <Planet

                                            size={78}

                                            fill={T.lime}

                                            style={{ left: "6%", top: -26 }}

                                            className="sv-bob"

                                        />

                                        <Sparkle

                                            size={34}

                                            fill={T.orange}

                                            style={{ right: "9%", top: -18 }}

                                            delay={0.6}

                                        />

                                        <Sparkle

                                            size={20}

                                            fill={T.butter}

                                            style={{ right: "5%", top: 30 }}

                                            delay={1.6}

                                        />

                                    </>

                                )}

                                <svg

                                    className="wm"

                                    viewBox="0 0 1000 190"

                                    aria-hidden="true"

                                    focusable="false"

                                >

                                    <text

                                        x="6"

                                        y="176"

                                        textLength="988"

                                        lengthAdjust="spacingAndGlyphs"

                                        style={{

                                            font: `800 196px ${"var(--display)"}`,

                                            fill: T.ink,

                                        }}

                                    >

                                        {String(

                                            wordmark || brand

                                        ).toUpperCase()}

                                    </text>

                                    <text

                                        x="0"

                                        y="170"

                                        textLength="988"

                                        lengthAdjust="spacingAndGlyphs"

                                        style={{

                                            font: `800 196px ${"var(--display)"}`,

                                            fill: T.butter,

                                        }}

                                    >

                                        {String(

                                            wordmark || brand

                                        ).toUpperCase()}

                                    </text>

                                </svg>

                            </div>

                        )}

                        {bottom}

                    </>

                )}

            </div>

        </Section>

    )

}



addPropertyControls(Footer, {

    tone: toneControl("cream"),

    variant: {

        type: ControlType.Enum,

        title: "Variant",

        options: ["full", "simple"],

        optionTitles: ["Full", "Simple (404 / utility)"],

        defaultValue: "full",

        displaySegmentedControl: true,

    },

    brand: {

        type: ControlType.String,

        title: "Brand",

        defaultValue: "OAUTH NAVIGATOR",

    },

    logo: {

        type: ControlType.ResponsiveImage,

        title: "Logo image",

        description: "Optional. Replaces the built-in mark.",

    },

    tagline: {

        type: ControlType.String,

        title: "Tagline",

        defaultValue: "Secure AI. Empower Innovation.",

    },

    description: {

        type: ControlType.String,

        title: "Description",

        displayTextArea: true,

        defaultValue:

            "Helping organizations build a clearer, more controlled approach to AI security and governance.",

    },

    col1Title: {

        type: ControlType.String,

        title: "Column 1 title",

        defaultValue: "Platform",

    },

    col1Links: {

        type: ControlType.String,

        title: "Column 1 links",

        displayTextArea: true,

        description: "One per line: Label | /link",

        defaultValue:

            "Overview | /platform\nAI Discovery | /platform#discovery\nRisk Intelligence | /platform#risk\nAI Protection | /platform#protection",

    },

    col2Title: {

        type: ControlType.String,

        title: "Column 2 title",

        defaultValue: "Company",

    },

    col2Links: {

        type: ControlType.String,

        title: "Column 2 links",

        displayTextArea: true,

        description: "One per line: Label | /link",

        defaultValue:

            "About | /about\nResources | /resources\nContact | /contact\nRequest a Demo | /contact",

    },

    col3Title: {

        type: ControlType.String,

        title: "Column 3 title",

        defaultValue: "",

        description: "Optional third column.",

    },

    col3Links: {

        type: ControlType.String,

        title: "Column 3 links",

        displayTextArea: true,

        defaultValue: "",

    },

    socials: {

        type: ControlType.String,

        title: "Socials",

        displayTextArea: true,

        description:

            "One per line: platform | URL (linkedin, instagram, github, portfolio, gmail).",

        defaultValue: DEFAULT_SOCIALS,

    },

    showWordmark: {

        type: ControlType.Boolean,

        title: "Big wordmark",

        defaultValue: true,

        enabledTitle: "Show",

        disabledTitle: "Hide",

    },

    wordmark: {

        type: ControlType.String,

        title: "Wordmark text",

        defaultValue: "",

        description: "Defaults to the brand name.",

        hidden: (p: any) => !p.showWordmark,

    },

    copyright: {

        type: ControlType.String,

        title: "Copyright",

        defaultValue: "© 2026 OAuth Navigator. Template demonstration brand.",

    },

    legalLinks: {

        type: ControlType.String,

        title: "Legal links",

        displayTextArea: true,

        description: "One per line: Label | /link",

        defaultValue: "Privacy Policy | /privacy\nTerms of Use | /terms",

    },

    decor: decorControl,

})



// Shared control types verified.

