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

  const [error, setError] = useState("");
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

  const inputWrapper = "flex items-center gap-3 px-4 py-3 bg-[#F8FAFC] rounded-lg border border-[#c3c6d4] transition-all focus-within:border-[#003366] focus-within:ring-1 focus-within:ring-[#003366]";
  const inputClass = "flex-1 bg-transparent border-none outline-none text-sm text-[#0b1c30] placeholder:text-[#434652]";
  const labelClass = "text-[11px] font-bold uppercase tracking-wider text-[#434652]";

  // Get today's max DOB (must be at least 18 years old)
  const today = new Date();
  const maxDate = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());
  const maxDateStr = maxDate.toISOString().split("T")[0];

  return (
    <div className="min-h-[calc(100vh-64px)] bg-[#F8FAFC] flex">
      {/* ── Left Panel: Form ─────────────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center pt-10 pb-16 px-6">
        <div className="w-full max-w-[440px] space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

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
            <div className="bg-white border border-[#E2E8F0] rounded-xl p-5">
              <button
                onClick={handleGoogleSignIn}
                disabled={googleLoading}
                className="w-flex items-center justify-center gap-3 py-3 px-5 bg-white border border-[#c3c6d4] rounded-lg hover:bg-[#F8FAFC] hover:border-[#003366] transition-all text-sm font-medium text-[#0b1c30] disabled:opacity-50"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                {googleLoading ? (
                  <span className="animate-spin w-4 h-4 border-2 border-[#003366]/30 border-t-[#003366] rounded-full" />
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                    </svg>
                    Sign in with Google
                  </>
                )}
              </button>
            </div>
          )}

          {/* ── Form Fields ──────────────────────────────────────── */}
          {activeTab === "signup" ? (
            <>
              <div className="space-y-3">
                <label className={labelClass}>PAN</label>
                <div className={inputWrapper}>
                  <input
                    type="text"
                    value={pan}
                    onChange={(e) => setPan(e.target.value)}
                    className={inputClass}
                    placeholder="ABCDE1234F"
                    maxLength={10}
                  />
                </div>
                {panTooLong && (
                  <p className="text-xs text-red-500">PAN too long</p>
                )}
                {!panValid && pan && (
                  <p className="text-xs text-red-500">Invalid PAN format</p>
                )}
              </div>

              <div className="space-y-3">
                <label className={labelClass}>Date of Birth</label>
                <div className={inputWrapper}>
                  <input
                    type="date"
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
                    className={inputClass}
                    max={maxDateStr}
                  />
                </div>
              </div>

              <div className="space-y-3">
                <label className={labelClass}>Name</label>
                <div className={inputWrapper}>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className={inputClass}
                    placeholder="Full Name"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <label className={labelClass}>Email</label>
                <div className={inputWrapper}>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={inputClass}
                    placeholder="you@example.com"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <label className={labelClass}>Password</label>
                <div className={inputWrapper}>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className={inputClass}
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-0 top-0 h-full w-10 flex items-center justify-center text-xs text-[#434652] hover:text-[#003366]"
                    >
                      {showPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="space-y-3">
                <label className={labelClass}>Email</label>
                <div className={inputWrapper}>
                  <input
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className={inputClass}
                    placeholder="you@example.com"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <label className={labelClass}>Password</label>
                <div className={inputWrapper}>
                  <div className="relative">
                    <input
                      type={showLoginPassword ? "text" : "password"}
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      className={inputClass}
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowLoginPassword(!showLoginPassword)}
                      className="absolute right-0 top-0 h-full w-10 flex items-center justify-center text-xs text-[#434652] hover:text-[#003366]"
                    >
                      {showLoginPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* ── Submit Button ─────────────────────────────────────── */}
          <div className="mt-6">
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
            <div className="mt-6 flex items-center gap-4">
              <div className="h-0.5 w-full bg-[#E2E8F0]" />
              <span className="text-xs text-[#434652]">Or continue with</span>
              <div className="h-0.5 w-full bg-[#E2E8F0]" />
            </div>
          )}

          {/* ── Error Message ─────────────────────────────────────── */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700">
              {error}
            </div>
          )}
        </div>
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
