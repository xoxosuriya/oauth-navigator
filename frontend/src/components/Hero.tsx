// SECUVANTA Hero: pluto.security's hero composition. A peach sky with plus-marks, a sunburst behind a central AI core,

// connected nodes (models, agents, APIs, data sources) with green verified badges and one amber risk alert, a small

// security overview panel, and a big butter "planet" horizon under the centered headline and CTAs.

// Motion: nodes pop in with a spring, packets travel along the links, the core ring spins slowly, the risk node

// pulses and the overview numbers count up. Everything renders still on the canvas and with reduced motion.

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

    CountUp,

    DemoTag,

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

.sv-hero{padding:150px 0 0;overflow:hidden}

.sv-hero .sky{position:absolute;inset:0;pointer-events:none}

.sv-hero .art{position:relative;max-width:1180px;margin:0 auto;z-index:3}

.sv-hero .net{max-width:780px;margin:0 auto 0 max(0px,calc(50% - 560px))}

.sv-hero .panel{position:absolute;right:0;top:40px;width:272px;z-index:3}

.sv-hero .horizon{position:relative;margin-top:-120px;padding:176px 0 120px;z-index:2}

.sv-hero .planet{position:absolute;left:50%;top:0;width:max(1900px,150%);height:2400px;translate:-50% 0;border-radius:50%;background:${T.butter};border:1.5px solid ${T.ink}}

