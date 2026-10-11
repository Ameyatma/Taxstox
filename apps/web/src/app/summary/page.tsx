"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { exportITR, processPDFs, type TaxSummaryData, type ExportData } from "@/lib/api";
import { getState, setState } from "@/lib/store";

// ────────────────────────────────────────────────────────────────────────
// Phase 8: FULL TAX SUMMARY UX
// ────────────────────────────────────────────────────────────────────────
// Components (in order of appearance):
//   1. Header summary          → Taxpayer PAN | Assessment Year | Recommended Regime badge
//   2. Regime comparison widget → New vs Old Regime total tax + savings highlight
//   3. Schedule breakdown grid  → Income | Capital Gains | Deductions | Net Tax/Refund
//   4. Primary action button    → "Download ITR-2 JSON" (browser download)
//   5. Offline filing guide     → 4-step Zerodha-model guide card
// ────────────────────────────────────────────────────────────────────────

// Default fiscal year used by the app (FY2025-26 → AY2026-27)
const DEFAULT_FY_LABEL = "FY2025-26";
const DEFAULT_AY_LABEL = "AY2026-27";

function SummaryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  // Defensive session resolution: support both "session" and "sessionId"
  // query params (Phase 10 rehydration hardening), then fall back to the
  // in-memory store so a page reload never wipes tax calculations.
  const sessionId =
    searchParams.get("session") ||
    searchParams.get("sessionId") ||
    getState().sessionId;
  const pan = getState().pan;

  const [summary, setSummary] = useState<TaxSummaryData | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportData, setExportData] = useState<ExportData | null>(null);
  const [error, setError] = useState("");
  const [downloaded, setDownloaded] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);
  const [missing, setMissing] = useState(false);
  const [rehydrating, setRehydrating] = useState(false);

  useEffect(() => {
    const cached = getState().taxSummary;
    if (cached) {
      setSummary(cached as unknown as TaxSummaryData);
    } else if (!sessionId) {
      setMissing(true);
    } else {
      // Session exists but the in-memory summary was lost — re-run
      // computation so the page reload does not wipe tax calculations.
      setRehydrating(true);
      processPDFs(sessionId)
        .then((res) => {
          // Persist the fresh summary into the store so subsequent
          // navigation (e.g. export) sees the same data.
          setState({ taxSummary: res as unknown as Record<string, unknown> });
          setSummary(res as unknown as TaxSummaryData);
        })
        .catch((err) => {
          setError(err.message || "Failed to rehydrate tax summary");
        })
        .finally(() => setRehydrating(false));
    }
  }, []);

  // ── Filing-year helpers ─────────────────────────────────────────────
  // Financial Year FY2025-26 ⇒ Assessment Year AY2026-27.
  // The ITR JSON filename uses the "2026_27" (underscored) form per CBDT naming.
  function fyLabel(): string {
    return sessionMetadata.fyLabel || DEFAULT_FY_LABEL;
  }
  function ayLabel(): string {
    return sessionMetadata.ayLabel || DEFAULT_AY_LABEL;
  }
  function ayFilenameSuffix(): string {
    // "2026_27" style suffix for the download filename.
    const ay = ayLabel().replace("AY", "").replace(/-/g, "_");
    return ay.replace(/\s+/g, "");
  }

  async function handleDownload() {
    if (!sessionId) return;
    const filename = `${pan}_ITR-2_AY${ayFilenameSuffix()}.json`;

    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/tax/export/${sessionId}`, {
      credentials: "include",
    });

    if (!res.ok) {
      throw new Error(await res.text());
    }

    // The GET export endpoint returns a plain JSON blob with a
    // Content-Disposition header. Build the blob manually so the exact
    // filename (PAN_ITR-2_AY2026_27.json) is used by the browser.
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  async function handleExport() {
    setExporting(true);
    setError("");
    try {
      const data = await exportITR(sessionId!);
      setExportData(data);
      setDownloaded(true);
      setShowInstructions(true);

      const blob = new Blob([JSON.stringify(data.json_data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = data.filename;
      document.body.appendChild(a); a.click();
      document.body.removeChild(a); URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExporting(false);
    }
  }

  // ── Loading ─────────────────────────────────────────────────────────
  if (!summary) {
    if (missing) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
          <div className="text-center space-y-4 max-w-md px-6">
            <div className="w-16 h-16 rounded-full bg-[#ffdad6] mx-auto flex items-center justify-center">
              <span className="material-symbols-outlined text-[#991B1B] text-3xl">error</span>
            </div>
            <h2 className="text-xl font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Session not found</h2>
            <p className="text-sm text-[#434652]">We couldn&apos;t find your tax computation. Please start a new filing.</p>
            <button onClick={() => router.push("/")} className="px-6 py-3 bg-[#003366] text-white rounded-lg font-semibold">Start Over</button>
          </div>
        </div>
      );
    }
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-[#eff4ff] mx-auto flex items-center justify-center">
            <span className="material-symbols-outlined text-[#003366] text-3xl animate-spin">sync</span>
          </div>
          <h2 className="text-xl font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Computing Your Tax</h2>
          <p className="text-sm text-[#434652]">Running regime optimizer with your inputs...</p>
        </div>
      </div>
    );
  }

  // ── Derived values (defensive: coerce Decimals / strings to numbers) ──
  const toNum = (v: any): number => {
    if (typeof v === "number") return v;
    if (typeof v === "object" && v !== null) return Number(v) || 0;
    return Number(v) || 0;
  };
  const balancePayable = Math.round(toNum(summary.balance_payable || 0));
  const regimeSavings = Math.round(toNum(summary.regime_savings || 0));
  const taxableIncome = Math.round(toNum(summary.taxable_income || 0));
  const grossTotal = Object.values(summary.income || {}).reduce((s: number, v: any) => s + toNum(v), 0);
  const totalDeductions = Object.values(summary.deductions || {}).reduce((s: number, v: any) => s + toNum(v), 0);
  const isNew = summary.regime === "new";
  const oldBreakdown: Record<string, number> = (summary as any).old_regime_breakdown || {};
  const newBreakdown: Record<string, number> = (summary as any).new_regime_breakdown || {};
  const showComparison = Object.keys(oldBreakdown).length > 0 && Object.keys(newBreakdown).length > 0;

  const oldTotalTax = Math.round(toNum(oldBreakdown.tax_slab || 0)) +
                      Math.round(toNum(oldBreakdown.surcharge || 0)) +
                      Math.round(toNum(oldBreakdown.cess || 0)) -
                      Math.round(toNum(oldBreakdown.rebate87a || 0));
  const newTotalTax = Math.round(toNum(newBreakdown.tax_slab || 0)) +
                      Math.round(toNum(newBreakdown.surcharge || 0)) +
                      Math.round(toNum(newBreakdown.cess || 0)) -
                      Math.round(toNum(newBreakdown.rebate87a || 0));

  const sessionMetadata = { fyLabel: DEFAULT_FY_LABEL, ayLabel: DEFAULT_AY_LABEL };

  // ── Schedule breakdown cards ────────────────────────────────────────
  const scheduleCards = [
    {
      title: "Income",
      icon: "payments",
      amount: grossTotal,
      sub: `Gross total income for ${fyLabel()}`,
      color: "blue",
      items: Object.entries(summary.income || {}).slice(0, 4),
    },
    {
      title: "Capital Gains",
      icon: "trending_up",
      amount: Math.round(toNum(summary.income?.["Capital Gains"] || 0)),
      sub: "Long/Short-term gains (AIS + broker)",
      color: "indigo",
      items: [],
    },
    {
      title: "Deductions",
      icon: "savings",
      amount: totalDeductions,
      sub: `Exemptions under ${isNew ? "New" : "Old"} Regime`,
      color: "green",
      items: Object.entries(summary.deductions || {}).slice(0, 4),
    },
    {
      title: `Net ${balancePayable >= 0 ? "Payable" : "Refund"}`,
      icon: "account_balance_wallet",
      amount: Math.abs(balancePayable),
      sub: `${balancePayable >= 0 ? "Payable" : "Refundable"} after TDS`,
      color: balancePayable >= 0 ? "amber" : "green",
      items: Object.entries(summary.payments || {}),
    },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] pb-20">
      {/* ── 1. Header summary: PAN | Assessment Year | Recommended Regime badge ── */}
      <div className="sticky top-0 z-40 bg-gradient-to-r from-[#003366] to-[#0d47a1] text-white shadow-lg">
        <div className="max-w-[1120px] mx-auto px-6 md:px-10 py-5">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2.5">
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 rounded-lg backdrop-blur-sm border border-white/15">
                  <span className="material-symbols-outlined text-sm text-[#B0C6FF]">qr_code_2</span>
                  <span className="text-[11px] font-bold text-[#B0C6FF] tracking-wider uppercase">PAN</span>
                  <span className="ml-1.5 text-sm font-mono font-bold tracking-widest">{pan || "XXXXXXXXXX"}</span>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 rounded-lg backdrop-blur-sm border border-white/15">
                  <span className="material-symbols-outlined text-sm text-[#B0C6FF]">calendar_today</span>
                  <span className="text-[11px] font-bold text-[#B0C6FF] tracking-wider uppercase">Assessment Year</span>
                  <span className="ml-1.5 text-sm font-mono font-bold">{ayLabel()}</span>
                  <span className="text-[11px] text-[#8FA8D0] ml-1">({fyLabel()})</span>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#F57C00] rounded-lg shadow-lg shadow-orange-500/20 border border-orange-400/30">
                  <span className="material-symbols-outlined text-sm">verified</span>
                  <span className="text-[11px] font-bold text-white tracking-wider uppercase">Recommended Regime</span>
                  <span className="ml-1.5 text-sm font-bold">{isNew ? "NEW Regime" : "OLD Regime"}</span>
                </div>
              </div>
              <p className="text-sm text-[#B0C6FF] ml-1">FY {fyLabel()} (AY {ayLabel()}) — review before export.</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right hidden md:block">
                <p className="text-[11px] text-[#B0C6FF] uppercase tracking-wider">Step</p>
                <p className="text-lg font-bold">4 of 5</p>
              </div>
              <button onClick={() => window.print()} className="flex items-center gap-1.5 px-4 py-2.5 bg-white/10 text-white rounded-lg text-sm font-semibold border border-white/15 hover:bg-white/20 transition-all">
                <span className="material-symbols-outlined text-sm">print</span> Print
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── 2. Regime comparison widget: New vs Old + savings highlight ── */}
      <div className="max-w-[1120px] mx-auto px-6 md:px-10 py-6">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#0d47a1] to-[#1565C0] p-6 md:p-8 text-white shadow-2xl mb-6">
          <div className="absolute top-0 right-0 w-40 h-40 opacity-10">
            <span className="material-symbols-outlined text-[160px]">compare_arrows</span>
          </div>
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-[#FFD54F]">analytics</span>
              <h2 className="text-lg font-bold uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Regime Comparison</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white/10 rounded-xl p-4 border border-white/10 backdrop-blur-sm">
                <p className="text-[11px] font-bold text-[#B0C6FF] uppercase tracking-wider mb-1">Old Regime</p>
                <p className="text-2xl font-bold font-mono">₹{Math.max(0, oldTotalTax).toLocaleString("en-IN")}</p>
                <p className="text-[11px] text-[#B0C6FF] mt-1">With all deductions & exemptions</p>
              </div>
              <div className="bg-white/10 rounded-xl p-4 border border-white/10 backdrop-blur-sm">
                <p className="text-[11px] font-bold text-[#B0C6FF] uppercase tracking-wider mb-1">New Regime</p>
                <p className="text-2xl font-bold font-mono">₹{Math.max(0, newTotalTax).toLocaleString("en-IN")}</p>
                <p className="text-[11px] text-[#B0C6FF] mt-1">Simplified slabs, fewer deductions</p>
              </div>
              <div className={`rounded-xl p-4 border-2 backdrop-blur-sm ${
                regimeSavings > 0
                  ? "bg-[#166534] border-[#4CAF50] shadow-lg shadow-green-500/30"
                  : "bg-white/10 border-white/10"
              }`}>
                <p className="text-[11px] font-bold text-[#C8E6C9] uppercase tracking-wider mb-1">
                  {regimeSavings > 0 ? "Switch to" : "Both regimes equal"}
                </p>
                <p className={`text-2xl font-bold font-mono ${regimeSavings > 0 ? "text-white" : "text-[#C8E6C9]"}`}>
                  {regimeSavings > 0 ? `Save ₹${regimeSavings.toLocaleString("en-IN")}` : "₹0"}
                </p>
                <p className="text-[11px] text-[#C8E6C9] mt-1">
                  {regimeSavings > 0
                    ? `${isNew ? "New" : "Old"} regime is best for you`
                    : "No financial advantage either way"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Full side-by-side comparison table */}
        {showComparison && (
          <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 mb-6 overflow-x-auto">
            <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-4 flex items-center gap-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              <span className="material-symbols-outlined text-base">table_view</span>
              Full Breakdown — Old vs New
            </h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#E2E8F0] text-left">
                  <th className="py-2 pr-4 text-[11px] font-bold text-[#434652] uppercase tracking-wider">Line Item</th>
                  <th className="py-2 pr-4 text-right text-[11px] font-bold text-[#003366] uppercase tracking-wider">Old Regime</th>
                  <th className="py-2 text-right text-[11px] font-bold text-[#166534] uppercase tracking-wider">New Regime</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {[
                  { label: "Gross Salary", ok: "gross_salary", nk: "gross_salary" },
                  { label: "Less: HRA Exemption", ok: "hra_exemption", nk: "hra_exemption", isDed: true },
                  { label: "Less: Standard Deduction", ok: "std_deduction", nk: "std_deduction", isDed: true },
                  { label: "Income from Salary", ok: "income_salary", nk: "income_salary", bold: true },
                  { label: "Capital Gains", ok: "income_cg", nk: "income_cg" },
                  { label: "Interest Income", ok: "income_interest", nk: "income_interest" },
                  { label: "Gross Total Income", ok: "gross_total", nk: "gross_total", bold: true },
                  { label: "Less: Total Deductions", ok: "deductions_total", nk: "deductions_total", isDed: true },
                  { label: "Total Taxable Income", ok: "total_income", nk: "total_income", bold: true },
                ].map((row) => {
                  const ov = Math.round(toNum(oldBreakdown[row.ok]));
                  const nv = Math.round(toNum(newBreakdown[row.nk]));
                  return (
                    <tr key={row.label} className={row.bold ? "bg-[#F8FAFC] font-semibold" : ""}>
                      <td className="py-2 pr-4 text-[#0b1c30]">{row.label}</td>
                      <td className={`py-2 pr-4 text-right font-mono text-xs ${row.isDed ? "text-[#991B1B]" : ""}`}>
                        {row.isDed ? "-" : ""}₹{ov.toLocaleString("en-IN")}
                      </td>
                      <td className={`py-2 text-right font-mono text-xs ${row.isDed ? "text-[#991B1B]" : ""}`}>
                        {row.isDed ? "-" : ""}₹{nv.toLocaleString("en-IN")}
                      </td>
                    </tr>
                  );
                })}
                <tr className="border-t-2 border-[#E2E8F0] bg-[#F8FAFC]">
                  <td className="py-2 pr-4 font-semibold text-[#0b1c30]">Tax on Slab Income</td>
                  <td className="py-2 pr-4 text-right font-mono text-xs font-semibold">₹{Math.round(toNum(oldBreakdown.tax_slab)).toLocaleString("en-IN")}</td>
                  <td className="py-2 text-right font-mono text-xs font-semibold">₹{Math.round(toNum(newBreakdown.tax_slab)).toLocaleString("en-IN")}</td>
                </tr>
                <tr className="bg-[#F8FAFC]">
                  <td className="py-2 pr-4 text-[#0b1c30]">+ Surcharge</td>
                  <td className="py-2 pr-4 text-right font-mono text-xs">₹{Math.round(toNum(oldBreakdown.surcharge)).toLocaleString("en-IN")}</td>
                  <td className="py-2 text-right font-mono text-xs">₹{Math.round(toNum(newBreakdown.surcharge)).toLocaleString("en-IN")}</td>
                </tr>
                <tr className="bg-[#F8FAFC]">
                  <td className="py-2 pr-4 text-[#0b1c30]">+ HEC @ 4%</td>
                  <td className="py-2 pr-4 text-right font-mono text-xs">₹{Math.round(toNum(oldBreakdown.cess)).toLocaleString("en-IN")}</td>
                  <td className="py-2 text-right font-mono text-xs">₹{Math.round(toNum(newBreakdown.cess)).toLocaleString("en-IN")}</td>
                </tr>
                <tr className="bg-[#003366]">
                  <td className="py-2 pr-4 font-bold text-white">Total Tax</td>
                  <td className="py-2 pr-4 text-right font-mono text-xs font-bold text-white">₹{Math.max(0, oldTotalTax).toLocaleString("en-IN")}</td>
                  <td className="py-2 text-right font-mono text-xs font-bold text-white">₹{Math.max(0, newTotalTax).toLocaleString("en-IN")}</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {/* ── 3. Schedule breakdown grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {scheduleCards.map((card) => {
            const colorStyles: Record<string, string> = {
              blue: "from-blue-50 to-blue-100 border-blue-300",
              indigo: "from-indigo-50 to-indigo-100 border-indigo-300",
              green: "from-green-50 to-green-100 border-green-300",
              amber: "from-amber-50 to-amber-100 border-amber-300",
            };
            const iconColors: Record<string, string> = {
              blue: "text-blue-600",
              indigo: "text-indigo-600",
              green: "text-green-600",
              amber: "text-amber-600",
            };
            const amountColor: Record<string, string> = {
              blue: "text-blue-700",
              indigo: "text-indigo-700",
              green: "text-green-700",
              amber: "text-amber-700",
            };
            return (
              <div key={card.title} className={`bg-gradient-to-br ${colorStyles[card.color]} border rounded-xl p-4 hover:shadow-lg transition-all`}>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`material-symbols-outlined text-base ${iconColors[card.color]}`}>{card.icon}</span>
                  <h3 className="text-sm font-bold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>{card.title}</h3>
                </div>
                <p className={`text-2xl font-bold font-mono ${amountColor[card.color]}`}>₹{card.amount.toLocaleString("en-IN")}</p>
                <p className="text-[11px] text-[#434652] mt-1">{card.sub}</p>
                {card.items.length > 0 && (
                  <div className="mt-3 space-y-1.5">
                    {card.items.map(([label, amount]: [string, any]) => (
                      <div key={label} className="flex justify-between text-[11px]">
                        <span className="text-[#434652]">{label}</span>
                        <span className="font-mono font-medium">₹{toNum(amount).toLocaleString("en-IN")}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Schedule detail cards ────────────────────────────────────────── */}
      <div className="max-w-[1120px] mx-auto px-6 md:px-10 pb-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Income card */}
          <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 hover:border-[#003366] transition-all">
            <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-4 flex items-center gap-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              <span className="material-symbols-outlined text-base">payments</span> Income Summary
            </h3>
            <div className="space-y-3">
              {Object.entries(summary.income || {}).map(([label, amount]) => (
                <div key={label} className="flex justify-between text-sm">
                  <span className="text-[#434652]">{label}</span>
                  <span className="font-mono font-medium">₹{toNum(amount).toLocaleString("en-IN")}</span>
                </div>
              ))}
              <hr className="border-dashed border-[#E2E8F0]" />
              <div className="flex justify-between text-sm font-bold">
                <span className="text-[#0b1c30]">Gross Total Income</span>
                <span className="font-mono">₹{grossTotal.toLocaleString("en-IN")}</span>
              </div>
            </div>
          </div>

          {/* Deductions card */}
          <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 hover:border-[#003366] transition-all">
            <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-4 flex items-center gap-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              <span className="material-symbols-outlined text-base">savings</span> Deduction Details
            </h3>
            {Object.keys(summary.deductions || {}).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(summary.deductions || {}).map(([label, amount]) => (
                  <div key={label} className="flex justify-between text-sm">
                    <span className="text-[#434652]">{label}</span>
                    <span className="font-mono text-[#166534]">- ₹{toNum(amount).toLocaleString("en-IN")}</span>
                  </div>
                ))}
                <hr className="border-dashed border-[#E2E8F0]" />
                <div className="flex justify-between text-sm font-bold">
                  <span className="text-[#0b1c30]">Total Deductions</span>
                  <span className="font-mono text-[#166534]">- ₹{totalDeductions.toLocaleString("en-IN")}</span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-[#737783] italic">No deductions applicable</p>
            )}
          </div>
        </div>

        <div className="mt-6 bg-white border border-[#E2E8F0] rounded-xl p-6 hover:border-[#003366] transition-all">
          <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-4 flex items-center gap-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
            <span className="material-symbols-outlined text-base">calculate</span> Tax Computation ({isNew ? "New" : "Old"} Regime)
          </h3>
          <div className="space-y-3">
            {Object.entries(summary.tax_breakdown || {}).map(([label, amount]) => (
              <div key={label} className="flex justify-between text-sm">
                <span className="text-[#434652]">{label}</span>
                <span className="font-mono">₹{toNum(amount).toLocaleString("en-IN")}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right column: result + payments + primary action + filing guide ── */}
      <div className="max-w-[1120px] mx-auto px-6 md:px-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4 space-y-6">
            {/* Computation result */}
            <div className={`bg-white rounded-xl p-6 border-l-4 ${
              balancePayable > 0 ? "border-l-[#92400E]" : "border-l-[#166534]"
            } border border-[#E2E8F0]`}>
              <span className="text-[11px] font-bold text-[#737783] uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Computation Result</span>
              <div className="flex items-baseline gap-2 mt-2 mb-1">
                <h2 className={`text-3xl font-bold ${
                  balancePayable > 0 ? "text-[#92400E]" : "text-[#166534]"
                }`} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                  ₹{Math.abs(balancePayable).toLocaleString("en-IN")}
                </h2>
                <span className={`text-lg font-semibold ${
                  balancePayable > 0 ? "text-[#92400E]" : "text-[#166534]"
                }`} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                  {balancePayable > 0 ? "PAYABLE" : "REFUND"}
                </span>
              </div>
              <p className="text-xs text-[#434652]">
                {balancePayable > 0
                  ? `You owe ₹${balancePayable.toLocaleString("en-IN")}. Pay via e-Pay Tax before filing.`
                  : "TDS covers your liability. No additional payment needed."}
              </p>
            </div>

            {/* Payments */}
            <div className="bg-white border border-[#E2E8F0] rounded-xl p-6">
              <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-3" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Payments (TDS)</h3>
              <div className="space-y-2">
                {Object.entries(summary.payments || {}).map(([label, amount]) => (
                  <div key={label} className="flex justify-between text-sm">
                    <span className="text-[#434652]">{label}</span>
                    <span className="font-mono">₹{toNum(amount).toLocaleString("en-IN")}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* ── 4. Primary action: Download ITR-2 JSON ── */}
            <div className="bg-gradient-to-br from-[#003366] to-[#0d47a1] rounded-xl p-6 space-y-4 shadow-xl">
              <h3 className="text-sm font-bold text-[#B0C6FF] uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Export Return</h3>
              <p className="text-xs text-[#B0C6FF]">
                Download the CBDT-compliant ITR-2 JSON file ({ayLabel()}) for offline filing on the Income Tax portal.
              </p>
              <button
                onClick={handleDownload}
                disabled={exporting || !!downloaded}
                className="w-full bg-[#F57C00] text-white py-4 rounded-xl font-bold flex items-center justify-center gap-3 shadow-lg hover:-translate-y-0.5 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                {exporting ? (
                  <><span className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" /> Generating...</>
                ) : downloaded ? (
                  <><span className="material-symbols-outlined">check_circle</span> Downloaded</>
                ) : (
                  <><span className="material-symbols-outlined">download</span> Download ITR-2 JSON</>
                )}
              </button>
              <p className="text-[10px] text-[#8FA8D0] text-center">
                Filename: {pan}_ITR-2_AY{ayFilenameSuffix()}.json
              </p>
            </div>

            {/* ── 5. Offline filing guide: 4-step Zerodha-model card ── */}
            <div className="bg-white border border-[#E2E8F0] rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-full bg-[#003366] flex items-center justify-center">
                  <span className="material-symbols-outlined text-white text-sm">school</span>
                </div>
                <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                  Offline Filing — Zerodha Model
                </h3>
              </div>
              <p className="text-xs text-[#434652] mb-4">
                Follow this exact 4-step flow (mirrors Zerodha's guide) to upload your JSON on the Income Tax e-filing portal.
              </p>
              <div className="space-y-3">
                {[
                  {
                    n: 1,
                    title: "Pay Tax (if applicable)",
                    body: balancePayable > 0
                      ? `Pay ₹${balancePayable.toLocaleString("en-IN")} as Self-Assessment Tax (Challan 300) at eportal.incometax.gov.in → e-Pay Tax.`
                      : "Skip — TDS fully covers your liability.",
                  },
                  {
                    n: 2,
                    title: "Login → File ITR",
                    body: "Go to eportal.incometax.gov.in → Login with PAN + password → e-File → Income Tax Returns → 'File Income Tax Return'.",
                  },
                  {
                    n: 3,
                    title: "Select Filing Options",
                    body: `Assessment Year ${ayLabel()} | Mode: Offline | Type: Original | ITR Form: ITR-2 → Continue.`,
                  },
                  {
                    n: 4,
                    title: "Upload JSON + Verify",
                    body: `Upload ${pan}_ITR-2_AY${ayFilenameSuffix()}.json → verify the pre-filled data → e-Verify with Aadhaar OTP → Download ITR-V.`,
                  },
                ].map((step) => (
                  <div key={step.n} className="flex items-start gap-3">
                    <div className="w-7 h-7 rounded-full bg-[#003366] text-white flex items-center justify-center font-bold text-xs shrink-0">
                      {step.n}
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>{step.title}</h4>
                      <p className="text-xs text-[#434652] mt-0.5">{step.body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Trust seal */}
            <div className="text-center p-4 border border-dashed border-[#E2E8F0] rounded-xl text-[10px] uppercase tracking-widest text-[#737783]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              Licensed ITR e-Return Intermediary
              <p className="font-bold mt-1">Reg No: 2024-STOX-1102</p>
            </div>
          </div>

          {/* ── Left/middle column: validation + full offline guide ── */}
          <div className="lg:col-span-8">
            {error && (
              <div className="bg-[#ffdad6] border border-red-200 rounded-lg p-3 text-xs text-[#991B1B] flex items-start gap-2 mb-4">
                <span className="material-symbols-outlined text-sm shrink-0">error</span>
                {error}
              </div>
            )}

            {/* Export validation status */}
            {exportData && (
              <div className={`rounded-xl p-5 mb-6 border ${
                exportData.validation_passed
                  ? "bg-[#E8F5E9] border-[#4CAF50]"
                  : "bg-[#FFF8E1] border-[#F57C00]"
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="material-symbols-outlined text-lg">
                    {exportData.validation_passed ? "verified" : "warning"}
                  </span>
                  <h3 className={`font-bold ${
                    exportData.validation_passed ? "text-[#166534]" : "text-[#92400E]"
                  }`} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                    {exportData.validation_passed ? "Validation Passed" : "Validation Warnings"}
                  </h3>
                </div>
                {exportData.validation_warnings && exportData.validation_warnings.length > 0 && (
                  <ul className="text-sm space-y-1 text-[#92400E]">
                    {exportData.validation_warnings.map((w, i) => (
                      <li key={i}>• {w}</li>
                    ))}
                  </ul>
                )}
                {exportData.validation_passed && (
                  <p className="text-sm text-[#166534]">Ready for the ITR portal — proceed to upload in the Offline Filing guide above.</p>
                )}
              </div>
            )}

            {/* ── Full 8-step offline filing guide (expanded) ── */}
            {showInstructions && (
              <div className="space-y-5">
                <div className="text-center space-y-3 pb-6 border-b border-[#E2E8F0]">
                  <div className="w-16 h-16 rounded-full bg-[#166534]/10 mx-auto flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#166534] text-3xl">check_circle</span>
                  </div>
                  <h2 className="text-2xl font-bold text-[#166534]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                    JSON Downloaded — File on the ITR Portal
                  </h2>
                  <p className="text-sm text-[#434652]">Complete the filing in these final steps.</p>
                </div>

                {[
                  { n: 1, title: "Pay Your Tax", body: balancePayable > 0
                      ? `You owe ₹${balancePayable.toLocaleString("en-IN")}. Go to eportal.incometax.gov.in → e-Pay Tax → Self-Assessment Tax (300) → AY ${ayLabel()} → Pay ₹${balancePayable.toLocaleString("en-IN")}.`
                      : "No payment needed — your TDS covers everything. Skip to Step 2.",
                    warn: balancePayable > 0 },
                  { n: 2, title: "Login to ITR Portal", body: "Go to eportal.incometax.gov.in → Click 'Login' → Enter PAN & password." },
                  { n: 3, title: "Navigate to File ITR", body: "Click e-File → Income Tax Returns → 'File Income Tax Return' (blue button)." },
                  { n: 4, title: "Select Filing Options", body: `Assessment Year: ${ayLabel()} | Mode: Offline | Type: Original | Audited: No | ITR: ITR-2 → Continue.`, critical: true },
                  { n: 5, title: "Upload JSON File", body: `Click 'Choose File' → Select ${exportData?.filename || `this file`} → Upload. Should show a green success message.`, hasError: true },
                  { n: 6, title: "Verify Tax Computation", body: `Cross-check: Total Income ₹${taxableIncome.toLocaleString("en-IN")}, Balance Payable ₹${Math.abs(balancePayable).toLocaleString("en-IN")}. If numbers differ by >₹5, STOP and contact support.`, },
                  { n: 7, title: "E-Verify with Aadhaar OTP", body: "Check declaration box → Proceed to Verification → Choose Aadhaar OTP → Enter OTP → Verify." },
                  { n: 8, title: "Download Acknowledgement", body: "After success: Download Acknowledgement PDF → Save ITR-V number. You're done!", done: true },
                ].map((step) => (
                  <div key={step.n} className={`bg-white border rounded-xl p-5 flex items-start gap-4 transition-all hover:border-[#003366] ${
                    step.warn ? "border-l-4 border-l-[#F57C00]" :
                    step.done ? "border-l-4 border-l-[#166534]" :
                    step.critical ? "border-l-4 border-l-[#003366]" : "border-[#E2E8F0]"
                  }`}>
                    <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 font-bold text-sm ${
                      step.done ? "bg-[#166534] text-white" :
                      step.warn ? "bg-[#F57C00] text-white" : "bg-[#003366] text-white"
                    }`} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                      {step.done ? <span className="material-symbols-outlined text-base">check</span> : step.n}
                    </div>
                    <div>
                      <h4 className="text-base font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>{step.title}</h4>
                      <p className="text-sm text-[#434652] mt-1">{step.body}</p>
                      {step.hasError && (
                        <div className="mt-3 p-3 bg-[#ffdad6] border border-red-200 rounded-lg text-xs text-[#93000a] flex items-start gap-2">
                          <span className="material-symbols-outlined text-sm shrink-0">error</span>
                          <span>If you see a red error: copy the exact error text → come back to TaxStox → Help → Paste it. We&apos;ll fix and re-generate.</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                <div className="text-center p-6 bg-white border border-[#E2E8F0] rounded-xl">
                  <p className="text-sm font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Need help?</p>
                  <p className="text-xs text-[#434652] mt-1">support@taxstox.com · WhatsApp: +91-XXXXX-XXXXX</p>
                </div>

                <div className="text-center pb-8">
                  <button onClick={() => router.push("/")} className="px-8 py-4 bg-[#003366] text-white rounded-lg font-semibold text-sm shadow-md hover:opacity-90 transition-all" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                    Start New Filing
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SummaryPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] text-sm text-[#434652]">Loading...</div>
    }>
      <SummaryContent />
    </Suspense>
  );
}
