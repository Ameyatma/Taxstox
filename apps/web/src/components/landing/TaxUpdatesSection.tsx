"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchTaxInsights } from "@/lib/api";
import type { TaxInsightsData, TaxUpdateItem, TaxDeadlineItem, TaxTipItem, TaxFactItem } from "@/lib/api";
import {
  taxUpdates as fallbackUpdates,
  taxDeadlines as fallbackDeadlines,
  taxTips as fallbackTips,
  taxFacts as fallbackFacts,
  getDeadlineStatus,
} from "@/lib/tax-data";
import type { TaxUpdate, TaxDeadline, TaxTip, TaxFact } from "@/lib/tax-data";

// ── Unified display types (works with both API and fallback data) ─────

interface DisplayUpdate {
  id: string;
  title: string;
  summary: string;
  category: string;
  publishedDate: string;
  url: string;
  source: string;
}

interface DisplayDeadline {
  id: string;
  title: string;
  date: string;
  description: string;
}

interface DisplayTip {
  id: string;
  text: string;
}

interface DisplayFact {
  id: string;
  title: string;
  description: string;
  icon: string;
}

// ── Mappers: API → Display ───────────────────────────────────────────

function mapApiUpdate(u: TaxUpdateItem): DisplayUpdate {
  return {
    id: u.id,
    title: u.title,
    summary: u.summary_short,
    category: u.category,
    publishedDate: u.published_date,
    url: u.source_url,
    source: u.source,
  };
}

// ── Category color map ───────────────────────────────────────────────

const categoryColors: Record<string, { bg: string; text: string }> = {
  Budget:     { bg: "#003366", text: "#ffffff" },
  ITR:        { bg: "#166534", text: "#ffffff" },
  TDS:        { bg: "#F57C00", text: "#ffffff" },
  GST:        { bg: "#0d47a1", text: "#ffffff" },
  CBDT:       { bg: "#92400E", text: "#ffffff" },
  Compliance: { bg: "#eff4ff", text: "#003366" },
  "Advance Tax": { bg: "#0d47a1", text: "#ffffff" },
};

function getCategoryStyle(category: string) {
  return categoryColors[category] || categoryColors["Compliance"];
}

// ── Sub-components ───────────────────────────────────────────────────

function CategoryBadge({ category }: { category: string }) {
  const c = getCategoryStyle(category);
  return (
    <span
      className="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
      style={{ background: c.bg, color: c.text, fontFamily: "var(--font-hanken-grotesk)" }}
    >
      {category}
    </span>
  );
}

