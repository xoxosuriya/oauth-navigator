// SECUVANTA UI Kit: design tokens, shared CSS, icons, decorations, brand and motion primitives used by every section.
// Look & feel follows pluto.security: flat pastel surfaces (peach, butter, cream), 1px black ink outlines, hard offset
// shadows with zero blur, pill buttons, chunky Unbounded headlines, friendly Poppins body copy, hand-drawn sparkles and
// planets, and springy "boing" hovers (cubic-bezier(.5,2.5,.7,.7)).
// Rebrand the template by editing `T` (colors) and the font constants. Values mirror the project's Color Styles
// (/Brand, /Surface, /Text, /Border, /Status) and Text Styles (Unbounded + Poppins).
// Every section has a "Tone" control (White / Cream / Peach / Butter / Ink) so buyers can alternate backgrounds.
// This file is a helper module. It is not meant to be placed on the canvas.
import * as React from "react"
import * as Framer from "framer"
import { motion, useInView, useReducedMotion, animate } from "framer-motion"

/* ----------------------------------------------------------------------------
 * Tokens
 * --------------------------------------------------------------------------*/
export const T = {
    ink: "#000000",
    inkSoft: "#111013",
    body: "#1A1A1A",
    mute: "#5E5E5E",
    white: "#FFFFFF",
    orange: "#FA683A",
    orangeDeep: "#F35F31",
    butter: "#FFFF78",
    peach: "#FFB89F",
    cream: "#FDF2D4",
    lime: "#C1F174",
    teal: "#5FB89B",
    pink: "#FCA5B5",
    coral: "#FDB2AD",
    blush: "#FFD9D9",
    mint: "#E9F0EB",
    verified: "#2E9E6A",
    risk: "#FFB23F",
    critical: "#F0533A",
}

export const DISPLAY = `"Unbounded", "Unbounded Placeholder", system-ui, -apple-system, "Segoe UI", sans-serif`
export const SANS = `"Poppins", "Poppins Placeholder", system-ui, -apple-system, "Segoe UI", sans-serif`

export type Tone = "white" | "cream" | "peach" | "butter" | "ink"
export const TONE_OPTIONS = {
    options: ["white", "cream", "peach", "butter", "ink"],
    optionTitles: ["White", "Cream", "Peach", "Butter (yellow)", "Ink (dark)"],
}
/** Pluto's overshoot curve, used for every hover "pop". */
export const POP = "cubic-bezier(.5,2.5,.7,.7)"
export const EASE = [0.22, 0.8, 0.3, 1] as const

/* ----------------------------------------------------------------------------
 * Shared CSS (every section renders it through <Section />)
 * --------------------------------------------------------------------------*/
