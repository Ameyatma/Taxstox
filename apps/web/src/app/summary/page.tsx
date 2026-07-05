"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { exportITR, type TaxSummaryData, type ExportData } from "@/lib/api";
import { getState } from "@/lib/store";

function SummaryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session") || getState().sessionId;

  const [summary, setSummary] = useState<TaxSummaryData | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportData, setExportData] = useState<ExportData | null>(null);
  const [error, setError] = useState("");
  const [downloaded, setDownloaded] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);

  useEffect(() => {
    const cached = getState().taxSummary;
    if (cached) setSummary(cached as unknown as TaxSummaryData);
  }, []);

  async function handleExport() {
    setExporting(true);
    setError("");
    try {
      const data = await exportITR(sessionId!);
      setExportData(data);
      setDownloaded(true);
      setShowInstructions(true);

      // Auto-download
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

  // ── Loading ──
  if (!summary) {
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

  const balancePayable = Number(summary.balance_payable || 0);
  const regimeSavings = Number(summary.regime_savings || 0);
  const taxableIncome = Number(summary.taxable_income || 0);
  const isNew = summary.regime === "new";
  const oldBreakdown = (summary as any).old_regime_breakdown || {};
  const newBreakdown = (summary as any).new_regime_breakdown || {};
  const showComparison = Object.keys(oldBreakdown).length > 0 && Object.keys(newBreakdown).length > 0;
  const grossTotal = Object.values(summary.income || {}).reduce((s: number, v: any) => {
    if (typeof v === "number") return s + v;
    if (typeof v === "object" && v !== null) {
      return s + Object.values(v).reduce((ss: number, vv: any) =>
        typeof vv === "number" ? ss + vv : ss, 0);
    }
    return s;
  }, 0);
  const totalDeductions = Object.values(summary.deductions || {}).reduce((s: number, v: any) =>
    typeof v === "number" ? s + v : s, 0);

  return (
    <div className="min-h-screen bg-[#F8FAFC] pb-20">
      {/* Header */}
      <div className="sticky top-16 z-30 bg-white border-b border-[#E2E8F0]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-10 py-4 flex flex-col md:flex-row justify-between md:items-end gap-4">
          <div>
            <span className="text-[11px] font-bold text-[#003178] tracking-widest uppercase" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Step 4 of 5</span>
            <h1 className="text-2xl font-semibold text-[#0b1c30] mt-1" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Review Your Tax Summary</h1>
            <p className="text-sm text-[#434652] mt-1">FY 2025-26 (AY 2026-27) — Verify the numbers below before export.</p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => window.print()} className="flex items-center gap-1.5 px-4 py-2 border border-[#E2E8F0] text-[#434652] rounded-lg text-[11px] font-bold uppercase tracking-wider hover:bg-[#eff4ff] transition-all" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              <span className="material-symbols-outlined text-base">print</span> Print
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-[1120px] mx-auto px-6 md:px-10 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* ── Left Column (8 cols) ── */}
          <div className="lg:col-span-8 space-y-6">

            {/* Regime Optimizer Banner — matches tax-summary-review/code.html */}
            <div className="relative overflow-hidden rounded-xl p-6 bg-[#0d47a1] text-white border-none shadow-lg">
              <div className="absolute top-0 right-0 w-32 h-32 opacity-10">
                <span className="material-symbols-outlined text-[128px]">verified</span>
              </div>
              <div className="flex flex-col md:flex-row items-center gap-5 relative z-10">
                <div className="bg-[#F57C00] p-3 rounded-full flex items-center justify-center">
                  <span className="material-symbols-outlined text-white text-2xl">bolt</span>
                </div>
                <div className="grow text-center md:text-left">
                  <h3 className="text-lg font-semibold mb-1" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Optimizer Recommendation</h3>
                  <p className="text-sm text-[#b0c6ff]">
                    {regimeSavings > 0
                      ? <>Switching to the <strong className="text-white">{isNew ? "New" : "Old"} Tax Regime</strong> will save you <span className="font-mono text-white font-bold">₹{regimeSavings.toLocaleString("en-IN")}</span> this year.</>
                      : <>Both regimes yield the same tax at your income level.</>
                    }
                  </p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <span className="px-4 py-2 bg-white text-[#003366] rounded-full text-[11px] font-bold uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                    {isNew ? "New Regime" : "Old Regime"} ✓
                  </span>
                </div>
              </div>
            </div>

            {/* Income Card */}
            <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 hover:border-[#003366] transition-all">
              <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-4 flex items-center gap-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                <span className="material-symbols-outlined text-base">payments</span> Income Summary
              </h3>
              <div className="space-y-3">
                {Object.entries(summary.income || {}).map(([label, amount]) => (
                  <div key={label} className="flex justify-between text-sm">
                    <span className="text-[#434652]">{label}</span>
                    <span className="font-mono font-medium">₹{Number(amount).toLocaleString("en-IN")}</span>
                  </div>
                ))}
                <hr className="border-dashed border-[#E2E8F0]" />
                <div className="flex justify-between text-sm font-bold">
                  <span className="text-[#0b1c30]">Gross Total Income</span>
                  <span className="font-mono">₹{grossTotal.toLocaleString("en-IN")}</span>
                </div>
              </div>
            </div>

            {/* Deductions */}
            <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 hover:border-[#003366] transition-all">
              <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-4 flex items-center gap-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                <span className="material-symbols-outlined text-base">savings</span> Deduction Details
              </h3>
              {Object.keys(summary.deductions || {}).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(summary.deductions || {}).map(([label, amount]) => (
                    <div key={label} className="flex justify-between text-sm">
                      <span className="text-[#434652]">{label}</span>
                      <span className="font-mono text-[#166534]">- ₹{Number(amount).toLocaleString("en-IN")}</span>
                    </div>
                  ))}
                  <hr className="border-dashed border-[#E2E8F0]" />
                  <div className="flex justify-between text-sm font-bold">
                    <span className="text-[#0b1c30]">Total Deductions</span>
                    <span className="font-mono text-[#166534]">- ₹{totalDeductions.toLocaleString("en-IN")}</span>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-[#737783] italic">No deductions applicable ({isNew ? "New Regime does not allow most deductions" : "None detected from your data"})</p>
              )}
            </div>

            {/* ── V2: Side-by-Side Regime Comparison ── */}
            {showComparison && (
              <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 overflow-x-auto">
                <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-4 flex items-center gap-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                  <span className="material-symbols-outlined text-base">compare_arrows</span>
                  Old vs New Regime — Full Comparison
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
                      const ov = Number(oldBreakdown[row.ok] || 0);
                      const nv = Number(newBreakdown[row.nk] || 0);
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
                    {/* Tax comparison */}
                    <tr className="border-t-2 border-[#E2E8F0] bg-[#F8FAFC]">
                      <td className="py-2 pr-4 font-semibold text-[#0b1c30]">Tax on Slab Income</td>
                      <td className="py-2 pr-4 text-right font-mono text-xs font-semibold">₹{Number(oldBreakdown.tax_slab || 0).toLocaleString("en-IN")}</td>
                      <td className="py-2 text-right font-mono text-xs font-semibold">₹{Number(newBreakdown.tax_slab || 0).toLocaleString("en-IN")}</td>
                    </tr>
                    <tr className="bg-[#F8FAFC]">
                      <td className="py-2 pr-4 text-[#0b1c30]">+ Surcharge</td>
                      <td className="py-2 pr-4 text-right font-mono text-xs">₹{Number(oldBreakdown.surcharge || 0).toLocaleString("en-IN")}</td>
                      <td className="py-2 text-right font-mono text-xs">₹{Number(newBreakdown.surcharge || 0).toLocaleString("en-IN")}</td>
                    </tr>
                    <tr className="bg-[#F8FAFC]">
                      <td className="py-2 pr-4 text-[#0b1c30]">+ HEC @ 4%</td>
                      <td className="py-2 pr-4 text-right font-mono text-xs">₹{Number(oldBreakdown.cess || 0).toLocaleString("en-IN")}</td>
                      <td className="py-2 text-right font-mono text-xs">₹{Number(newBreakdown.cess || 0).toLocaleString("en-IN")}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}

            {/* Tax Computation */}
            <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 hover:border-[#003366] transition-all">
              <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-4 flex items-center gap-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                <span className="material-symbols-outlined text-base">calculate</span> Tax Computation ({isNew ? "New Regime" : "Old Regime"})
              </h3>
              <div className="space-y-3">
                {Object.entries(summary.tax_breakdown || {}).map(([label, amount]) => (
                  <div key={label} className="flex justify-between text-sm">
                    <span className="text-[#434652]">{label}</span>
                    <span className="font-mono">₹{Number(amount).toLocaleString("en-IN")}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ── Right Column (4 cols) ── */}
          <div className="lg:col-span-4 space-y-6">

            {/* Computation Result */}
            <div className={`bg-white rounded-xl p-6 border-l-4 ${balancePayable > 0 ? "border-l-[#92400E]" : "border-l-[#166534]"} border border-[#E2E8F0]`}>
              <span className="text-[11px] font-bold text-[#737783] uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Computation Result</span>
              <div className="flex items-baseline gap-2 mt-2 mb-1">
                <h2 className={`text-3xl font-bold ${balancePayable > 0 ? "text-[#92400E]" : "text-[#166534]"}`} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                  ₹{Math.abs(balancePayable).toLocaleString("en-IN")}
                </h2>
                <span className={`text-lg font-semibold ${balancePayable > 0 ? "text-[#92400E]" : "text-[#166534]"}`} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
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
                    <span className="font-mono">₹{Number(amount).toLocaleString("en-IN")}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Action: Download */}
            <div className="bg-[#eff4ff] rounded-xl p-6 space-y-4">
              <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Next Steps</h3>

              <button onClick={handleExport} disabled={exporting}
                className="w-full bg-[#003366] text-white py-4 rounded-xl font-semibold flex items-center justify-center gap-3 shadow-lg hover:-translate-y-0.5 active:scale-[0.98] transition-all disabled:opacity-50"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                {exporting ? (
                  <><span className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" /> Building JSON...</>
                ) : downloaded ? (
                  <><span className="material-symbols-outlined">check_circle</span> Downloaded — Click to Re-download</>
                ) : (
                  <><span className="material-symbols-outlined">download</span> Download ITR JSON</>
                )}
              </button>

              {/* Validation warnings */}
              {exportData?.validation_warnings && exportData.validation_warnings.length > 0 && (
                <div className="p-3 bg-[#fef3c7] border border-[#f59e0b]/30 rounded-lg text-xs text-[#92400E] space-y-1">
                  <p className="font-bold">Validation Warnings:</p>
                  {exportData.validation_warnings.map((w, i) => <p key={i}>• {w}</p>)}
                </div>
              )}

              {exportData && exportData.validation_passed && (
                <p className="text-center text-xs font-medium text-[#166534] flex items-center justify-center gap-1">
                  <span className="material-symbols-outlined text-sm">verified</span>
                  Validation passed — ready for ITR portal
                </p>
              )}

              {error && (
                <div className="p-3 bg-[#ffdad6] border border-red-200 rounded-lg text-xs text-[#991B1B] flex items-start gap-2">
                  <span className="material-symbols-outlined text-sm shrink-0">error</span>
                  {error}
                </div>
              )}
            </div>

            {/* Trust Seal */}
            <div className="text-center p-4 border border-dashed border-[#E2E8F0] rounded-xl text-[10px] uppercase tracking-widest text-[#737783]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              Licensed ITR e-Return Intermediary
              <p className="font-bold mt-1">Reg No: 2024-STOX-1102</p>
            </div>
          </div>
        </div>

        {/* ── Post-Export Instructions (matches post-export-instructions/code.html) ── */}
        {showInstructions && (
          <div className="mt-10 max-w-[880px] mx-auto space-y-5">
            <div className="text-center space-y-3 pb-6 border-b border-[#E2E8F0]">
              <div className="w-16 h-16 rounded-full bg-[#166534]/10 mx-auto flex items-center justify-center">
                <span className="material-symbols-outlined text-[#166534] text-3xl">check_circle</span>
              </div>
              <h2 className="text-2xl font-bold text-[#166534]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>JSON Downloaded — Now File on ITR Portal</h2>
              <p className="text-sm text-[#434652]">Follow these 8 steps to submit your return.</p>
            </div>

            {/* Step cards */}
            {[
              { n: 1, title: "Pay Your Tax", body: balancePayable > 0 ? `You owe ₹${balancePayable.toLocaleString("en-IN")}. Go to eportal.incometax.gov.in → e-Pay Tax → Self-Assessment Tax (300) → AY 2026-27 → Pay ₹${balancePayable.toLocaleString("en-IN")}.` : "No payment needed — your TDS covers everything. Skip to Step 2.", warn: balancePayable > 0 },
              { n: 2, title: "Login to ITR Portal", body: "Go to eportal.incometax.gov.in → Click 'Login' → Enter PAN & password." },
              { n: 3, title: "Navigate to File ITR", body: "Click e-File → Income Tax Returns → 'File Income Tax Return' (blue button)." },
              { n: 4, title: "Select Filing Options", body: "Assessment Year: 2026-27 | Mode: Offline | Type: Original | Audited: No | ITR: ITR-2 → Continue.", critical: true },
              { n: 5, title: "Upload JSON File", body: `Click 'Choose File' → Select ${exportData?.filename || "your JSON"} → Upload. Should show green success message.`, hasError: true },
              { n: 6, title: "Verify Tax Computation", body: `Cross-check: Total Income ₹${taxableIncome.toLocaleString("en-IN")}, Balance Payable ₹${Math.abs(balancePayable).toLocaleString("en-IN")}. If numbers differ by >₹5, STOP and contact support.` },
              { n: 7, title: "E-Verify with Aadhaar OTP", body: "Check declaration box → Proceed to Verification → Choose Aadhaar OTP (easiest) → Enter OTP → Verify." },
              { n: 8, title: "Download Acknowledgement", body: "After success: Download Acknowledgement PDF → Save ITR-V number. You're done!", done: true },
            ].map((step) => (
              <div key={step.n} className={`bg-white border rounded-xl p-5 flex items-start gap-4 transition-all hover:border-[#003366] ${step.warn ? "border-l-4 border-l-[#F57C00]" : step.done ? "border-l-4 border-l-[#166534]" : step.critical ? "border-l-[#E2E8F0]" : "border-[#E2E8F0]"}`}>
                <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 font-bold text-sm ${step.done ? "bg-[#166534] text-white" : step.warn ? "bg-[#F57C00] text-white" : "bg-[#003366] text-white"}`} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
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

            {/* Support */}
            <div className="text-center p-6 bg-white border border-[#E2E8F0] rounded-xl">
              <p className="text-sm font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Need help?</p>
              <p className="text-xs text-[#434652] mt-1">support@taxstox.com · WhatsApp: +91-XXXXX-XXXXX</p>
            </div>

            <div className="text-center pb-10">
              <button onClick={() => router.push("/")} className="px-8 py-4 bg-[#003366] text-white rounded-lg font-semibold text-sm shadow-md hover:opacity-90 transition-all" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                Start New Filing
              </button>
            </div>
          </div>
        )}
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
