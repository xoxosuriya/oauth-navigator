import React from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import LandingPage from "./pages/LandingPage.tsx"
import PlatformPage from "./pages/PlatformPage.tsx"
import SolutionsPage from "./pages/SolutionsPage.tsx"
import ResourcesPage from "./pages/ResourcesPage.tsx"
import AboutPage from "./pages/AboutPage.tsx"
import ContactPage from "./pages/ContactPage.tsx"
import WorkspacePage from "./pages/WorkspacePage.tsx"
import GuidePage from "./pages/GuidePage.tsx"
import NotFoundPage from "./pages/NotFoundPage.tsx"

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/platform" element={<PlatformPage />} />
                <Route path="/solutions" element={<SolutionsPage />} />
                <Route path="/resources" element={<ResourcesPage />} />
                <Route path="/about" element={<AboutPage />} />
                <Route path="/contact" element={<ContactPage />} />
                <Route path="/workspace" element={<WorkspacePage />} />
                <Route path="/guide/:guideId" element={<GuidePage />} />
                <Route path="/404" element={<NotFoundPage />} />
                <Route path="*" element={<NotFoundPage />} />
            </Routes>
        </BrowserRouter>
    )
}
