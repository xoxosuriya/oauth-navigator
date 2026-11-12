import React from "react"
import Navbar from "../components/Navbar.tsx"
import PageHero from "../components/PageHero.tsx"
import Split from "../components/Split.tsx"
import CardGrid from "../components/CardGrid.tsx"
import OAuthWorkspace from "../components/OAuth_Navigator/OAuthWorkspace.tsx"
import Footer from "../components/Footer.tsx"
import { T } from "../components/Kit.tsx"

export default function ResourcesPage() {
    return (
        <main className="resources-page" style={{ width: "100%", overflowX: "hidden" }}>
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
                eyebrow="DOCUMENTATION"
                title={"From first investigation\nto *informed integration.*"}
                body="Learn how the workspace handles evidence, unknown requirements and managed versus custom pathways."
                primaryLabel="OPEN THE WORKSPACE"
                primaryLink="/workspace"
                decor={true}
                sectionId="top"
            />

            <Split
                tone="cream"
                eyebrow="HUMAN & AGENT BOUNDARIES"
                title={"A clearer handoff between\n*people and agents.*"}
                body="See which setup tasks require a developer and which can be automated by an agent, based on the returned guide."
                points="Human actions · Agent automation · Setup steps"
                ctaLabel="INVESTIGATE AN APP"
                ctaLink="/workspace"
                flip={false}
                sectionId="boundaries"
            />

            <CardGrid
                tone="white"
                eyebrow="TOPICS"
                title="Clarity at every decision point."
                body="Four fundamental tenets ensure your AI integrations remain reliable, secure and verifiable."
                items={`Evidence first | Every claim links directly to official provider documentation citations. | shield-check | /workspace
Unknown means unknown | Unverified fields remain explicitly null, not assumed false. | alert-circle | /workspace
Human-led setup | Clearly separates developer portal tasks from automated agent tasks. | code | /workspace
Managed or custom | Distinguishes Composio managed OAuth from custom developer credentials. | plug | /workspace`}
                sectionId="topics"
            />

            <div style={{ padding: "80px 24px", background: T.cream, borderTop: "1.5px solid black" }}>
                <div style={{ maxWidth: 1200, margin: "0 auto" }}>
                    <OAuthWorkspace embedded />
                </div>
            </div>

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