export const KIT_CSS = `
@import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@400;600;700;800&family=Poppins:wght@300;400;500;600;700&display=swap');
.sv-root{position:relative;width:100%;box-sizing:border-box;container-type:inline-size;font-family:${SANS};font-size:16px;line-height:1.4;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
  --bg:${T.white};--card:${T.white};--card2:${T.cream};--text:${T.ink};--body:${T.body};--mute:${T.mute};--line:${T.ink};--line2:rgba(0,0,0,.14);--line3:rgba(0,0,0,.07);
  --sh:${T.ink};--accent:${T.orange};--accent-h:${T.orangeDeep};--hl:${T.butter};
  --btn-bg:${T.ink};--btn-fg:${T.white};--btn-sh:${T.orange};--btn2-bg:${T.white};--btn2-fg:${T.ink};
  --good:${T.verified};--warn:${T.risk};--bad:${T.critical};--plus:rgba(0,0,0,.12);
  --pop:${POP};--e:cubic-bezier(.4,0,.2,1);--display:${DISPLAY};--sans:${SANS};
  background:var(--bg);color:var(--text);overflow-x:clip;color-scheme:light}
.sv-root[data-tone="cream"]{--bg:${T.cream};--card2:${T.white}}
.sv-root[data-tone="peach"]{--bg:${T.peach};--card2:${T.cream};--plus:rgba(255,255,255,.55)}
.sv-root[data-tone="butter"]{--bg:${T.butter};--card2:${T.cream}}
.sv-root[data-tone="ink"]{--bg:${T.ink};--card:${T.inkSoft};--card2:#1E1C22;--text:${T.white};--body:rgba(255,255,255,.86);--mute:rgba(255,255,255,.6);--line:rgba(255,255,255,.9);--line2:rgba(255,255,255,.18);--line3:rgba(255,255,255,.08);
  --sh:${T.orange};--btn-bg:${T.butter};--btn-fg:${T.ink};--btn-sh:${T.orange};--btn2-bg:transparent;--btn2-fg:${T.white};--plus:rgba(255,255,255,.1);color-scheme:dark}
.sv-root *,.sv-root *::before,.sv-root *::after{box-sizing:border-box}
:where(.sv-root) a{color:inherit;text-decoration:none}
:where(.sv-root) button{font-family:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer;letter-spacing:inherit}
:where(.sv-root) :is(p,h1,h2,h3,h4,h5,h6,ul,ol,li,figure,blockquote,dl,dd){margin:0;padding:0}
:where(.sv-root) :is(ul,ol){list-style:none}
:where(.sv-root) img{display:block;max-width:100%}
.sv-root :focus-visible{outline:2.5px solid var(--accent);outline-offset:3px;border-radius:6px}

:where(.sv-section){padding:128px 0}
.sv-wrap{position:relative;width:100%;max-width:1360px;margin:0 auto;padding:0 40px}
/* Type: sizes follow the section width (cqw) between the phone and desktop values of the Text Styles */
.sv-display{font-family:var(--display);font-weight:700;font-size:clamp(48px,7.8cqw,112px);line-height:1;letter-spacing:-.02em;color:var(--text);text-wrap:balance}
.sv-h1{font-family:var(--display);font-weight:800;font-size:clamp(38px,4.4cqw,64px);line-height:1.04;letter-spacing:-.02em;color:var(--text);text-wrap:balance}
.sv-h2{font-family:var(--display);font-weight:700;font-size:clamp(30px,3.6cqw,52px);line-height:1.15;letter-spacing:-.01em;color:var(--text);text-wrap:balance}
.sv-h3{font-family:var(--display);font-weight:800;font-size:clamp(26px,2.8cqw,40px);line-height:1.05;letter-spacing:-.02em;color:var(--text);text-wrap:balance}
.sv-h4{font-family:var(--display);font-weight:700;font-size:clamp(21px,1.95cqw,28px);line-height:1.12;color:var(--text)}
.sv-h5{font-family:var(--display);font-weight:600;font-size:clamp(17px,1.4cqw,20px);line-height:1.15;color:var(--text)}
.sv-eyebrow{font-family:var(--sans);font-weight:500;font-size:clamp(16px,1.7cqw,24px);line-height:1.3;text-transform:uppercase;color:var(--accent)}
.sv-tag{font-family:var(--sans);font-weight:600;font-size:12px;line-height:1.35;letter-spacing:.12em;text-transform:uppercase;color:var(--body)}
.sv-lead{font-family:var(--sans);font-weight:300;font-size:clamp(18px,1.7cqw,23px);line-height:1.45;color:var(--text);text-wrap:pretty}
.sv-body{font-size:16.5px;line-height:1.5;color:var(--body);text-wrap:pretty}
.sv-small{font-size:14px;line-height:1.5;color:var(--body)}
.sv-cap{font-size:12px;line-height:1.5;letter-spacing:.01em;color:var(--mute)}
.sv-num{font-family:var(--display);font-variant-numeric:tabular-nums}
.sv-acc{color:var(--accent)}
.sv-hl{padding:0 .06em;margin:0 -.06em;border-radius:.18em;background:linear-gradient(180deg,transparent 56%,var(--hl) 56%,var(--hl) 94%,transparent 94%);-webkit-box-decoration-break:clone;box-decoration-break:clone}
.sv-root[data-tone="butter"] .sv-hl{--hl:${T.white}}

/* Buttons: pill, uppercase Poppins, springy lift with a hard offset shadow */
.sv-btn{position:relative;display:inline-flex;align-items:center;justify-content:center;gap:10px;height:56px;padding:0 30px;border-radius:999px;font-family:var(--sans);font-weight:700;font-size:15px;line-height:1;letter-spacing:.09em;text-transform:uppercase;white-space:nowrap;cursor:pointer;border:1.5px solid var(--line);
  transition:translate .2s var(--pop),box-shadow .2s var(--pop),background-color .2s,color .2s}
.sv-btn-sm{height:44px;padding:0 22px;font-size:13px}
.sv-btn-primary{background:var(--btn-bg);color:var(--btn-fg);border-color:var(--btn-bg);box-shadow:0 0 0 0 var(--btn-sh)}
.sv-btn-primary:hover{translate:-3px -3px;box-shadow:4px 4px 0 0 var(--btn-sh)}
.sv-btn-secondary{background:var(--btn2-bg);color:var(--btn2-fg);box-shadow:2.25px 2.25px 0 0 var(--sh)}
.sv-btn-secondary:hover{translate:-2px -2px;box-shadow:5px 5px 0 0 var(--sh)}
.sv-btn:active{translate:0 0;box-shadow:0 0 0 0 var(--sh)}
.sv-btn svg{transition:translate .2s var(--pop)}
.sv-btn:hover svg{translate:3px 0}
.sv-link{display:inline-flex;align-items:center;gap:8px;font-weight:600;font-size:15px;color:var(--text);text-decoration:underline;text-decoration-thickness:1.5px;text-underline-offset:4px;transition:color .2s}
.sv-link:hover{color:var(--accent)}
.sv-link svg{transition:translate .2s var(--pop)}
.sv-link:hover svg{translate:3px 0}

/* Surfaces: white sticker cards with ink outline and hard shadow */
.sv-card{position:relative;border-radius:22px;background:var(--card);border:1px solid var(--line);box-shadow:4.5px 4.5px 0 0 var(--sh)}
.sv-card.sm{border-radius:14px;box-shadow:2.25px 2.25px 0 0 var(--sh)}
.sv-card.flat{box-shadow:none}
.sv-card.hover{transition:translate .2s var(--pop),box-shadow .2s var(--pop)}
.sv-card.hover:hover{translate:-3px -3px;box-shadow:7.5px 7.5px 0 0 var(--sh)}
.sv-chip{display:inline-flex;align-items:center;gap:7px;height:30px;padding:0 13px;border-radius:999px;font-family:var(--sans);font-weight:600;font-size:12.5px;line-height:1;white-space:nowrap;color:${T.ink};background:${T.cream};border:1px solid ${T.ink};box-shadow:1.2px 1.2px 0 0 ${T.ink}}
.sv-chip.good{background:${T.lime}}
.sv-chip.warn{background:#FFE1A6}
.sv-chip.bad{background:${T.blush}}
.sv-chip.white{background:${T.white}}
.sv-chip.ink{background:${T.ink};color:${T.white}}
.sv-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:currentColor;flex-shrink:0;border:1px solid ${T.ink}}
.sv-dot.live{position:relative}
.sv-dot.live::after{content:"";position:absolute;inset:-1px;border-radius:50%;background:inherit;animation:sv-ping 1.8s cubic-bezier(0,0,.2,1) infinite}
.sv-ico{display:inline-grid;place-items:center;width:52px;height:52px;border-radius:16px;border:1px solid ${T.ink};background:var(--tile,${T.cream});color:${T.ink};box-shadow:2.25px 2.25px 0 0 ${T.ink};flex-shrink:0}
.sv-plusfield{position:absolute;inset:0;pointer-events:none;opacity:1;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cpath d='M60 53v14M53 60h14' stroke='white' stroke-opacity='.7' stroke-width='1.6' stroke-linecap='round'/%3E%3C/svg%3E");background-size:120px 120px}
.sv-sr{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.sv-check{display:flex;gap:12px;align-items:flex-start;font-size:16.5px;line-height:1.45;color:var(--body)}
.sv-check>i{flex-shrink:0;display:grid;place-items:center;width:24px;height:24px;margin-top:0;border-radius:50%;border:1px solid ${T.ink};background:${T.butter};color:${T.ink}}
/* product UI fragments */
.sv-ui{font-family:var(--sans);font-size:12.5px;color:${T.ink}}
.sv-ui-h{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 16px;border-bottom:1px solid ${T.ink}}
.sv-ui-h b{font-family:var(--display);font-weight:600;font-size:13px}
.sv-row{display:grid;align-items:center;gap:10px;padding:0 16px;height:40px;border-top:1px solid rgba(0,0,0,.1)}
.sv-row:first-child{border-top:0}
.sv-th{color:${T.mute};font-size:10.5px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;height:32px}
.sv-demo{display:inline-flex;align-items:center;gap:6px;height:22px;padding:0 9px;border-radius:999px;border:1px dashed ${T.ink};background:${T.white};font-size:10.5px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:${T.ink}}

@keyframes sv-ping{0%{transform:scale(1);opacity:.6}80%,100%{transform:scale(2.8);opacity:0}}
@keyframes sv-marquee{from{transform:translate3d(0,0,0)}to{transform:translate3d(-50%,0,0)}}
@keyframes sv-float{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-10px) rotate(var(--fr,4deg))}}
@keyframes sv-spin{to{transform:rotate(360deg)}}
@keyframes sv-twinkle{0%,100%{transform:scale(1) rotate(0)}50%{transform:scale(.72) rotate(18deg)}}
@keyframes sv-flow{to{stroke-dashoffset:-28}}
@keyframes sv-wobble{0%,100%{transform:rotate(-2deg)}50%{transform:rotate(2deg)}}
.sv-bob{animation:sv-float var(--bd,7s) ease-in-out infinite var(--bdl,0s)}
.sv-spin{animation:sv-spin var(--sd,40s) linear infinite}
.sv-twinkle{animation:sv-twinkle var(--td,3.6s) ease-in-out infinite var(--tdl,0s);transform-box:fill-box;transform-origin:center}
.sv-flow{stroke-dasharray:5 9;animation:sv-flow 1.4s linear infinite}
@container (max-width:680px){.sv-dec{display:none}}
.sv-root[data-off] *,.sv-root[data-off] *::before,.sv-root[data-off] *::after{animation-play-state:paused!important}

:where(.sv-section[data-w="md"]){padding:104px 0}
:where(.sv-section[data-w="sm"]){padding:80px 0}
@container (max-width:1000px){.sv-wrap{padding:0 24px}}
@container (max-width:680px){.sv-wrap{padding:0 16px}.sv-body{font-size:16px}.sv-btn{height:52px;padding:0 24px;font-size:14px}}
@media (prefers-reduced-motion:reduce){
  .sv-root *,.sv-root *::before,.sv-root *::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}
}
`

