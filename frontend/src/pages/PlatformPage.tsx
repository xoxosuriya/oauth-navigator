import React from "react"
import Navbar from "../components/Navbar.tsx"
import PageHero from "../components/PageHero.tsx"
import Split from "../components/Split.tsx"
import FinalCTA from "../components/FinalCTA.tsx"
import Footer from "../components/Footer.tsx"

export default function PlatformPage() {
    return (
        <main className="platform-page" style={{ width: "100%", overflowX: "hidden" }}>
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
                eyebrow="THE PLATFORM"
                title={"Know the requirements.\n*Navigate the integration.*"}
                body="Discover, assess, connect and verify with OAuth intelligence backed by evidence."
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

            <Split
                tone="butter"
                eyebrow="COMPOSIO INTELLIGENCE"
                title={"Managed or custom.\n*Understand the difference.*"}
                body="Check Composio toolkit metadata and distinguish a managed OAuth pathway from mandatory custom authentication."
                points="Managed availability · Supported schemes · Classification"
                ctaLabel="INVESTIGATE AN APP"
                ctaLink="/workspace"
                flip={false}
                sectionId="composio-intelligence"
            />

            <Split
                tone="peach"
                eyebrow="EVIDENCE & VERIFICATION"
                title={"Documented findings.\n*Explicit uncertainty.*"}
                body="Inspect official sources, excerpts and confidence. A missing field is not treated as a negative finding."
                points="Evidence excerpts · Field provenance · Partial research"
                ctaLabel="INVESTIGATE AN APP"
                ctaLink="/workspace"
                flip={true}
                sectionId="evidence-verification"
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
                sectionId="human-agent"
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
                socials={`linkedin | https://www.linkedin.com/in/suriya-prakash-28a5273ba
instagram | https://www.instagram.com/xoxo.suriya/
github | https://github.com/xoxosuriya
portfolio | https://xoxosuriya.github.io/suriya_portfolio/
gmail | https://mail.google.com/mail/?view=cm&fs=1&to=sp2742006@gmail.com`}
                copyright="© 2026 OAuth Navigator."
                variant="full"
            />
        </main>
    )
}
