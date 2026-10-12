"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { uploadPDFs, uploadBrokerPL, processPDFs, type UploadResponseData } from "@/lib/api";
import { getState, setState } from "@/lib/store";

// ────────────────────────────────────────────────────────────────────────
// Phase 9: DOCUMENT INGESTION & INTAKE UI
// ────────────────────────────────────────────────────────────────────────
// A single-page intake dashboard where users upload:
//   1. Form 16 (Part A & B)      → POST /api/v1/upload
//   2. Annual Information State-  → POST /api/v1/upload
//      ment (AIS)                → POST /api/v1/tax/upload/broker-pl
//   3. Broker P&L                → POST /api/v1/process/{sessionId}
//      (compute bridge)
//
// State management:
//   - sessionId persists in lib/store (AppState) across uploads
//   - uploadStatus tracks per-document state: idle → uploading → success/error
//   - "Compute My Taxes" enables only after ≥1 successful upload
// ────────────────────────────────────────────────────────────────────────

const DEFAULT_FY = "FY2025-26";
const DEFAULT_AY = "AY2026-27";

type DocType = "form16" | "ais" | "broker_pl";

interface UploadStatus {
  state: "idle" | "awaiting" | "uploading" | "success" | "error" | "password_required";
  message?: string;
  passwordRequired?: boolean;
  passwordHint?: string;
}

interface DocCardConfig {
  id: DocType;
  title: string;
  subtitle: string;
  description: string;
  icon: string;
  accepted: string;
  colorFrom: string;
  colorTo: string;
  badgeColor: string;
  hint: string;
}

