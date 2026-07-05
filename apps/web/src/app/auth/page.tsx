"use client";

import { useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

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
  // We no longer use GIS One Tap (FedCM) — use traditional OAuth popup instead.
  // The GIS script is not needed; we construct the OAuth URL directly.

  const handleGoogleSignIn = useCallback(async () => {
    setGoogleLoading(true);
    setError("");
    try {
      if (!googleClientId) {
        setError("Google Sign-In is not configured yet. Please use email to create an account.");
        setGoogleLoading(false);
        return;
      }

      // Build the Google OAuth 2.0 URL for an ID token via popup
      const redirectUri = `${window.location.origin}/auth/google-callback`;
      const nonce = crypto.randomUUID();
      const params = new URLSearchParams({
        client_id: googleClientId,
        response_type: "id_token",
        redirect_uri: redirectUri,
        scope: "openid email profile",
        nonce: nonce,
        prompt: "select_account",
      });
      const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;

      // Open Google sign-in popup
      const width = 500;
      const height = 600;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;
      const popup = window.open(
        authUrl,
        "google-signin",
        `width=${width},height=${height},left=${left},top=${top}`
      );

      if (!popup) {
        setError("Popup was blocked. Please allow popups for this site and try again.");
        setGoogleLoading(false);
        return;
      }

      // Listen for postMessage from the callback page
      const handleMessage = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return;

        const { type, idToken, error } = event.data || {};
        if (type === "google-signin-success" && idToken) {
          window.removeEventListener("message", handleMessage);
          if (popup && !popup.closed) popup.close();
          sendGoogleToken(idToken);
        } else if (type === "google-signin-error") {
          window.removeEventListener("message", handleMessage);
          if (popup && !popup.closed) popup.close();
          setError(error || "Google sign-in failed. Please try again.");
          setGoogleLoading(false);
        }
      };
      window.addEventListener("message", handleMessage);

      // Fallback polling for popup close without message
      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed);
          // If popup closed without sending a message, user cancelled
          setTimeout(() => {
            window.removeEventListener("message", handleMessage);
            // Only show error if still loading (no success message received)
            setGoogleLoading(prev => {
              if (prev) {
                setError("Google sign-in was cancelled. Please try again.");
              }
              return false;
            });
          }, 1000);
        }
      }, 500);

      // Safety timeout — stop after 2 minutes
      setTimeout(() => {
        clearInterval(checkClosed);
        window.removeEventListener("message", handleMessage);
        if (popup && !popup.closed) popup.close();
        setGoogleLoading(false);
      }, 120000);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load Google Sign-In.");
      setGoogleLoading(false);
    }
  }, [googleClientId]);

  // Send the Google ID token to our backend
  const sendGoogleToken = async (idToken: string) => {
    try {
      const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${base}/auth/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential: idToken }),
      });
      const text = await res.text();
      if (!res.ok) {
        let msg = "Google sign-in failed";
        try { const err = JSON.parse(text); msg = err.detail || msg; } catch {}
        throw new Error(msg);
      }
      const data = JSON.parse(text);
      // Use signInWithToken to set user directly in AuthContext
      // This avoids the race condition where router.push navigates
      // before AuthProvider re-checks localStorage on mount
      signInWithToken(data.access_token, data.user);
      router.push(redirect);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg === "Failed to fetch" ? "Network error. Please try again or use email sign-up." : msg);
      setGoogleLoading(false);
    }
  };

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
      <div className="flex-1 flex items-start justify-center pt-10 pb-16 px-6">
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
                className="w-full flex items-center justify-center gap-3 py-3 px-5 bg-white border border-[#c3c6d4] rounded-lg hover:bg-[#F8FAFC] hover:border-[#003366] transition-all text-sm font-medium text-[#0b1c30] disabled:opacity-50"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                {googleLoading ? (
                  <span className="animate-spin w-4 h-4 border-2 border-[#003366]/30 border-t-[#003366] rounded-full" />
                ) : (
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                )}
                Continue with Google
              </button>
              <div className="relative mt-4">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-[#E2E8F0]" /></div>
                <div className="relative flex justify-center">
                  <span className="px-4 bg-white text-[11px] font-bold uppercase tracking-wider text-[#737783]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>or use email</span>
                </div>
              </div>
            </div>
          )}

          {/* ── Sign Up Form ─────────────────────────────────────── */}
          {activeTab === "signup" && (
            <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              {/* PAN */}
              <div className="space-y-1">
                <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>PAN Card Number</label>
                <div className={inputWrapper}>
                  <span className="material-symbols-outlined text-[#737783]">credit_card</span>
                  <input value={pan} onChange={e => setPan(e.target.value.toUpperCase())} placeholder="ABCDE1234F" maxLength={10}
                    className={`${inputClass} font-mono uppercase tracking-widest`} />
                  {panValid && <span className="material-symbols-outlined text-[#166534] text-sm fill-icon">verified</span>}
                </div>
                <p className={`text-xs ${panTooLong ? "text-[#991B1B]" : panValid ? "text-[#166534]" : "text-[#737783]"}`}>
                  {panTooLong ? "Invalid PAN format. Use: ABCDE1234F"
                    : panValid ? "✓ Valid PAN format" : "10 characters. Format: ABCDE1234F"}
                </p>
              </div>

              {/* DOB — Date Picker */}
              <div className="space-y-1">
                <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Date of Birth (as per PAN)</label>
                <div className={inputWrapper}>
                  <span className="material-symbols-outlined text-[#737783]">calendar_today</span>
                  <input
                    type="date"
                    value={dob}
                    onChange={e => setDob(e.target.value)}
                    max={maxDateStr}
                    min="1920-01-01"
                    className={`${inputClass} text-[#0b1c30]`}
                    style={{ colorScheme: "light" }}
                  />
                </div>
                <p className="text-xs text-[#737783]">Must match your PAN card. You must be 18+ years old.</p>
              </div>

              {/* Full Name */}
              <div className="space-y-1">
                <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Full Name (as per PAN)</label>
                <div className={inputWrapper}>
                  <span className="material-symbols-outlined text-[#737783]">person</span>
                  <input value={name} onChange={e => setName(e.target.value)} placeholder="Aman Mishra"
                    className={`${inputClass} font-sans`} />
                </div>
              </div>

              {/* Email */}
              <div className="space-y-1">
                <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Email Address</label>
                <div className={inputWrapper}>
                  <span className="material-symbols-outlined text-[#737783]">mail</span>
                  <input value={email} onChange={e => setEmail(e.target.value)} placeholder="aman@example.com" type="email"
                    className={`${inputClass} font-sans`} />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-1">
                <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Create Password</label>
                <div className={inputWrapper}>
                  <span className="material-symbols-outlined text-[#737783]">lock</span>
                  <input value={password} onChange={e => setPassword(e.target.value)} placeholder="Min. 8 characters"
                    type={showPassword ? "text" : "password"} className={`${inputClass} font-sans`} />
                  <button type="button" onClick={() => setShowPassword(!showPassword)}
                    className="material-symbols-outlined text-[#737783] hover:text-[#0b1c30] transition-colors cursor-pointer">
                    {showPassword ? "visibility" : "visibility_off"}
                  </button>
                </div>
                {password.length > 0 && password.length < 8 && (
                  <p className="text-xs text-[#991B1B]">Password must be at least 8 characters</p>
                )}
              </div>

              {/* Privacy */}
              <div className="bg-[#eff4ff] rounded-lg p-4 flex items-start gap-3">
                <span className="material-symbols-outlined text-[#003366] mt-0.5 fill-icon">shield_with_heart</span>
                <div className="space-y-1">
                  <p className="text-sm font-bold text-[#0b1c30]">Your data is never stored</p>
                  <p className="text-xs text-[#434652] leading-relaxed">
                    PAN &amp; DOB are encrypted with AES-256 at rest. All financial data is purged 24 hours after ITR generation. We <strong>never</strong> store your Form 16 or AIS content.
                  </p>
                </div>
              </div>

              {error && (
                <div className="p-4 rounded-xl bg-[#ffdad6] border border-red-200 flex items-start gap-3 text-sm text-[#93000a]">
                  <span className="material-symbols-outlined shrink-0 mt-0.5">error</span>
                  <span>{error}</span>
                </div>
              )}

              <button onClick={handleSignUp} disabled={loading}
                className="w-full bg-[#003366] text-white py-4 rounded-xl font-semibold text-lg flex items-center justify-center gap-2 shadow-lg hover:shadow-xl hover:opacity-95 active:scale-[0.98] transition-all disabled:opacity-50"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                {loading ? (
                  <><span className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" /> Creating Account...</>
                ) : (
                  <>Create Account <span className="material-symbols-outlined">arrow_forward</span></>
                )}
              </button>

              <p className="text-center text-xs text-[#737783]">
                By signing up, you agree to our <Link className="text-[#003178] underline hover:text-[#003366]" href="/legal/terms">Terms</Link> and <Link className="text-[#003178] underline hover:text-[#003366]" href="/legal/privacy">Privacy Policy</Link>
              </p>
            </div>
          )}

          {/* ── Sign In Form ─────────────────────────────────────── */}
          {activeTab === "signin" && (
            <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="text-center space-y-2">
                <h1 className="text-2xl font-bold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Welcome Back</h1>
                <p className="text-sm text-[#434652]">Sign in to continue your filing.</p>
              </div>

              <div className="space-y-1">
                <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Email Address</label>
                <div className={inputWrapper}>
                  <span className="material-symbols-outlined text-[#737783]">mail</span>
                  <input value={loginEmail} onChange={e => setLoginEmail(e.target.value)} placeholder="aman@example.com"
                    type="email" className={`${inputClass} font-sans`} />
                </div>
              </div>

              <div className="space-y-1">
                <label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Password</label>
                <div className={inputWrapper}>
                  <span className="material-symbols-outlined text-[#737783]">lock</span>
                  <input value={loginPassword} onChange={e => setLoginPassword(e.target.value)}
                    placeholder="Enter your password" type={showLoginPassword ? "text" : "password"}
                    className={`${inputClass} font-sans`} />
                  <button type="button" onClick={() => setShowLoginPassword(!showLoginPassword)}
                    className="material-symbols-outlined text-[#737783] hover:text-[#0b1c30] transition-colors cursor-pointer">
                    {showLoginPassword ? "visibility" : "visibility_off"}
                  </button>
                </div>
              </div>

              <div className="flex justify-end">
                <a href="#" className="text-xs text-[#003178] hover:underline" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                  Forgot password?
                </a>
              </div>

              {error && (
                <div className="p-4 rounded-xl bg-[#ffdad6] border border-red-200 flex items-start gap-3 text-sm text-[#93000a]">
                  <span className="material-symbols-outlined shrink-0 mt-0.5">error</span>
                  <span>{error}</span>
                </div>
              )}

              <button onClick={handleSignIn} disabled={loading}
                className="w-full bg-[#003366] text-white py-4 rounded-xl font-semibold text-lg flex items-center justify-center gap-2 shadow-lg hover:shadow-xl hover:opacity-95 active:scale-[0.98] transition-all disabled:opacity-50"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                {loading ? (
                  <><span className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" /> Signing In...</>
                ) : (
                  <>Sign In <span className="material-symbols-outlined">login</span></>
                )}
              </button>

              {/* OTP Option */}
              <div className="relative py-2">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-[#c3c6d4]" /></div>
                <div className="relative flex justify-center">
                  <span className="px-4 bg-white text-[11px] font-bold uppercase tracking-wider text-[#737783]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>OR</span>
                </div>
              </div>

              <button type="button"
                className="w-full bg-[#eff4ff] text-[#003366] border border-[#c3c6d4] py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 hover:bg-[#d3e4fe] transition-all"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                <span className="material-symbols-outlined">smartphone</span>
                Sign In with OTP
              </button>
            </div>
          )}

          {/* Trust Badges */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center space-y-1">
              <span className="material-symbols-outlined text-[#003366] text-[28px] fill-icon">verified_user</span>
              <p className="text-[11px] font-bold uppercase tracking-wider text-[#737783]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>NSDL Verified</p>
            </div>
            <div className="text-center space-y-1">
              <span className="material-symbols-outlined text-[#003366] text-[28px] fill-icon">encrypted</span>
              <p className="text-[11px] font-bold uppercase tracking-wider text-[#737783]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>AES-256</p>
            </div>
            <div className="text-center space-y-1">
              <span className="material-symbols-outlined text-[#003366] text-[28px] fill-icon">account_balance</span>
              <p className="text-[11px] font-bold uppercase tracking-wider text-[#737783]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>ITD Licensed</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Right Panel: Feature Highlights ──────────────────────── */}
      <div className="hidden lg:flex w-[440px] bg-[#003366] text-white flex-col justify-center px-12 py-16 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#0d47a1] rounded-full blur-3xl -translate-y-1/2 translate-x-1/4" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-[#F57C00]/20 rounded-full blur-3xl translate-y-1/3 -translate-x-1/3" />

        <div className="relative z-10 space-y-8">
          <div className="space-y-2">
            <h2 className="text-3xl font-bold" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              File your ITR in <span className="text-[#F57C00]">2 minutes.</span>
            </h2>
            <p className="text-[#b0c6ff] text-sm leading-relaxed">
              Upload Form 16 + AIS. Answer 5 questions. Download your ready-to-file ITR JSON. No CA required.
            </p>
          </div>

          <div className="space-y-5">
            {[
              { icon: "bolt", title: "Auto-Extraction", desc: "AI reads your Form 16 and AIS PDFs. Zero manual data entry." },
              { icon: "calculate", title: "Regime Optimizer", desc: "Computes both Old & New regimes. Guarantees lowest legal tax." },
              { icon: "fact_check", title: "400+ Validation Checks", desc: "Catches notice-triggering errors before you file to ITD portal." },
              { icon: "shield_with_heart", title: "Bank-Grade Security", desc: "Documents auto-purged after 24h. AES-256 encryption at rest." },
            ].map((feature) => (
              <div key={feature.title} className="flex items-start gap-4">
                <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-[#F57C00]">{feature.icon}</span>
                </div>
                <div>
                  <p className="font-semibold text-sm">{feature.title}</p>
                  <p className="text-xs text-[#b0c6ff] leading-relaxed mt-0.5">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Social proof */}
          <div className="border-t border-white/10 pt-6">
            <p className="text-[10px] font-bold uppercase tracking-widest text-[#b0c6ff] mb-3">
              Trusted by taxpayers at
            </p>
            <div className="flex gap-4 opacity-60 text-xs font-bold tracking-tight">
              <span>Infosys</span>
              <span>TCS</span>
              <span>Wipro</span>
              <span>HCL</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AuthPage() {
  return (
    <Suspense fallback={
      <div className="min-h-[calc(100vh-64px)] bg-[#F8FAFC] flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-[#003366]/30 border-t-[#003366] rounded-full" />
      </div>
    }>
      <AuthContent />
    </Suspense>
  );
}
