// SECUVANTA Navbar: optional announcement strip, butter logo pill, links with one dropdown, a soft cream pill and a
// black "Request a Demo" pill (pluto.security header). Transparent on top of the hero; after scrolling the bar
// becomes a floating white sticker (ink outline + hard shadow). Mobile: full-screen sheet with a sticky CTA.
// Place it inside a fixed frame (top 0, width 100%, z-index 10).
// Dropdown items are edited as lines: "Title | Description | /link | icon". Plain links: "Label | /link".
import * as React from "react"
import { addPropertyControls, ControlType } from "framer"
import {
    Section,
    Logo,
    Btn,
    Icon,
    IconTile,
    lines,
    cells,
    T,
    ICON_NAMES,
} from "./Kit.tsx"

const CSS = `
.sv-nav{padding:0;background:transparent}
.sv-nav .ann{display:flex;align-items:center;justify-content:center;gap:10px;min-height:40px;padding:8px 16px;background:${T.white};border-bottom:1px solid ${T.ink};font-size:14px;font-weight:500;line-height:1.4;color:${T.inkSoft};text-align:center}
.sv-nav .ann svg{color:${T.orange};flex-shrink:0}
.sv-nav .ann a{font-weight:600;text-decoration:underline;text-underline-offset:3px;white-space:nowrap}
.sv-nav .ann a:hover{color:${T.orange}}
.sv-nav .shell{padding:14px 24px 0;transition:padding .3s var(--e)}
.sv-nav .bar{position:relative;display:flex;align-items:center;gap:28px;height:72px;max-width:1360px;margin:0 auto;padding:0 16px;border-radius:999px;border:1.5px solid transparent;
  transition:background-color .3s var(--e),border-color .3s var(--e),box-shadow .3s var(--pop)}
.sv-nav[data-solid] .bar{background:${T.white};border-color:${T.ink};box-shadow:4.5px 4.5px 0 0 ${T.ink}}
.sv-nav .links{display:flex;align-items:center;gap:6px;margin-left:auto}
.sv-nav .lk{position:relative;display:inline-flex;align-items:center;gap:6px;height:40px;padding:0 14px;font-family:var(--sans);font-weight:600;font-size:16px;line-height:20px;color:${T.ink};border-radius:999px;
  transition:background-color .2s,translate .2s var(--pop)}
.sv-nav .lk:hover,.sv-nav .lk[aria-expanded="true"]{background:rgba(255,255,255,.55);translate:0 -1px}
.sv-nav[data-solid] .lk:hover,.sv-nav[data-solid] .lk[aria-expanded="true"]{background:${T.cream}}
.sv-nav .lk svg{transition:rotate .25s var(--e)}
.sv-nav .lk[aria-expanded="true"] svg{rotate:180deg}
.sv-nav .acts{display:flex;align-items:center;gap:10px;margin-left:12px}
.sv-nav .soft{display:inline-flex;align-items:center;gap:8px;height:44px;padding:0 18px;border-radius:999px;background:${T.cream};border:1px solid ${T.ink};font-weight:600;font-size:15px;color:${T.ink};box-shadow:1.2px 1.2px 0 0 ${T.ink};transition:translate .2s var(--pop),box-shadow .2s var(--pop)}
.sv-nav .soft:hover{translate:-2px -2px;box-shadow:3.5px 3.5px 0 0 ${T.ink}}
.sv-nav .soft svg{color:${T.orange}}
.sv-nav .drop{position:absolute;top:calc(100% + 12px);left:50%;width:min(620px,92vw);translate:-50% -6px;opacity:0;visibility:hidden;pointer-events:none;transition:opacity .25s var(--e),translate .3s var(--pop),visibility .25s}
.sv-nav .drop[data-open]{opacity:1;translate:-50% 0;visibility:visible;pointer-events:auto}
.sv-nav .panel{display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:10px;background:${T.white};border:1.5px solid ${T.ink};border-radius:24px;box-shadow:6px 7px 0 0 ${T.ink}}
.sv-nav .it{display:flex;gap:14px;align-items:flex-start;padding:14px;border-radius:16px;transition:background-color .2s}
.sv-nav .it:hover{background:${T.cream}}
.sv-nav .it b{display:block;font-family:var(--display);font-weight:600;font-size:15px;line-height:1.2;color:${T.ink};margin-bottom:4px}
.sv-nav .it span{display:block;font-size:13.5px;line-height:1.45;color:${T.mute}}
.sv-nav .burger{display:none;width:48px;height:48px;margin-left:auto;place-items:center;border-radius:50%;border:1.5px solid ${T.ink};background:${T.white};color:${T.ink};box-shadow:2.25px 2.25px 0 0 ${T.ink}}
.sv-nav .sheet{position:fixed;left:0;right:0;bottom:0;top:var(--sheet-top,112px);z-index:30;display:flex;flex-direction:column;background:${T.cream};border-top:1.5px solid ${T.ink};overflow:auto;padding:8px 20px 0}
.sv-nav .sheet .row{display:flex;align-items:center;justify-content:space-between;width:100%;padding:18px 4px;border-bottom:1px solid rgba(0,0,0,.14);font-family:var(--display);font-weight:700;font-size:22px;color:${T.ink};text-align:left}
.sv-nav .sheet .sub{display:grid;gap:2px;padding:6px 0 14px}
.sv-nav .sheet .sub a{padding:10px 8px;font-weight:500;font-size:16px;color:${T.body}}
.sv-nav .sheet .cta{position:sticky;bottom:0;display:grid;gap:10px;margin-top:auto;padding:16px 0 24px;background:${T.cream}}
.sv-nav .sheet .cta .sv-btn{width:100%}
@container (max-width:1080px){.sv-nav .links,.sv-nav .acts{display:none}.sv-nav .burger{display:grid}.sv-nav .drop{display:none}}
@container (max-width:680px){.sv-nav .shell{padding:10px 12px 0}.sv-nav .bar{height:64px;padding:0 8px 0 10px}.sv-nav .ann{font-size:12.5px}}
`

