import type { NextConfig } from "next";

// Resolve the backend origin (scheme + host) once. We tolerate an env value that
// is either the bare origin or already carries a trailing `/api/v1` segment, so
// the same-origin proxy rewrite below can safely append `/api/:path*`.
const backendOrigin = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000")
  .trim()
  .replace(/\/+$/, "")
  .replace(/\/api\/v1$/, "");

const nextConfig: NextConfig = {
  /* config options here */
  async rewrites() {
    return [
      {
        // Exclude Google OAuth callback from rewrite so it goes to our API route
        source: '/api/v1/auth/google/callback',
        destination: '/api/v1/auth/google/callback', // Handle via Next.js API route
      },
      {
        source: '/api/:path*',
        destination: `${backendOrigin}/api/:path*`,
      },
    ];
  }
};

export default nextConfig;
