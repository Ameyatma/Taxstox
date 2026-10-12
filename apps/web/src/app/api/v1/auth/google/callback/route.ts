import { NextRequest, NextResponse } from "next/server";

/**
 * API route to handle Google OAuth callback.
 * This proxies the request to the backend to avoid any issues with Next.js rewrites.
 */
export async function GET(request: NextRequest) {
  try {
    // Get the base URL for the backend API
    let baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    
    // Remove trailing slash if present to avoid double slashes
    if (baseUrl.endsWith("/")) {
      baseUrl = baseUrl.slice(0, -1);
    }
    
    // Get the original URL from the request to preserve query parameters
    const url = new URL(request.url);
    
    // Construct the backend URL
    // We want to go to: {baseUrl}/auth/google/callback{pathAfterCallback}{search}
    // Where pathAfterCallback is everything after "/api/v1/auth/google/callback" in the original path
    const pathAfterCallback = url.pathname.replace(/^\/api\/v1\/auth\/google\/callback/, "");
    const backendUrl = `${baseUrl}/auth/google/callback${pathAfterCallback}${url.search}`;
    
    // Forward the request to the backend
    const backendResponse = await fetch(backendUrl, {
      method: request.method,
      headers: request.headers,
    });

    // Create a new headers object and strip problematic headers
    const responseHeaders = new Headers(backendResponse.headers);
    responseHeaders.delete('content-encoding');
    responseHeaders.delete('content-length');
    responseHeaders.delete('transfer-encoding');

    // Create a new response to send back to the client
    const response = new NextResponse(backendResponse.body, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: responseHeaders,
    });

    return response;
  } catch (error) {
    console.error("Error proxying Google OAuth callback:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
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
