// Framer API Compatibility Layer for standalone React execution
export { motion, AnimatePresence } from "framer-motion"

export const addPropertyControls = (component: any, controls: Record<string, any>) => {
    if (!component || !controls) return
    const defaults: Record<string, any> = {}
    for (const [key, val] of Object.entries(controls)) {
        if (val && typeof val === "object" && "defaultValue" in val) {
            defaults[key] = (val as any).defaultValue
        }
    }
    // Set defaultProps on component
    component.defaultProps = { ...defaults, ...(component.defaultProps || {}) }
}

export enum ControlType {
    Number = "number",
    Boolean = "boolean",
    String = "string",
    Enum = "enum",
    SegmentedEnum = "segmentedEnum",
    FusedNumber = "fusedNumber",
    Transition = "transition",
    Color = "color",
    ComponentInstance = "componentInstance",
    Array = "array",
    Object = "object",
    File = "file",
    Image = "image",
    Link = "link",
    ResponsiveImage = "responsiveImage",
}

export const RenderTarget = {
    current: () => ({ kind: "preview" }),
    canvas: "canvas",
}

export const useIsStaticRenderer = () => false

export const useRouter = () => ({
    navigate: (url: string) => {
        window.location.href = url
    },
    pathname: typeof window !== "undefined" ? window.location.pathname : "/",
})

// Namespace export for components using Framer.ControlType
import * as FramerShim from "./framer-shim"
export { FramerShim as Framer }
