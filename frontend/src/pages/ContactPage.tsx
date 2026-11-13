import React from "react"
import Navbar from "../components/Navbar.tsx"
import PageHero from "../components/PageHero.tsx"
import Steps from "../components/Steps.tsx"
import { Section, Head, Btn, T } from "../components/Kit.tsx"
import Footer from "../components/Footer.tsx"

export default function ContactPage() {
    return (
        <main className="contact-page" style={{ width: "100%", overflowX: "hidden" }}>
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
                eyebrow="GET STARTED"
                title={"Your next integration.\n*Start with the requirements.*"}
                body="Open the workspace to investigate an application using the real backend."
                primaryLabel="OPEN THE WORKSPACE"
                primaryLink="/workspace"
                decor={true}
                sectionId="top"
            />

            <Steps
                tone="cream"
                eyebrow="WHAT HAPPENS NEXT"
                title={"From application name to\n*integration intelligence.*"}
                body="A structured sequence that transforms an unknown application into an evidence-backed integration guide."
                steps={`Step 1: Investigate | Enter an application name. | Start with a question
Step 2: Assess | Review provider and Composio requirements. | Keep unknowns explicit
Step 3: Research | Load detailed technical findings. | Inspect the evidence
Step 4: Prepare | Follow documented setup steps. | Human and agent handoffs
Step 5: Share | Generate a saved guide permalink. | Real backend guide`}
                sectionId="steps"
            />

            <Section tone="white" style={{ padding: "80px 24px", borderTop: "1.5px solid black" }}>
                <div style={{ maxWidth: 840, margin: "0 auto", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
                    <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: "0.08em", color: T.ink, border: "1.5px solid black", background: T.butter, padding: "4px 14px", borderRadius: 999 }}>
                        LOCAL API READY
                    </span>
                    <h2 style={{ fontFamily: "var(--display, Unbounded, sans-serif)", fontSize: "clamp(24px, 3.5vw, 40px)", margin: 0, color: T.ink }}>
                        Direct workspace access.<br />
                        <span style={{ background: T.butter, padding: "0 8px", borderRadius: 8 }}>Zero credential storage.</span>
                    </h2>
                    <p style={{ maxWidth: 640, fontSize: 16, lineHeight: 1.6, color: T.body, margin: 0 }}>
                        The frontend connects directly to your local FastAPI backend service at <code>http://127.0.0.1:8000/api/v1</code>. No client secrets or tokens are ever stored or transmitted to external servers.
                    </p>
                    <div style={{ marginTop: 12 }}>
                        <Btn label="GO TO WORKSPACE" href="/workspace" arrow />
                    </div>
                </div>
            </Section>

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
