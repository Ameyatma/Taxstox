import { NextResponse } from "next/server";
import type { NextRequest } from "next/request";

/**
 * Set httpOnly auth cookies on the frontend origin.
 * Called by the Google OAuth handoff page after receiving tokens in query string.
 */
export async function POST(request: NextRequest) {
  try {
    const { access_token, refresh_token, redirect } = await request.json();

    const redirectUrl = redirect ?? "/dashboard";

    const response = NextResponse.redirect(new URL(redirectUrl, request.url));
    
    // Set access token cookie (httpOnly, secure in production)
    response.cookies.set({
      name: "taxstox_token",
      value: access_token,
      httpOnly: true,
      secure: process.env.NODE_ENV === "production", // HTTPS in production
      sameSite: "strict", // Strict for same-site requests (frontend to its own API)
      path: "/",
      maxAge: 60 * 60 * 24, // 24 hours
    });

    // Set refresh token cookie
    response.cookies.set({
      name: "taxstox_refresh_token",
      value: refresh_token,
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });

    return response;
  } catch (error) {
    console.error("Failed to set auth cookies:", error);
    return new NextResponse(
      JSON.stringify({ error: "Failed to set authentication cookies" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