/* ----------------------------------------------------------------------------
 * Hooks & helpers
 * --------------------------------------------------------------------------*/
/** True on the Framer canvas / static export or with reduced motion: render the final state. */
export function useStill() {
    const isStatic = (Framer as any).useIsStaticRenderer
        ? (Framer as any).useIsStaticRenderer()
        : false
    const reduced = useReducedMotion()
    return !!isStatic || !!reduced
}
export const useIsoLayoutEffect =
    typeof window !== "undefined" ? React.useLayoutEffect : React.useEffect

/** Headline syntax: *highlighted words* (butter marker) · _orange words_ · new line = line break. */
const SPLIT = /(\*[^*]+\*|_[^_]+_)/g
const kindOf = (p: string) =>
    p.length > 2 && p[0] === "*" && p.endsWith("*")
        ? "sv-hl"
        : p.length > 2 && p[0] === "_" && p.endsWith("_")
          ? "sv-acc"
          : ""
export function rich(text: string = "") {
    return String(text)
        .split("\n")
        .map((line, li) => (
            <React.Fragment key={li}>
                {li > 0 && <br />}
                {line.split(SPLIT).map((part, i) => {
                    const k = kindOf(part)
                    return k ? (
                        <span key={i} className={k}>
                            {part.slice(1, -1)}
                        </span>
                    ) : (
                        <React.Fragment key={i}>{part}</React.Fragment>
                    )
                })}
            </React.Fragment>
        ))
}
export const plain = (text: string = "") =>
    String(text).replace(/[*_]/g, "").replace(/\n/g, " ")
