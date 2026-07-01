"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { fetchDashboard, type DashboardData, type FilingRecord, type TaxCalendarEvent } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/auth?redirect=/dashboard");
      return;
    }
    if (isAuthenticated) loadDashboard();
  }, [isAuthenticated, authLoading]);

  async function loadDashboard() {
    try {
      const d = await fetchDashboard();
      setData(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }

  // ── Loading ──
  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-[#eff4ff] mx-auto flex items-center justify-center">
            <span className="material-symbols-outlined text-[#003366] text-3xl animate-spin">sync</span>
          </div>
          <p className="text-sm text-[#434652]">Loading your tax command center...</p>
        </div>
      </div>
    );
  }

  // ── Error ──
  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="text-center space-y-4 max-w-md px-6">
          <div className="w-16 h-16 rounded-full bg-[#ffdad6] mx-auto flex items-center justify-center">
            <span className="material-symbols-outlined text-[#991B1B] text-3xl">error</span>
          </div>
          <h2 className="text-xl font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Could not load dashboard</h2>
          <p className="text-sm text-[#434652]">{error}</p>
          <button onClick={loadDashboard} className="px-6 py-3 bg-[#003366] text-white rounded-lg font-semibold">Retry</button>
        </div>
      </div>
    );
  }

  const { stats, quick_actions, filings, tax_calendar } = data;

  return (
    <div className="min-h-screen bg-[#F8FAFC] pb-16">
      {/* Page Header */}
      <div className="bg-white border-b border-[#E2E8F0]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-10 py-6 flex flex-col md:flex-row justify-between md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Tax Command Center</h1>
            <p className="text-sm text-[#434652] mt-1">Welcome back. Here&apos;s your tax overview for AY 2026-27.</p>
          </div>
          <button
            onClick={() => router.push("/?filing=true")}
            className="bg-[#F57C00] text-white px-6 py-3 rounded-xl font-semibold flex items-center gap-2 shadow-lg hover:bg-[#E67600] transition-all active:scale-95"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            <span className="material-symbols-outlined">bolt</span>
            File New ITR
          </button>
        </div>
      </div>

      <div className="max-w-[1120px] mx-auto px-6 md:px-10 py-8 space-y-8">

        {/* ── Hero Stats Row ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            icon="account_balance"
            iconBg="bg-[#eff4ff]"
            iconColor="text-[#003366]"
            label="Total Refunds"
            value={`₹${Number(stats.total_refunds || 0).toLocaleString("en-IN")}`}
          />
          <StatCard
            icon="savings"
            iconBg="bg-green-50"
            iconColor="text-[#166534]"
            label="Tax Saved"
            value={`₹${Number(stats.total_tax_saved || 0).toLocaleString("en-IN")}`}
          />
          <StatCard
            icon="description"
            iconBg="bg-[#eff4ff]"
            iconColor="text-[#003366]"
            label="Filings Done"
            value={String(stats.filed_count)}
          />
          <StatCard
            icon="calendar_today"
            iconBg={stats.days_remaining <= 10 ? "bg-red-50" : "bg-amber-50"}
            iconColor={stats.days_remaining <= 10 ? "text-[#991B1B]" : "text-[#92400E]"}
            label="Days to Deadline"
            value={String(stats.days_remaining)}
            sub={stats.days_remaining <= 10 ? "Urgent!" : "July 31"}
          />
        </div>

        {/* ── Quick Actions ── */}
        <div>
          <h2 className="text-sm font-bold text-[#003366] uppercase tracking-wider mb-4" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {quick_actions.map((action) => (
              <button
                key={action.id}
                onClick={() => router.push(action.href)}
                className={`p-5 rounded-xl border text-left transition-all hover:-translate-y-0.5 active:scale-95 ${
                  action.primary
                    ? "bg-[#003366] text-white border-[#003366] shadow-lg"
                    : "bg-white border-[#E2E8F0] hover:border-[#003366] hover:shadow-md"
                }`}
              >
                <span className={`material-symbols-outlined text-2xl mb-3 block ${action.primary ? "text-[#F57C00]" : "text-[#003366]"}`}>
                  {action.icon}
                </span>
                <span className="text-sm font-semibold" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>{action.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* ── Two Column: History + Calendar ── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Filing History */}
          <div className="lg:col-span-8 space-y-4">
            <h2 className="text-sm font-bold text-[#003366] uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              Filing History
            </h2>
            {filings.length === 0 ? (
              <EmptyState
                icon="folder_open"
                title="No filings yet"
                description="Start your first ITR filing — it takes just 2 minutes."
                action="File Now"
                onAction={() => router.push("/?filing=true")}
              />
            ) : (
              <div className="bg-white border border-[#E2E8F0] rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-[#F8FAFC] border-b border-[#E2E8F0]">
                    <tr className="text-left">
                      <Th>AY</Th>
                      <Th>ITR Type</Th>
                      <Th>Regime</Th>
                      <Th className="text-right">Gross Income</Th>
                      <Th>Status</Th>
                      <Th className="text-right">Action</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {filings.map((f) => (
                      <FilingRow key={f.id} filing={f} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Tax Calendar */}
          <div className="lg:col-span-4 space-y-4">
            <h2 className="text-sm font-bold text-[#003366] uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              Tax Calendar
            </h2>
            <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 space-y-4">
              {tax_calendar.map((event, i) => (
                <CalendarEvent key={i} event={event} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ───────────────────────────────────────────────────

function StatCard({ icon, iconBg, iconColor, label, value, sub }: {
  icon: string; iconBg: string; iconColor: string; label: string; value: string; sub?: string;
}) {
  return (
    <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 hover:border-[#003366] transition-all">
      <div className={`w-10 h-10 ${iconBg} rounded-lg flex items-center justify-center mb-3`}>
        <span className={`material-symbols-outlined ${iconColor}`}>{icon}</span>
      </div>
      <p className="text-[11px] font-bold text-[#434652] uppercase tracking-wider" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>{label}</p>
      <p className="text-xl font-bold text-[#0b1c30] mt-1" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>{value}</p>
      {sub && <p className="text-[10px] text-[#737783] mt-0.5">{sub}</p>}
    </div>
  );
}

function Th({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <th className={`px-4 py-3 text-[11px] font-bold text-[#434652] uppercase tracking-wider ${className}`} style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
      {children}
    </th>
  );
}

function FilingRow({ filing }: { filing: FilingRecord }) {
  const statusColors: Record<string, string> = {
    filed: "bg-green-50 text-[#166534]",
    draft: "bg-amber-50 text-[#92400E]",
    processing: "bg-blue-50 text-[#003366]",
    rejected: "bg-red-50 text-[#991B1B]",
  };
  const statusBadge = statusColors[filing.status] || "bg-gray-50 text-gray-600";

  return (
    <tr className="border-b border-[#E2E8F0] last:border-b-0 hover:bg-[#F8FAFC] transition-colors">
      <td className="px-4 py-3 font-mono text-[#0b1c30] text-xs">{filing.assessment_year}</td>
      <td className="px-4 py-3 font-mono text-xs text-[#0b1c30]">{filing.itr_type}</td>
      <td className="px-4 py-3 text-xs">{filing.regime ? (filing.regime === "new" ? "New" : "Old") : "—"}</td>
      <td className="px-4 py-3 text-right font-mono text-xs">
        {filing.gross_income ? `₹${Number(filing.gross_income).toLocaleString("en-IN")}` : "—"}
      </td>
      <td className="px-4 py-3">
        <span className={`inline-block px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${statusBadge}`}>
          {filing.status}
        </span>
      </td>
      <td className="px-4 py-3 text-right">
        <button className="text-[11px] font-bold text-[#003178] uppercase tracking-wider hover:underline">
          View
        </button>
      </td>
    </tr>
  );
}

function CalendarEvent({ event }: { event: TaxCalendarEvent }) {
  const iconMap: Record<string, string> = {
    deadline: "event_busy",
    payment: "payments",
  };
  const colorMap: Record<string, string> = {
    deadline: "text-[#991B1B] bg-red-50",
    payment: "text-[#F57C00] bg-amber-50",
  };
  const iconColor = colorMap[event.type] || "text-[#003366] bg-[#eff4ff]";
  const icon = iconMap[event.type] || "event";

  return (
    <div className="flex items-start gap-3">
      <div className={`w-9 h-9 rounded-lg ${iconColor} flex items-center justify-center shrink-0`}>
        <span className="material-symbols-outlined text-base">{icon}</span>
      </div>
      <div>
        <p className="text-sm font-medium text-[#0b1c30]">{event.title}</p>
        <p className="text-xs text-[#434652]">{new Date(event.date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</p>
      </div>
    </div>
  );
}

function EmptyState({ icon, title, description, action, onAction }: {
  icon: string; title: string; description: string; action: string; onAction: () => void;
}) {
  return (
    <div className="bg-white border border-dashed border-[#c3c6d4] rounded-xl p-10 text-center space-y-4">
      <div className="w-16 h-16 rounded-full bg-[#F8FAFC] mx-auto flex items-center justify-center">
        <span className="material-symbols-outlined text-[#c3c6d4] text-3xl">{icon}</span>
      </div>
      <div>
        <h3 className="text-base font-semibold text-[#0b1c30]" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>{title}</h3>
        <p className="text-sm text-[#434652] mt-1">{description}</p>
      </div>
      <button onClick={onAction} className="px-6 py-2.5 bg-[#003366] text-white rounded-lg text-sm font-bold hover:opacity-90 transition-all">
        {action}
      </button>
    </div>
  );
}
