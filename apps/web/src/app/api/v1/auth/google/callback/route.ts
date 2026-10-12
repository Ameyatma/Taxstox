import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

/**
 * API route to handle Google OAuth callback with native cookie issuance.
 *
 * Phase 13A.12: Fixed cross-site OAuth cookie rejection by using
 * sameSite: 'none' and secure: true for cookies issued during the
 * cross-site OAuth redirect from Google to taxstox.com.
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const code = searchParams.get("code");

    if (!code) {
      return NextResponse.redirect(new URL('/auth?error=MissingCode', request.url));
    }

    // Backend base URL (ensure no trailing slash)
    let baseUrl = process.env.NEXT_PUBLIC_API_URL || "https://taxstox-api-435349196142.asia-south1.run.app/api/v1";
    if (baseUrl.endsWith("/")) {
      baseUrl = baseUrl.slice(0, -1);
    }

    // 1. Exchange code with FastAPI backend server-side to get token JSON
    const backendRes = await fetch(`${baseUrl}/api/v1/auth/google/callback?code=${code}&format=json`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!backendRes.ok) {
      throw new Error('Backend token exchange failed');
    }

    const data = await backendRes.json();
    const accessToken = data.access_token;
    const refreshToken = data.refresh_token;

    if (!accessToken) {
      throw new Error('No access token returned from backend');
    }

    // 2. Natively set the cookies on taxstox.com using Next.js cookies API
    const cookieStore = await cookies();

    // Set access/session token (1 week expiry)
    cookieStore.set({
      name: 'session_token', // matches backend TOKEN_COOKIE_NAME
      value: accessToken,
      httpOnly: true,
      secure: true, // Required when sameSite is 'none'
      sameSite: 'none', // Allows cross-site redirect acceptance from Google
      path: '/',
      maxAge: 60 * 60 * 24 * 7, // 1 week
    });

    // Set refresh token if available (7 days expiry to match backend)
    if (refreshToken) {
      cookieStore.set({
        name: 'taxstox_refresh_token', // matches backend REFRESH_TOKEN_COOKIE_NAME
        value: refreshToken,
        httpOnly: true,
        secure: true,
        sameSite: 'none',
        path: '/',
        maxAge: 60 * 60 * 24 * 7, // 7 days
      });
    }

    // 3. Redirect user to dashboard with cookies securely attached
    return NextResponse.redirect(new URL('/dashboard', request.url), 303);
  } catch (error) {
    console.error('OAuth native callback error:', error);
    return NextResponse.redirect(new URL('/auth?error=OAuthFailed', request.url));
  }
}

// Handle OPTIONS requests for CORS preflight
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    },
  });
}