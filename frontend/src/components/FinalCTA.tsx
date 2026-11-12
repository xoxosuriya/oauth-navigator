// SECUVANTA Final CTA: a secured AI network inside a soft radial glow (every node carries a green check, packets

// circulate, the guard ring spins), then a spacious cream sticker panel with the headline, body and a big pill CTA.

// Pluto's closing "Ready to go where no CISO has gone before" moment, in the template's own words.

import * as React from "react"

import { addPropertyControls, ControlType } from "framer"

import {

    Section,

    Title,

    Reveal,

    Pop,

    Btn,

    Icon,

    IconTile,

    Packet,

    Stage,

    Sparkle,

    Planet,

    lines,

    cells,

    toneControl,

    decorControl,

    T,

    ICON_NAMES,

} from "./Kit.tsx"



const CSS = `

.sv-fcta{overflow:hidden}

.sv-fcta .glow{position:absolute;left:50%;top:40px;width:1100px;height:760px;translate:-50% 0;pointer-events:none;background:radial-gradient(closest-side,rgba(255,255,120,.38),rgba(250,104,58,.16) 55%,transparent 80%)}

.sv-fcta .net{position:relative;max-width:700px;margin:0 auto}

.sv-fcta .nd{position:absolute;translate:-50% -50%;z-index:2}

.sv-fcta .nd .b{position:relative;display:grid;place-items:center;width:64px;height:64px;border-radius:50%;background:${T.white};border:1.5px solid ${T.ink};box-shadow:3px 3px 0 0 ${T.orange};color:${T.ink}}

.sv-fcta .nd .ok{position:absolute;right:-6px;top:-6px;display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:${T.lime};border:1.5px solid ${T.ink}}

.sv-fcta .nd small{position:absolute;top:calc(100% + 8px);left:50%;translate:-50% 0;white-space:nowrap;font-size:12.5px;font-weight:600;color:var(--text)}

.sv-fcta .core{position:absolute;left:350px;top:190px;translate:-50% -50%;z-index:2;display:grid;place-items:center;width:150px;height:150px;border-radius:50%;background:${T.butter};border:1.5px solid ${T.ink};box-shadow:5px 5px 0 0 ${T.orange}}

.sv-fcta .panel{position:relative;z-index:3;display:flex;flex-direction:column;align-items:center;gap:22px;max-width:1080px;margin:20px auto 0;padding:72px 48px;text-align:center;border-radius:36px;background:${T.cream};border:1.5px solid ${T.ink};box-shadow:8px 9px 0 0 var(--sh);color:${T.ink}}

.sv-fcta .panel .sv-h1{color:${T.ink};max-width:900px}

.sv-fcta .panel .sv-lead{color:${T.ink};max-width:680px}

.sv-fcta .panel .sv-btn-primary{--btn-bg:${T.ink};--btn-fg:${T.white};height:68px;padding:0 44px;font-size:18px}

.sv-fcta .panel .sv-btn-secondary{--btn2-bg:${T.white};--btn2-fg:${T.ink};--sh:${T.ink}}

.sv-fcta .ctas{display:flex;flex-wrap:wrap;justify-content:center;gap:14px;margin-top:8px}

@container (max-width:680px){.sv-fcta .panel{padding:48px 22px;border-radius:26px}.sv-fcta .ctas{width:100%}.sv-fcta .ctas .sv-btn{flex:1 1 100%}.sv-fcta .panel .sv-btn-primary{height:58px;padding:0 24px;font-size:15px}}

`

const POS: [number, number][] = [

    [110, 90],

    [590, 90],

    [60, 260],

    [640, 260],

    [230, 340],

    [470, 340],

]