export const lines = (s: string = "") =>
    String(s)
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean)
export const cells = (s: string = "") =>
    String(s)
        .split("|")
        .map((x) => x.trim())

/* Page links inside Framer Preview: route "/page" links through Framer's router (published sites are untouched). */
const useFramerRouter: () => any = (Framer as any).useRouter || (() => null)
const normPath = (p: string) => p.replace(/\/$/, "") || "/"
export function usePreviewLinks() {
    const router = useFramerRouter()
    const ref = React.useRef(router)
    ref.current = router
    React.useEffect(() => {
        if (typeof document === "undefined") return
        const onClick = (e: MouseEvent) => {
            const r = ref.current
            if (
                !r ||
                !r.routes ||
                e.defaultPrevented ||
                e.button !== 0 ||
                e.metaKey ||
                e.ctrlKey ||
                e.shiftKey ||
                e.altKey
            )
                return
            const a = (e.target as HTMLElement)?.closest?.(
                "a"
            ) as HTMLAnchorElement | null
            if (!a || !a.closest(".sv-root") || a.target === "_blank") return
            const href = a.getAttribute("href") || ""
            if (!href.startsWith("/")) return
            const current = r.routes[r.currentRouteId]
            if (
                current &&
                current.path &&
                normPath(current.path) === normPath(window.location.pathname)
            )
                return
            const [rest, hash] = href.split("#")
            const path = normPath(rest.split("?")[0] || "/")
            const id = Object.keys(r.routes).find(
                (k) => r.routes[k].path && normPath(r.routes[k].path) === path
            )
            if (!id) return
            e.preventDefault()
            r.navigate(id, hash || undefined)
        }
        document.addEventListener("click", onClick)
        return () => document.removeEventListener("click", onClick)
    }, [])
}

/** Steps through 0..count-1 every `ms` while visible. Still = last step. */
export function useTicker(count: number, ms: number) {
    const still = useStill()
    const ref = React.useRef<HTMLDivElement>(null)
    const inView = useInView(ref, { margin: "0px 0px -10% 0px" })
    const [i, setI] = React.useState(0)
    React.useEffect(() => {
        if (still || !inView || count < 2) return
        const id = setInterval(() => setI((x) => (x + 1) % count), ms)
        return () => clearInterval(id)
    }, [still, inView, count, ms])
    return [ref, still ? count - 1 : i] as const
}

/* ----------------------------------------------------------------------------
 * Section shell
 * --------------------------------------------------------------------------*/
export function Section({
    tone = "white",
    id,
    label,
    css = "",
    className = "",
    style,
    children,
    as = "section",
    pad = true,
}: {
    tone?: Tone
    id?: string
    label?: string
    css?: string
    className?: string
    style?: React.CSSProperties
    children?: React.ReactNode
    as?: "section" | "header" | "footer" | "div" | "nav"
    pad?: boolean
}) {
    const Tag = as as any
    usePreviewLinks()
    const ref = React.useRef<HTMLElement>(null)
    const [w, setW] = React.useState<string | undefined>(undefined)
    const [off, setOff] = React.useState(false)
    React.useEffect(() => {
        const el = ref.current
        if (!el || typeof IntersectionObserver === "undefined") return
        const io = new IntersectionObserver(
            ([e]) => setOff(!e.isIntersecting),
            { rootMargin: "200px 0px" }
        )
        io.observe(el)
        return () => io.disconnect()
    }, [])
    useIsoLayoutEffect(() => {
        const el = ref.current
        if (!el) return
        const size = (x: number) => (x <= 680 ? "sm" : x <= 1000 ? "md" : "lg")
        setW(size(el.getBoundingClientRect().width))
        if (typeof ResizeObserver === "undefined") return
        const ro = new ResizeObserver(([e]) => setW(size(e.contentRect.width)))
        ro.observe(el)
        return () => ro.disconnect()
    }, [])
    return (
        <Tag
            ref={ref}
            data-w={w}
            data-off={off ? "" : undefined}
            data-tone={tone}
            className={`sv-root${pad ? " sv-section" : ""} ${className}`}
            id={id || undefined}
            aria-label={label || undefined}
            style={style}
        >
            <style dangerouslySetInnerHTML={{ __html: KIT_CSS + css }} />
            {children}
        </Tag>
    )
}

/* ----------------------------------------------------------------------------
 * Icons (24px grid, rounded strokes, Lucide, ISC license)
 * --------------------------------------------------------------------------*/
