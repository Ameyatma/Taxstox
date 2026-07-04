// ── Tax Updates & Insights — Data Models ─────────────────────────────
// Designed to be easily replaced with an API response.
// All data is factually accurate as of July 2025 (AY 2025-26).

export interface TaxUpdate {
  id: string;
  title: string;
  summary: string;
  category: "Budget" | "ITR" | "TDS" | "GST" | "CBDT" | "Compliance";
  publishedDate: string; // ISO date string
  url?: string;
}

export interface TaxDeadline {
  id: string;
  title: string;
  date: string; // ISO date string (YYYY-MM-DD)
  description: string;
}

export interface TaxTip {
  id: string;
  text: string;
}

export interface TaxFact {
  id: string;
  title: string;
  description: string;
  icon: string; // Material Symbols icon name
}

// ── Latest Tax Updates ───────────────────────────────────────────────

export const taxUpdates: TaxUpdate[] = [
  {
    id: "itu-1",
    title: "CBDT Extends ITR Filing Deadline for AY 2025-26 to July 31, 2025",
    summary:
      "The Central Board of Direct Taxes has confirmed the due date for non-audit cases remains July 31, 2025. Taxpayers are advised to file early to avoid last-minute portal congestion.",
    category: "CBDT",
    publishedDate: "2025-06-15",
    url: "https://incometaxindia.gov.in",
  },
  {
    id: "itu-2",
    title: "New TDS Rate on Dividend Income Exceeding ₹5,000 Takes Effect",
    summary:
      "Section 194K now mandates 10% TDS on dividend income from mutual funds exceeding ₹5,000 in a financial year. Ensure your AIS reflects this correctly before filing.",
    category: "TDS",
    publishedDate: "2025-06-01",
    url: "https://incometaxindia.gov.in",
  },
  {
    id: "itu-3",
    title: "Budget 2025: Standard Deduction Raised to ₹75,000 Under New Regime",
    summary:
      "The standard deduction for salaried taxpayers under the New Tax Regime has been increased from ₹50,000 to ₹75,000 for FY 2024-25, making the new regime more attractive for many filers.",
    category: "Budget",
    publishedDate: "2025-02-01",
    url: "https://www.indiabudget.gov.in",
  },
  {
    id: "itu-4",
    title: "ITR-1 and ITR-2 JSON Schemas Updated for AY 2025-26",
    summary:
      "The Income Tax Department has released updated JSON schemas for ITR-1 (Sahaj) and ITR-2 with new validation rules for foreign assets, virtual digital assets, and high-value transactions.",
    category: "ITR",
    publishedDate: "2025-04-10",
    url: "https://incometaxindia.gov.in",
  },
];

// ── Important Deadlines ──────────────────────────────────────────────

export const taxDeadlines: TaxDeadline[] = [
  {
    id: "dl-1",
    title: "ITR Filing (Non-Audit Cases)",
    date: "2025-07-31",
    description:
      "Last date to file ITR for individuals, HUFs, and other non-audit taxpayers for FY 2024-25 (AY 2025-26). Late filing attracts penalty up to ₹5,000 under Section 234F.",
  },
  {
    id: "dl-2",
    title: "Advance Tax — 2nd Instalment",
    date: "2025-09-15",
    description:
      "Second instalment of advance tax for FY 2025-26. Pay at least 45% of your total advance tax liability by this date to avoid interest under Section 234C.",
  },
  {
    id: "dl-3",
    title: "TDS Return — Q1 FY 2025-26",
    date: "2025-07-31",
    description:
      "Deadline for filing quarterly TDS/TCS return (Form 24Q/26Q/27Q) for the April–June 2025 quarter. Late filing attracts penalty under Section 271H.",
  },
  {
    id: "dl-4",
    title: "GST Return — GSTR-3B (Monthly)",
    date: "2025-07-20",
    description:
      "Due date for filing GSTR-3B for June 2025 for taxpayers with aggregate turnover above ₹5 crore. Late fee of ₹50/day (₹25 CGST + ₹25 SGST) applies.",
  },
];

// ── Tax-Saving Tips ──────────────────────────────────────────────────

export const taxTips: TaxTip[] = [
  {
    id: "tip-1",
    text: "Keep your Form 16 and AIS (Annual Information Statement) ready and cross-checked before you start filing. Any mismatch can trigger a notice from the IT Department.",
  },
  {
    id: "tip-2",
    text: "Verify your bank account is linked and pre-validated on the IT e-filing portal. Refunds are only credited to validated bank accounts — unvalidated accounts cause delays.",
  },
  {
    id: "tip-3",
    text: "Match your AIS and Form 26AS before filing. Discrepancies in TDS, interest income, or high-value transactions are the #1 cause of defective return notices under Section 139(9).",
  },
  {
    id: "tip-4",
    text: "Claim all eligible deductions — Section 80C (₹1.5L), 80D (health insurance up to ₹1L), 80CCD(1B) (NPS ₹50K), and home loan interest under Section 24(b) (₹2L).",
  },
  {
    id: "tip-5",
    text: "If you traded stocks or mutual funds, download your Capital Gains statement from Zerodha, Groww, or CAMS. LTCG above ₹1.25L is taxed at 12.5% — don't miss reporting it.",
  },
  {
    id: "tip-6",
    text: "File early. The IT e-filing portal slows down in the last week of July. Filing by mid-July gives you buffer time to fix any rejection or mismatch issues.",
  },
];

// ── Did You Know? ────────────────────────────────────────────────────

export const taxFacts: TaxFact[] = [
  {
    id: "fact-1",
    title: "Filing ITR even with zero tax liability has benefits",
    description:
      "A filed ITR serves as official proof of income — required for visa applications, loan approvals, credit card applications, and carrying forward capital losses for up to 8 years.",
    icon: "description",
  },
  {
    id: "fact-2",
    title: "Old vs New Tax Regime — you can switch every year",
    description:
      "Salaried taxpayers can choose between Old and New regimes each financial year. The New Regime offers lower slab rates with fewer deductions, while the Old Regime rewards investments with exemptions.",
    icon: "compare_arrows",
  },
  {
    id: "fact-3",
    title: "E-verification is mandatory — don't skip it",
    description:
      "Filing your ITR is not complete until you e-verify it within 30 days. Unverified returns are treated as 'not filed,' which can lead to penalties, delayed refunds, and loss of carried-forward losses.",
    icon: "verified_user",
  },
  {
    id: "fact-4",
    title: "Common filing mistakes that trigger notices",
    description:
      "The top mistakes: not reporting savings bank interest (even if below ₹10K), missing TDS entries from Form 26AS, incorrect personal details, and wrong assessment year selection.",
    icon: "warning",
  },
];

// ── Helpers ──────────────────────────────────────────────────────────

/** Compute deadline status and days remaining from a given date string. */
export function getDeadlineStatus(
  dateStr: string,
): { status: "upcoming" | "today" | "passed"; daysRemaining: number } {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(dateStr + "T00:00:00");

  const diffMs = target.getTime() - today.getTime();
  const daysRemaining = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  if (daysRemaining < 0) return { status: "passed", daysRemaining };
  if (daysRemaining === 0) return { status: "today", daysRemaining: 0 };
  return { status: "upcoming", daysRemaining };
}