.sv-hero .crater{position:absolute;border:1.5px solid ${T.ink};border-radius:50%;background:#F4F06A}

.sv-hero .copy{position:relative;display:flex;flex-direction:column;align-items:center;text-align:center;gap:24px;max-width:860px;margin:0 auto}

.sv-hero .copy .sv-lead{max-width:640px}

.sv-hero .ctas{display:flex;flex-wrap:wrap;justify-content:center;gap:14px;margin-top:6px}
.sv-hero .search-wrap{display:flex;align-items:center;justify-content:center;gap:12px;flex-wrap:wrap;width:100%;max-width:680px;margin:12px auto 0}
.sv-hero .search-input-box{position:relative;flex:1 1 240px;min-width:240px}
.sv-hero .search-input{width:100%;height:48px;padding:0 18px 0 42px;border-radius:999px;border:1.5px solid ${T.ink};background:${T.white};font-size:14px;font-family:inherit;box-shadow:3px 3px 0 0 ${T.ink};box-sizing:border-box;outline:none}
.sv-hero .search-icon{position:absolute;left:14px;top:50%;translate:0 -50%;color:${T.mute};display:flex;pointer-events:none}


/* nodes on the 780 × 470 canvas */

.sv-hero .node{position:absolute;translate:-50% -50%;z-index:2}

.sv-hero .nd{display:flex;align-items:center;gap:10px;height:52px;padding:0 16px 0 6px;border-radius:999px;background:${T.white};border:1.5px solid ${T.ink};box-shadow:3px 3px 0 0 ${T.ink};white-space:nowrap;font-weight:600;font-size:14.5px;color:${T.ink}}

.sv-hero .nd .badge{position:absolute;right:-8px;top:-9px;display:grid;place-items:center;width:24px;height:24px;border-radius:50%;border:1.5px solid ${T.ink};color:${T.ink}}

.sv-hero .nd.ok .badge{background:${T.lime}}

.sv-hero .nd.risk{background:#FFE1A6}

.sv-hero .nd.risk .badge{background:${T.risk}}

.sv-hero .nd.risk .badge::after{content:"";position:absolute;inset:-6px;border-radius:50%;border:2px solid ${T.risk};animation:sv-ping 1.8s cubic-bezier(0,0,.2,1) infinite}

.sv-hero .alert{position:absolute;left:calc(100% + 14px);top:50%;translate:0 -50%;display:grid;gap:3px;width:176px;padding:10px 12px;border-radius:14px;background:${T.white};border:1.5px solid ${T.ink};box-shadow:2.25px 2.25px 0 0 ${T.ink};font-size:12px;line-height:1.35;color:${T.body};white-space:normal}

.sv-hero .alert b{display:flex;align-items:center;gap:6px;font-family:var(--display);font-weight:600;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:${T.ink}}

.sv-hero .core{position:absolute;left:390px;top:225px;translate:-50% -50%;z-index:2;display:grid;place-items:center;width:172px;height:172px}

.sv-hero .core .disc{position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;width:150px;height:150px;border-radius:50%;background:${T.cream};border:1.5px solid ${T.ink};box-shadow:5px 5px 0 0 ${T.ink};text-align:center}

.sv-hero .core .disc b{font-family:var(--display);font-weight:700;font-size:13px;letter-spacing:.06em;text-transform:uppercase}

.sv-hero .core .ring{position:absolute;inset:-26px;pointer-events:none}

.sv-hero .core .sv-ico,.sv-hero .nd .sv-ico{border-radius:50%!important}

/* overview panel */

.sv-hero .ov{padding:0;overflow:hidden;border-radius:20px}

.sv-hero .ov .hd{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:12px 14px;border-bottom:1.5px solid ${T.ink};background:${T.cream}}

.sv-hero .ov .hd b{font-family:var(--display);font-weight:600;font-size:12.5px}

.sv-hero .ov .rw{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:11px 14px;border-top:1px solid rgba(0,0,0,.1);font-size:13px;color:${T.body}}

.sv-hero .ov .rw:first-of-type{border-top:0}

.sv-hero .ov .rw span{display:flex;align-items:center;gap:8px}

.sv-hero .ov .rw strong{font-family:var(--display);font-weight:700;font-size:15px;color:${T.ink}}

.sv-hero .ov .meter{padding:4px 14px 14px}

.sv-hero .ov .meter div{height:10px;border-radius:999px;border:1px solid ${T.ink};background:${T.white};overflow:hidden}

.sv-hero .ov .meter i{display:block;height:100%;background:${T.lime};border-right:1px solid ${T.ink}}

.sv-hero .ov .ft{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-top:1.5px solid ${T.ink}}

@container (max-width:1180px){.sv-hero .panel{right:8px;width:250px}}

@container (max-width:1000px){.sv-hero .net{margin:0 auto}.sv-hero{padding-top:130px}.sv-hero .panel{position:relative;right:auto;top:auto;width:min(340px,100%);margin:8px auto 0}.sv-hero .horizon{margin-top:-40px;padding-top:150px}}

@container (max-width:680px){.sv-hero{padding-top:118px}.sv-hero .horizon{padding:128px 0 88px}.sv-hero .ctas{width:100%}.sv-hero .ctas .sv-btn{flex:1 1 100%}.sv-hero .panel{display:none}}

`



type NodeT = { label: string; icon: string; status: "ok" | "risk" }

const POS: [number, number][] = [

    [128, 92],

    [652, 86],

    [96, 318],

    [680, 312],

    [300, 424],

]

const TILES = [T.peach, T.lime, T.pink, T.mint, T.butter]



function Network({

    nodes,

    riskTitle,

    riskText,

    coreLabel,

    decor,

}: {

    nodes: NodeT[]

    riskTitle: string

    riskText: string

    coreLabel: string

    decor: boolean

}) {

    const C: [number, number] = [390, 225]

    const path = (p: [number, number], i: number) => {

        const mx = (p[0] + C[0]) / 2 + (i % 2 ? 40 : -40)

        const my = (p[1] + C[1]) / 2 + (i % 2 ? -30 : 30)

        return `M${C[0]} ${C[1]} Q${mx} ${my} ${p[0]} ${p[1]}`

    }

    const rays = Array.from({ length: 30 }, (_, i) => {

        const a = Math.PI + (i / 29) * Math.PI

        const r1 = 104

        const r2 = 150 + ((i * 37) % 5) * 22

        return `M${C[0] + Math.cos(a) * r1} ${C[1] + Math.sin(a) * r1}L${C[0] + Math.cos(a) * r2} ${C[1] + Math.sin(a) * r2}`

    })

    return (

        <Stage w={780} h={470} className="net">

            <svg

                width="780"

                height="470"

                viewBox="0 0 780 470"

                style={{ position: "absolute", inset: 0, overflow: "visible" }}

                aria-hidden="true"

            >

                <path

                    d={rays.join("")}

                    stroke={T.ink}

                    strokeWidth="1.3"

                    strokeLinecap="round"

                />

                {nodes.slice(0, 5).map((n, i) => (

                    <path

                        key={i}

                        d={path(POS[i], i)}

                        fill="none"

                        stroke={T.ink}

                        strokeWidth="1.5"

                        className="sv-flow"

                        strokeDasharray="4 7"

                    />

                ))}

                {nodes.slice(0, 5).map((n, i) => (

                    <Packet

                        key={i}

                        d={path(POS[i], i)}

                        dur={2.4 + i * 0.35}

                        delay={i * 0.5}

                        color={n.status === "risk" ? T.risk : T.lime}

                    />

                ))}

            </svg>

            {decor && (

                <>

                    <Planet

                        size={74}

                        fill={T.teal}

                        style={{ left: -40, top: 150 }}

                        className="sv-bob"

                    />

                    <Sparkle

                        size={26}

                        fill={T.white}

                        style={{ left: 250, top: 20 }}

                        delay={0.4}

                    />

                    <Sparkle

                        size={20}

                        fill={T.butter}

                        style={{ left: 540, top: 6 }}

                        delay={1.2}

                    />

                    <Sparkle

                        size={30}

                        fill={T.pink}

                        style={{ left: 560, top: 400 }}

                        delay={2}

                    />

                </>

            )}

            <div className="core">

                <svg

                    className="ring sv-spin"

                    viewBox="0 0 224 224"

                    style={{ ["--sd" as any]: "36s" }}

                    aria-hidden="true"

                >

                    <circle

                        cx="112"

                        cy="112"

                        r="110"

                        fill="none"

                        stroke={T.ink}

                        strokeWidth="1.2"

                        strokeDasharray="4 8"

                    />

                    <circle

                        cx="112"

                        cy="2"

                        r="6"

                        fill={T.orange}

                        stroke={T.ink}

                        strokeWidth="1.2"

                    />

                    <circle

                        cx="2"

                        cy="112"

                        r="4.5"

                        fill={T.butter}

                        stroke={T.ink}

                        strokeWidth="1.2"

                    />

                </svg>

                <Pop className="disc" rotate={0} now>

                    <IconTile

                        name="layers"

                        tile={T.butter}

                        size={56}

                        icon={28}

                    />

                    <b>{coreLabel}</b>

                </Pop>

            </div>

            {nodes.slice(0, 5).map((n, i) => (

                <div

                    key={i}

                    className="node"

                    style={{ left: POS[i][0], top: POS[i][1] }}

                >

                    <Pop delay={0.25 + i * 0.12} rotate={i % 2 ? 8 : -8} now>

                        <div

                            className={`nd ${n.status} sv-bob`}

                            style={{

                                position: "relative",

                                ["--bd" as any]: `${6 + i}s`,

                                ["--bdl" as any]: `${i * 0.6}s`,

                                ["--fr" as any]: "0deg",

                            }}

                        >

                            <IconTile

                                name={

                                    ICON_NAMES.includes(n.icon) ? n.icon : "cpu"

                                }

                                tile={

                                    n.status === "risk"

                                        ? T.white

                                        : TILES[i % TILES.length]

                                }

                                size={40}

                                icon={19}

                            />

                            {n.label}

                            <span

                                className="badge"

                                aria-label="Architecture node"

                            >

                                <Icon

                                    name={

                                        n.status === "risk" ? "help" : "route"

                                    }

                                    size={13}

                                    stroke={2.6}

                                />

                            </span>

                            {n.status === "risk" && (riskTitle || riskText) && (

                                <span className="alert">

                                    <b>

                                        <Icon

                                            name="alert"

                                            size={12}

                                            stroke={2.4}

                                        />

                                        {riskTitle}

                                    </b>

                                    {riskText}

                                </span>

                            )}

                        </div>

                    </Pop>

                </div>

            ))}

        </Stage>

    )

}



function Overview({

    title,

    rows,

    meterLabel,

    meterValue,

    demoLabel,

}: {

    title: string

    rows: string[][]

    meterLabel: string

    meterValue: number

    demoLabel: string

}) {

    const color = (t: string) =>

        t === "risk"

            ? T.risk

            : t === "bad"

              ? T.critical

              : t === "info"

                ? T.peach

                : T.verified

    return (

        <Pop delay={0.7} rotate={4} className="panel" now>

            <div className="sv-card ov" role="group" aria-label={title}>

                <div className="hd">

                    <b>{title}</b>

                    <Icon name="activity" size={16} stroke={2} />

                </div>

                {rows.map(([label, value, tone], i) => (

                    <div className="rw" key={i}>

                        <span>

                            <i

                                className="sv-dot"

                                style={{ color: color(tone) }}

                            />

                            {label}

                        </span>

                        <strong>

                            <CountUp value={value} />

                        </strong>

                    </div>

                ))}

                {meterLabel && (

                    <>

                        <div

                            className="rw"

                            style={{ borderTop: "1px solid rgba(0,0,0,.1)" }}

                        >

                            <span>{meterLabel}</span>

                            <strong>

                                <CountUp value={`${meterValue}%`} />

                            </strong>

                        </div>

                        <div className="meter">

                            <div>

                                <i

                                    style={{

                                        width: `${Math.max(0, Math.min(100, meterValue))}%`,

                                    }}

                                />

                            </div>

                        </div>

                    </>

                )}

                <div className="ft">

                    <DemoTag text={demoLabel} />

                </div>

            </div>

        </Pop>

    )

}



export default function Hero(props: any) {

    const [searchApp, setSearchApp] = React.useState("")

    const {

        tone,

        title,

        body,

        primaryLabel,

        primaryLink,

        secondaryLabel,

        secondaryLink,

        coreLabel,

        nodes,

        riskTitle,

        riskText,

        showPanel,

        panelTitle,

        panelRows,

        meterLabel,

        meterValue,

        demoLabel,

        decor,

        sectionId,

    } = props

    const parsed: NodeT[] = lines(nodes).map((l) => {

        const [label, icon, status] = cells(l)

        return {

            label,

            icon: icon || "cpu",

            status: status === "risk" ? "risk" : "ok",

        }

    })

    const rows = lines(panelRows).map(cells)

    return (

        <Section

            tone={tone}

            id={sectionId}

            className="sv-hero"

            css={CSS}

            label="Hero"

        >

            {decor && (

                <div className="sky" aria-hidden="true">

                    <div className="sv-plusfield" />

                    <Planet

                        size={96}

                        fill={T.lime}

                        style={{ left: "4%", top: 210 }}

                        className="sv-bob"

                    />

                    <Planet

                        size={130}

                        fill={T.coral}

                        ring={false}

                        style={{ right: "-34px", top: 430 }}

                        className="sv-bob"

                    />

                    <Sparkle

                        size={34}

                        fill={T.ink}

                        style={{ left: "16%", top: 150 }}

                        delay={0.8}

                    />

                    <Sparkle

                        size={22}

                        fill={T.white}

                        style={{ right: "18%", top: 140 }}

                        delay={1.6}

                    />

                </div>

            )}

            <div className="sv-wrap">

                <div className="art">

                    <Network

                        nodes={parsed}

                        riskTitle={riskTitle}

                        riskText={riskText}

                        coreLabel={coreLabel}

                        decor={decor}

                    />

                    {showPanel && (

                        <Overview

                            title={panelTitle}

                            rows={rows}

                            meterLabel={meterLabel}

                            meterValue={meterValue}

                            demoLabel={demoLabel}

                        />

                    )}

                </div>

            </div>

            <div className="horizon">

                <div className="planet" aria-hidden="true">

                    <i

                        className="crater"

                        style={{ left: "31%", top: 70, width: 120, height: 34 }}

                    />

                    <i

                        className="crater"

                        style={{ left: "62%", top: 46, width: 80, height: 22 }}

                    />

                </div>

                <div className="sv-wrap">

                    <div className="copy">

                        <Title

                            as="h1"

                            text={title}

                            className="sv-h1"

                            now

                            delay={0.1}

                        />

                        {body && (

                            <Reveal delay={0.3} now>

                                <p className="sv-lead">{body}</p>

                            </Reveal>

                        )}

                        <Reveal delay={0.4} now>

                            <form

                                className="search-wrap"

                                onSubmit={(e) => {

                                    e.preventDefault()

                                    const target = searchApp.trim()

                                        ? `/workspace?app=${encodeURIComponent(searchApp.trim())}`

                                        : primaryLink || "/workspace"

                                    window.location.href = target

                                }}

                            >

                                <div className="search-input-box">

                                    <input

                                        className="search-input"

                                        type="text"

                                        placeholder="Search an app (e.g. Slack, Notion)..."

                                        value={searchApp}

                                        onChange={(e) => setSearchApp(e.target.value)}

                                        aria-label="Search an application to investigate"

                                    />

                                    <span className="search-icon">

                                        <Icon name="search" size={17} stroke={2} />

                                    </span>

                                </div>

                                <Btn

                                    label={primaryLabel}

                                    arrow

                                    href={searchApp.trim() ? `/workspace?app=${encodeURIComponent(searchApp.trim())}` : primaryLink}

                                />

                                <Btn

                                    label={secondaryLabel}

                                    href={secondaryLink}

                                    variant="secondary"

                                />

                            </form>

                        </Reveal>

                    </div>

                </div>

            </div>

        </Section>

    )

}



addPropertyControls(Hero, {

    tone: toneControl("peach"),

    title: {

        type: ControlType.String,

        title: "Title",

        displayTextArea: true,

        defaultValue: "Secure AI.\nEmpower Innovation.",

        description:

            "*stars* = yellow marker · _underscores_ = orange · new line = line break.",

    },

    body: {

        type: ControlType.String,

        title: "Body",

        displayTextArea: true,

        defaultValue:

            "Discover, assess, and protect every AI system across your organization. Secuvanta gives security teams the visibility and control to adopt AI with confidence.",

    },

    primaryLabel: {

        type: ControlType.String,

        title: "Primary CTA",

        defaultValue: "Request a Demo",

    },

    primaryLink: {

        type: ControlType.Link,

        title: "Primary link",

        defaultValue: "/contact",

    },

    secondaryLabel: {

        type: ControlType.String,

        title: "Secondary CTA",

        defaultValue: "Explore the Platform",

    },

    secondaryLink: {

        type: ControlType.Link,

        title: "Secondary link",

        defaultValue: "/platform",

    },

    coreLabel: {

        type: ControlType.String,

        title: "Core label",

        defaultValue: "AI Core",

    },

    nodes: {

        type: ControlType.String,

        title: "Nodes",

        displayTextArea: true,

        description:

            "Up to 5, one per line: Label | icon | ok or risk. Icons: cpu, bot, plug, database, server, code, key…",

        defaultValue:

            "Models | cpu | ok\nAPIs | plug | ok\nAgents | bot | ok\nData sources | database | ok\nShadow plugin | zap | risk",

    },

    riskTitle: {

        type: ControlType.String,

        title: "Risk title",

        defaultValue: "Risk alert",

    },

    riskText: {

        type: ControlType.String,

        title: "Risk text",

        displayTextArea: true,

        defaultValue: "Unreviewed plugin requests access to customer data.",

    },

    showPanel: {

        type: ControlType.Boolean,

        title: "Overview panel",

        defaultValue: true,

        enabledTitle: "Show",

        disabledTitle: "Hide",

    },

    panelTitle: {

        type: ControlType.String,

        title: "Panel title",

        defaultValue: "Security overview",

        hidden: (p: any) => !p.showPanel,

    },

    panelRows: {

        type: ControlType.String,

        title: "Panel rows",

        displayTextArea: true,

        description: "One per line: Label | value | ok, risk or info",

        defaultValue:

            "AI assets found | 248 | info\nVerified | 231 | ok\nNeeds review | 1 | risk",

        hidden: (p: any) => !p.showPanel,

    },

    meterLabel: {

        type: ControlType.String,

        title: "Meter label",

        defaultValue: "Policy coverage",

        hidden: (p: any) => !p.showPanel,

    },

    meterValue: {

        type: ControlType.Number,

        title: "Meter %",

        defaultValue: 92,

        min: 0,

        max: 100,

        step: 1,

        unit: "%",

        hidden: (p: any) => !p.showPanel,

    },

    demoLabel: {

        type: ControlType.String,

        title: "Data note",

        defaultValue: "Live data after API connect",

        description:

            "Small tag under the panel: tells visitors these numbers are a sample until real data is connected. Leave empty to hide.",

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