const P: Record<string, string> = {
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "arrow-up-right": '<path d="M7 7h10v10"/><path d="M7 17 17 7"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
    menu: '<path d="M4 8h16"/><path d="M4 16h16"/>',
    shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "shield-check":
        '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    radar: '<path d="M19.07 4.93A10 10 0 0 0 6.99 3.34"/><path d="M4 6h.01"/><path d="M2.29 9.62A10 10 0 1 0 21.31 8.35"/><path d="M16.24 7.76A6 6 0 1 0 8.23 16.67"/><path d="M12 18h.01"/><path d="M17.99 11.66A6 6 0 0 1 15.77 16.67"/><circle cx="12" cy="12" r="2"/><path d="m13.41 10.59 5.66-5.66"/>',
    gauge: '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    eye: '<path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/>',
    scale: '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    bot: '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>',
    cpu: '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
    database:
        '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>',
    plug: '<path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z"/>',
    server: '<rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/><path d="M6 6h.01"/><path d="M6 18h.01"/>',
    code: '<path d="m16 18 6-6-6-6"/><path d="m8 6-6 6 6 6"/>',
    building:
        '<rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    clipboard:
        '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
    layers: '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
    zap: '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',
    activity:
        '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>',
    sparkles:
        '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/>',
    route: '<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
    key: '<path d="m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"/><path d="m21 2-9.6 9.6"/><circle cx="7.5" cy="15.5" r="5.5"/>',
    file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    help: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    linkedin:
        '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"/><rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/>',
    x_social:
        '<path d="M4 4l11.73 16H20L8.27 4z"/><path d="M4 20l6.77-6.77"/><path d="M13.23 10.77 20 4"/>',
    github: '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>',
    youtube:
        '<path d="M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.56 49.56 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24.12 24.12 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.55 49.55 0 0 1-16.2 0A2 2 0 0 1 2.5 17"/><path d="m10 15 5-3-5-3z"/>',
}
export const ICON_NAMES = Object.keys(P).filter(
    (k) =>
        ![
            "linkedin",
            "x_social",
            "github",
            "youtube",
            "menu",
            "x",
            "chevron-down",
        ].includes(k)
)
export function Icon({
    name,
    size = 18,
    stroke = 1.75,
    className,
    style,
}: {
    name: string
    size?: number
    stroke?: number
    className?: string
    style?: React.CSSProperties
}) {
    return (
        <svg
            className={className}
            style={style}
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            focusable="false"
            dangerouslySetInnerHTML={{ __html: P[name] || P.sparkles }}
        />
    )
}

/* ----------------------------------------------------------------------------
 * Decorations (Pluto's hand-drawn space doodles). All aria-hidden.
 * --------------------------------------------------------------------------*/
/** Four-point sparkle star with an ink outline. */
export function Sparkle({
    size = 28,
    fill = T.pink,
    style,
    className = "",
    delay = 0,
    dur = 3.6,
}: {
    size?: number
    fill?: string
    style?: React.CSSProperties
    className?: string
    delay?: number
    dur?: number
}) {
    return (
        <svg
            className={className}
            width={size}
            height={size}
            viewBox="0 0 40 40"
            aria-hidden="true"
            focusable="false"
            style={{ position: "absolute", overflow: "visible", ...style }}
        >
            <path
                className="sv-twinkle"
                style={{
                    ["--tdl" as any]: `${delay}s`,
                    ["--td" as any]: `${dur}s`,
                }}
                d="M20 1c1.6 9.6 9.4 17.4 19 19-9.6 1.6-17.4 9.4-19 19-1.6-9.6-9.4-17.4-19-19C10.6 18.4 18.4 10.6 20 1Z"
                fill={fill}
                stroke={T.ink}
                strokeWidth="1.2"
                strokeLinejoin="round"
            />
        </svg>
    )
}
/** Ringed planet sticker with crater spots. */
export function Planet({
    size = 90,
    fill = T.lime,
    ring = true,
    style,
    className = "",
    spots = true,
}: {
    size?: number
    fill?: string
    ring?: boolean
    style?: React.CSSProperties
    className?: string
    spots?: boolean
}) {
    return (
        <svg
            className={className}
            width={size}
            height={size}
            viewBox="0 0 100 100"
            aria-hidden="true"
            focusable="false"
            style={{ position: "absolute", overflow: "visible", ...style }}
        >
            {ring && (
                <path
                    d="M8 62c-10 9-6 16 13 14 21-2 50-14 66-28 11-10 11-17-4-16"
                    fill="none"
                    stroke={T.ink}
                    strokeWidth="1.6"
                    strokeLinecap="round"
                />
            )}
            <circle
                cx="50"
                cy="50"
                r="34"
                fill={fill}
                stroke={T.ink}
                strokeWidth="1.6"
            />
            {spots && (
                <>
                    <ellipse
                        cx="38"
                        cy="38"
                        rx="7"
                        ry="5"
                        fill="none"
                        stroke={T.ink}
                        strokeWidth="1.2"
                    />
                    <ellipse
                        cx="62"
                        cy="58"
                        rx="5"
                        ry="3.5"
                        fill="none"
                        stroke={T.ink}
                        strokeWidth="1.2"
                    />
                    <path
                        d="M30 60c4 5 10 7 15 7"
                        fill="none"
                        stroke={T.ink}
                        strokeWidth="1.2"
                        strokeLinecap="round"
                    />
                </>
            )}
            {ring && (
                <path
                    d="M84 42c4 4 2 9-6 14-15 10-41 20-58 22"
                    fill="none"
                    stroke={T.ink}
                    strokeWidth="1.6"
                    strokeLinecap="round"
                />
            )}
        </svg>
    )
}
/** Thin elliptical orbit line. */
export function Orbit({
    w = 300,
    h = 120,
    style,
    dashed = false,
}: {
    w?: number
    h?: number
    style?: React.CSSProperties
    dashed?: boolean
}) {
    return (
        <svg
            width={w}
            height={h}
            viewBox={`0 0 ${w} ${h}`}
            aria-hidden="true"
            focusable="false"
            style={{ position: "absolute", overflow: "visible", ...style }}
        >
            <ellipse
                cx={w / 2}
                cy={h / 2}
                rx={w / 2 - 1}
                ry={h / 2 - 1}
                fill="none"
                stroke={T.ink}
                strokeWidth="1"
                strokeDasharray={dashed ? "3 6" : undefined}
            />
        </svg>
    )
}

