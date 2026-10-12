import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * Google OAuth callback — server-side orchestrator (Phase 13B).
 *
 * Replaces the previous "transparent proxy" (which attempted to forward a
 * cross-domain `Set-Cookie` from Cloud Run > Vercel — a flow browsers strip)
 * with native cookie issuance on the frontend origin.
 *
 * Flow:
 *   1. Google redirects the browser here with `?code=...`.
 *   2. We exchange that code with FastAPI *server-to-server* and receive the
 *      TaxStox session tokens as JSON. No cookie ever crosses a domain boundary.
 *   3. We mint the httpOnly session cookies natively on the frontend domain
 *      (taxstox.com) so the browser accepts them unconditionally.
 *   4. We redirect the now-authenticated browser straight to /dashboard.
 */

const TOKEN_COOKIE_NAME = "taxstox_token";
const REFRESH_TOKEN_COOKIE_NAME = "taxstox_refresh_token";

const ACCESS_TOKEN_MAX_AGE = 60 * 60 * 24 * 7; // 1 week
const REFRESH_TOKEN_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

/**
 * Resolve the backend *origin* (scheme + host), tolerating an env value that
 * either is the bare origin or already carries a trailing `/api/v1` segment.
 */
function getBackendOrigin(): string {
  const raw =
    process.env.NEXT_PUBLIC_API_URL ||
    "https://taxstox-api-435349196142.asia-south1.run.app";
  return raw.trim().replace(/\/+$/, "").replace(/\/api\/v1$/, "");
}

/** Only allow same-site, path-relative redirect targets (prevents open redirects). */
function safeRedirect(target: string | null): string {
  if (target && target.startsWith("/") && !target.startsWith("//")) {
    return target;
  }
  return "/dashboard";
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get("code");
  const redirectTo = safeRedirect(searchParams.get("redirect"));

  if (!code) {
    return NextResponse.redirect(
      new URL("/auth?error=MissingOAuthCode", request.url)
    );
  }

  try {
    // 1. Server-to-server code exchange with FastAPI → tokens as JSON.
    const exchangeUrl = new URL(
      `${getBackendOrigin()}/api/v1/auth/google/callback`
    );
    exchangeUrl.searchParams.set("code", code);
    exchangeUrl.searchParams.set("format", "json");

    const backendRes = await fetch(exchangeUrl, {
      method: "GET",
      headers: { Accept: "application/json" },
      redirect: "follow",
      cache: "no-store",
    });

    if (!backendRes.ok) {
      throw new Error(
        `Backend token exchange failed with status ${backendRes.status}`
      );
    }

    const data = await backendRes.json();
    const token = data.access_token || data.token || data.session_token;
    const refreshToken = data.refresh_token || data.taxstox_refresh_token;

    if (!token) {
      throw new Error("No authentication token found in backend response");
    }

    // 2. Natively mint the session cookies on the frontend origin.
    //    Next.js merges these onto the redirect response (see app-route
    //    `finalizeResponse` → `appendMutableCookies`).
    const cookieStore = await cookies();

    cookieStore.set({
      name: TOKEN_COOKIE_NAME,
      value: token,
      httpOnly: true,
      secure: true,
      sameSite: "none",
      path: "/",
      maxAge: ACCESS_TOKEN_MAX_AGE,
    });

    if (refreshToken) {
      cookieStore.set({
        name: REFRESH_TOKEN_COOKIE_NAME,
        value: refreshToken,
        httpOnly: true,
        secure: true,
        sameSite: "none",
        path: "/",
        maxAge: REFRESH_TOKEN_MAX_AGE,
      });
    }

    // 3. Redirect the authenticated browser to the dashboard.
    return NextResponse.redirect(new URL(redirectTo, request.url), 303);
  } catch (error) {
    console.error("Google OAuth callback failed:", error);
    return NextResponse.redirect(new URL("/auth?error=OAuthFailed", request.url));
  }
}