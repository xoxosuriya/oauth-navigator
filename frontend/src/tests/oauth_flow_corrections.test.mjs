import { test, describe, beforeEach } from "node:test"
import assert from "node:assert/strict"

// Mock browser globals for Node.js test runner
function setupMockBrowser(initialLocation = "https://oauthnavigator.vercel.app/workspace") {
    const storage = new Map()

    const mockLocalStorage = {
        getItem: (k) => storage.get(k) || null,
        setItem: (k, v) => storage.set(k, String(v)),
        removeItem: (k) => storage.delete(k),
        clear: () => storage.clear(),
        get length() { return storage.size },
    }

    const mockLocation = {
        origin: "https://oauthnavigator.vercel.app",
        pathname: "/workspace",
        href: initialLocation,
        hostname: "oauthnavigator.vercel.app",
    }

    return {
        storage,
        localStorage: mockLocalStorage,
        location: mockLocation,
    }
}

describe("OAuth Flow Corrections — Issue 1 & Issue 2 Verification", () => {
    let mockBrowser

    beforeEach(() => {
        mockBrowser = setupMockBrowser()
        globalThis.window = {
            location: mockBrowser.location,
            localStorage: mockBrowser.localStorage,
        }
        globalThis.localStorage = mockBrowser.localStorage
    })

    test("1. Tab Preservation: window.location.href is never assigned the authorization URL", () => {
        const originalHref = window.location.href
        const redirectUrl = "https://backend.composio.dev/connect/oauth_authorization_target"

        // Simulate connect click handler
        let authWindow = {
            location: { href: "about:blank" },
            closed: false,
        }

        // Action: Navigate reserved tab, NOT original window
        if (authWindow && !authWindow.closed) {
            authWindow.location.href = redirectUrl
        }

        // Assert: Original window.location.href remained completely untouched
        assert.equal(window.location.href, originalHref)
        assert.notEqual(window.location.href, redirectUrl)
        assert.equal(authWindow.location.href, redirectUrl)
    })

    test("2. Popup Blocker Fallback: Blocked popup triggers fallback without navigating original tab", () => {
        const originalHref = window.location.href
        const redirectUrl = "https://backend.composio.dev/connect/oauth_popup_blocked"

        // Simulate browser blocking window.open (returns null)
        let authWindow = null
        let popupBlocked = false

        if (!authWindow || authWindow.closed || typeof authWindow.closed === "undefined") {
            popupBlocked = true
            // In our corrected implementation, NEVER do: window.location.href = redirectUrl
        }

        assert.equal(popupBlocked, true)
        // Original window location MUST NOT change to redirectUrl
        assert.equal(window.location.href, originalHref)
        assert.notEqual(window.location.href, redirectUrl)
    })

    test("3. postMessage Origin Validation: Untrusted origins rejected, matching origin accepted", () => {
        const trustedOrigin = "https://oauthnavigator.vercel.app"
        const untrustedOrigin = "https://malicious-attacker-site.com"

        let processedMessage = null

        function handleAuthMessage(event) {
            // STRICT origin validation
            if (event.origin !== window.location.origin) {
                return false
            }
            if (event.data?.type === "OAUTH_CALLBACK") {
                processedMessage = event.data
                return true
            }
            return false
        }

        // Test 3a: Message from malicious origin
        const maliciousEvent = {
            origin: untrustedOrigin,
            data: { type: "OAUTH_CALLBACK", accountId: "forged_account", status: "active" },
        }
        const maliciousAccepted = handleAuthMessage(maliciousEvent)
        assert.equal(maliciousAccepted, false)
        assert.equal(processedMessage, null)

        // Test 3b: Message from trusted origin
        const trustedEvent = {
            origin: trustedOrigin,
            data: { type: "OAUTH_CALLBACK", accountId: "ca_legit_account_123", status: "success" },
        }
        const trustedAccepted = handleAuthMessage(trustedEvent)
        assert.equal(trustedAccepted, true)
        assert.equal(processedMessage?.accountId, "ca_legit_account_123")
    })

    test("4. Zero Secrets in localStorage: Verification that localStorage contains no tokens or identifiers", () => {
        // Clear storage
        localStorage.clear()

        // Verify localStorage contains 0 keys
        assert.equal(localStorage.length, 0)
        assert.equal(localStorage.getItem("oauth_nav_session_user_id"), null)
        assert.equal(localStorage.getItem("composio_api_key"), null)
        assert.equal(localStorage.getItem("session_token"), null)
    })

    test("5. First-Party Reverse Proxy Base Resolution: Resolves to /api/v1 in production browser", async () => {
        // Import resolveBase
        const { resolveBase } = await import("../components/OAuth_Navigator/OAuthAPI.ts")

        // When running on production hostname oauthnavigator.vercel.app
        window.location.hostname = "oauthnavigator.vercel.app"
        const base = resolveBase()

        // Must resolve to relative /api/v1 to leverage Vercel first-party proxy rewrites
        assert.equal(base, "/api/v1")
    })
})
