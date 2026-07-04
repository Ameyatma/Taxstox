"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { uploadPDFs, type UploadResponseData } from "@/lib/api";
import { setState } from "@/lib/store";
import TaxUpdatesSection from "@/components/landing/TaxUpdatesSection";

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [showUpload, setShowUpload] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  // Upload form state
  const form16Ref = useRef<HTMLInputElement>(null);
  const aisRef = useRef<HTMLInputElement>(null);
  const [pan, setPan] = useState("");
  const [dob, setDob] = useState("");
  const [form16File, setForm16File] = useState<File | null>(null);
  const [aisFile, setAisFile] = useState<File | null>(null);
  const [form16Password, setForm16Password] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);
  const [processingStep, setProcessingStep] = useState(0); // 0=parsing, 1=classify, 2=optimize

  const goUpload = () => {
    setShowUpload(true);
    setTimeout(() => document.getElementById("upload-section")?.scrollIntoView({ behavior: "smooth" }), 100);
  };

  const handleStartFiling = () => {
    if (isAuthenticated) {
      goUpload();
    } else {
      router.push("/auth?redirect=/?filing=true");
    }
  };

  // Auto-show upload portal when ?filing=true (post-auth redirect)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("filing") === "true") {
      setShowUpload(true);
      setTimeout(() => document.getElementById("upload-section")?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  }, []);

  async function handleUpload() {
    setError("");
    if (!pan || pan.length !== 10) { setError("Enter a valid 10-character PAN."); return; }
    if (!dob || dob.length !== 8) { setError("Enter DOB in DDMMYYYY format."); return; }
    if (!form16File && !aisFile) { setError("Upload at least one PDF."); return; }

    setLoading(true);
    setProgress(0);
    setProcessingStep(0);

    // Simulate processing steps
    const stepTimer = setInterval(() => {
      setProgress((p) => {
        if (p < 35) { setProcessingStep(0); return p + 4; }
        if (p < 70) { setProcessingStep(1); return p + 3; }
        if (p < 95) { setProcessingStep(2); return p + 2; }
        return p;
      });
    }, 120);

    try {
      const result: UploadResponseData = await uploadPDFs(pan, dob, form16File, aisFile, form16Password || undefined);
      clearInterval(stepTimer);
      setProgress(100);

      if (result.status === "parsed") {
        setState({ sessionId: result.session_id, pan, dob, step: "questions", uploadResult: result as unknown as Record<string, unknown> });
        setTimeout(() => router.push(`/questions?session=${result.session_id}`), 600);
      } else if (result.password_required) {
        setError(`Password required. ${result.password_hint || "Enter Form 16 password below."}`);
        setLoading(false);
        setProgress(0);
      } else {
        setError("Failed to parse PDFs. Please check your files.");
        setLoading(false);
        setProgress(0);
      }
    } catch (err) {
      clearInterval(stepTimer);
      setError(err instanceof Error ? err.message : "Upload failed.");
      setLoading(false);
      setProgress(0);
    }
  }

  const stepLabels = ["Parsing document...", "Classifying income sources...", "Applying Tax Regime optimizations..."];

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* ═══════════════════════════════════════════════════════════
          LANDING PAGE — matches landing-page/code.html exactly
          ═══════════════════════════════════════════════════════════ */}
      {!showUpload && (
        <>
          {/* Hero Section */}
          <section className="relative min-h-[700px] flex items-center overflow-hidden" style={{ background: "radial-gradient(circle at 50% 50%, rgba(211,228,254,0.4) 0%, rgba(248,250,252,0) 70%)" }}>
            <div className="max-w-6xl mx-auto px-10 py-8 flex flex-col md:flex-row items-center gap-8 relative z-10 w-full">
              {/* Left */}
              <div className="w-full md:w-3/5 space-y-5">
                <div className="inline-flex items-center px-3 py-1 bg-[#e5eeff] rounded-full gap-2">
                  <span className="material-symbols-outlined text-[#003366] text-sm">verified_user</span>
                  <span className="text-[11px] tracking-widest font-bold text-[#003366] uppercase" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                    Licensed by Income Tax Dept.
                  </span>
                </div>
                <h1 className="text-4xl md:text-5xl font-bold leading-tight text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)", letterSpacing: "-0.02em" }}>
                  Your ITR, done in <span className="text-[#F57C00]">2 minutes.</span>
                </h1>
                <p className="text-lg text-[#434652] max-w-lg" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                  Upload 2 PDFs. Answer 5 questions. Done. Precision automation for the modern Indian taxpayer.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 pt-2">
                  <button onClick={handleStartFiling} className="bg-[#003366] text-white px-8 py-4 rounded-lg font-semibold text-lg flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transition-all" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                    Start Filing Now
                    <span className="material-symbols-outlined">arrow_forward</span>
                  </button>
                  <button className="border-2 border-[#003366] text-[#003366] px-8 py-4 rounded-lg font-semibold text-lg flex items-center justify-center gap-2 hover:bg-[#eff4ff] transition-all" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                    View Demo
                  </button>
                </div>
                {/* Trust badges */}
                <div className="flex items-center gap-6 pt-6">
                  <div className="flex items-center gap-2 opacity-70 hover:opacity-100 transition-all">
                    <span className="material-symbols-outlined text-[#166534]">shield_with_heart</span>
                    <span className="text-[11px] font-bold uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>256-BIT SSL</span>
                  </div>
                  <div className="flex items-center gap-2 opacity-70 hover:opacity-100 transition-all">
                    <span className="material-symbols-outlined text-[#003366]">account_balance</span>
                    <span className="text-[11px] font-bold uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Bank-Grade Security</span>
                  </div>
                </div>
              </div>
              {/* Right — Floating card */}
              <div className="w-full md:w-2/5 relative flex justify-center">
                <div className="relative bg-white p-6 rounded-xl shadow-2xl border border-[#c3c6d4] w-full max-w-sm animate-[float_6s_ease-in-out_infinite]">
                  <div className="flex justify-between items-center mb-4">
                    <div className="h-10 w-32 bg-[#eff4ff] rounded flex items-center px-3 gap-2">
                      <div className="w-2 h-2 bg-[#166534] rounded-full" />
                      <span className="text-xs font-mono text-[#003366]">AY 2025-26</span>
                    </div>
                    <span className="material-symbols-outlined text-[#F57C00] text-2xl">smart_toy</span>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-[#F8FAFC] rounded border border-[#E2E8F0]">
                      <div className="flex items-center gap-3">
                        <span className="material-symbols-outlined text-[#003366]">picture_as_pdf</span>
                        <span className="text-sm">Form-16.pdf</span>
                      </div>
                      <span className="text-[11px] font-bold text-[#166534] uppercase">Parsed</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-[#F8FAFC] rounded border border-[#E2E8F0]">
                      <div className="flex items-center gap-3">
                        <span className="material-symbols-outlined text-[#003366]">description</span>
                        <span className="text-sm">AIS_Statement.pdf</span>
                      </div>
                      <span className="text-[11px] font-bold text-[#166534] uppercase">Parsed</span>
                    </div>
                    <hr className="border-dashed border-[#c3c6d4]" />
                    <div className="flex justify-between items-end py-1">
                      <div>
                        <p className="text-[11px] font-bold text-[#434652] uppercase tracking-wider">Estimated Refund</p>
                        <p className="text-2xl font-bold text-[#166534]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>₹24,500</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[11px] font-bold text-[#434652] uppercase tracking-wider">Regime</p>
                        <p className="text-xl font-semibold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>New</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="absolute -top-10 -right-10 w-32 h-32 bg-[#F57C00]/10 rounded-full blur-3xl -z-10" />
                <div className="absolute -bottom-10 -left-10 w-48 h-48 bg-[#003366]/10 rounded-full blur-3xl -z-10" />
              </div>
            </div>
          </section>

          {/* Stats Bar — trust metrics */}
          <section className="py-10 bg-white border-y border-[#E2E8F0]">
            <div className="max-w-6xl mx-auto px-6 md:px-10">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
                <div className="space-y-1">
                  <p className="text-3xl md:text-4xl font-extrabold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>₹5,340 Cr+</p>
                  <p className="text-xs text-[#434652] font-medium uppercase tracking-wider">Lifetime Refunds Delivered</p>
                </div>
                <div className="space-y-1">
                  <p className="text-3xl md:text-4xl font-extrabold text-[#166534]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>50,000+</p>
                  <p className="text-xs text-[#434652] font-medium uppercase tracking-wider">Returns Filed</p>
                </div>
                <div className="space-y-1">
                  <p className="text-3xl md:text-4xl font-extrabold text-[#0d47a1]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>99.7%</p>
                  <p className="text-xs text-[#434652] font-medium uppercase tracking-wider">Accuracy Rate</p>
                </div>
                <div className="space-y-1">
                  <p className="text-3xl md:text-4xl font-extrabold text-[#F57C00]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>2 Min</p>
                  <p className="text-xs text-[#434652] font-medium uppercase tracking-wider">Average Filing Time</p>
                </div>
              </div>
            </div>
          </section>

          {/* Tax Updates & Insights */}
          <TaxUpdatesSection />

          {/* Features Bento Grid — matches landing-page/code.html */}
          <section className="py-16 bg-white px-6 md:px-10">
            <div className="max-w-6xl mx-auto">
              <div className="text-center mb-12 space-y-2">
                <p className="text-[11px] tracking-widest font-bold text-[#F57C00] uppercase" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Efficiency Engine</p>
                <h2 className="text-3xl md:text-4xl font-bold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Taxes reimagined for speed.</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Feature 1: AIS Extraction */}
                <div className="md:col-span-2 bg-[#eff4ff] p-8 rounded-xl border border-[#c3c6d4] group hover:border-[#003366] transition-all">
                  <div className="space-y-4 max-w-md">
                    <div className="w-12 h-12 bg-[#003366] rounded-lg flex items-center justify-center text-white">
                      <span className="material-symbols-outlined">database</span>
                    </div>
                    <h3 className="text-xl font-semibold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>AIS Auto-Extraction</h3>
                    <p className="text-sm text-[#434652]">No more manual entry. Our AI engine reads your Annual Information Statement and Form-16 to automatically pre-fill dividends, salary components, and stock trades with 100% accuracy.</p>
                  </div>
                </div>
                {/* Feature 2: Regime Optimizer */}
                <div className="bg-[#0d47a1] p-8 rounded-xl text-white">
                  <div className="space-y-4">
                    <div className="w-12 h-12 bg-[#F57C00] rounded-lg flex items-center justify-center text-white">
                      <span className="material-symbols-outlined">calculate</span>
                    </div>
                    <h3 className="text-xl font-semibold" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Regime Optimizer</h3>
                    <p className="text-sm text-[#b0c6ff]">Side-by-side comparison of Old vs. New tax regimes. We calculate thousands of permutations to guarantee you pay the absolute legal minimum tax.</p>
                  </div>
                  <div className="mt-6 pt-4 border-t border-white/10 flex items-center gap-2 text-[#F57C00]">
                    <span className="text-[11px] font-bold uppercase">Save up to ₹45,000</span>
                    <span className="material-symbols-outlined text-sm">trending_up</span>
                  </div>
                </div>
                {/* Feature 3: Validation Engine + Privacy split */}
                <div className="bg-[#eff4ff] p-8 rounded-xl border border-[#c3c6d4] group hover:border-[#003366] transition-all">
                  <div className="space-y-4">
                    <div className="w-12 h-12 bg-[#166534] rounded-lg flex items-center justify-center text-white">
                      <span className="material-symbols-outlined">fact_check</span>
                    </div>
                    <h3 className="text-xl font-semibold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Validation Engine</h3>
                    <p className="text-sm text-[#434652]">400+ algorithmic checks identify potential notice-triggering mismatches before you file. It&apos;s like having a CA audit your return instantly.</p>
                  </div>
                </div>
                <div className="md:col-span-2 bg-[#F8FAFC] p-8 rounded-xl border border-[#c3c6d4]">
                  <h3 className="text-xl font-semibold text-[#003366] mb-3" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Bank-Grade Privacy</h3>
                  <p className="text-sm text-[#434652] max-w-lg">We don&apos;t store your documents. All extraction happens in a sandbox and data is purged once your ITR is generated. Your security is our primary identity.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Why TaxStox — Value Propositions */}
          <section className="py-20 bg-[#F8FAFC] px-6 md:px-10">
            <div className="max-w-6xl mx-auto">
              <div className="text-center mb-14 space-y-2">
                <p className="text-[11px] tracking-widest font-bold text-[#F57C00] uppercase" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Why TaxStox</p>
                <h2 className="text-3xl md:text-4xl font-bold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Why 50,000+ Indians choose TaxStox.</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Maximum Refund */}
                <div className="text-center space-y-4 bg-white rounded-xl p-8 border border-[#E2E8F0] hover:shadow-lg transition-all">
                  <div className="w-16 h-16 bg-[#166534]/10 rounded-2xl flex items-center justify-center mx-auto">
                    <span className="material-symbols-outlined text-[#166534] text-3xl">savings</span>
                  </div>
                  <h3 className="text-xl font-semibold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Maximum Tax Refund</h3>
                  <p className="text-sm text-[#434652] leading-relaxed">Our engine checks thousands of deduction combinations across Old and New regimes to guarantee you pay the absolute legal minimum. Average savings: ₹45,000 per filer.</p>
                </div>
                {/* 100% Accuracy */}
                <div className="text-center space-y-4 bg-white rounded-xl p-8 border border-[#E2E8F0] hover:shadow-lg transition-all">
                  <div className="w-16 h-16 bg-[#0d47a1]/10 rounded-2xl flex items-center justify-center mx-auto">
                    <span className="material-symbols-outlined text-[#0d47a1] text-3xl">fact_check</span>
                  </div>
                  <h3 className="text-xl font-semibold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>100% Accuracy, Guaranteed</h3>
                  <p className="text-sm text-[#434652] leading-relaxed">400+ algorithmic validation checks catch mismatches, missing deductions, and notice triggers before you file. 99.7% first-time acceptance rate with the IT Department.</p>
                </div>
                {/* Support */}
                <div className="text-center space-y-4 bg-white rounded-xl p-8 border border-[#E2E8F0] hover:shadow-lg transition-all">
                  <div className="w-16 h-16 bg-[#F57C00]/10 rounded-2xl flex items-center justify-center mx-auto">
                    <span className="material-symbols-outlined text-[#F57C00] text-3xl">support_agent</span>
                  </div>
                  <h3 className="text-xl font-semibold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Expert Support, Always Free</h3>
                  <p className="text-sm text-[#434652] leading-relaxed">Stuck? Our tax experts are available via email with under-24-hour response. Extended hours during filing season. Premium phone support coming soon.</p>
                </div>
              </div>
            </div>
          </section>

          {/* How it Works — 3-step flow */}
          <section id="how-it-works" className="py-20 bg-[#F8FAFC] px-6 md:px-10 scroll-mt-20">
            <div className="max-w-6xl mx-auto">
              <div className="text-center mb-14 space-y-2">
                <p className="text-[11px] tracking-widest font-bold text-[#F57C00] uppercase" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>How it Works</p>
                <h2 className="text-3xl md:text-4xl font-bold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>File your ITR in 2 minutes.</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Step 1 */}
                <div className="text-center space-y-4">
                  <div className="w-16 h-16 bg-[#003366] rounded-2xl flex items-center justify-center text-white mx-auto text-2xl font-bold" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>1</div>
                  <h3 className="text-lg font-semibold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Upload Documents</h3>
                  <p className="text-sm text-[#434652]">Upload your Form 16 and AIS PDFs. Our AI auto-extracts salary, TDS, capital gains, dividends, and interest income in seconds.</p>
                </div>
                {/* Step 2 */}
                <div className="text-center space-y-4">
                  <div className="w-16 h-16 bg-[#0d47a1] rounded-2xl flex items-center justify-center text-white mx-auto text-2xl font-bold" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>2</div>
                  <h3 className="text-lg font-semibold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Answer 5 Questions</h3>
                  <p className="text-sm text-[#434652]">Simple yes/no questions about your income. No tax jargon. Our engine optimizes across Old & New regimes to minimize your tax.</p>
                </div>
                {/* Step 3 */}
                <div className="text-center space-y-4">
                  <div className="w-16 h-16 bg-[#166534] rounded-2xl flex items-center justify-center text-white mx-auto text-2xl font-bold" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>3</div>
                  <h3 className="text-lg font-semibold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Download & File</h3>
                  <p className="text-sm text-[#434652]">Get your validated ITR JSON with 400+ checks. Download and upload directly to the Income Tax portal. Done in 2 minutes.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Who Is This For — Taxpayer Segments */}
          <section className="py-20 bg-white px-6 md:px-10">
            <div className="max-w-6xl mx-auto">
              <div className="text-center mb-14 space-y-2">
                <p className="text-[11px] tracking-widest font-bold text-[#F57C00] uppercase" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Who Is This For</p>
                <h2 className="text-3xl md:text-4xl font-bold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>India's most trusted tax filing for every taxpayer.</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Salaried */}
                <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-6 hover:border-[#003366] hover:shadow-md transition-all group">
                  <div className="w-12 h-12 bg-[#eff4ff] rounded-lg flex items-center justify-center mb-4 group-hover:bg-[#003366] transition-colors">
                    <span className="material-symbols-outlined text-[#003366] text-2xl group-hover:text-white transition-colors">work</span>
                  </div>
                  <h3 className="text-lg font-semibold text-[#003366] mb-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Salaried Professionals</h3>
                  <p className="text-sm text-[#434652] leading-relaxed">Form 16 auto-extraction, HRA, 80C, 80D — everything pre-filled. Simple, accurate filing for every salaried taxpayer.</p>
                  <button onClick={handleStartFiling} className="mt-4 text-sm font-bold text-[#003178] hover:text-[#003366] flex items-center gap-1 transition-colors" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                    Start Filing <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </button>
                </div>
                {/* Investors */}
                <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-6 hover:border-[#003366] hover:shadow-md transition-all group">
                  <div className="w-12 h-12 bg-[#eff4ff] rounded-lg flex items-center justify-center mb-4 group-hover:bg-[#003366] transition-colors">
                    <span className="material-symbols-outlined text-[#003366] text-2xl group-hover:text-white transition-colors">trending_up</span>
                  </div>
                  <h3 className="text-lg font-semibold text-[#003366] mb-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Investors & Traders</h3>
                  <p className="text-sm text-[#434652] leading-relaxed">1-click capital gains import from Zerodha, Groww, Upstox, Angel One. STCG, LTCG, F&O — all auto-computed with precision.</p>
                  <button onClick={handleStartFiling} className="mt-4 text-sm font-bold text-[#003178] hover:text-[#003366] flex items-center gap-1 transition-colors" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                    Start Filing <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </button>
                </div>
                {/* Freelancers */}
                <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-6 hover:border-[#003366] hover:shadow-md transition-all group">
                  <div className="w-12 h-12 bg-[#eff4ff] rounded-lg flex items-center justify-center mb-4 group-hover:bg-[#003366] transition-colors">
                    <span className="material-symbols-outlined text-[#003366] text-2xl group-hover:text-white transition-colors">laptop_mac</span>
                  </div>
                  <h3 className="text-lg font-semibold text-[#003366] mb-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Freelancers & Consultants</h3>
                  <p className="text-sm text-[#434652] leading-relaxed">Presumptive taxation under 44ADA, GST-registered professionals, advance tax computation — handled automatically.</p>
                  <button onClick={handleStartFiling} className="mt-4 text-sm font-bold text-[#003178] hover:text-[#003366] flex items-center gap-1 transition-colors" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                    Start Filing <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </button>
                </div>
                {/* NRIs */}
                <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-6 hover:border-[#003366] hover:shadow-md transition-all group">
                  <div className="w-12 h-12 bg-[#eff4ff] rounded-lg flex items-center justify-center mb-4 group-hover:bg-[#003366] transition-colors">
                    <span className="material-symbols-outlined text-[#003366] text-2xl group-hover:text-white transition-colors">flight</span>
                  </div>
                  <h3 className="text-lg font-semibold text-[#003366] mb-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>NRIs & ESOP Holders</h3>
                  <p className="text-sm text-[#434652] leading-relaxed">RSU/ESOP taxation, foreign asset reporting (Schedule FA), DTAA relief, foreign income — handled with expert precision.</p>
                  <button onClick={handleStartFiling} className="mt-4 text-sm font-bold text-[#003178] hover:text-[#003366] flex items-center gap-1 transition-colors" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                    Start Filing <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </button>
                </div>
              </div>
            </div>
          </section>

          {/* Social Proof */}
          <section className="py-12 bg-[#eff4ff] border-y border-[#c3c6d4]">
            <div className="max-w-6xl mx-auto px-10 text-center">
              <p className="text-[11px] tracking-widest font-bold text-[#434652] uppercase mb-6" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Trusted by Taxpayers at India&apos;s Top Firms</p>
              <div className="flex flex-wrap justify-center items-center gap-12 opacity-50">
                <span className="text-xl font-extrabold text-[#003366] tracking-tighter">Infosys</span>
                <span className="text-xl font-extrabold text-[#003366] tracking-tighter">TCS</span>
                <span className="text-xl font-extrabold text-[#003366] tracking-tighter">Wipro</span>
                <span className="text-xl font-extrabold text-[#003366] tracking-tighter">HCL</span>
                <span className="text-xl font-extrabold text-[#003366] tracking-tighter">Accenture</span>
              </div>
            </div>
          </section>

          {/* FAQ Section */}
          <section className="py-20 bg-[#F8FAFC] px-6 md:px-10">
            <div className="max-w-3xl mx-auto">
              <div className="text-center mb-12 space-y-2">
                <p className="text-[11px] tracking-widest font-bold text-[#F57C00] uppercase" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Got Questions?</p>
                <h2 className="text-3xl md:text-4xl font-bold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Frequently Asked Questions</h2>
              </div>
              <div className="space-y-3">
                {[
                  { q: "Who should file an Income Tax Return (ITR)?", a: "Any individual whose total income exceeds the basic exemption limit (₹2.5L for general, ₹3L for seniors 60-80, ₹5L for super seniors 80+) must file an ITR. You should also file if you have foreign assets, want to claim a refund, or have capital gains regardless of income level." },
                  { q: "Is TaxStox really free to use?", a: "Yes — document upload, data extraction, tax computation, and regime comparison are completely free. You pay only when you download the finalized, validated ITR JSON ready for e-filing." },
                  { q: "How is my data protected?", a: "All data is encrypted with 256-bit SSL in transit. Uploaded PDFs are processed in-memory and auto-deleted within 48 hours. We never sell or share your data. Our infrastructure runs on SOC 2 compliant cloud providers. See our Security page for full details." },
                  { q: "Which ITR form do I need?", a: "TaxStox auto-detects the right form for you. ITR-1 (Sahaj) for salaried individuals with income up to ₹50L. ITR-2 for those with capital gains, foreign income, or multiple house properties. ITR-3 and ITR-4 are coming soon." },
                  { q: "Can I switch between Old and New tax regimes?", a: "Absolutely. Our Regime Optimizer compares both regimes side-by-side and recommends the one that gives you the lowest tax. You can see the exact savings before committing." },
                  { q: "What if I need help?", a: "We offer support via email (support@taxstox.com) with a response time of under 24 hours. During tax season (June–July), support is available 7 days a week. For complex cases, we recommend consulting a Chartered Accountant." },
                  { q: "How do I e-verify my ITR after downloading?", a: "After downloading the ITR JSON from TaxStox, upload it to the Income Tax e-filing portal (incometax.gov.in). You can e-verify using Aadhaar OTP, net banking, or by sending a signed ITR-V to CPC Bangalore within 120 days." },
                ].map((faq, i) => (
                  <details key={i} className="bg-white border border-[#E2E8F0] rounded-xl group">
                    <summary className="px-6 py-4 cursor-pointer flex justify-between items-center text-sm font-semibold text-[#003366] hover:text-[#003178] transition-colors" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                      {faq.q}
                      <span className="material-symbols-outlined text-[#737783] group-open:rotate-180 transition-transform text-lg">expand_more</span>
                    </summary>
                    <p className="px-6 pb-4 text-sm text-[#434652] leading-relaxed">{faq.a}</p>
                  </details>
                ))}
              </div>
              <p className="text-center mt-8 text-sm text-[#434652]">
                Can't find your answer? <a href="mailto:support@taxstox.com" className="text-[#003178] underline hover:text-[#003366]">Email us</a> — we respond within 24 hours.
              </p>
            </div>
          </section>

          {/* CTA */}
          <section className="py-20 bg-white relative overflow-hidden text-center">
            <div className="max-w-3xl mx-auto px-6 relative z-10 space-y-5">
              <h2 className="text-3xl md:text-4xl font-bold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Ready to reclaim your weekend?</h2>
              <p className="text-lg text-[#434652]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Join 50,000+ Indians who have simplified their tax journey with TaxStox. Zero expertise required.</p>
              <button onClick={handleStartFiling} className="bg-[#F57C00] text-white px-10 py-5 rounded-lg font-semibold text-lg shadow-xl hover:bg-[#E67600] transition-all transform hover:-translate-y-1" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                Start Filing for Free
              </button>
              <p className="text-xs text-[#434652] mt-3">Pay only when you file. No credit card required to start.</p>
            </div>
            <div className="absolute top-1/2 left-0 -translate-y-1/2 -translate-x-1/2 w-96 h-96 bg-[#0d47a1]/5 rounded-full blur-3xl" />
            <div className="absolute bottom-0 right-0 translate-y-1/3 translate-x-1/3 w-80 h-80 bg-[#F57C00]/5 rounded-full blur-3xl" />
          </section>
        </>
      )}

      {/* ═══════════════════════════════════════════════════════════
          UPLOAD PORTAL — matches secure-upload-portal/code.html
          ═══════════════════════════════════════════════════════════ */}
      {showUpload && (
        <section id="upload-section" className="min-h-screen pt-24 pb-16 px-6 flex flex-col items-center bg-[#F8FAFC]">
          <div className="w-full max-w-[640px] space-y-8">
            {/* Header */}
            <div className="text-center space-y-2">
              <h1 className="text-2xl font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Import Your Tax Data</h1>
              <p className="text-sm text-[#434652] max-w-md mx-auto">Upload your Form 16 or AIS PDF. Our AI engine will automatically classify and optimize your deductions.</p>
            </div>

            {/* PAN + DOB */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[11px] font-bold uppercase tracking-wider text-[#434652]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>PAN</label>
                <input value={pan} onChange={(e) => setPan(e.target.value.toUpperCase())} placeholder="CFFPM4503N" maxLength={10}
                  className="w-full px-4 py-3 bg-white border border-[#c3c6d4] rounded text-sm font-mono uppercase tracking-widest focus:border-[#003366] focus:ring-1 focus:ring-[#003366] outline-none transition-all" />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-bold uppercase tracking-wider text-[#434652]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Date of Birth</label>
                <input value={dob} onChange={(e) => setDob(e.target.value.replace(/\D/g, ""))} placeholder="DDMMYYYY" maxLength={8}
                  className="w-full px-4 py-3 bg-white border border-[#c3c6d4] rounded text-sm font-mono focus:border-[#003366] focus:ring-1 focus:ring-[#003366] outline-none transition-all" />
              </div>
            </div>

            {/* Form 16 Dropzone */}
            <div className={`relative group cursor-pointer border-2 border-dashed rounded-xl p-8 text-center transition-all ${dragOver ? "border-[#003366] bg-[#e5eeff]" : form16File ? "border-[#166534] bg-green-50/20" : "border-[#c3c6d4] hover:border-[#003366] bg-white"}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f?.name.endsWith(".pdf")) setForm16File(f); }}
              onClick={() => form16Ref.current?.click()}>
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-full bg-[#eff4ff] flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span className="material-symbols-outlined text-[#003366] text-3xl">upload_file</span>
                </div>
                {form16File ? (
                  <>
                    <p className="text-sm font-medium text-[#166534]">✓ {form16File.name}</p>
                    <p className="text-xs text-[#434652]">{(form16File.size / 1024).toFixed(0)} KB</p>
                  </>
                ) : (
                  <>
                    <p className="text-base font-medium text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Drag & drop Form 16 here</p>
                    <p className="text-xs text-[#434652]">PDF format (Max 10MB)</p>
                    <span className="mt-1 px-5 py-2 bg-[#003366] text-white text-sm font-bold rounded hover:opacity-90 transition-all">Browse Files</span>
                  </>
                )}
              </div>
              <input ref={form16Ref} type="file" accept=".pdf" className="absolute inset-0 opacity-0 cursor-pointer" onChange={(e) => setForm16File(e.target.files?.[0] || null)} />
            </div>

            {/* Form 16 Password */}
            {form16File && (
              <div className="space-y-1">
                <label className="text-[11px] font-bold uppercase tracking-wider text-[#434652]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Form 16 Password (if encrypted)</label>
                <input value={form16Password} onChange={(e) => setForm16Password(e.target.value)} placeholder="Usually your PAN — auto-tried if blank"
                  className="w-full px-4 py-3 bg-white border border-[#c3c6d4] rounded text-sm focus:border-[#003366] outline-none transition-all" />
              </div>
            )}

            {/* AIS Dropzone */}
            <div className={`relative border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer ${aisFile ? "border-[#166534] bg-green-50/20" : "border-[#c3c6d4] hover:border-[#003366] bg-white"}`}
              onClick={() => aisRef.current?.click()}>
              <div className="flex flex-col items-center gap-2">
                <div className="w-14 h-14 rounded-full bg-[#eff4ff] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[#003366] text-2xl">description</span>
                </div>
                {aisFile ? (
                  <>
                    <p className="text-sm font-medium text-[#166534]">✓ {aisFile.name}</p>
                    <p className="text-xs text-[#434652]">Password auto-computed from PAN + DOB</p>
                  </>
                ) : (
                  <>
                    <p className="text-sm font-medium text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Drop AIS PDF here</p>
                    <p className="text-xs text-[#434652]">Annual Information Statement (PDF)</p>
                  </>
                )}
              </div>
              <input ref={aisRef} type="file" accept=".pdf" className="absolute inset-0 opacity-0 cursor-pointer" onChange={(e) => setAisFile(e.target.files?.[0] || null)} />
            </div>

            {/* Processing State */}
            {loading && (
              <div className="bg-white border border-[#c3c6d4] rounded-xl p-6 space-y-4 animate-in fade-in">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[#d3e4fe] flex items-center justify-center">
                      <span className="material-symbols-outlined text-[#003178]">picture_as_pdf</span>
                    </div>
                    <div>
                      <p className="text-sm font-bold text-[#0b1c30]">{form16File?.name || "Processing..."}</p>
                      <p className="text-xs text-[#434652]">{stepLabels[processingStep]}</p>
                    </div>
                  </div>
                  <span className="text-sm font-mono text-[#003178]">{progress}%</span>
                </div>
                {/* Progress Bar */}
                <div className="w-full h-2 bg-[#eff4ff] rounded-full overflow-hidden">
                  <div className="h-full bg-[#003366] transition-all duration-300 relative" style={{ width: `${progress}%` }}>
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />
                  </div>
                </div>
                {/* Step indicators */}
                <div className="grid grid-cols-3 gap-2">
                  {["Parsing", "Classification", "Optimization"].map((label, i) => (
                    <div key={label} className={`flex flex-col gap-1 transition-opacity ${processingStep >= i ? "opacity-100" : "opacity-40"}`}>
                      <div className="h-1 bg-[#d3e4fe] rounded-full overflow-hidden">
                        <div className={`h-full bg-[#166534] transition-all ${processingStep > i ? "w-full" : processingStep === i ? "w-1/2 animate-pulse" : "w-0"}`} />
                      </div>
                      <span className="text-[11px] font-bold uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>{label}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="p-4 rounded-xl bg-[#ffdad6] border border-red-200 flex items-start gap-3 text-sm text-[#93000a]">
                <span className="material-symbols-outlined shrink-0 mt-0.5">error</span>
                <span>{error}</span>
              </div>
            )}

            {/* Submit */}
            <button onClick={handleUpload} disabled={loading}
              className="w-full bg-[#003366] text-white py-4 rounded-xl font-semibold text-lg flex items-center justify-center gap-2 shadow-lg hover:shadow-xl hover:opacity-95 active:scale-[0.98] transition-all disabled:opacity-50"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              {loading ? (
                <><span className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" /> Processing...</>
              ) : (
                <><span className="material-symbols-outlined">bolt</span> Start Filing</>
              )}
            </button>

            {/* Trust Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-white border border-[#c3c6d4]/30 rounded-xl flex items-start gap-3">
                <span className="material-symbols-outlined text-[#003366] mt-0.5">verified_user</span>
                <div><p className="text-sm font-bold text-[#003366]">Government Licensed</p><p className="text-xs text-[#434652]">Official ERI licensed by ITD.</p></div>
              </div>
              <div className="p-4 bg-white border border-[#c3c6d4]/30 rounded-xl flex items-start gap-3">
                <span className="material-symbols-outlined text-[#003366] mt-0.5">encrypted</span>
                <div><p className="text-sm font-bold text-[#003366]">Bank-Grade Privacy</p><p className="text-xs text-[#434652]">Auto-deleted after 48 hours.</p></div>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
