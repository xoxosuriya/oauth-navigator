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
            <Footer
                brand="OAUTH NAVIGATOR"
                tagline="OAuth Ready. Agent Connected."
                description="OAuth readiness and integration intelligence for AI-agent developers."
                col1Title="PLATFORM"
                col1Links={`Platform overview | /platform\nApplication workspace | /workspace`}
                col2Title="LEARN"
                col2Links={`Documentation | /resources\nAbout OAuth Navigator | /about\nSolutions | /solutions\nContact | /contact`}
                socials={`linkedin | https://www.linkedin.com/in/suriya-prakash-28a5273ba
instagram | https://www.instagram.com/xoxo.suriya/
github | https://github.com/xoxosuriya
portfolio | https://xoxosuriya.github.io/suriya_portfolio/
gmail | https://mail.google.com/mail/?view=cm&fs=1&to=sp2742006@gmail.com`}
                copyright="© 2026 OAuth Navigator."
                variant="full"
            />
        </div>
    )
}

