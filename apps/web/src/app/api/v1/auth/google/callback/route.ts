import { NextRequest, NextResponse } from "next/server";

/**
 * API route to handle Google OAuth callback as a transparent proxy.
 *
 * Phase 13A.14: Refactored to act as a transparent proxy that forwards
 * query parameters to FastAPI, captures Set-Cookie and Location headers,
 * and passes them securely to the browser.
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "https://taxstox-api-435349196142.asia-south1.run.app/api/v1";

  // Forward all query params (code, state, etc.) to FastAPI backend
  const targetUrl = `${backendUrl}/api/v1/auth/google/callback?${searchParams.toString()}`;

  try {
    // Fetch from backend with redirect: 'manual' to intercept cookies and redirect instructions
    const backendRes = await fetch(targetUrl, {
      method: 'GET',
      redirect: 'manual',
      headers: {
        'Accept': 'application/json, text/plain, */*',
      },
    });

    const setCookie = backendRes.headers.get('set-cookie');
    const location = backendRes.headers.get('location') || '/dashboard';

    // Create a redirect response to the frontend dashboard
    const redirectUrl = location.startsWith('http') ? location : new URL(location, backendUrl).toString();
    const response = NextResponse.redirect(redirectUrl, 303);

    // Forward the backend cookies directly to the client browser
    if (setCookie) {
      response.headers.set('set-cookie', setCookie);
    }

    return response;
  } catch (error) {
    console.error('OAuth callback proxy exception:', error);
    return NextResponse.redirect(new URL('/auth?error=OAuthProxyException', request.url));
  }
}

// Handle OPTIONS requests for CORS preflight
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  });
}