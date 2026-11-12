import React from "react"
import Navbar from "../components/Navbar.tsx"
import PageHero from "../components/PageHero.tsx"
import Split from "../components/Split.tsx"
import CardGrid from "../components/CardGrid.tsx"
import FinalCTA from "../components/FinalCTA.tsx"
import Footer from "../components/Footer.tsx"

export default function AboutPage() {
    return (
        <main className="about-page" style={{ width: "100%", overflowX: "hidden" }}>
            <Navbar
                brand="OAUTH NAVIGATOR"
                links={`Platform | /platform
Documentation | /resources`}
                softLabel="Catalogue"
                softLink="/workspace?view=catalog"
                ctaLabel="INVESTIGATE AN APP"
                ctaLink="/workspace"
            />

            <PageHero
                tone="peach"
                eyebrow="ABOUT OAUTH NAVIGATOR"
                title={"Integration starts with\n*understanding.*"}
                body="OAuth Navigator helps AI-agent developers understand authentication requirements without disguising uncertainty."
                primaryLabel="OPEN THE WORKSPACE"
                primaryLink="/workspace"
                secondaryLabel="Contact"
                secondaryLink="/contact"
                decor={true}
                sectionId="top"
            />

            <Split
                tone="cream"
                eyebrow="OAUTH DISCOVERY"
                title={"Start with the application’s\n*authentication pathway.*"}
                body="Identify OAuth support and available authentication methods. Unknown applications and undocumented capabilities remain unverified."
                points="OAuth support · Authentication methods · Source confidence"
                ctaLabel="INVESTIGATE AN APP"
                ctaLink="/workspace"
                flip={false}
                sectionId="discovery"
            />

            <CardGrid
                tone="white"
                eyebrow="PRINCIPLES"
                title="Clarity at every decision point."
                body="We believe integration intelligence must be rooted in truth, transparency, and explicit boundaries."
                items={`Evidence first | Every claim links directly to official provider documentation citations. | shield-check | /workspace
Unknown means unknown | Unverified fields remain explicitly null, not assumed false. | alert-circle | /workspace
Human-led setup | Clearly separates developer portal tasks from automated agent tasks. | code | /workspace
Managed or custom | Distinguishes Composio managed OAuth from custom developer credentials. | plug | /workspace`}
                sectionId="principles"
            />

            <Split
                tone="white"
                eyebrow="PROVIDER REQUIREMENTS"
                title={"Know what you need\n*before you connect.*"}
                body="Understand account registration, credentials, scopes and redirect URI constraints from detailed provider research."
                points="Developer portal · Client credentials · Redirect rules"
                ctaLabel="INVESTIGATE AN APP"
                ctaLink="/workspace"
                flip={true}
                sectionId="provider-requirements"
            />

            <FinalCTA
                tone="charcoal"
                title={"Make every integration a\nmore *informed one.*"}
                body="Start with the authentication requirements. Build with confidence."
                primaryLabel="INVESTIGATE YOUR FIRST APP"
                primaryLink="/workspace"
                secondaryLabel="Contact"
                secondaryLink="/contact"
                nodes={`Application | cpu
OAuth Provider | key
Composio | plug
AI Agent | bot
Developer Config | code
Authorization | route`}
                showNetwork={true}
                sectionId="cta"
            />

            <Footer
                brand="OAUTH NAVIGATOR"
                tagline="OAuth Ready. Agent Connected."
                description="OAuth readiness and integration intelligence for AI-agent developers."
                col1Title="PLATFORM"
                col1Links={`Platform overview | /platform
Application workspace | /workspace`}
                col2Title="LEARN"
                col2Links={`Documentation | /resources
About OAuth Navigator | /about
Solutions | /solutions
Contact | /contact`}
                socials={`linkedin | https://www.linkedin.com/
instagram | https://www.instagram.com/
github | https://github.com/`}
                copyright="© 2026 OAuth Navigator."
                variant="full"
            />
        </main>
    )
}
