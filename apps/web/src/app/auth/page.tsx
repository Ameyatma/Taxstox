"use client";

import { useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { getApiBase } from "@/lib/api";

const PAN_REGEX = /^[A-Z]{5}[0-9]{4}[A-Z]$/;

function AuthContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/dashboard";

  const { signIn, signUp, signInWithToken } = useAuth();

  const [activeTab, setActiveTab] = setActiveTab || useState<"signup" | "signin">("signup");

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
      const result = await signUp(email, password, pan, name, dob);
      // Store the access token for API calls
      if (result.accessToken) {
        localStorage.setItem("taxstox_access_token", result.accessToken);
      }
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
      const result = await signIn(loginEmail, loginPassword);
      // Store the access token for API calls
      if (result.accessToken) {
        localStorage.setItem("taxstox_access_token", result.accessToken);
      }
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
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="mr-2">
                      <circle cx="12" cy="12" r="10" />
                      <path d="M12 12a2 2 0 0 1 1.416-.584l2.75-2.75a5 5 0 0 1 7.07 2.93" />
                      <path d="M6.343 18.343a9 9 0 0 1 12.728-2.343" />
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
                <label className={labelCell}>PAN</label>
                <input
                  type="text"
                  value={pan}
                  onChange={(e) => setPan(e.target.value)}
                  className={inputClass}
                  placeholder="ABCDE1234F"
                  maxLength="10"
                />
                {panTooLong && (
                  <p className="text-xs text-red-500">PAN too long</p>
                )}
                {!panValid && pan && (
                  <p className="text-xs text-red-500">Invalid PAN format</p>
                )}
              </div>

              <div className="space-y-3">
                <label className={labelCell}>Date of Birth</label>
                <input
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  className={inputClass}
                  max={maxDateStr}
                />
              </div>

              <div className="space-y-3">
                <label className={labelCell}>Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className={inputClass}
                  placeholder="Full Name"
                />
              </div>

              <div className="space-y-3">
                <label className={labelCell}>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputClass}
                  placeholder="you@example.com"
                />
              </div>

              <div className="space-y-3">
                <label className={labelCell}>Password</label>
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
            </>
          ) : (
            <>
              <div className="space-y-3">
                <label className={labelCell}>Email</label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className={inputClass}
                  placeholder="you@example.com"
                />
              </div>

              <div className="space-y-3">
                <label className={labelCell}>Password</label>
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
            </>
          )}

          {/* ── Error Message ─────────────────────────────────────── */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700">
              {error}
            </>
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
      <AuthContent />
    </AuthProvider>
  );
}
