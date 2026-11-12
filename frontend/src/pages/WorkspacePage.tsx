import React from "react"
import Navbar from "../components/Navbar.tsx"
import OAuthWorkspace from "../components/OAuth_Navigator/OAuthWorkspace.tsx"
import Footer from "../components/Footer.tsx"
import { useSearchParams } from "react-router-dom"

export default function WorkspacePage() {
    const [searchParams] = useSearchParams()
    const view = (searchParams.get("view") || "investigate") as "investigate" | "catalog" | "docs"

    return (
        <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "#FDF2D4" }}>
            <Navbar
                brand="OAUTH NAVIGATOR"
                showAnnouncement={false}
                links={`Platform | /platform
Documentation | /resources`}
                softLabel="Catalogue"
                softLink="/workspace?view=catalog"
                ctaLabel="INVESTIGATE AN APP"
                ctaLink="/workspace"
            />
            <div style={{ flex: 1, padding: "32px 24px 64px", maxWidth: 1280, margin: "0 auto", width: "100%", boxSizing: "border-box" }}>
                <OAuthWorkspace embedded={false} mode={view} />
            </div>
            <Footer
                brand="OAUTH NAVIGATOR"
                tagline="OAuth Ready. Agent Connected."
                description="OAuth readiness and integration intelligence for AI-agent developers."
                col1Title="PLATFORM"
                col1Links={`Platform overview | /platform\nApplication workspace | /workspace`}
                col2Title="LEARN"
                col2Links={`Documentation | /resources\nAbout OAuth Navigator | /about\nSolutions | /solutions\nContact | /contact`}
                copyright="© 2026 OAuth Navigator."
                socials={`linkedin | https://www.linkedin.com/\ninstagram | https://www.instagram.com/\ngithub | https://github.com/`}
            />
        </div>
    )
}
