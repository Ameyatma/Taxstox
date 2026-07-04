"use client";

import { useEffect } from "react";

/**
 * Google OAuth callback page.
 *
 * Google redirects here after the user consents in the popup.
 * The ID token is in the URL fragment (hash), which the parent
 * window reads directly from popup.location.hash.
 *
 * This page just shows a spinner and closes itself — the real
 * work is done by the parent window's polling loop.
 */
export default function GoogleCallbackPage() {
  useEffect(() => {
    // Signal to the parent window that we're on the callback URL.
    // The parent's polling loop will detect this and extract the token.
    // If opened directly (not in a popup), redirect to auth page.
    if (!window.opener || window.opener === window) {
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