/* ----------------------------------------------------------------------------
 * Brand
 * --------------------------------------------------------------------------*/
/** Secuvanta mark: a ringed shield planet. Uses ink outline + butter fill so it works on every tone. */
export function LogoMark({ size = 34 }: { size?: number }) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 40 40"
            aria-hidden="true"
            focusable="false"
            style={{ overflow: "visible" }}
        >
            <path
                d="M3 27c-4 4-1 7 7 5 9-2 19-8 25-15 4-5 3-7-2-6"
                fill="none"
                stroke={T.ink}
                strokeWidth="1.6"
                strokeLinecap="round"
            />
            <path
                d="M20 5a15 15 0 1 1 0 30 15 15 0 0 1 0-30Z"
                fill={T.butter}
                stroke={T.ink}
                strokeWidth="1.6"
                strokeLinejoin="round"
            />
            <path
                d="M15 24l10-10M21 14h4v4M15 20v4h4"
                fill="none"
                stroke={T.ink}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    )
}
export function Logo({
    name = "OAuth Navigator",
    href = "/",
    image,
    size = 34,
    pill = true,
}: {
    name?: string
    href?: string
    image?: { src?: string; alt?: string }
    size?: number
    pill?: boolean
}) {
    return (
        <a
            href={href}
            aria-label={`${name} home`}
            style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 10,
                color: "#000",
                height: size + 12,
                padding: pill ? "0 18px 0 8px" : 0,
                borderRadius: 999,
                border: pill ? "1.5px solid #000" : "none",
                background: pill ? T.butter : "transparent",
            }}
        >
            {image?.src ? (
                <img
                    src={image.src}
                    alt=""
                    style={{ height: size, width: "auto" }}
                />
            ) : (
                <LogoMark size={size} />
            )}
            {name && (
                <span
                    style={{
                        fontFamily: "var(--display)",
                        fontWeight: 700,
                        fontSize: Math.round(size * 0.5),
                        lineHeight: 1,
                        letterSpacing: ".04em",
                        textTransform: "uppercase",
                    }}
                >
                    {name}
                </span>
            )}
        </a>
    )
}

/* ----------------------------------------------------------------------------
 * Primitives
 * --------------------------------------------------------------------------*/
export type BtnVariant = "primary" | "secondary"
export function Btn({
    label,
    href,
    variant = "primary",
    size = "md",
    arrow,
    newTab,
}: {
    label?: string
    href?: string
    variant?: BtnVariant
    size?: "sm" | "md"
    arrow?: boolean
    newTab?: boolean
}) {
    if (!label) return null
    return (
        <a
            className={`sv-btn sv-btn-${variant}${size === "sm" ? " sv-btn-sm" : ""}`}
            href={href || "#"}
            target={newTab ? "_blank" : undefined}
            rel={newTab ? "noopener noreferrer" : undefined}
        >
            <span>{label}</span>
            {arrow && <Icon name="arrow-right" size={16} stroke={2.2} />}
        </a>
    )
}
export function TextLink({ label, href }: { label?: string; href?: string }) {
    if (!label) return null
    return (
        <a className="sv-link" href={href || "#"}>
            <span>{label.replace(/\s*[→>]\s*$/, "")}</span>
            <Icon name="arrow-right" size={16} stroke={2} />
        </a>
    )
}
export function Chip({
    children,
    tone = "",
    dot,
    live,
    color,
}: {
    children?: React.ReactNode
    tone?: "" | "good" | "warn" | "bad" | "white" | "ink"
    dot?: boolean
    live?: boolean
    color?: string
}) {
    return (
        <span className={`sv-chip ${tone}`}>
            {dot && (
                <i
                    className={`sv-dot${live ? " live" : ""}`}
                    style={{ color: color || T.verified }}
                />
            )}
            {children}
        </span>
    )
}
export function IconTile({
    name,
    tile = T.cream,
    size = 52,
    icon = 24,
}: {
    name: string
    tile?: string
    size?: number
    icon?: number
}) {
    return (
        <span
            className="sv-ico"
            style={{
                ["--tile" as any]: tile,
                width: size,
                height: size,
                borderRadius: Math.round(size * 0.3),
            }}
        >
            <Icon name={name} size={icon} />
        </span>
    )
}
/** Fictional-data marker used on every product mockup. */
export function DemoTag({ text = "Demo data" }: { text?: string }) {
    if (!text) return null
    return (
        <span className="sv-demo">
            <Icon name="sparkles" size={11} stroke={2} />
            {text}
        </span>
    )
}

/* ----------------------------------------------------------------------------
 * Motion primitives: all static on the canvas / reduced motion. `now` animates on mount (above the fold).
 * --------------------------------------------------------------------------*/
