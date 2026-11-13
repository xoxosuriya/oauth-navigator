import React from "react"
import Navbar from "../components/Navbar.tsx"
import NotFound from "../components/NotFound.tsx"
import Footer from "../components/Footer.tsx"

export default function NotFoundPage() {
    return (
        <main className="notfound-page" style={{ width: "100%", overflowX: "hidden" }}>
            <Navbar
                brand="OAUTH NAVIGATOR"
                links={`Platform | /platform
Documentation | /resources`}
                softLabel="Catalogue"
                softLink="/workspace?view=catalog"
                ctaLabel="INVESTIGATE AN APP"
                ctaLink="/workspace"
            />

            <NotFound
                tone="peach"
                eyebrow="ERROR 404"
                title={"This signal went\n*missing.*"}
                body="The page you’re looking for may have moved. Return to OAuth Navigator to investigate an application."
                primaryLabel="BACK TO HOME"
                primaryLink="/"
                secondaryLabel="EXPLORE PLATFORM"
                secondaryLink="/platform"
                linksLabel="OR TRY"
                links={`Platform | /platform
Workspace | /workspace
Documentation | /resources`}
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
