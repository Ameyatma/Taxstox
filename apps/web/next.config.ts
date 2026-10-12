import type { NextConfig } from "next";

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
        destination: process.env.NEXT_PUBLIC_API_URL
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`
          : 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  }
};

export default nextConfig;
