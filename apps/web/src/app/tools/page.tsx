"use client";

import { useState } from "react";

type CalcResult = Record<string, unknown> | null;

export default function ToolsPage() {
  const [activeTab, setActiveTab] = useState<"regime" | "hra" | "cg" | "estimate">("regime");

  return (
    <div className="min-h-screen bg-[#F8FAFC] pb-16">
      {/* Header */}
      <div className="bg-white border-b border-[#E2E8F0]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-10 py-6">
          <h1 className="text-2xl font-bold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Tax Calculators</h1>
          <p className="text-sm text-[#434652] mt-1">Plan your taxes with precision. All calculations based on FY 2025-26 rules.</p>
        </div>
      </div>

      <div className="max-w-[1120px] mx-auto px-6 md:px-10 py-8">
        {/* Tab Switcher */}
        <div className="flex flex-wrap gap-2 mb-8">
          {[
            { id: "regime" as const, label: "Regime Compare", icon: "compare_arrows" },
            { id: "hra" as const, label: "HRA Exemption", icon: "home" },
            { id: "cg" as const, label: "Capital Gains Tax", icon: "trending_up" },
            { id: "estimate" as const, label: "Quick Estimate", icon: "calculate" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-bold transition-all ${
                activeTab === tab.id
                  ? "bg-[#003366] text-white shadow-md"
                  : "bg-white border border-[#E2E8F0] text-[#434652] hover:border-[#003366]"
              }`}
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              <span className="material-symbols-outlined text-base">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Calculator Content */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7">
            {activeTab === "regime" && <RegimeCompareCalculator />}
            {activeTab === "hra" && <HRACalculator />}
            {activeTab === "cg" && <CGTaxCalculator />}
            {activeTab === "estimate" && <QuickEstimateCalculator />}
          </div>
          <div className="lg:col-span-5">
            <InfoCard />
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Shared input styles ─────────────────────────────────────────────

const inputClass = "w-full px-4 py-3 bg-white border border-[#E2E8F0] rounded-lg text-sm focus:border-[#003366] focus:ring-1 focus:ring-[#003366] outline-none transition-all";
const labelClass = "text-[11px] font-bold text-[#434652] uppercase tracking-wider block mb-1";
const sectionClass = "bg-white border border-[#E2E8F0] rounded-xl p-6 space-y-5";

// ── Regime Compare Calculator ───────────────────────────────────────

function RegimeCompareCalculator() {
  const [salary, setSalary] = useState("1200000");
  const [ded80c, setDed80c] = useState("150000");
  const [ded80d, setDed80d] = useState("25000");
  const [hra, setHra] = useState("0");
  const [homeInt, setHomeInt] = useState("0");
  const [npsEmp, setNpsEmp] = useState("0");
  const [other, setOther] = useState("0");
  const [result, setResult] = useState<CalcResult>(null);
  const [loading, setLoading] = useState(false);

  async function calculate() {
    setLoading(true);
    const params = new URLSearchParams({ salary, deductions_80c: ded80c, deductions_80d: ded80d, hra_exemption: hra, home_loan_interest: homeInt, nps_employer: npsEmp, other_income: other });
    try {
      const res = await fetch(`http://localhost:8000/api/v1/calculator/regime-compare?${params}`);
      setResult(await res.json());
    } catch { setResult(null); }
    setLoading(false);
  }

  const resultAny = result as Record<string, unknown> | null;

  return (
    <div className={sectionClass}>
      <h2 className="text-lg font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Old vs New Regime Comparison</h2>
      <div className="grid grid-cols-2 gap-4">
        <div><label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Annual Gross Salary (₹)</label><input type="number" value={salary} onChange={e => setSalary(e.target.value)} className={inputClass} /></div>
        <div><label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>80C Investments (₹)</label><input type="number" value={ded80c} onChange={e => setDed80c(e.target.value)} className={inputClass} /></div>
        <div><label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>80D Health Insurance (₹)</label><input type="number" value={ded80d} onChange={e => setDed80d(e.target.value)} className={inputClass} /></div>
        <div><label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>HRA Exemption (₹)</label><input type="number" value={hra} onChange={e => setHra(e.target.value)} className={inputClass} /></div>
        <div><label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Home Loan Interest (₹)</label><input type="number" value={homeInt} onChange={e => setHomeInt(e.target.value)} className={inputClass} /></div>
        <div><label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Employer NPS 80CCD(2) (₹)</label><input type="number" value={npsEmp} onChange={e => setNpsEmp(e.target.value)} className={inputClass} /></div>
        <div><label className={labelClass} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Other Income (₹)</label><input type="number" value={other} onChange={e => setOther(e.target.value)} className={inputClass} /></div>
      </div>
      <button onClick={calculate} disabled={loading} className="w-full bg-[#F57C00] text-white py-3 rounded-xl font-semibold hover:bg-[#E67600] transition-all disabled:opacity-50">
        {loading ? "Calculating..." : "Compare Regimes"}
      </button>

      {resultAny && (
        <div className="grid grid-cols-2 gap-4 mt-4 animate-in fade-in">
          {["old_regime", "new_regime"].map((regime) => {
            const data = resultAny[regime] as Record<string, string> | undefined;
            const recommended = String(resultAny["recommended"] || "");
            const isWinner = recommended === (regime === "new_regime" ? "new" : "old");
            return (
              <div key={regime} className={`p-4 rounded-lg border-2 ${isWinner ? "border-[#166534] bg-green-50/30" : "border-[#E2E8F0] bg-white"}`}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-sm font-bold" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>{regime === "new_regime" ? "New Regime" : "Old Regime"}</span>
                  {isWinner && <span className="text-[10px] font-bold text-[#166534] bg-green-100 px-2 py-0.5 rounded-full">RECOMMENDED</span>}
                </div>
                <div className="space-y-2 text-xs">
                  <Row label="Taxable Income" value={`₹${Number(data?.taxable_income || 0).toLocaleString("en-IN")}`} />
                  <Row label="Tax" value={`₹${Number(data?.tax || 0).toLocaleString("en-IN")}`} />
                  <Row label="Cess (4%)" value={`₹${Number(data?.cess || 0).toLocaleString("en-IN")}`} />
                  <hr className="border-[#E2E8F0]" />
                  <Row label="Total Tax" value={`₹${Number(data?.total_tax || 0).toLocaleString("en-IN")}`} bold />
                </div>
              </div>
            );
          })}
          {Number(resultAny["savings"] || 0) > 0 && (
            <div className="col-span-2 p-4 bg-[#eff4ff] rounded-lg text-center">
              <p className="text-sm font-bold text-[#003366]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
                Save ₹{Number(resultAny["savings"]).toLocaleString("en-IN")} by choosing the {String(resultAny["recommended"]) === "new" ? "New" : "Old"} Regime
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── HRA Calculator ──────────────────────────────────────────────────

function HRACalculator() {
  const [basic, setBasic] = useState("50000");
  const [hraReceived, setHraReceived] = useState("25000");
  const [rent, setRent] = useState("20000");
  const [metro, setMetro] = useState(true);
  const [result, setResult] = useState<CalcResult>(null);
  const [loading, setLoading] = useState(false);

  async function calculate() {
    setLoading(true);
    const params = new URLSearchParams({ basic_salary: basic, hra_received: hraReceived, rent_paid: rent, metro_city: String(metro) });
    try {
      const res = await fetch(`http://localhost:8000/api/v1/calculator/hra?${params}`);
      setResult(await res.json());
    } catch { setResult(null); }
    setLoading(false);
  }

  const r = result as Record<string, string | boolean | Record<string, string>> | null;

  return (
    <div className={sectionClass}>
      <h2 className="text-lg font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>HRA Exemption Calculator</h2>
      <div className="grid grid-cols-2 gap-4">
        <div><label className={labelClass}>Monthly Basic + DA (₹)</label><input type="number" value={basic} onChange={e => setBasic(e.target.value)} className={inputClass} /></div>
        <div><label className={labelClass}>Monthly HRA Received (₹)</label><input type="number" value={hraReceived} onChange={e => setHraReceived(e.target.value)} className={inputClass} /></div>
        <div><label className={labelClass}>Monthly Rent Paid (₹)</label><input type="number" value={rent} onChange={e => setRent(e.target.value)} className={inputClass} /></div>
        <div className="flex items-end pb-1">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={metro} onChange={e => setMetro(e.target.checked)} className="w-4 h-4 accent-[#003366]" />
            <span className="text-sm text-[#0b1c30]">Metro City (50%)</span>
          </label>
        </div>
      </div>
      <button onClick={calculate} disabled={loading} className="w-full bg-[#F57C00] text-white py-3 rounded-xl font-semibold hover:bg-[#E67600] transition-all disabled:opacity-50">
        {loading ? "Calculating..." : "Calculate HRA Exemption"}
      </button>

      {r && (
        <div className="p-4 bg-[#eff4ff] rounded-lg space-y-3 animate-in fade-in">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <span className="text-[#434652]">Annual Basic:</span><span className="font-mono text-right">₹{Number(r["annual_basic"]).toLocaleString("en-IN")}</span>
            <span className="text-[#434652]">Annual HRA:</span><span className="font-mono text-right">₹{Number(r["annual_hra_received"]).toLocaleString("en-IN")}</span>
            <span className="text-[#434652]">Annual Rent:</span><span className="font-mono text-right">₹{Number(r["annual_rent_paid"]).toLocaleString("en-IN")}</span>
          </div>
          <hr className="border-[#c3c6d4]" />
          <div className="flex justify-between items-center">
            <span className="text-sm font-bold text-[#003366]">HRA Exemption:</span>
            <span className="text-lg font-bold text-[#166534] font-mono">₹{Number(r["hra_exemption"]).toLocaleString("en-IN")}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-bold text-[#003366]">Taxable HRA:</span>
            <span className="text-sm font-bold text-[#92400E] font-mono">₹{Number(r["taxable_hra"]).toLocaleString("en-IN")}</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Capital Gains Tax Calculator ────────────────────────────────────

function CGTaxCalculator() {
  const [gainType, setGainType] = useState("ltcg_equity");
  const [amount, setAmount] = useState("200000");
  const [result, setResult] = useState<CalcResult>(null);
  const [loading, setLoading] = useState(false);

  async function calculate() {
    setLoading(true);
    const params = new URLSearchParams({ gain_type: gainType, gain_amount: amount });
    try {
      const res = await fetch(`http://localhost:8000/api/v1/calculator/capital-gains?${params}`);
      setResult(await res.json());
    } catch { setResult(null); }
    setLoading(false);
  }

  const r = result as Record<string, string> | null;

  return (
    <div className={sectionClass}>
      <h2 className="text-lg font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Capital Gains Tax Calculator</h2>
      <div>
        <label className={labelClass}>Gain Type</label>
        <select value={gainType} onChange={e => setGainType(e.target.value)} className={inputClass}>
          <option value="ltcg_equity">LTCG Equity/MF (112A) — 12.5% over ₹1.25L</option>
          <option value="stcg_equity">STCG Equity/MF (111A) — 15%</option>
          <option value="ltcg_other">LTCG Other Assets — 12.5%</option>
          <option value="stcg_other">STCG Other Assets — Slab Rate</option>
        </select>
      </div>
      <div>
        <label className={labelClass}>Total Capital Gain (₹)</label>
        <input type="number" value={amount} onChange={e => setAmount(e.target.value)} className={inputClass} />
      </div>
      <button onClick={calculate} disabled={loading} className="w-full bg-[#F57C00] text-white py-3 rounded-xl font-semibold hover:bg-[#E67600] transition-all disabled:opacity-50">
        {loading ? "Calculating..." : "Calculate Tax"}
      </button>

      {r && (
        <div className="p-4 bg-[#eff4ff] rounded-lg space-y-3 animate-in fade-in">
          <p className="text-xs text-[#434652]">{r["gain_type"]}</p>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <span className="text-[#434652]">Total Gain:</span><span className="font-mono text-right">₹{Number(r["total_gain"]).toLocaleString("en-IN")}</span>
            {Number(r["exemption"] || 0) > 0 && (<><span className="text-[#166534]">Exemption (112A):</span><span className="font-mono text-right text-[#166534]">- ₹{Number(r["exemption"]).toLocaleString("en-IN")}</span></>)}
            <span className="text-[#434652]">Taxable Gain:</span><span className="font-mono text-right">₹{Number(r["taxable_gain"]).toLocaleString("en-IN")}</span>
            <span className="text-[#434652]">Tax Rate:</span><span className="font-mono text-right">{r["tax_rate"]}</span>
          </div>
          <hr className="border-[#c3c6d4]" />
          <div className="flex justify-between items-center">
            <span className="text-sm font-bold text-[#003366]">Tax Amount:</span>
            <span className="text-lg font-bold text-[#166534] font-mono">₹{Number(r["tax_amount"]).toLocaleString("en-IN")}</span>
          </div>
          {r["note"] && <p className="text-xs text-[#92400E] italic">{r["note"]}</p>}
        </div>
      )}
    </div>
  );
}

// ── Quick Estimate Calculator ────────────────────────────────────────

function QuickEstimateCalculator() {
  const [income, setIncome] = useState("1200000");
  const [regime, setRegime] = useState("new");
  const [result, setResult] = useState<CalcResult>(null);
  const [loading, setLoading] = useState(false);

  async function calculate() {
    setLoading(true);
    const params = new URLSearchParams({ annual_income: income, regime });
    try {
      const res = await fetch(`http://localhost:8000/api/v1/calculator/quick-estimate?${params}`);
      setResult(await res.json());
    } catch { setResult(null); }
    setLoading(false);
  }

  const r = result as Record<string, string> | null;

  return (
    <div className={sectionClass}>
      <h2 className="text-lg font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Quick Tax Estimate</h2>
      <div>
        <label className={labelClass}>Annual Income (₹)</label>
        <input type="number" value={income} onChange={e => setIncome(e.target.value)} className={inputClass} />
      </div>
      <div className="flex gap-4">
        <label className={`flex items-center gap-2 px-5 py-3 border-2 rounded-lg cursor-pointer flex-1 ${regime === "new" ? "border-[#003366] bg-[#eff4ff]" : "border-[#E2E8F0]"}`}>
          <input type="radio" name="regime" checked={regime === "new"} onChange={() => setRegime("new")} className="sr-only" />
          <span className="text-sm font-semibold">New Regime</span>
        </label>
        <label className={`flex items-center gap-2 px-5 py-3 border-2 rounded-lg cursor-pointer flex-1 ${regime === "old" ? "border-[#003366] bg-[#eff4ff]" : "border-[#E2E8F0]"}`}>
          <input type="radio" name="regime" checked={regime === "old"} onChange={() => setRegime("old")} className="sr-only" />
          <span className="text-sm font-semibold">Old Regime</span>
        </label>
      </div>
      <button onClick={calculate} disabled={loading} className="w-full bg-[#F57C00] text-white py-3 rounded-xl font-semibold hover:bg-[#E67600] transition-all disabled:opacity-50">
        {loading ? "Calculating..." : "Estimate Tax"}
      </button>

      {r && (
        <div className="p-4 bg-[#eff4ff] rounded-lg space-y-3 animate-in fade-in">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <span className="text-[#434652]">Annual Income:</span><span className="font-mono text-right">₹{Number(r["annual_income"]).toLocaleString("en-IN")}</span>
            <span className="text-[#434652]">Regime:</span><span className="font-mono text-right">{r["regime"]}</span>
            <span className="text-[#434652]">Taxable Income:</span><span className="font-mono text-right">₹{Number(r["taxable_income"]).toLocaleString("en-IN")}</span>
            <span className="text-[#434652]">Tax:</span><span className="font-mono text-right">₹{Number(r["tax"]).toLocaleString("en-IN")}</span>
            <span className="text-[#434652]">Cess (4%):</span><span className="font-mono text-right">₹{Number(r["cess"]).toLocaleString("en-IN")}</span>
          </div>
          <hr className="border-[#c3c6d4]" />
          <div className="flex justify-between items-center">
            <span className="text-sm font-bold text-[#003366]">Total Annual Tax:</span>
            <span className="text-lg font-bold text-[#166534] font-mono">₹{Number(r["total_tax"]).toLocaleString("en-IN")}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-[#434652]">Monthly Equivalent:</span>
            <span className="text-xs font-mono">₹{Number(r["monthly_equivalent"]).toLocaleString("en-IN")}/month</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Helper ──────────────────────────────────────────────────────────

function Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className={`text-[#434652] ${bold ? "font-bold" : ""}`}>{label}</span>
      <span className={`font-mono ${bold ? "font-bold" : ""}`}>{value}</span>
    </div>
  );
}

function InfoCard() {
  return (
    <div className="space-y-4">
      <div className="bg-[#0d47a1] text-white rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-2" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Tax Saving Tips</h3>
        <ul className="space-y-3 text-sm text-[#b0c6ff]">
          <li className="flex items-start gap-2">
            <span className="material-symbols-outlined text-[#F57C00] text-base shrink-0 mt-0.5">lightbulb</span>
            <span>Max out 80C (₹1.5L) via PPF, ELSS, EPF, or life insurance.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="material-symbols-outlined text-[#F57C00] text-base shrink-0 mt-0.5">lightbulb</span>
            <span>NPS 80CCD(1B) gives an extra ₹50K deduction beyond 80C.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="material-symbols-outlined text-[#F57C00] text-base shrink-0 mt-0.5">lightbulb</span>
            <span>Health insurance under 80D: ₹25K (self) + ₹50K (senior parents).</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="material-symbols-outlined text-[#F57C00] text-base shrink-0 mt-0.5">lightbulb</span>
            <span>Home loan interest up to ₹2L deductible under Section 24(b).</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="material-symbols-outlined text-[#F57C00] text-base shrink-0 mt-0.5">lightbulb</span>
            <span>LTCG on equity up to ₹1.25L is tax-free under Section 112A.</span>
          </li>
        </ul>
      </div>

      <div className="bg-white border border-[#E2E8F0] rounded-xl p-6">
        <h3 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-3" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>FY 2025-26 Deadlines</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-[#434652]">Original Return</span><span className="font-mono font-bold text-[#991B1B]">Jul 31, 2026</span></div>
          <div className="flex justify-between"><span className="text-[#434652]">Belated Return</span><span className="font-mono">Dec 31, 2026</span></div>
          <div className="flex justify-between"><span className="text-[#434652]">Revised Return</span><span className="font-mono">Dec 31, 2026</span></div>
          <div className="flex justify-between"><span className="text-[#434652]">Updated Return</span><span className="font-mono">Mar 31, 2029</span></div>
        </div>
      </div>
    </div>
  );
}