export function Reveal({
    children,
    delay = 0,
    y = 24,
    className,
    style,
    as = "div",
    now,
}: {
    now?: boolean
    children?: React.ReactNode
    delay?: number
    y?: number
    className?: string
    style?: React.CSSProperties
    as?: "div" | "li" | "span" | "p" | "article"
}) {
    const still = useStill()
    if (still) {
        const Tag = as as any
        return (
            <Tag className={className} style={style}>
                {children}
            </Tag>
        )
    }
    const M = (motion as any)[as]
    return (
        <M
            className={className}
            style={style}
            initial={{ opacity: 0, y }}
            {...(now
                ? { animate: { opacity: 1, y: 0 } }
                : { whileInView: { opacity: 1, y: 0 } })}
            viewport={{ once: true, margin: "0px 0px -8% 0px" }}
            transition={{ duration: 0.7, delay, ease: EASE }}
        >
            {children}
        </M>
    )
}
/** Sticker entrance: scales up from 0.6 with Pluto's springy overshoot and a little rotation. */
export function Pop({
    children,
    delay = 0,
    rotate = -6,
    className,
    style,
    now,
}: {
    now?: boolean
    children?: React.ReactNode
    delay?: number
    rotate?: number
    className?: string
    style?: React.CSSProperties
}) {
    const still = useStill()
    if (still)
        return (
            <div className={className} style={style}>
                {children}
            </div>
        )
    return (
        <motion.div
            className={className}
            style={style}
            initial={{ opacity: 0, scale: 0.6, rotate }}
            {...(now
                ? { animate: { opacity: 1, scale: 1, rotate: 0 } }
                : { whileInView: { opacity: 1, scale: 1, rotate: 0 } })}
            viewport={{ once: true, margin: "0px 0px -6% 0px" }}
            transition={{
                type: "spring",
                stiffness: 420,
                damping: 16,
                mass: 1,
                delay,
            }}
        >
            {children}
        </motion.div>
    )
}

/**
 * Headline. Above the fold (`now`) each line slides up from a mask (Pluto's text reveal); further down the page the
 * whole heading fades up when it scrolls into view (same trigger as Reveal, which is reliable everywhere).
 * Supports *highlight*, _orange_ and line breaks.
 */
export function Title({
    text,
    as = "h2",
    className = "sv-h2",
    delay = 0,
    style,
    now,
}: {
    now?: boolean
    text?: string
    as?: "h1" | "h2" | "h3" | "p"
    className?: string
    delay?: number
    style?: React.CSSProperties
}) {
    const still = useStill()
    const Tag = as as any
    if (!text) return null
    if (still)
        return (
            <Tag className={className} style={style}>
                {rich(text)}
            </Tag>
        )
    if (!now) {
        const M = (motion as any)[as]
        return (
            <M
                className={className}
                style={style}
                initial={{ opacity: 0, y: 28 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "0px 0px -8% 0px" }}
                transition={{ duration: 0.7, delay, ease: EASE }}
            >
                {rich(text)}
            </M>
        )
    }
    const parts = String(text).split("\n")
    return (
        <Tag className={className} style={style} aria-label={plain(text)}>
            {parts.map((line, li) => (
                <span
                    key={li}
                    aria-hidden="true"
                    style={{
                        display: "block",
                        overflow: "hidden",
                        paddingBottom: ".08em",
                        marginBottom: "-.08em",
                    }}
                >
                    <motion.span
                        style={{ display: "inline-block" }}
                        initial={{ y: "105%", opacity: 0 }}
                        animate={{ y: "0%", opacity: 1 }}
                        transition={{
                            y: {
                                duration: 0.6,
                                ease: [0.5, 0, 0, 1],
                                delay: delay + li * 0.09,
                            },
                            opacity: {
                                duration: 0.15,
                                delay: delay + li * 0.09,
                            },
                        }}
                    >
                        {rich(line)}
                    </motion.span>
                </span>
            ))}
        </Tag>
    )
}

/** Counts the number inside a string up when visible ("248", "92%", "36"). */
export function CountUp({
    value = "",
    duration = 1.4,
    className,
    style,
}: {
    value?: string
    duration?: number
    className?: string
    style?: React.CSSProperties
}) {
    const still = useStill()
    const ref = React.useRef<HTMLSpanElement>(null)
    const inView = useInView(ref, { once: true, margin: "0px 0px -10% 0px" })
    const m = String(value).match(/^(.*?)(\d[\d,]*\.?\d*)(.*)$/)
    const target = m ? parseFloat(m[2].replace(/,/g, "")) : 0
    const decimals = m && m[2].includes(".") ? m[2].split(".")[1].length : 0
    const comma = m ? m[2].includes(",") : false
    const [v, setV] = React.useState(still || !m ? target : 0)
    React.useEffect(() => {
        if (still || !m || !inView) return
        const c = animate(0, target, {
            duration,
            ease: [0.2, 0.8, 0.2, 1],
            onUpdate: setV,
        })
        return () => c.stop()
    }, [inView, still, target])
    if (!m)
        return (
            <span className={className} style={style}>
                {value}
            </span>
        )
    const num = comma
        ? v.toLocaleString("en-US", {
              minimumFractionDigits: decimals,
              maximumFractionDigits: decimals,
          })
        : v.toFixed(decimals)
    return (
        <span ref={ref} className={className} style={style} aria-label={value}>
            <span aria-hidden="true">
                {m[1]}
                {num}
                {m[3]}
            </span>
        </span>
    )
}

/** Infinite horizontal marquee (static when motion is reduced). */
export function Marquee({
    children,
    speed = 40,
}: {
    children?: React.ReactNode
    speed?: number
}) {
    const still = useStill()
    return (
        <div
            style={{
                overflow: "hidden",
                width: "100%",
                WebkitMaskImage:
                    "linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent)",
                maskImage:
                    "linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent)",
            }}
        >
            <div
                style={{
                    display: "flex",
                    width: "max-content",
                    animation: still
                        ? undefined
                        : `sv-marquee ${speed}s linear infinite`,
                }}
            >
                <div style={{ display: "flex", flexShrink: 0 }}>{children}</div>
                <div
                    style={{ display: "flex", flexShrink: 0 }}
                    aria-hidden="true"
                >
                    {children}
                </div>
            </div>
        </div>
    )
}

