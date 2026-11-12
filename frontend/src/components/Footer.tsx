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

.sv-foot .soc{display:flex;gap:10px;margin-top:4px}

.sv-foot .soc a{display:grid;place-items:center;width:42px;height:42px;border-radius:50%;background:${T.white};border:1.2px solid ${T.ink};color:${T.ink};box-shadow:2px 2px 0 0 ${T.ink};transition:translate .2s var(--pop),box-shadow .2s var(--pop)}

.sv-foot .soc a:hover{translate:-2px -2px;box-shadow:4px 4px 0 0 ${T.ink}}

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

const SOC: Record<string, string> = {
    linkedin: "linkedin",
    instagram: "instagram",
    github: "github",
    youtube: "youtube",
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

    const soc = parse(socials).filter((s) => SOC[s.label.toLowerCase()])

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

                                    <div className="soc">

                                        {soc.map((s, i) => (

                                            <a

                                                key={i}

                                                href={s.href}

                                                target="_blank"

                                                rel="noopener noreferrer"

                                                aria-label={s.label}

                                            >

                                                <Icon

                                                    name={

                                                        SOC[

                                                            s.label.toLowerCase()

                                                        ]

                                                    }

                                                    size={17}

                                                />

                                            </a>

                                        ))}

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

            "One per line: linkedin | URL (also x, github, youtube). Leave empty to hide.",

        defaultValue: "linkedin | https://www.linkedin.com\nx | https://x.com",

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

