"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Google OAuth callback page.
 *
 * Handles two flows:
 * 1. Popup-based flow: Google redirects here with ID token in URL fragment (#id_token=...)
 *    - Extracts token and sends via postMessage to opener window
 * 2. Server-side flow: Backend redirects here with access_token and refresh_token in query string
 *    - Stores tokens in localStorage and redirects to dashboard
 */
export default function GoogleCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    // Check for server-side flow tokens in query string
    const searchParams = new URLSearchParams(window.location.search);
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");
    const redirect = searchParams.get("redirect") || "/dashboard";

    if (accessToken && refreshToken) {
      // Server-side flow: store tokens and redirect
      localStorage.setItem("taxstox_access_token", accessToken);
      localStorage.setItem("taxstox_refresh_token", refreshToken);
      // In a real app, we would set httpOnly cookies via an API endpoint
      // For now, we rely on localStorage and Authorization header
      router.push(redirect);
      return;
    }

    // Popup-based flow: handle ID token in URL fragment
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
          { type: "google-signin-error", error: "No id_token in redirect" },
          window.location.origin
        );
      } else {
        window.opener.postMessage(
          { type: "google-signin-error", error: "No token or error in redirect" },
          window.location.origin
        );
      }
      // Close the popup after a short delay
      setTimeout(() => window.close(), 500);
    } else {
      // Opened directly (not a popup) — redirect to auth page
      router.push("/auth");
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
