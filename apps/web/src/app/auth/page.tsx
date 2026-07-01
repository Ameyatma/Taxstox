"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";

// ── PAN validation regex ──────────────────────────────────────────

const PAN_REGEX = /^[A-Z]{5}[0-9]{4}[A-Z]$/;

// ── Inner content (needs Suspense for useSearchParams) ─────────────

function AuthContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/?filing=true";

  const { signIn, signUp } = useAuth();

  const [activeTab, setActiveTab] = useState<"signup" | "signin">("signup");

  // ── Sign Up form state ──────────────────────────────────────────
  const [pan, setPan] = useState("");
  const [dob, setDob] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // ── Sign In form state ──────────────────────────────────────────
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // ── PAN live validation on sign-up ───────────────────────────────
  const panValid = PAN_REGEX.test(pan.toUpperCase());
  const panTooLong = pan.length >= 10 && !panValid;

  // ── Handlers ────────────────────────────────────────────────────

  const handleSignUp = async () => {
    setError("");

    if (!pan || !dob || !name || !email || !password) {
      setError("All fields are required.");
      return;
    }
    if (!panValid) {
      setError("Enter a valid PAN (format: ABCDE1234F).");
      return;
    }
    if (dob.length !== 8) {
      setError("Enter DOB in DDMMYYYY format.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);

    try {
      await signUp(email, password, pan, name);
      router.push(redirect);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign up failed.");
      setLoading(false);
    }
  };

  const handleSignIn = async () => {
    setError("");

    if (!loginEmail || !loginPassword) {
      setError("Email and password are required.");
      return;
    }

    setLoading(true);

    try {
      await signIn(loginEmail, loginPassword);
      router.push(redirect);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed.");
      setLoading(false);
    }
  };

  // ── Shared input class ──────────────────────────────────────────

  const inputClass =
    "flex-1 bg-transparent border-none outline-none text-sm text-[#0b1c30] placeholder:text-[#434652]";

  const inputWrapperClass =
    "flex items-center gap-3 px-4 py-3 bg-[#F8FAFC] rounded-lg border border-[#c3c6d4] transition-all focus-within:border-[#003366] focus-within:ring-1 focus-within:ring-[#003366]";

  const labelClass = "text-[11px] font-bold uppercase tracking-wider text-[#434652]";

  // ── Render ──────────────────────────────────────────────────────

  return (
    <div className="min-h-[calc(100vh-64px)] bg-[#F8FAFC] flex items-start justify-center pt-12 pb-16 px-4">
      <div className="w-full max-w-[480px] space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
        {/* ── Tab Switcher ─────────────────────────────────────────── */}
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

        {/* ── Sign Up Form ────────────────────────────────────────── */}
        {activeTab === "signup" && (
          <div className="bg-white border border-[#E2E8F0] rounded-b-xl p-8 space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="text-center space-y-2">
              <h1
                className="text-2xl font-bold text-[#003366]"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                Welcome to TaxStox
              </h1>
              <p className="text-sm text-[#434652]">
                File your ITR in 2 minutes. Your data stays with you.
              </p>
            </div>

            {/* PAN */}
            <div className="space-y-1">
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                PAN Card Number
              </label>
              <div className={inputWrapperClass}>
                <span className="material-symbols-outlined text-[#434652]">credit_card</span>
                <input
                  value={pan}
                  onChange={(e) => setPan(e.target.value.toUpperCase())}
                  placeholder="ABCDE1234F"
                  maxLength={10}
                  className={`${inputClass} font-mono uppercase tracking-widest`}
                />
                {panValid && (
                  <span className="material-symbols-outlined text-[#166534] text-sm fill-icon">
                    verified
                  </span>
                )}
              </div>
              <p className={`text-xs ${panTooLong ? "text-[#991B1B]" : panValid ? "text-[#166534]" : "text-[#434652]"}`}>
                {panTooLong
                  ? "Invalid PAN format. Use: ABCDE1234F"
                  : panValid
                    ? "✓ Valid PAN format — will be verified via NSDL"
                    : "10 characters. Format: ABCDE1234F"}
              </p>
            </div>

            {/* DOB */}
            <div className="space-y-1">
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                Date of Birth (as per PAN)
              </label>
              <div className={inputWrapperClass}>
                <span className="material-symbols-outlined text-[#434652]">calendar_today</span>
                <input
                  value={dob}
                  onChange={(e) => setDob(e.target.value.replace(/\D/g, ""))}
                  placeholder="DDMMYYYY"
                  maxLength={8}
                  className={`${inputClass} font-mono`}
                />
              </div>
            </div>

            {/* Full Name */}
            <div className="space-y-1">
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                Full Name (as per PAN)
              </label>
              <div className={inputWrapperClass}>
                <span className="material-symbols-outlined text-[#434652]">person</span>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Aman Mishra"
                  className={`${inputClass} font-sans`}
                />
              </div>
            </div>

            {/* Email */}
            <div className="space-y-1">
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                Email Address
              </label>
              <div className={inputWrapperClass}>
                <span className="material-symbols-outlined text-[#434652]">mail</span>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="aman@example.com"
                  type="email"
                  className={`${inputClass} font-sans`}
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1">
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                Create Password
              </label>
              <div className={inputWrapperClass}>
                <span className="material-symbols-outlined text-[#434652]">lock</span>
                <input
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min. 8 characters"
                  type={showPassword ? "text" : "password"}
                  className={`${inputClass} font-sans`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="material-symbols-outlined text-[#434652] hover:text-[#0b1c30] transition-colors cursor-pointer"
                >
                  {showPassword ? "visibility" : "visibility_off"}
                </button>
              </div>
            </div>

            {/* Privacy Notice */}
            <div className="bg-[#eff4ff] rounded-lg p-4 flex items-start gap-3">
              <span className="material-symbols-outlined text-[#003366] mt-0.5 fill-icon">
                shield_with_heart
              </span>
              <div className="space-y-1">
                <p className="text-sm font-bold text-[#0b1c30]">Your data is never stored</p>
                <p className="text-xs text-[#434652] leading-relaxed">
                  PAN &amp; DOB are encrypted with AES-256 at rest. All financial data is purged 24
                  hours after ITR generation. We <strong>never</strong> store your Form 16 or AIS
                  content.
                </p>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="p-4 rounded-xl bg-[#ffdad6] border border-red-200 flex items-start gap-3 text-sm text-[#93000a]">
                <span className="material-symbols-outlined shrink-0 mt-0.5">error</span>
                <span>{error}</span>
              </div>
            )}

            <button
              onClick={handleSignUp}
              disabled={loading}
              className="w-full bg-[#003366] text-white py-4 rounded-xl font-semibold text-lg flex items-center justify-center gap-2 shadow-lg hover:shadow-xl hover:opacity-95 active:scale-[0.98] transition-all disabled:opacity-50"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              {loading ? (
                <>
                  <span className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" />
                  Creating Account...
                </>
              ) : (
                <>
                  Create Account
                  <span className="material-symbols-outlined">arrow_forward</span>
                </>
              )}
            </button>

            <p className="text-center text-xs text-[#434652]">
              By signing up, you agree to our{" "}
              <a className="text-[#003178] underline hover:text-[#003366]" href="#">
                Terms
              </a>{" "}
              and{" "}
              <a className="text-[#003178] underline hover:text-[#003366]" href="#">
                Privacy Policy
              </a>
            </p>
          </div>
        )}

        {/* ── Sign In Form ────────────────────────────────────────── */}
        {activeTab === "signin" && (
          <div className="bg-white border border-[#E2E8F0] rounded-b-xl p-8 space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="text-center space-y-2">
              <h1
                className="text-2xl font-bold text-[#003366]"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                Welcome Back
              </h1>
              <p className="text-sm text-[#434652]">
                Sign in to continue your filing.
              </p>
            </div>

            {/* Email */}
            <div className="space-y-1">
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                Email Address
              </label>
              <div className={inputWrapperClass}>
                <span className="material-symbols-outlined text-[#434652]">mail</span>
                <input
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="aman@example.com"
                  type="email"
                  className={`${inputClass} font-sans`}
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1">
              <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                Password
              </label>
              <div className={inputWrapperClass}>
                <span className="material-symbols-outlined text-[#434652]">lock</span>
                <input
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="Enter your password"
                  type={showLoginPassword ? "text" : "password"}
                  className={`${inputClass} font-sans`}
                />
                <button
                  type="button"
                  onClick={() => setShowLoginPassword(!showLoginPassword)}
                  className="material-symbols-outlined text-[#434652] hover:text-[#0b1c30] transition-colors cursor-pointer"
                >
                  {showLoginPassword ? "visibility" : "visibility_off"}
                </button>
              </div>
            </div>

            <div className="flex justify-end">
              <a
                href="#"
                className="text-xs text-[#003178] hover:underline"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                Forgot password?
              </a>
            </div>

            {/* Error */}
            {error && (
              <div className="p-4 rounded-xl bg-[#ffdad6] border border-red-200 flex items-start gap-3 text-sm text-[#93000a]">
                <span className="material-symbols-outlined shrink-0 mt-0.5">error</span>
                <span>{error}</span>
              </div>
            )}

            <button
              onClick={handleSignIn}
              disabled={loading}
              className="w-full bg-[#003366] text-white py-4 rounded-xl font-semibold text-lg flex items-center justify-center gap-2 shadow-lg hover:shadow-xl hover:opacity-95 active:scale-[0.98] transition-all disabled:opacity-50"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              {loading ? (
                <>
                  <span className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" />
                  Signing In...
                </>
              ) : (
                <>
                  Sign In
                  <span className="material-symbols-outlined">login</span>
                </>
              )}
            </button>

            {/* OTP Option */}
            <div className="relative py-2">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[#c3c6d4]" />
              </div>
              <div className="relative flex justify-center">
                <span
                  className="px-4 bg-white text-[11px] font-bold uppercase tracking-wider text-[#434652]"
                  style={{ fontFamily: "var(--font-hanken-grotesk)" }}
                >
                  OR
                </span>
              </div>
            </div>

            <button
              type="button"
              className="w-full bg-[#eff4ff] text-[#003366] border border-[#c3c6d4] py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 hover:bg-[#d3e4fe] transition-all"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              <span className="material-symbols-outlined">smartphone</span>
              Sign In with OTP
            </button>
          </div>
        )}

        {/* ── Trust Badges ─────────────────────────────────────────── */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center space-y-1">
            <span className="material-symbols-outlined text-[#003366] text-[28px] fill-icon">
              verified_user
            </span>
            <p
              className="text-[11px] font-bold uppercase tracking-wider text-[#434652]"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              NSDL Verified
            </p>
          </div>
          <div className="text-center space-y-1">
            <span className="material-symbols-outlined text-[#003366] text-[28px] fill-icon">
              encrypted
            </span>
            <p
              className="text-[11px] font-bold uppercase tracking-wider text-[#434652]"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              AES-256
            </p>
          </div>
          <div className="text-center space-y-1">
            <span className="material-symbols-outlined text-[#003366] text-[28px] fill-icon">
              account_balance
            </span>
            <p
              className="text-[11px] font-bold uppercase tracking-wider text-[#434652]"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              ITD Licensed
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Page export with Suspense boundary ─────────────────────────────

export default function AuthPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[calc(100vh-64px)] bg-[#F8FAFC] flex items-center justify-center">
          <div className="animate-spin w-8 h-8 border-2 border-[#003366]/30 border-t-[#003366] rounded-full" />
        </div>
      }
    >
      <AuthContent />
    </Suspense>
  );
}