type Item = { title: string; desc: string; href: string; icon: string }
const parseItems = (s: string): Item[] =>
    lines(s).map((l) => {
        const [title, desc, href, icon] = cells(l)
        return {
            title,
            desc: desc || "",
            href: href || "#",
            icon: icon || "sparkles",
        }
    })
const parseLinks = (s: string) =>
    lines(s).map((l) => {
        const [label, href] = cells(l)
        return { label, href: href || "#" }
    })
const TILES = [T.butter, T.peach, T.lime, T.pink, T.cream, T.mint]

export default function Navbar(props: any) {
    const {
        brand,
        logo,
        showAnnouncement,
        announcement,
        announcementLinkLabel,
        announcementLink,
        dropLabel,
        dropItems,
        links,
        softLabel,
        softLink,
        ctaLabel,
        ctaLink,
        solidOnTop,
    } = props
    const [open, setOpen] = React.useState(false)
    const [sheet, setSheet] = React.useState(false)
    const [acc, setAcc] = React.useState(false)
    const [solid, setSolid] = React.useState(!!solidOnTop)
    const rootRef = React.useRef<HTMLDivElement>(null)
    const close = React.useRef<any>(null)
    React.useEffect(() => {
        if (solidOnTop || typeof window === "undefined")
            return setSolid(!!solidOnTop)
        const on = () => setSolid(window.scrollY > 24)
        on()
        window.addEventListener("scroll", on, { passive: true })
        return () => window.removeEventListener("scroll", on)
    }, [solidOnTop])
    React.useEffect(() => {
        const k = (e: KeyboardEvent) =>
            e.key === "Escape" && (setOpen(false), setSheet(false))
        window.addEventListener("keydown", k)
        return () => window.removeEventListener("keydown", k)
    }, [])
    React.useEffect(() => {
        if (!sheet || !rootRef.current) return
        const r = rootRef.current.getBoundingClientRect()
        rootRef.current.style.setProperty(
            "--sheet-top",
            `${Math.round(r.bottom)}px`
        )
    }, [sheet])
    const enter = () => {
        clearTimeout(close.current)
        setOpen(true)
    }
    const leave = () => {
        close.current = setTimeout(() => setOpen(false), 160)
    }
    const items = parseItems(dropItems)
    const plainLinks = parseLinks(links)
    const isSolid = solid || sheet

    return (
        <Section
            as="header"
            pad={false}
            className="sv-nav"
            css={CSS}
            label="Site header"
        >
            <div
                ref={rootRef}
                data-solid={isSolid ? "" : undefined}
                className="sv-nav"
            >
                {showAnnouncement && announcement && (
                    <div className="ann">
                        <Icon name="sparkles" size={15} stroke={2} />
                        <span>
                            {announcement}{" "}
                            {announcementLinkLabel && (
                                <a href={announcementLink || "#"}>
                                    {announcementLinkLabel}
                                </a>
                            )}
                        </span>
                    </div>
                )}
                <div className="shell">
                    <nav className="bar" aria-label="Main">
                        <Logo name={brand} image={logo} size={32} />
                        <div className="links">
                            {dropLabel && items.length > 0 && (
                                <div
                                    style={{ position: "relative" }}
                                    onMouseEnter={enter}
                                    onMouseLeave={leave}
                                >
                                    <button
                                        className="lk"
                                        aria-expanded={open}
                                        aria-controls="sv-drop"
                                        onClick={() => setOpen(!open)}
                                    >
                                        {dropLabel}
                                        <Icon
                                            name="chevron-down"
                                            size={15}
                                            stroke={2}
                                        />
                                    </button>
                                    <div
                                        id="sv-drop"
                                        className="drop"
                                        data-open={open ? "" : undefined}
                                    >
                                        <div className="panel">
                                            {items.map((it, i) => (
                                                <a
                                                    key={i}
                                                    className="it"
                                                    href={it.href}
                                                    onClick={() =>
                                                        setOpen(false)
                                                    }
                                                >
                                                    <IconTile
                                                        name={
                                                            ICON_NAMES.includes(
                                                                it.icon
                                                            )
                                                                ? it.icon
                                                                : "sparkles"
                                                        }
                                                        tile={
                                                            TILES[
                                                                i % TILES.length
                                                            ]
                                                        }
                                                        size={40}
                                                        icon={19}
                                                    />
                                                    <span>
                                                        <b>{it.title}</b>
                                                        <span>{it.desc}</span>
                                                    </span>
                                                </a>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                            {plainLinks.map((l, i) => (
                                <a key={i} className="lk" href={l.href}>
                                    {l.label}
                                </a>
                            ))}
                        </div>
                        <div className="acts">
                            {softLabel && (
                                <a
                                    className="soft"
                                    href={
                                        softLabel === "Catalogue"
                                            ? "/workspace?view=catalog"
                                            : softLink || "#"
                                    }
                                >
                                    <Icon
                                        name="sparkles"
                                        size={15}
                                        stroke={2}
                                    />
                                    {softLabel}
                                </a>
                            )}
                            <Btn label={ctaLabel} href={ctaLink} size="sm" />
                        </div>
                        <button
                            className="burger"
                            aria-label={sheet ? "Close menu" : "Open menu"}
                            aria-expanded={sheet}
                            onClick={() => setSheet(!sheet)}
                        >
                            <Icon
                                name={sheet ? "x" : "menu"}
                                size={20}
                                stroke={2}
                            />
                        </button>
                    </nav>
                </div>

                {sheet && (
                    <div className="sheet" role="dialog" aria-label="Menu">
                        {dropLabel && items.length > 0 && (
                            <div>
                                <button
                                    className="row"
                                    aria-expanded={acc}
                                    onClick={() => setAcc(!acc)}
                                >
                                    {dropLabel}
                                    <Icon
                                        name={acc ? "x" : "plus"}
                                        size={20}
                                        stroke={2}
                                    />
                                </button>
                                {acc && (
                                    <div className="sub">
                                        {items.map((s, i) => (
                                            <a
                                                key={i}
                                                href={s.href}
                                                onClick={() => setSheet(false)}
                                            >
                                                {s.title}
                                            </a>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                        {plainLinks.map((l, i) => (
                            <a
                                key={i}
                                className="row"
                                href={l.href}
                                onClick={() => setSheet(false)}
                            >
                                {l.label}
                                <Icon name="arrow-right" size={18} stroke={2} />
                            </a>
                        ))}
                        <div className="cta">
                            {softLabel && (
                                <Btn
                                    label={softLabel}
                                    href={softLink}
                                    variant="secondary"
                                />
                            )}
                            <Btn label={ctaLabel} href={ctaLink} />
                        </div>
                    </div>
                )}
            </div>
        </Section>
    )
}

addPropertyControls(Navbar, {
    brand: {
        type: ControlType.String,
        title: "Brand",
        defaultValue: "Secuvanta",
    },
    logo: {
        type: ControlType.ResponsiveImage,
        title: "Logo image",
        description: "Optional. Replaces the built-in mark.",
    },
    showAnnouncement: {
        type: ControlType.Boolean,
        title: "Announcement",
        defaultValue: true,
        enabledTitle: "Show",
        disabledTitle: "Hide",
    },
    announcement: {
        type: ControlType.String,
        title: "Announcement text",
        defaultValue:
            "New: the 2026 guide to securing AI agents and connected tools.",
        hidden: (p: any) => !p.showAnnouncement,
    },
    announcementLinkLabel: {
        type: ControlType.String,
        title: "Announcement link label",
        defaultValue: "Read here",
        hidden: (p: any) => !p.showAnnouncement,
    },
    announcementLink: {
        type: ControlType.Link,
        title: "Announcement link",
        defaultValue: "",
        hidden: (p: any) => !p.showAnnouncement,
    },
    dropLabel: {
        type: ControlType.String,
        title: "Dropdown label",
        defaultValue: "Platform",
    },
    dropItems: {
        type: ControlType.String,
        title: "Dropdown items",
        displayTextArea: true,
        description:
            "One per line: Title | Description | /link | icon (search, gauge, shield-check, scale, activity, plug, bot, lock…)",
        defaultValue:
            "Overview | One platform, four layers of AI protection | /platform | layers\nAI Discovery | Find every model, agent and integration | /platform#discovery | search\nRisk Intelligence | Turn findings into clear priorities | /platform#risk | gauge\nAI Protection | Guardrails where AI meets your systems | /platform#protection | shield-check",
    },
    links: {
        type: ControlType.String,
        title: "Links",
        displayTextArea: true,
        description: "One per line: Label | /link",
        defaultValue:
            "Solutions | /solutions\nResources | /resources\nAbout | /about",
    },
    softLabel: {
        type: ControlType.String,
        title: "Soft pill label",
        defaultValue: "Contact",
        description: "Cream pill next to the CTA. Leave empty to hide.",
    },
    softLink: {
        type: ControlType.Link,
        title: "Soft pill link",
        defaultValue: "/contact",
    },
    ctaLabel: {
        type: ControlType.String,
        title: "CTA label",
        defaultValue: "Request a Demo",
    },
    ctaLink: {
        type: ControlType.Link,
        title: "CTA link",
        defaultValue: "/contact",
    },
    solidOnTop: {
        type: ControlType.Boolean,
        title: "Solid on top",
        defaultValue: false,
        description:
            "Show the white sticker bar before scrolling (use on pages without a colored hero).",
    },
})
