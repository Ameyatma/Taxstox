import { NextRequest, NextResponse } from "next/server";

/**
 * API route to handle Google OAuth callback.
 * Acts as a transparent proxy: forwards query params to backend,
 * captures Set-Cookie and Location headers, and redirects client accordingly.
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;

    // Backend base URL (ensure no trailing slash)
    let baseUrl = process.env.NEXT_PUBLIC_API_URL || "https://taxstox-api-435349196142.asia-south1.run.app/api/v1";
    if (baseUrl.endsWith("/")) {
      baseUrl = baseUrl.slice(0, -1);
    }

    // Forward query params (code, state, etc.) to FastAPI backend
    const targetUrl = `${baseUrl}/api/v1/auth/google/callback?${searchParams.toString()}`;

    // Fetch from backend with redirect: 'manual' so we can catch cookies and redirect instructions
    const backendRes = await fetch(targetUrl, {
      method: 'GET',
      redirect: 'manual',
      headers: {
        'Accept': 'application/json',
      },
    });

    const setCookie = backendRes.headers.get('set-cookie');
    const location = backendRes.headers.get('location') || '/dashboard';

    // Create the redirect response to the frontend dashboard
    const response = NextResponse.redirect(new URL(location, request.url), 303);

    // Explicitly pass the session cookie to the client browser
    if (setCookie) {
      response.headers.set('set-cookie', setCookie);
    }

    return response;
  } catch (error) {
    console.error('OAuth callback proxy error:', error);
    return NextResponse.redirect(new URL('/auth?error=OAuthProxyFailed', request.url));
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