import * as React from "react"
import {
    Section,
    Stage,
    IconTile,
    Sparkle,
    Planet,
    Packet,
    Pop,
    T,
} from "../Kit.tsx"
export function OAuthDiagram({
    dark = false,
    compact = false,
}: {
    dark?: boolean
    compact?: boolean
}) {
    const ink = dark ? T.cream : T.ink
    const labels = [
        ["OAuth Provider", "key", 110, 85],
        ["Composio", "plug", 530, 85],
        ["Developer Config", "code", 110, 300],
        ["AI Agent", "bot", 530, 300],
    ]
    return (
        <Stage w={640} h={compact ? 370 : 420}>
            <svg
                width="640"
                height="400"
                viewBox="0 0 640 400"
                style={{ position: "absolute", inset: 0 }}
                aria-hidden="true"
            >
                <ellipse
                    cx="320"
                    cy="198"
                    rx="240"
                    ry="140"
                    fill="none"
                    stroke={ink}
                    strokeDasharray="3 8"
                />
                {labels.map(([label, ic, x, y], i) => {
                    const d =
                        "M320 195 Q" +
                        (i % 2 ? 470 : 170) +
                        " 190 " +
                        x +
                        " " +
                        y
                    return (
                        <React.Fragment key={String(label)}>
                            <path
                                d={d}
                                fill="none"
                                stroke={ink}
                                strokeWidth="1.5"
                                strokeDasharray="4 7"
                            />
                            <Packet d={d} delay={i * 0.5} color={T.orange} />
                        </React.Fragment>
                    )
                })}
            </svg>
            <div
                style={{
                    position: "absolute",
                    left: 245,
                    top: 120,
                    width: 150,
                    height: 150,
                    borderRadius: "50%",
                    background: T.butter,
                    border: "1.5px solid black",
                    boxShadow: "5px 5px 0 " + (dark ? T.orange : T.ink),
                    display: "grid",
                    placeContent: "center",
                    justifyItems: "center",
                    gap: 12,
                    color: T.ink,
                }}
            >
                <IconTile name="layers" tile={T.cream} />
                <b style={{ fontFamily: "var(--display)", fontSize: 12 }}>
                    APPLICATION
                </b>
            </div>
            {labels.map(([label, ic, x, y], i) => (
                <div
                    key={String(label)}
                    style={{
                        position: "absolute",
                        left: Number(x),
                        top: Number(y),
                        transform: "translate(-50%,-50%)",
                    }}
                >
                    <Pop delay={i * 0.08}>
                        <div
                            className="sv-bob"
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 10,
                                border: "1.5px solid black",
                                borderRadius: 999,
                                padding: "6px 16px 6px 6px",
                                background: T.white,
                                boxShadow:
                                    "3px 3px 0 " + (dark ? T.orange : T.ink),
                                color: T.ink,
                                fontWeight: 600,
                                fontSize: 13,
                                whiteSpace: "nowrap",
                            }}
                        >
                            <IconTile
                                name={String(ic)}
                                size={36}
                                icon={18}
                                tile={i % 2 ? T.peach : T.cream}
                            />
                            {label}
                        </div>
                    </Pop>
                </div>
            ))}
            <Sparkle size={25} style={{ left: 300, top: 15 }} fill={T.peach} />
            <Planet size={55} style={{ left: 550, top: 175 }} fill={T.butter} />
            <span
                style={{
                    position: "absolute",
                    left: 245,
                    top: 325,
                    fontSize: 12,
                    color: ink,
                    border: "1px dashed " + ink,
                    borderRadius: 999,
                    padding: "6px 16px",
                }}
            >
                Authorization pathways
            </span>
        </Stage>
    )
}
interface Props {
    kind?: string
    style?: React.CSSProperties
}
export default function OAuthVisual({ style }: Props) {
    return (
        <Section pad={false} style={style}>
            <OAuthDiagram />
        </Section>
    )
}

// Verified module path

// OAuth Navigator integration

// Final module verification.
