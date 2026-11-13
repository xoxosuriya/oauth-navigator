import React from "react"
import Navbar from "../components/Navbar.tsx"
import Hero from "../components/Hero.tsx"
import TrustStrip from "../components/TrustStrip.tsx"
import Problem from "../components/Problem.tsx"
import PlatformLayers from "../components/PlatformLayers.tsx"
import ProductPreview from "../components/ProductPreview.tsx"
import Benefits from "../components/Benefits.tsx"
import FinalCTA from "../components/FinalCTA.tsx"
import Footer from "../components/Footer.tsx"

export default function LandingPage() {
    return (
        <main className="landing-page" style={{ width: "100%", overflowX: "hidden" }}>
            <Navbar
                brand="OAUTH NAVIGATOR"
                showAnnouncement={true}
                announcement="New: Live OAuth intelligence for AI agents. Read here."
                announcementLinkLabel="Read here"
                announcementLink="/resources"
                links={`Platform | /platform
Documentation | /resources`}
                softLabel="Catalogue"
                softLink="/workspace?view=catalog"
                ctaLabel="INVESTIGATE AN APP"
                ctaLink="/workspace"
            />

            <Hero
                tone="peach"
                title={"OAuth Ready.\n*Agent Connected.*"}
                body="Understand authentication requirements, discover Composio-managed pathways and prepare applications for AI-agent integration — without the guesswork."
                primaryLabel="INVESTIGATE AN APP"
                primaryLink="/workspace"
                secondaryLabel="EXPLORE THE PLATFORM"
                secondaryLink="/platform"
                coreLabel="APPLICATION"
                nodes={`OAuth Provider | key | ok
Composio | plug | ok
Authorization | route | ok
Developer Config | code | ok
AI Agent | bot | ok`}
                showRisk={false}
                showPanel={true}
                panelTitle="Integration intelligence"
                panelRows={`OAuth support | Unverified | info
Managed pathway | Unverified | info
Evidence | Not loaded | info`}
                demoLabel="LIVE DATA AFTER INVESTIGATION"
                decor={true}
                sectionId="top"
            />

            <TrustStrip
                title="From unknown requirements to a clearer integration path"
                items={`OAuth Discovery | key
Composio Intelligence | plug
Provider Requirements | code
Evidence & Verification | shield-check`}
                sectionId="teams"
            />

            <Problem
                tone="cream"
                eyebrow="THE PROBLEM"
                title={"AI agents are moving faster than\n*OAuth integrations.*"}
                body="Every application has different authentication requirements. Developers need to understand provider configuration, permissions, verification and the work required before an agent can connect."
                points={`Undocumented OAuth schemes stall agent setups. | eye
Custom versus managed requirements stay unclear. | plug
Scattered provider documentation slows review. | scale`}
                ctaLabel="INVESTIGATE REQUIREMENTS"
                ctaLink="/workspace"
                hub="OAUTH REQUIREMENTS"
                callouts={`Unknown scheme | Scheme not documented
Custom OAuth | Manual provider registration
Review requirements | Provider verification pending`}
                sectionId="problem"
            />

            <PlatformLayers
                tone="butter"
                eyebrow="PLATFORM OVERVIEW"
                title={"One platform.\nFour layers of *OAuth intelligence.*"}
                body="From discovery to ongoing protection, OAuth Navigator provides the visibility and controls teams need to adopt agent integrations safely."
                cards={`01 Discover | Identify OAuth support and available authentication methods. | search
02 Assess | Understand provider registration, credentials, redirect rules and scopes. | gauge
03 Connect | Discover Composio-managed OAuth and custom authentication requirements. | plug
04 Verify | Review evidence, confidence, human responsibilities and potential blockers. | shield-check`}
                showPreviews={false}
                ctaLabel="EXPLORE THE WORKSPACE"
                ctaLink="/workspace"
                sectionId="platform"
            />

            <ProductPreview
                tone="peach"
                eyebrow="PRODUCT PREVIEW"
                title={"Your investigation.\n*Every requirement in view.*"}
                body="Explore OAuth readiness, Composio pathways, technical requirements and the evidence behind them — together in one workspace."
                url="workspace.oauth-navigator.example"
                demoLabel="Illustrative interface with fictional demo data"
                note="Illustrative interface with fictional demo data"
                decor={true}
                sectionId="preview"
            />

            <Benefits
                tone="white"
                eyebrow="BENEFITS"
                title={"OAuth integration without\nthe uncertainty."}
                body="Connecting agents shouldn't require trial and error. OAuth Navigator gives developers an evidence-backed roadmap."
                cards={`Greater Clarity | Know what an application requires before integration. | Requirements, made readable | eye
Faster Decisions | Discover managed and custom OAuth pathways. | Choose an informed pathway | zap
Evidence-backed Guidance | Understand which requirements are actually documented. | Sources behind the findings | shield-check
Clear Responsibilities | Know what developers must do and what agents can automate. | Human and agent boundaries | bot`}
                sectionId="benefits"
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
