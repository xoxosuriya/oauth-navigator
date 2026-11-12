import React, { useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import Navbar from "../components/Navbar.tsx"
import OAuthWorkspace from "../components/OAuth_Navigator/OAuthWorkspace.tsx"
import Footer from "../components/Footer.tsx"

export default function GuidePage() {
    const { guideId } = useParams<{ guideId: string }>()
    const navigate = useNavigate()

    useEffect(() => {
        if (guideId && !window.location.search.includes("share=")) {
            // Keep workspace query params synchronized
            navigate(`/workspace?share=${encodeURIComponent(guideId)}`, { replace: true })
        }
    }, [guideId, navigate])

    return (
        <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "#FDF2D4" }}>
            <Navbar />
            <div style={{ flex: 1, padding: "32px 24px 64px", maxWidth: 1280, margin: "0 auto", width: "100%", boxSizing: "border-box" }}>
                <OAuthWorkspace embedded={false} mode="investigate" />
            </div>
            <Footer />
        </div>
    )
}

