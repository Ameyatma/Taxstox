"use client";

import { useEffect } from "react";

/**
 * Google OAuth callback page.
 *
 * Google redirects here after the user consents in the popup.
 * The ID token is in the URL fragment (#id_token=...).
 *
 * This page extracts the token and sends it back to the parent window
 * via postMessage, then closes itself.
 */
export default function GoogleCallbackPage() {
  useEffect(() => {
    // Extract id_token from URL hash
    const hash = window.location.hash;
    const hasToken = hash.includes("id_token=");

    if (window.opener && window.opener !== window) {
      // We're in a popup — send token back to parent
      if (hasToken) {
        const idToken = new URLSearchParams(hash.substring(1)).get("id_token");
        if (idToken) {
          window.opener.postMessage(
            { type: "google-signin-success", idToken },
            window.location.origin
          );
        } else {
          window.opener.postMessage(
            { type: "google-signin-error", error: "No id_token in redirect" },
            window.location.origin
          );
        }
      } else if (hash.includes("error=")) {
        const error = new URLSearchParams(hash.substring(1)).get("error") || "Google auth failed";
        window.opener.postMessage(
          { type: "google-signin-error", error },
          window.location.origin
        );
      } else {
        window.opener.postMessage(
          { type: "google-signin-error", error: "No token or error in redirect URL" },
          window.location.origin
        );
      }
      // Close the popup after a short delay
      setTimeout(() => window.close(), 500);
    } else {
      // Opened directly (not a popup) — redirect to auth page
      window.location.href = "/auth";
    }
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
      <div className="text-center space-y-4">
        <div className="animate-spin w-8 h-8 border-2 border-[#003366]/30 border-t-[#003366] rounded-full mx-auto" />
        <p className="text-[#434652] text-sm" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
          Completing sign-in...
        </p>
      </div>
    </div>
  );
}