function SecureNet({

    nodes,

    decor,

}: {

    nodes: { label: string; icon: string }[]

    decor: boolean

}) {

    const C: [number, number] = [350, 190]

    return (

        <Stage w={700} h={400} className="net">

            <svg

                width="700"

                height="400"

                style={{ position: "absolute", inset: 0, overflow: "visible" }}

                aria-hidden="true"

            >

                <ellipse

                    cx={C[0]}

                    cy={C[1]}

                    rx="300"

                    ry="150"

                    fill="none"

                    stroke="currentColor"

                    strokeOpacity=".35"

                    strokeWidth="1"

                    strokeDasharray="3 7"

                />

                {nodes.slice(0, 6).map((_, i) => (

                    <path

                        key={i}

                        d={`M${C[0]} ${C[1]} L${POS[i][0]} ${POS[i][1]}`}

                        stroke="currentColor"

                        strokeOpacity=".7"

                        strokeWidth="1.4"

                    />

                ))}

                {nodes.slice(0, 6).map((_, i) => (

                    <Packet

                        key={i}

                        d={`M${POS[i][0]} ${POS[i][1]} L${C[0]} ${C[1]}`}

                        dur={2.2 + i * 0.3}

                        delay={i * 0.4}

                        color={T.lime}

                        r={4}

                    />

                ))}

            </svg>

            <div className="core">

                <svg

                    className="sv-spin"

                    viewBox="0 0 200 200"

                    style={{

                        position: "absolute",

                        inset: -24,

                        width: 198,

                        height: 198,

                        ["--sd" as any]: "30s",

                    }}

                    aria-hidden="true"

                >

                    <circle

                        cx="100"

                        cy="100"

                        r="98"

                        fill="none"

                        stroke="currentColor"

                        strokeWidth="1.2"

                        strokeDasharray="5 9"

                    />

                    <circle

                        cx="100"

                        cy="2"

                        r="6"

                        fill={T.orange}

                        stroke={T.ink}

                        strokeWidth="1.2"

                    />

                </svg>

                <IconTile name="lock" tile={T.white} size={64} icon={30} />

            </div>

            {nodes.slice(0, 6).map((n, i) => (

                <div

                    key={i}

                    className="nd"

                    style={{ left: POS[i][0], top: POS[i][1] }}

                >

                    <Pop delay={0.1 * i} rotate={0}>

                        <div

                            className="b sv-bob"

                            style={{

                                ["--bd" as any]: `${6 + i * 0.7}s`,

                                ["--fr" as any]: "0deg",

                            }}

                        >

                            <Icon name={n.icon} size={24} />

                            <span className="ok" aria-hidden="true">

                                <Icon name="route" size={12} stroke={2.8} />

                            </span>

                            {n.label && <small>{n.label}</small>}

                        </div>

                    </Pop>

                </div>

            ))}

            {decor && (

                <>

                    <Sparkle

                        size={28}

                        fill={T.butter}

                        style={{ left: 300, top: 20 }}

                        delay={0.3}

                    />

                    <Sparkle

                        size={18}

                        fill={T.pink}

                        style={{ left: 660, top: 150 }}

                        delay={1.3}

                    />

                    <Planet

                        size={64}

                        fill={T.peach}

                        style={{ left: -40, top: 20 }}

                        className="sv-bob"

                    />

                </>

            )}

        </Stage>

    )

}



export default function FinalCTA(props: any) {

    const {

        tone,

        showNetwork,

        nodes,

        title,

        body,

        primaryLabel,

        primaryLink,

        secondaryLabel,

        secondaryLink,

        decor,

        sectionId,

    } = props

    const list = lines(nodes).map((l) => {

        const [label, icon] = cells(l)

        return { label, icon: ICON_NAMES.includes(icon) ? icon : "cpu" }

    })

    return (

        <Section

            tone={tone}

            id={sectionId}

            className="sv-fcta"

            css={CSS}

            label="Get started"

        >

            <div className="glow" aria-hidden="true" />

            {decor && (

                <div

                    className="sv-plusfield"

                    aria-hidden="true"

                    style={{ opacity: tone === "ink" ? 0.18 : 1 }}

                />

            )}

            <div className="sv-wrap">

                {showNetwork && (

                    <div style={{ color: "var(--text)" }}>

                        <SecureNet nodes={list} decor={decor} />

                    </div>

                )}

                <Reveal y={40}>

                    <div className="panel">

                        <Title text={title} className="sv-h1" />

                        {body && <p className="sv-lead">{body}</p>}

                        <div className="ctas">

                            <Btn

                                label={primaryLabel}

                                href={primaryLink}

                                arrow

                            />

                            <Btn

                                label={secondaryLabel}

                                href={secondaryLink}

                                variant="secondary"

                            />

                        </div>

                    </div>

                </Reveal>

            </div>

        </Section>

    )

}



addPropertyControls(FinalCTA, {

    tone: toneControl("ink"),

    showNetwork: {

        type: ControlType.Boolean,

        title: "Network art",

        defaultValue: true,

        enabledTitle: "Show",

        disabledTitle: "Hide",

    },

    nodes: {

        type: ControlType.String,

        title: "Network nodes",

        displayTextArea: true,

        description: "Up to 6, one per line: Label | icon",

        defaultValue:

            "Models | cpu\nAgents | bot\nAPIs | plug\nData | database\nApps | layers\nTeams | users",

        hidden: (p: any) => !p.showNetwork,

    },

    title: {

        type: ControlType.String,

        title: "Title",

        displayTextArea: true,

        defaultValue: "Make AI adoption a strength,\nnot a *blind spot.*",

        description:

            "*stars* = yellow marker · _underscores_ = orange · new line = line break.",

    },

    body: {

        type: ControlType.String,

        title: "Body",

        displayTextArea: true,

        defaultValue:

            "Build a clearer picture of your AI environment and take the next step toward stronger security governance.",

    },

    primaryLabel: {

        type: ControlType.String,

        title: "Primary CTA",

        defaultValue: "Book Your Demo",

    },

    primaryLink: {

        type: ControlType.Link,

        title: "Primary link",

        defaultValue: "/contact",

    },

    secondaryLabel: {

        type: ControlType.String,

        title: "Secondary CTA",

        defaultValue: "",

        description: "Optional. Leave empty to hide.",

    },

    secondaryLink: {

        type: ControlType.Link,

        title: "Secondary link",

        defaultValue: "/platform",

    },

    decor: decorControl,

    sectionId: {

        type: ControlType.String,

        title: "Section ID",

        defaultValue: "demo",

    },

})



// OAuth Navigator integration



// Shared control types verified.