const DOC_CARDS: Record<DocType, DocCardConfig> = {
  form16: {
    id: "form16",
    title: "Form 16 (Part A & B)",
    subtitle: "Salary income, TDS",
    description: "Upload your employer-issued Form 16 for FY2025-26. Contains Part A (TDS details) and Part B (salary breakup).",
    icon: "fact_check",
    accepted: ".pdf",
    colorFrom: "from-[#003366]",
    colorTo: "to-[#0d47a1]",
    badgeColor: "bg-[#003366]",
    hint: "Download your Form 16 from your employer's HR portal or the TRACES portal (tracer.tdsonline.gov.in).",
  },
  ais: {
    id: "ais",
    title: "Annual Information Statement (AIS)",
    subtitle: "All reportable income",
    description: "A consolidated view of your financial transactions — savings interest, dividends, mutual funds, and more.",
    icon: "receipt_long",
    accepted: ".pdf, .json",
    colorFrom: "from-[#0b7a52]",
    colorTo: "to-[#145a3f]",
    badgeColor: "bg-[#166534]",
    hint: "Log in to incometax.gov.in → Services → AIS (Annual Information Statement) → View/Download AIS.",
  },
  broker_pl: {
    id: "broker_pl",
    title: "Broker P&L",
    subtitle: "Capital gains",
    description: "Upload your broker's P&L statement (e.g., Zerodha Tax P&L, Groww, Upstox). Auto-classifies equity & mutual fund sales.",
    icon: "bar_chart",
    accepted: ".csv, .xlsx, .xls",
    colorFrom: "from-[#b45309]",
    colorTo: "to-[#92400e]",
    badgeColor: "bg-[#F57C00]",
    hint: "Zerodha: Console → Reports → Tax → Tax P&L (CSV). Groww: Profile → Tax Documents. Upstox: Reports → Tax P&L.",
  },
};

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();

  // ── Filing-year metadata ────────────────────────────────────────────
  const fyLabel = DEFAULT_FY;
  const ayLabel = DEFAULT_AY;

  // ── State ────────────────────────────────────────────────────────────
  const [status, setStatus] = useState<string>("idle");
  const [error, setError] = useState("");
  const [sessionData, setSessionData] = useState<UploadResponseData | null>(null);
  const [sessionId, setSessionId] = useState<string>("");

  const [passwords, setPasswords] = useState<Record<DocType, string>>({
    form16: "",
    ais: "",
    broker_pl: "",
  });

  const [uploadStatus, setUploadStatus] = useState<Record<DocType, UploadStatus>>({
    form16: { state: "idle" },
    ais: { state: "idle" },
    broker_pl: { state: "idle" },
  });

  const [draggedFile, setDraggedFile] = useState<{ type: DocType; file: File } | null>(null);

  // Session ID persisted in lib/store so all uploads aggregate in one session
  const storedSessionId = getState().sessionId || "";
  const [pan, setPan] = useState(getState().pan);
  const [dob, setDob] = useState(getState().dob);

  // ── Refs ─────────────────────────────────────────────────────────────
  const fileInputs = useRef<Record<DocType, HTMLInputElement | null>>({
    form16: null,
    ais: null,
    broker_pl: null,
  });

  // ── Lifecycle: redirect if unauthenticated ───────────────────────────
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push(`/auth?redirect=/dashboard`);
      return;
    }
    if (isAuthenticated && storedSessionId) {
      setSessionId(storedSessionId);
      setState({ sessionId: storedSessionId });
    }
  }, [isAuthenticated, authLoading, storedSessionId]);

  // ── Drag & drop handlers (shared across all cards) ───────────────────
  const onDragOver = useCallback((e: React.DragEvent, type: DocType) => {
    e.preventDefault();
    e.stopPropagation();
    setDraggedFile((prev) => (prev?.type === type ? prev : { type, file: prev?.file! }));
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent, type: DocType) => {
    e.preventDefault();
    e.stopPropagation();
    setDraggedFile((prev) => (prev?.type === type ? null : prev));
  }, []);

  const onDrop = useCallback((e: React.DragEvent, type: DocType) => {
    e.preventDefault();
    e.stopPropagation();
    setDraggedFile(null);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(type, files[0]);
    }
  }, []);

  // ── File validation ──────────────────────────────────────────────────
  const validateFile = (file: File, doc: DocType): boolean => {
    const config = DOC_CARDS[doc];
    const validExt = config.accepted.split(",").some((ext) => file.name.toLowerCase().endsWith(ext.trim()));
    if (!validExt) {
      setError(`Unsupported file type for ${config.title}. Please upload a${config.accepted}.`);
      return false;
    }
    const maxSize = doc === "broker_pl" ? 10 * 1024 * 1024 : 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setError(`${config.title} exceeds 10MB limit.`);
      return false;
    }
    return true;
  };

  // ── Handle file selection (click or drop) ────────────────────────────
  const handleFileSelect = (type: DocType, file: File) => {
    if (!validateFile(file, type)) return;
    handleUpload(type, file, storedSessionId);
  };

  // ── Document upload handler ──────────────────────────────────────────
  const handleUpload = async (type: DocType, file: File, session: string) => {
    setUploadStatus((prev) => ({ ...prev, [type]: { state: "uploading", message: "Parsing document..." } }));
    setError("");

    try {
      let result: UploadResponseData;

      if (type === "broker_pl") {
        result = await uploadBrokerPL(file, session, passwords.broker_pl || "zerodha");
      } else if (type === "form16" || type === "ais") {
        if (!pan || !dob) {
          throw new Error("PAN and DOB are required to identify your tax records. Please enter them above.");
        }
        result = await uploadPDFs(pan, dob, type === "form16" ? file : undefined, type === "ais" ? file : undefined, type === "form16" ? passwords.form16 : undefined);
      } else {
        throw new Error("Unknown document type");
      }

      // Persist session across uploads (aggregate in single unified session)
      setSessionId(result.session_id);
      setState({ sessionId: result.session_id });

      setSessionData(result);
      const status = result.status;

      if (status === "parsed") {
        setUploadStatus((prev) => ({
          ...prev,
          [type]: { state: "success", message: "Document parsed successfully. Details synced to your records." },
        }));
      } else if (status === "password_required") {
        setUploadStatus((prev) => ({
          ...prev,
          [type]: { state: "password_required", passwordRequired: true, passwordHint: result.password_hint },
        }));
      } else {
        throw new Error(result.password_hint || "Document could not be parsed. Please verify the file and try again.");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setUploadStatus((prev) => ({ ...prev, [type]: { state: "error", message } }));
      setError(message);
    }
  };

  // ── File input change handler (click-to-upload) ──────────────────────
  const onInputChange = (type: DocType) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(type, file);
  };

  // ── Password change handler ──────────────────────────────────────────
  const onPasswordChange = (type: DocType) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setPasswords((prev) => ({ ...prev, [type]: e.target.value }));
  };

  // ── Clear status after error auto-dismiss ────────────────────────────
  useEffect(() => {
    if (uploadStatus.form16.state === "error" || uploadStatus.ais.state === "error" || uploadStatus.broker_pl.state === "error") {
      const timer = setTimeout(() => {
        setUploadStatus((prev) => {
          const next = { ...prev };
          if (prev.form16.message === error) next.form16.state = "idle";
          if (prev.ais.message === error) next.ais.state = "idle";
          if (prev.broker_pl.message === error) next.broker_pl.state = "idle";
          return next;
        });
        setError("");
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, uploadStatus]);

  // ── Computation bridge ───────────────────────────────────────────────
  const hasSuccessfulUpload =
    uploadStatus.form16.state === "success" || uploadStatus.ais.state === "success" || uploadStatus.broker_pl.state === "success";

  const handleCompute = async () => {
    if (!sessionId) {
      setError("No documents uploaded yet. Please upload at least one document first.");
      return;
    }
    setUploadStatus((prev) => ({ ...prev, form16: { ...prev.form16, state: "uploading", message: "Computing your taxes..." } }));
    try {
      const result = await processPDFs(sessionId);
      // Redirect to summary page with the session ID
      router.push(`/summary?session=${sessionId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tax computation failed. Please try again.");
      setUploadStatus((prev) => ({ ...prev, form16: { ...prev.form16, state: "idle" } }));
    }
  };

  // ── Status badge helper ──────────────────────────────────────────────
  const StatusBadge = ({ state }: { state: UploadStatus["state"] }) => {
    const configs: Record<UploadStatus["state"], { label: string; icon: string; color: string; ring: string }> = {
      idle: { label: "Awaiting Upload", icon: "upload_file", color: "text-[#6b7280]", ring: "ring-gray-300" },
      awaiting: { label: "Awaiting Upload", icon: "upload_file", color: "text-[#6b7280]", ring: "ring-gray-300" },
      uploading: { label: "Parsing...", icon: "sync", color: "text-[#003366]", ring: "ring-blue-300" },
      success: { label: "Successfully Parsed", icon: "check_circle", color: "text-[#166534]", ring: "ring-green-300" },
      error: { label: "Failed", icon: "error", color: "text-[#991B1B]", ring: "ring-red-300" },
      password_required: { label: "Password Required", icon: "password", color: "text-[#92400E]", ring: "ring-amber-300" },
    };
    const cfg = configs[state] || configs.idle;

    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-gray-50 ${cfg.color} ${cfg.ring} ring-1`}>
        <span className="material-symbols-outlined text-sm">{cfg.icon}</span>
        {cfg.label}
      </span>
    );
  };

  // ── Loading ──────────────────────────────────────────────────────────
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-[#eff4ff] mx-auto flex items-center justify-center">
            <span className="material-symbols-outlined text-[#003366] text-3xl animate-spin">sync</span>
          </div>
          <p className="text-sm text-[#434652]">Loading your tax intake...</p>
        </div>
      </div>
    );
  }

  // ── Main Layout ──────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#F8FAFC] pb-24">
      {/* ── Header: Tax Intake + Progress ───────────────────────────────── */}
      <div className="bg-gradient-to-r from-[#003366] to-[#0d47a1] text-white shadow-lg">
        <div className="max-w-[1120px] mx-auto px-6 md:px-10 py-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Tax Intake {fyLabel}</h1>
                <span className="px-2.5 py-0.5 bg-white/15 rounded-full text-[10px] font-bold uppercase tracking-wider">
                  {ayLabel}
                </span>
              </div>
              <p className="text-sm text-[#B0C6FF] mt-1">Upload your tax documents. We&apos;ll compute and compare your tax automatically.</p>
            </div>
            {/* Progress Indicator */}
            <div className="flex items-center gap-4 bg-white/10 rounded-xl px-4 py-2.5 backdrop-blur-sm border border-white/15">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[#FFD54F] text-base">progress_activity</span>
                <div>
                  <p className="text-[10px] text-[#B0C6FF] uppercase tracking-wider">Progress</p>
                  <p className="text-sm font-bold">
                    {hasSuccessfulUpload ? "Ready to Compute" : "Upload Documents"}
                  </p>
                </div>
              </div>
              <div className="w-24 h-2 bg-white/20 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#F57C00] transition-all duration-500"
                  style={{ width: hasSuccessfulUpload ? "100%" : "33%" }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Error Toast ──────────────────────────────────────────────────── */}
      {error && (
        <div className="max-w-[1120px] mx-auto px-6 md:px-10 mt-4">
          <div className="bg-[#ffdad6] border border-red-200 rounded-xl p-4 flex items-start gap-3 animate-[slideIn_0.3s_ease-out]">
            <span className="material-symbols-outlined text-[#991B1B] text-xl shrink-0 mt-0.5">error</span>
            <div className="flex-1">
              <p className="text-sm font-semibold text-[#991B1B]">Upload failed</p>
              <p className="text-xs text-[#7f1d1d] mt-0.5">{error}</p>
            </div>
            <button onClick={() => setError("")} className="text-[#991B1B] hover:text-[#7f1d1d]">
              <span className="material-symbols-outlined text-lg">close</span>
            </button>
          </div>
        </div>
      )}

      {/* ── PAN & DOB Entry (inline) ─────────────────────────────────────── */}
      <div className="max-w-[1120px] mx-auto px-6 md:px-10 mt-6">
        <div className="bg-white border border-[#E2E8F0] rounded-xl p-5">
          <h2 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-3 flex items-center gap-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
            <span className="material-symbols-outlined text-base">person</span> Taxpayer Details
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold text-[#434652] uppercase tracking-wider mb-1.5" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>PAN</label>
              <input
                type="text"
                placeholder="ABCDE1234F"
                value={pan}
                onChange={(e) => setPan(e.target.value.toUpperCase())}
                className="w-full px-4 py-2.5 border border-[#E2E8F0] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#003366] focus:border-transparent font-mono"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-[#434652] uppercase tracking-wider mb-1.5" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Date of Birth (DDMMYYYY)</label>
              <input
                type="text"
                placeholder="01011990"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                className="w-full px-4 py-2.5 border border-[#E2E8F0] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#003366] focus:border-transparent font-mono"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              />
            </div>
            <div className="flex items-end">
              <p className="text-xs text-[#737783]">Required to locate your Form 16 and compute your AIS password from the Income Tax portal.</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Upload Grid ──────────────────────────────────────────────────── */}
      <div className="max-w-[1120px] mx-auto px-6 md:px-10 mt-6">
        <h2 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-4" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Upload Documents</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {(Object.keys(DOC_CARDS) as DocType[]).map((key) => {
            const card = DOC_CARDS[key];
            const docStatus = uploadStatus[key];
            const isDragged = draggedFile?.type === key;
            const isError = docStatus.state === "error";
            const isPasswordRequired = docStatus.state === "password_required";

            return (
              <div
                key={card.id}
                onDragOver={(e) => onDragOver(e, key)}
                onDragLeave={(e) => onDragLeave(e, key)}
                onDrop={(e) => onDrop(e, key)}
                className={`relative bg-white border-2 rounded-2xl p-6 transition-all duration-200 group ${
                  isDragged ? "border-[#F57C00] bg-[#FFFBF0] shadow-lg" : isError ? "border-[#ef4444]" : "border-[#E2E8F0] hover:border-[#003366] hover:shadow-md"
                }`}
              >
                {/* Status Badge (top-right) */}
                <div className="absolute top-4 right-4 z-10">
                  <StatusBadge state={docStatus.state} />
                </div>

                {/* Document Type / Icon */}
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${card.colorFrom} ${card.colorTo} flex items-center justify-center mb-4 shadow-lg`}>
                  <span className="material-symbols-outlined text-white text-2xl">{card.icon}</span>
                </div>

                {/* Title & Subtitle */}
                <h3 className="text-lg font-bold text-[#0b1c30] mb-0.5" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>{card.title}</h3>
                <p className="text-xs font-bold text-[#434652] uppercase tracking-wider mb-2">{card.subtitle}</p>

                {/* Description */}
                <p className="text-sm text-[#434652] mb-4 leading-relaxed">{card.description}</p>

                {/* Drop Zone */}
                <div
                  className={`border-2 border-dashed rounded-xl p-4 text-center transition-all ${
                    isDragged ? "border-[#F57C00] bg-[#FFF7E6]" : "border-[#E2E8F0] group-hover:border-[#003366]/40 group-hover:bg-[#EFF4FF]"
                  }`}
                >
                  {docStatus.state === "uploading" ? (
                    <div className="flex flex-col items-center gap-2">
                      <span className="material-symbols-outlined text-[#003366] text-2xl animate-spin">sync</span>
                      <p className="text-xs text-[#003366] font-medium">{docStatus.message || "Parsing document..."}</p>
                    </div>
                  ) : isError ? (
                    <div className="flex flex-col items-center gap-2">
                      <span className="material-symbols-outlined text-[#ef4444] text-2xl">error</span>
                      <p className="text-xs text-[#991B1B] font-medium">{docStatus.message}</p>
                    </div>
                  ) : docStatus.state === "success" ? (
                    <div className="flex flex-col items-center gap-2">
                      <span className="material-symbols-outlined text-[#166534] text-2xl">check_circle</span>
                      <p className="text-xs text-[#166534] font-medium">{docStatus.message}</p>
                    </div>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-[#003366] text-3xl mb-2">cloud_upload</span>
                      <p className="text-sm font-semibold text-[#0b1c30] mb-1">Drag & drop here</p>
                      <p className="text-xs text-[#737783] mb-3">or click to browse ({card.accepted})</p>
                      <button
                        onClick={() => fileInputs.current[key]?.click()}
                        className="px-4 py-2 bg-[#003366] text-white rounded-lg text-sm font-semibold hover:bg-[#0d47a1] transition-all"
                        style={{ fontFamily: "var(--font-hanken-grotesk)" }}
                      >
                        Select File
                      </button>
                    </>
                  )}
                </div>

                {/* Password Input (Form 16 / AIS) */}
                {(key === "form16" || key === "ais") && (
                  <div className="mt-4">
                    <label className="block text-xs font-bold text-[#434652] uppercase tracking-wider mb-1.5 flex items-center gap-1.5" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                      <span className="material-symbols-outlined text-sm">lock</span> PDF Password (optional)
                    </label>
                    <div className="relative">
                      <input
                        type={passwords[key as "form16" | "ais"] ? "text" : "password"}
                        placeholder="PAN + DOB (e.g., ABCDE1234F01011990)"
                        value={passwords[key as "form16" | "ais"]}
                        onChange={onPasswordChange(key)}
                        className="w-full pl-4 pr-10 py-2.5 border border-[#E2E8F0] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#003366] focus:border-transparent font-mono"
                        style={{ fontFamily: "var(--font-hanken-grotesk)" }}
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[#737783] text-sm">
                        {passwords[key as "form16" | "ais"] ? "show" : "hide"}
                      </span>
                    </div>
                    {isPasswordRequired && card.id === "form16" && docStatus.passwordHint && (
                      <p className="text-xs text-[#92400E] mt-1.5 flex items-start gap-1.5">
                        <span className="material-symbols-outlined text-sm shrink-0 mt-0.5">info</span>
                        <span>{docStatus.passwordHint}</span>
                      </p>
                    )}
                  </div>
                )}

                {/* Hint / Location Helper */}
                <div className="mt-4 pt-4 border-t border-[#E2E8F0]">
                  <p className="text-[10px] text-[#737783] leading-relaxed flex items-start gap-1.5">
                    <span className="material-symbols-outlined text-sm shrink-0 mt-0.5">help</span>
                    <span>{card.hint}</span>
                  </p>
                </div>

                {/* Hidden file input */}
                <input
                  ref={(el) => {
                    fileInputs.current[key] = el;
                  }}
                  type="file"
                  accept={card.accepted}
                  onChange={onInputChange(key)}
                  className="hidden"
                />
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Computation Bridge ───────────────────────────────────────────── */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-[#E2E8F0] shadow-2xl p-4 z-40">
        <div className="max-w-[1120px] mx-auto px-6 md:px-10">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                {hasSuccessfulUpload
                  ? "Documents ready — compute your tax now"
                  : "Upload at least one document to enable tax computation"}
              </p>
              <p className="text-xs text-[#734652] mt-0.5">We&apos;ll classify income, optimize your regime, and generate your ITR.</p>
            </div>
            <button
              onClick={handleCompute}
              disabled={!hasSuccessfulUpload || status !== "idle"}
              className="w-full md:w-auto px-8 py-4 bg-[#F57C00] text-white rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg hover:bg-[#E67600] disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              {uploadStatus.form16.state === "uploading" && !hasSuccessfulUpload ? (
                <>
                  <span className="animate-spin text-xl">sync</span> Computing...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-xl">bolt</span>
                  Compute My Taxes
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