function StatusPill({ status }: { status: "upcoming" | "today" | "passed" }) {
  const styles: Record<string, string> = {
    upcoming: "bg-[#166534]/10 text-[#166534]",
    today:    "bg-[#F57C00]/10 text-[#F57C00]",
    passed:   "bg-gray-100 text-[#737783]",
  };
  return (
    <span
      className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${styles[status]}`}
      style={{ fontFamily: "var(--font-hanken-grotesk)" }}
    >
      {status === "today" ? "Today" : status === "upcoming" ? "Upcoming" : "Passed"}
    </span>
  );
}

function UpdateCard({ item }: { item: DisplayUpdate }) {
  return (
    <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 hover:border-[#003366] hover:shadow-md transition-all flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <CategoryBadge category={item.category} />
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-[#737783] uppercase tracking-wider"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
            {item.source}
          </span>
          <span className="text-[11px] text-[#737783] font-medium">
            {new Date(item.publishedDate).toLocaleDateString("en-IN", {
              day: "numeric",
              month: "short",
              year: "numeric",
            })}
          </span>
        </div>
      </div>
      <h4
        className="text-sm font-semibold text-[#003366] leading-snug"
        style={{ fontFamily: "var(--font-hanken-grotesk)" }}
      >
        {item.title}
      </h4>
      <p className="text-xs text-[#434652] leading-relaxed flex-1">{item.summary}</p>
      <a
        href={item.url || "#"}
        className="inline-flex items-center gap-1 text-xs font-bold text-[#003178] hover:text-[#003366] transition-colors mt-auto"
        style={{ fontFamily: "var(--font-hanken-grotesk)" }}
        target="_blank"
        rel="noopener noreferrer"
      >
        Read on {item.source === "pib" ? "PIB" : item.source === "incometax" ? "IT Dept" : item.source === "cbdt" ? "CBDT" : item.source === "mof" ? "MoF" : "Source"}
        <span className="material-symbols-outlined text-xs">arrow_forward</span>
      </a>
    </div>
  );
}

function DeadlineCard({ item }: { item: DisplayDeadline }) {
  const { status, daysRemaining } = getDeadlineStatus(item.date);
  const d = new Date(item.date + "T00:00:00");
  const formattedDate = d.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  return (
    <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 hover:border-[#003366] hover:shadow-md transition-all flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span
          className="text-xl font-extrabold text-[#003366]"
          style={{ fontFamily: "var(--font-hanken-grotesk)" }}
        >
          {formattedDate}
        </span>
        <StatusPill status={status} />
      </div>
      <h4
        className="text-sm font-semibold text-[#003366]"
        style={{ fontFamily: "var(--font-hanken-grotesk)" }}
      >
        {item.title}
      </h4>
      <p className="text-xs text-[#434652] leading-relaxed flex-1">{item.description}</p>
      <div className="flex items-center gap-1.5 mt-1">
        <span className="material-symbols-outlined text-sm text-[#F57C00]">schedule</span>
        <span
          className={`text-xs font-bold ${
            status === "passed"
              ? "text-[#737783]"
              : status === "today"
                ? "text-[#F57C00]"
                : "text-[#166534]"
          }`}
          style={{ fontFamily: "var(--font-hanken-grotesk)" }}
        >
          {status === "passed"
            ? `${Math.abs(daysRemaining)} days ago`
            : status === "today"
              ? "Due today"
              : `${daysRemaining} days left`}
        </span>
      </div>
    </div>
  );
}

function RotatingTipCard({ tips }: { tips: DisplayTip[] }) {
  const [index, setIndex] = useState(0);
  const [fading, setFading] = useState(false);

  const goTo = useCallback(
    (next: number) => {
      if (next === index || tips.length === 0) return;
      setFading(true);
      setTimeout(() => {
        setIndex(next);
        setFading(false);
      }, 150);
    },
    [index, tips.length],
  );

  const next = useCallback(() => goTo((index + 1) % tips.length), [index, tips.length, goTo]);
  const prev = useCallback(() => goTo((index - 1 + tips.length) % tips.length), [index, tips.length, goTo]);

  useEffect(() => {
    if (tips.length === 0) return;
    const timer = setInterval(next, 8000);
    return () => clearInterval(timer);
  }, [next, tips.length]);

  if (tips.length === 0) {
    return (
      <div className="bg-white border border-[#E2E8F0] rounded-xl p-6">
        <p className="text-sm text-[#434652]">Tax tips coming soon.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-[#E2E8F0] rounded-xl p-6 hover:shadow-md transition-all">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[#F57C00]">lightbulb</span>
          <h4
            className="text-sm font-semibold text-[#003366] uppercase tracking-wider"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            Tax Tip
          </h4>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={prev}
            className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-[#eff4ff] transition-colors"
            aria-label="Previous tip"
          >
            <span className="material-symbols-outlined text-sm text-[#434652]">chevron_left</span>
          </button>
          <button
            onClick={next}
            className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-[#eff4ff] transition-colors"
            aria-label="Next tip"
          >
            <span className="material-symbols-outlined text-sm text-[#434652]">chevron_right</span>
          </button>
        </div>
      </div>
      <p
        className="text-sm text-[#434652] leading-relaxed transition-opacity duration-150"
        style={{ opacity: fading ? 0 : 1 }}
      >
        {tips[index].text}
      </p>
      <div className="flex items-center justify-center gap-1.5 mt-4">
        {tips.map((_, i) => (
          <button
            key={i}
            onClick={() => goTo(i)}
            className={`w-1.5 h-1.5 rounded-full transition-all ${
              i === index ? "bg-[#F57C00] w-4" : "bg-[#c3c6d4] hover:bg-[#737783]"
            }`}
            aria-label={`Tip ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
}

function FactCard({ item }: { item: DisplayFact }) {
  return (
    <div className="bg-white border border-[#E2E8F0] rounded-xl p-4 hover:border-[#003366] hover:shadow-sm transition-all flex gap-3">
      <div className="w-9 h-9 bg-[#eff4ff] rounded-lg flex items-center justify-center shrink-0 mt-0.5">
        <span className="material-symbols-outlined text-[#003366] text-lg">{item.icon || "info"}</span>
      </div>
      <div className="space-y-1">
        <h5
          className="text-xs font-semibold text-[#003366] leading-snug"
          style={{ fontFamily: "var(--font-hanken-grotesk)" }}
        >
          {item.title}
        </h5>
        <p className="text-[11px] text-[#434652] leading-relaxed">{item.description}</p>
      </div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 animate-pulse space-y-3">
      <div className="flex justify-between">
        <div className="h-4 w-16 bg-[#E2E8F0] rounded-full" />
        <div className="h-3 w-20 bg-[#E2E8F0] rounded" />
      </div>
      <div className="h-4 w-full bg-[#E2E8F0] rounded" />
      <div className="h-3 w-full bg-[#E2E8F0] rounded" />
      <div className="h-3 w-2/3 bg-[#E2E8F0] rounded" />
    </div>
  );
}

// ── Main Section ─────────────────────────────────────────────────────

export default function TaxUpdatesSection() {
  const [apiData, setApiData] = useState<TaxInsightsData | null>(null);
  const [apiError, setApiError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchTaxInsights();
        if (!cancelled) {
          setApiData(data);
          setApiError(false);
        }
      } catch {
        if (!cancelled) setApiError(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  // Derive display data — prefer API, fall back to local
  const updates: DisplayUpdate[] = apiData?.updates?.length
    ? apiData.updates.map(mapApiUpdate)
    : fallbackUpdates.map((u: TaxUpdate) => ({
        id: u.id, title: u.title, summary: u.summary,
        category: u.category, publishedDate: u.publishedDate,
        url: u.url || "#", source: "static",
      }));

  const deadlines: DisplayDeadline[] = apiData?.deadlines?.length
    ? apiData.deadlines.map((d: TaxDeadlineItem) => ({
        id: d.id, title: d.title, date: d.date, description: d.description,
      }))
    : fallbackDeadlines.map((d: TaxDeadline) => ({
        id: d.id, title: d.title, date: d.date, description: d.description,
      }));

  const tips: DisplayTip[] = apiData?.tips?.length
    ? apiData.tips.map((t: TaxTipItem) => ({ id: t.id, text: t.text }))
    : fallbackTips.map((t: TaxTip) => ({ id: t.id, text: t.text }));

  const facts: DisplayFact[] = apiData?.facts?.length
    ? apiData.facts.map((f: TaxFactItem) => ({
        id: f.id, title: f.title, description: f.description, icon: f.icon,
      }))
    : fallbackFacts.map((f: TaxFact) => ({
        id: f.id, title: f.title, description: f.description, icon: f.icon,
      }));

  const lastSynced = apiData?.last_synced;
  const usingFallback = apiError || (!loading && !apiData);

  return (
    <section className="py-20 bg-[#F8FAFC] px-6 md:px-10">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-14 space-y-2">
          <p
            className="text-[11px] tracking-widest font-bold text-[#F57C00] uppercase"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            Stay Informed
          </p>
          <h2
            className="text-3xl md:text-4xl font-bold text-[#003366]"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            Tax Updates &amp; Insights
          </h2>
          <p className="text-sm text-[#434652] max-w-lg mx-auto">
            Stay ahead of deadlines, understand policy changes, and file with confidence.
          </p>
          {lastSynced && !usingFallback && (
            <p className="text-[10px] text-[#737783]">
              Last synced: {new Date(lastSynced).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
              {" · "}Source: Income Tax Dept, CBDT, PIB, MoF
            </p>
          )}
        </div>

        {/* Main Grid — 2 columns on desktop */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* ── Left Column (spans 2/3): Updates + Deadlines ── */}
          <div className="lg:col-span-2 space-y-12">
            {/* Latest Tax Updates */}
            <div className="space-y-5">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[#003366]">breaking_news</span>
                <h3
                  className="text-lg font-semibold text-[#003366]"
                  style={{ fontFamily: "var(--font-hanken-grotesk)" }}
                >
                  Latest Tax Updates
                </h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {loading
                  ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
                  : updates.map((item) => <UpdateCard key={item.id} item={item} />)}
              </div>
            </div>

            {/* Important Deadlines */}
            <div className="space-y-5">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[#003366]">calendar_month</span>
                <h3
                  className="text-lg font-semibold text-[#003366]"
                  style={{ fontFamily: "var(--font-hanken-grotesk)" }}
                >
                  Important Deadlines
                </h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {loading
                  ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
                  : deadlines.map((item) => <DeadlineCard key={item.id} item={item} />)}
              </div>
            </div>
          </div>

          {/* ── Right Column (1/3): Tips + Facts ── */}
          <div className="space-y-8">
            {/* Rotating Tax Tips */}
            <RotatingTipCard tips={tips} />

            {/* Did You Know? */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[#003366]">psychology</span>
                <h3
                  className="text-lg font-semibold text-[#003366]"
                  style={{ fontFamily: "var(--font-hanken-grotesk)" }}
                >
                  Did You Know?
                </h3>
              </div>
              <div className="space-y-3">
                {loading
                  ? Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="bg-white border border-[#E2E8F0] rounded-xl p-4 animate-pulse flex gap-3">
                        <div className="w-9 h-9 bg-[#E2E8F0] rounded-lg shrink-0" />
                        <div className="space-y-2 flex-1">
                          <div className="h-3 w-2/3 bg-[#E2E8F0] rounded" />
                          <div className="h-3 w-full bg-[#E2E8F0] rounded" />
                        </div>
                      </div>
                    ))
                  : facts.map((item) => <FactCard key={item.id} item={item} />)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