/** A dot travelling along an SVG path. Static on canvas / reduced motion. */
export function Packet({
    d,
    dur = 2.6,
    delay = 0,
    color = T.orange,
    r = 4.5,
}: {
    d: string
    dur?: number
    delay?: number
    color?: string
    r?: number
}) {
    const still = useStill()
    if (still) return null
    return (
        <circle r={r} fill={color} stroke={T.ink} strokeWidth="1" opacity="0">
            <animateMotion
                dur={`${dur}s`}
                begin={`${delay}s`}
                repeatCount="indefinite"
                path={d}
            />
            <animate
                attributeName="opacity"
                dur={`${dur}s`}
                begin={`${delay}s`}
                repeatCount="indefinite"
                values="0;1;1;0"
                keyTimes="0;.1;.85;1"
            />
        </circle>
    )
}

/**
 * Illustration stage: children are laid out on a fixed design canvas (w × h px) and the whole canvas scales down to
 * the available width, so every illustration keeps its composition from desktop to phone.
 */
export function Stage({
    w,
    h,
    children,
    className,
    style,
    max = 1,
}: {
    w: number
    h: number
    children?: React.ReactNode
    className?: string
    style?: React.CSSProperties
    max?: number
}) {
    const ref = React.useRef<HTMLDivElement>(null)
    const [s, setS] = React.useState(1)
    useIsoLayoutEffect(() => {
        const el = ref.current
        if (!el) return
        const fit = (x: number) => setS(Math.min(max, x / w))
        fit(el.getBoundingClientRect().width)
        if (typeof ResizeObserver === "undefined") return
        const ro = new ResizeObserver(([e]) => fit(e.contentRect.width))
        ro.observe(el)
        return () => ro.disconnect()
    }, [w, max])
    return (
        <div
            ref={ref}
            className={className}
            style={{
                position: "relative",
                width: "100%",
                height: h * s,
                ...style,
            }}
        >
            <div
                style={{
                    position: "absolute",
                    left: "50%",
                    top: 0,
                    width: w,
                    height: h,
                    transformOrigin: "50% 0",
                    transform: `translateX(-50%) scale(${s})`,
                }}
            >
                {children}
            </div>
        </div>
    )
}

/* ----------------------------------------------------------------------------
 * Section header
 * --------------------------------------------------------------------------*/
export function Head({
    eyebrow,
    title,
    body,
    align = "left",
    children,
    maxWidth = 900,
    titleClass = "sv-h2",
}: {
    eyebrow?: string
    title?: string
    body?: string
    align?: "left" | "center"
    children?: React.ReactNode
    maxWidth?: number
    titleClass?: string
}) {
    const c = align === "center"
    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                alignItems: c ? "center" : "flex-start",
                textAlign: c ? "center" : "left",
                gap: 22,
                maxWidth,
                margin: c ? "0 auto" : undefined,
            }}
        >
            {eyebrow && (
                <Reveal>
                    <p className="sv-eyebrow">{eyebrow}</p>
                </Reveal>
            )}
            <Title text={title} className={titleClass} />
            {body && (
                <Reveal delay={0.12}>
                    <p className="sv-lead" style={{ maxWidth: 720 }}>
                        {body}
                    </p>
                </Reveal>
            )}
            {children}
        </div>
    )
}

/** Shared header controls so every section edits the same way. */
export const headControls = (d: {
    eyebrow?: string
    title?: string
    body?: string
}) => ({
    eyebrow: {
        type: Framer.ControlType.String as Framer.ControlType.String,
        title: "Eyebrow",
        defaultValue: d.eyebrow || "",
    },
    title: {
        type: Framer.ControlType.String as Framer.ControlType.String,
        title: "Title",
        displayTextArea: true,
        defaultValue: d.title || "",
        description:
            "*stars* = yellow marker · _underscores_ = orange · new line = line break.",
    },
    body: {
        type: Framer.ControlType.String as Framer.ControlType.String,
        title: "Body",
        displayTextArea: true,
        defaultValue: d.body || "",
    },
})
export const toneControl = (d: Tone = "white") => ({
    type: Framer.ControlType.Enum as Framer.ControlType.Enum,
    title: "Tone",
    options: TONE_OPTIONS.options,
    optionTitles: TONE_OPTIONS.optionTitles,
    defaultValue: d,
})
export const idControl = (id: string) => ({
    type: Framer.ControlType.String as Framer.ControlType.String,
    title: "Section ID",
    defaultValue: id,
    description: "Anchor for #links",
})
export const linkControl = (title: string, d: string) => ({
    type: Framer.ControlType.Link as Framer.ControlType.Link,
    title,
    defaultValue: d,
})
export const decorControl = {
    type: Framer.ControlType.Boolean as Framer.ControlType.Boolean,
    title: "Doodles",
    defaultValue: true,
    enabledTitle: "Show",
    disabledTitle: "Hide",
    description: "Sparkles, planets and orbit doodles.",
}

export default function Kit() {
    return null
}

// OAuth Navigator uses the preserved shared visual system.
