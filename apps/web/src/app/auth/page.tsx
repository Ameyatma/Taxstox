"use client";

import { useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth, AuthProvider } from "@/lib/auth";
import { getApiBase } from "@/lib/api";

const PAN_REGEX = /^[A-Z]{5}[0-9]{4}[A-Z]$/;

function AuthContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/dashboard";

  const { signIn, signUp, signInWithToken } = useAuth();

  const [activeTab, setActiveTab] = useState<"signup" | "signin">("signup");

  // Sign Up
  const [pan, setPan] = useState("");
  const [dob, setDob] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Sign In
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  const [error, setError] = useState(() => {
    // Surface OAuth failures forwarded by the callback route
    // (e.g. /auth?error=OAuthFailed).
    const oauthError = searchParams.get("error");
    if (!oauthError) return "";
    const messages: Record<string, string> = {
      OAuthFailed: "Google sign-in failed. Please try again.",
      MissingOAuthCode: "Google sign-in was cancelled or returned no code. Please try again.",
      OAuthProxyException: "Google sign-in failed. Please try again.",
    };
    return messages[oauthError] || `Google sign-in failed (${oauthError}).`;
  });
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const panValid = PAN_REGEX.test(pan.toUpperCase());
  const panTooLong = pan.length >= 10 && !panValid;

  const handleSignUp = async () => {
    setError("");
    if (!pan || !dob || !name || !email || !password) { setError("All fields are required."); return; }
    if (!panValid) { setError("Enter a valid PAN (format: ABCDE1234F)."); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }

    setLoading(true);
    try {
      await signUp(email, password, pan, name, dob);
      router.push(redirect);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign up failed.");
      setLoading(false);
    }
  };

  const handleSignIn = async () => {
    setError("");
    if (!loginEmail || !loginPassword) { setError("Email and password are required."); return; }
    setLoading(true);
    try {
      await signIn(loginEmail, loginPassword);
      router.push(redirect);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed.");
      setLoading(false);
    }
  };

  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

  const handleGoogleSignIn = useCallback(async () => {
    setGoogleLoading(true);
    setError("");
    try {
      if (!googleClientId) {
        setError("Google Sign-In is not configured yet. Please use email to create an account.");
        setGoogleLoading(false);
        return;
      }
      // Server-side Google OAuth redirect flow (PRRP-DEFER-001)
      const base = getApiBase();
      const res = await fetch(`${base}/auth/google/login`, {
        method: "GET",
        credentials: "include",
      });
      if (!res.ok) {
        throw new Error("Failed to initiate Google sign-in.");
      }
      const data = await res.json();
      // Redirect to Google's OAuth page
      window.location.href = data.redirect_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load Google Sign-In.");
      setGoogleLoading(false);
    }
  }, [googleClientId]);

  // Get today's max DOB (must be at least 18 years old)
  const today = new Date();
  const maxDate = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());
  const maxDateStr = maxDate.toISOString().split("T")[0];

  return (
    <div className="min-h-[calc(100vh-64px)] bg-[#F8FAFC] flex">
      {/* ── Left Panel: Form ─────────────────────────────────────── */}
      <div className="max-w-md w-full mx-auto bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
        {/* Tab Switcher */}
        <div className="flex border-b border-[#E2E8F0] bg-white rounded-t-xl">
          <button
            onClick={() => { setActiveTab("signup"); setError(""); }}
            className={`flex-1 py-4 text-center text-base font-semibold transition-colors ${
              activeTab === "signup"
                ? "border-b-2 border-[#003366] text-[#003366]"
                : "text-[#434652] hover:text-[#003366]"
            }`}
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            Create Account
          </button>
          <button
            onClick={() => { setActiveTab("signin"); setError(""); }}
            className={`flex-1 py-4 text-center text-base font-semibold transition-colors ${
              activeTab === "signin"
                ? "border-b-2 border-[#003366] text-[#003366]"
                : "text-[#434652] hover:text-[#003366]"
            }`}
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            Sign In
          </button>
        </div>

        {/* ── Google Sign-In Button (only shown when configured) ─ */}
        {googleClientId && (
          <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 mb-6">
            <button
              onClick={handleGoogleSignIn}
              disabled={googleLoading}
              className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
              </svg>
              Sign in with Google
            </button>
          </div>
        )}

        {/* ── Form Fields ──────────────────────────────────────── */}
        {activeTab === "signup" ? (
          <>
            <div className="flex flex-col space-y-1.5 mb-4">
              <label className="text-xs font-bold tracking-wider text-gray-600 uppercase">PAN</label>
              <input
                type="text"
                value={pan}
                onChange={(e) => setPan(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 text-gray-900 focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition-all text-sm"
                placeholder="ABCDE1234F"
                maxLength={10}
              />
              {panTooLong && (
                <p className="text-xs text-red-500">PAN too long</p>
              )}
              {!panValid && pan && (
                <p className="text-xs text-red-500">Invalid PAN format</p>
              )}
            </div>

            <div className="flex flex-col space-y-1.5 mb-4">
              <label className="text-xs font-bold tracking-wider text-gray-600 uppercase">Date of Birth</label>
              <input
                type="date"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 text-gray-900 focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition-all text-sm"
                max={maxDateStr}
              />
            </div>

            <div className="flex flex-col space-y-1.5 mb-4">
              <label className="text-xs font-bold tracking-wider text-gray-600 uppercase">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 text-gray-900 focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition-all text-sm"
                placeholder="Full Name"
              />
            </div>

            <div className="flex flex-col space-y-1.5 mb-4">
              <label className="text-xs font-bold tracking-wider text-gray-600 uppercase">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 text-gray-900 focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition-all text-sm"
                placeholder="you@example.com"
              />
            </div>

            <div className="flex flex-col space-y-1.5 mb-4">
              <label className="text-xs font-bold tracking-wider text-gray-600 uppercase">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 text-gray-900 focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition-all text-sm"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-0 top-0 h-full w-10 flex items-center justify-center text-xs text-gray-500 hover:text-gray-700"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="flex flex-col space-y-1.5 mb-4">
              <label className="text-xs font-bold tracking-wider text-gray-600 uppercase">Email</label>
              <input
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 text-gray-900 focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition-all text-sm"
                placeholder="you@example.com"
              />
            </div>

            <div className="flex flex-col space-y-1.5 mb-4">
              <label className="text-xs font-bold tracking-wider text-gray-600 uppercase">Password</label>
              <div className="relative">
                <input
                  type={showLoginPassword ? "text" : "password"}
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 text-gray-900 focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none transition-all text-sm"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowLoginPassword(!showLoginPassword)}
                  className="absolute right-0 top-0 h-full w-10 flex items-center justify-center text-xs text-gray-500 hover:text-gray-700"
                >
                  {showLoginPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>
          </>
        )}

        {/* ── Submit Button ─────────────────────────────────────── */}
        <div className="mb-4">
          {activeTab === "signup" ? (
            <button
              onClick={handleSignUp}
              disabled={loading}
              className="w-full bg-[#003366] hover:bg-[#004d80] text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50"
            >
              Create Account
            </button>
          ) : (
            <button
              onClick={handleSignIn}
              disabled={loading}
              className="w-full bg-[#003366] hover:bg-[#004d80] text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50"
            >
              Sign In
            </button>
          )}
        </div>

        {/* ── Divider ─────────────────────────────────────────── */}
        {activeTab === "signup" && (
          <div className="mt-4 flex items-center gap-4">
            <div className="h-0.5 w-full bg-gray-200" />
            <span className="text-xs text-gray-500">Or continue with</span>
            <div className="h-0.5 w-full bg-gray-200" />
          </div>
        )}

        {/* ── Error Message ─────────────────────────────────────── */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-lg">
            {error}
          </div>
        )}
      </div>

      {/* ── Right Panel: Illustration ─────────────────────────────── */}
      <div className="hidden w-[280px] md:block">
        <div className="relative h-[240px] w-full">
          <div className="absolute inset-0">
            <div className="relative h-full w-full">
              <img
                src="/assets/illustrations/auth-right.png"
                alt="Auth illustration"
                className="object-contain w-full h-full"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AuthPage() {
  return (
    <AuthProvider>
      <Suspense fallback={<div>Loading...</div>}>
        <AuthContent />
      </Suspense>
    </AuthProvider>
  );
}
