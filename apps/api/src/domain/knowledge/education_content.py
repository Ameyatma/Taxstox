"""Taxpayer Education Content — Structured educational articles for taxpayers.

Content is keyed by topic and expertise level. Powers the education
features of the AI intelligence platform.

Traceability: C11.6 (Taxpayer Education Content — 0%→50%, P4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ExpertiseLevel(str, Enum):
    BEGINNER = "beginner"              # First-time taxpayer
    INTERMEDIATE = "intermediate"      # Has filed before
    ADVANCED = "advanced"              # CA-level understanding


@dataclass(frozen=True)
class EducationArticle:
    """A single taxpayer education article."""

    article_id: str
    title: str
    summary: str                        # One-paragraph overview
    content: str                        # Full educational content (markdown)
    topic: str                          # "deduction", "regime", "capital_gains", "filing", "general"
    expertise: ExpertiseLevel
    provision_references: tuple[str, ...] = ()  # provision_ids
    related_articles: tuple[str, ...] = ()      # article_ids
    estimated_read_minutes: int = 3
    keywords: tuple[str, ...] = ()      # For search


class EducationContent:
    """Taxpayer education content repository.

    Domain service. Provides topic-based and expertise-based content
    lookup. Content is provision-referenced for traceability.
    """

    def __init__(self) -> None:
        self._articles: dict[str, EducationArticle] = {}
        self._by_topic: dict[str, list[EducationArticle]] = {}
        self._by_expertise: dict[str, list[EducationArticle]] = {}

    def register(self, article: EducationArticle) -> None:
        """Register an education article."""
        self._articles[article.article_id] = article

        if article.topic not in self._by_topic:
            self._by_topic[article.topic] = []
        self._by_topic[article.topic].append(article)

        key = article.expertise.value
        if key not in self._by_expertise:
            self._by_expertise[key] = []
        self._by_expertise[key].append(article)

    def get(self, article_id: str) -> Optional[EducationArticle]:
        """Get an article by ID."""
        return self._articles.get(article_id)

    def get_by_topic(self, topic: str, expertise: ExpertiseLevel | None = None) -> tuple[EducationArticle, ...]:
        """Get articles for a topic, optionally filtered by expertise."""
        articles = self._by_topic.get(topic, [])
        if expertise:
            articles = [a for a in articles if a.expertise == expertise]
        return tuple(articles)

    def get_by_expertise(self, expertise: ExpertiseLevel) -> tuple[EducationArticle, ...]:
        """Get all articles at an expertise level."""
        return tuple(self._by_expertise.get(expertise.value, []))

    def search(self, keyword: str) -> tuple[EducationArticle, ...]:
        """Search articles by keyword in title, summary, or keywords."""
        kw = keyword.lower()
        results = []
        for article in self._articles.values():
            if (kw in article.title.lower()
                or kw in article.summary.lower()
                or any(kw in k.lower() for k in article.keywords)):
                results.append(article)
        return tuple(results)

    def get_related(self, article_id: str) -> tuple[EducationArticle, ...]:
        """Get related articles for a given article."""
        article = self._articles.get(article_id)
        if not article:
            return ()
        return tuple(
            self._articles[rid] for rid in article.related_articles
            if rid in self._articles
        )

    @property
    def all_topics(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_topic.keys()))

    @property
    def article_count(self) -> int:
        return len(self._articles)


# ── Build education content ───────────────────────────────────────────

def _build_education_content() -> EducationContent:
    """Build the complete taxpayer education content library."""
    ec = EducationContent()

    # ── Beginner: Regime Choice ──
    ec.register(EducationArticle(
        article_id="edu_regime_intro",
        title="Old vs New Tax Regime: Which Should You Choose?",
        summary="A simple guide to choosing between the Old and New Tax Regimes. Learn which one saves you more tax based on your salary, deductions, and lifestyle.",
        content="""## Old vs New Tax Regime

### What Are They?
The government gives you two ways to calculate your income tax:

**New Regime (Default)**
- Lower tax rates
- Fewer deductions and exemptions
- Simpler — less paperwork
- Default from FY2023-24

**Old Regime**
- Higher tax rates
- All deductions available (80C, 80D, HRA, etc.)
- More complex — need proof of investments
- Must be explicitly chosen

### Simple Rule of Thumb
- If your total deductions (80C + 80D + HRA + home loan interest + others) exceed ₹3,75,000 → Old Regime usually better
- If you have few deductions → New Regime usually better

### Don't Guess — Use TaxStox
Upload your Form 16 and AIS. We compute both regimes automatically and tell you which saves more tax — with exact numbers and explanations.""",
        topic="regime", expertise=ExpertiseLevel.BEGINNER,
        provision_references=("sec_115bac",),
        related_articles=("edu_80c_intro", "edu_hra_intro"),
        estimated_read_minutes=4,
        keywords=("regime", "old", "new", "comparison", "save tax"),
    ))

    ec.register(EducationArticle(
        article_id="edu_80c_intro",
        title="Section 80C: Your Biggest Tax-Saving Tool",
        summary="Section 80C lets you reduce taxable income by up to ₹1.5 lakh through investments and expenses you may already be making.",
        content="""## Section 80C: Save Tax While Saving Money

### What Is 80C?
Section 80C is the most popular tax-saving section. It gives you a deduction of up to **₹1,50,000** from your taxable income for money you invest or spend on specified items.

### What Qualifies for 80C?
| Category | Examples | Notes |
|----------|---------|-------|
| **Automatic** | EPF (Provident Fund) | Already deducted from your salary |
| **Investments** | PPF, ELSS, NSC, Tax-saving FD, NPS | Must invest before March 31 |
| **Insurance** | LIC premium | Max 10% of sum assured |
| **Children** | Tuition fees | Max 2 children |
| **Home Loan** | Principal repayment | Only principal, not interest |
| **Savings** | Sukanya Samriddhi, SCSS | Specific eligible schemes |

### Pro Tips
1. Check your Form 16 — EPF is already counted
2. Don't over-invest beyond ₹1.5L (no additional benefit)
3. Consider ELSS (3-year lock-in, shortest among 80C options)
4. Home loan principal + EPF often fills most of the limit""",
        topic="deduction", expertise=ExpertiseLevel.BEGINNER,
        provision_references=("sec_80c",),
        related_articles=("edu_80c_advanced", "edu_regime_intro"),
        estimated_read_minutes=5,
        keywords=("80c", "deduction", "PPF", "ELSS", "EPF", "tax saving", "investment"),
    ))

    ec.register(EducationArticle(
        article_id="edu_hra_intro",
        title="HRA: How to Save Tax on Rent You Already Pay",
        summary="If you receive HRA from your employer and pay rent, you can claim substantial tax exemption. Learn how the formula works.",
        content="""## HRA Exemption: Tax-Free Rent Allowance

### What Is HRA?
House Rent Allowance (HRA) is part of your salary that can be tax-free if you pay rent. Under Section 10(13A), the **minimum** of these three amounts is exempt:

1. Actual HRA received from employer
2. Rent paid minus 10% of Basic Salary
3. 50% of Basic (metro cities) or 40% (non-metro)

### Example
- Basic Salary: ₹6,00,000
- HRA Received: ₹2,40,000
- Rent Paid: ₹1,80,000 (₹15,000/month)
- Metro city: Yes
  - 50% of Basic: ₹3,00,000
  - Rent minus 10% of Basic: ₹1,80,000 - ₹60,000 = ₹1,20,000
  - HRA exempt: min(₹2,40,000, ₹1,20,000, ₹3,00,000) = **₹1,20,000**

### Important
- HRA exemption is ONLY available under Old Regime
- Landlord PAN required if annual rent > ₹1,00,000
- If you don't get HRA but pay rent, check Section 80GG""",
        topic="exemption", expertise=ExpertiseLevel.BEGINNER,
        provision_references=("hra_1013a", "sec_80gg"),
        related_articles=("edu_regime_intro", "edu_salary_intro"),
        estimated_read_minutes=4,
        keywords=("HRA", "rent", "exemption", "salary", "metro", "house rent"),
    ))

    # ── Intermediate: Capital Gains ──
    ec.register(EducationArticle(
        article_id="edu_cg_basics",
        title="Capital Gains Tax: What Every Investor Must Know",
        summary="Selling shares, mutual funds, or property? Understand short-term vs long-term capital gains, tax rates, and how to report them correctly.",
        content="""## Capital Gains Tax Explained

### Two Types of Capital Gains

**Short-Term Capital Gains (STCG)**
- Equity (shares/MF): Held ≤12 months → **15% tax** under Section 111A
- Non-equity (debt funds, gold, property): Held ≤24 months → Taxed at your slab rate

**Long-Term Capital Gains (LTCG)**
- Equity: Held >12 months → **12.5% tax** under Section 112A (₹1.25L exemption)
- Non-equity: Held >24 months → **12.5% tax** without indexation

### The ₹1.25 Lakh Exemption
Under Section 112A, the first ₹1,25,000 of equity LTCG is tax-free. This is a per-year exemption — use it!

### How TaxStox Helps
- Upload your broker statements (Zerodha, Groww, Upstox, Angel One)
- We automatically classify every trade as STCG or LTCG
- We apply the ₹1.25L exemption and compute exact tax
- We map everything to the correct ITR schedules (112A, CG A2, A5, B8)""",
        topic="capital_gains", expertise=ExpertiseLevel.INTERMEDIATE,
        provision_references=("sec_112a", "sec_111a"),
        related_articles=("edu_cg_advanced",),
        estimated_read_minutes=6,
        keywords=("capital gains", "STCG", "LTCG", "shares", "equity", "mutual funds", "112A", "exemption"),
    ))

    ec.register(EducationArticle(
        article_id="edu_home_loan",
        title="Home Loan Tax Benefits: Interest + Principal",
        summary="A home loan gives you two types of tax benefits — principal under 80C and interest under Section 24(b). Here's how to maximize both.",
        content="""## Home Loan Tax Benefits

### Two Separate Deductions

1. **Principal Repayment → Section 80C**
   - Part of the ₹1.5L aggregate limit
   - Must hold property for 5 years; else earlier deductions are reversed

2. **Interest Payment → Section 24(b)**
   - Self-occupied: Max ₹2,00,000 deduction
   - Let-out property: Full interest deductible
   - Pre-construction interest: Amortized over 5 years from possession

### First-Time Homebuyer Bonus
Section 80EEA: Additional ₹1,50,000 deduction for affordable housing if:
- Loan sanctioned between April 2019 and March 2022
- Stamp duty ≤₹45 lakh
- You don't own any other residential property

### Pro Tip
If both spouses are co-borrowers and co-owners, both can claim the deduction (doubling the benefit).""",
        topic="deduction", expertise=ExpertiseLevel.INTERMEDIATE,
        provision_references=("sec_24b", "sec_80c", "sec_80eea"),
        related_articles=("edu_80c_intro",),
        estimated_read_minutes=5,
        keywords=("home loan", "housing loan", "interest", "principal", "24b", "80EEA"),
    ))

    # ── Advanced ──
    ec.register(EducationArticle(
        article_id="edu_surcharge_marginal",
        title="Surcharge & Marginal Relief: The Advanced Guide",
        summary="When income crosses ₹50 lakh, surcharge kicks in. But marginal relief ensures surcharge never exceeds the excess income. Understand how this works.",
        content="""## Surcharge & Marginal Relief

### Surcharge Rates (Individuals, FY2025-26)
| Total Income | Surcharge Rate |
|-------------|---------------|
| ≤₹50 lakh | 0% |
| ₹50L – ₹1Cr | 10% |
| ₹1Cr – ₹2Cr | 15% |
| ₹2Cr – ₹5Cr | 25% |
| >₹5Cr | 37% |

### Marginal Relief Explained
Imagine your income is ₹50,10,000 (just ₹10,000 above the threshold):
- Tax (say): ₹13,10,000
- Surcharge at 10%: ₹1,31,000
- But excess income over ₹50L is only ₹10,000
- Marginal relief: Surcharge limited to ₹10,000
- **Net surcharge: ₹10,000** (instead of ₹1,31,000)

### After Surcharge: HEC
Health & Education Cess at 4% is applied on (Tax + Surcharge). It applies to everyone, with no exemption.""",
        topic="computation", expertise=ExpertiseLevel.ADVANCED,
        provision_references=("surcharge", "cess"),
        related_articles=(),
        estimated_read_minutes=6,
        keywords=("surcharge", "marginal relief", "high income", "cess", "HEC"),
    ))

    ec.register(EducationArticle(
        article_id="edu_cg_advanced",
        title="Capital Gains: Grandfathering, Corporate Actions & Carry-Forward",
        summary="Deep dive into LTCG grandfathering for pre-2018 equity, corporate action cost adjustments, and capital loss set-off and carry-forward rules.",
        content="""## Advanced Capital Gains

### Grandfathering (Section 112A)
For equity shares/MF units acquired before **January 31, 2018**:
- Cost of acquisition = Higher of: (a) Actual cost, or (b) Lower of: (i) FMV on Jan 31, 2018, or (ii) Sale consideration
- This prevents taxing gains that accrued before the LTCG tax was introduced

### Corporate Actions
- **Bonus shares**: Cost = Zero (for bonus), holding period from allotment
- **Rights shares**: Cost = amount paid, holding period from allotment
- **Stock split**: Cost per share = Original cost ÷ Split ratio

### Capital Loss Rules
- **STCL** can be set off against both STCG and LTCG
- **LTCL** can be set off ONLY against LTCG
- Unabsorbed losses: STCL carried forward 8 years, LTCL 8 years
- Must file ITR before due date to carry forward losses""",
        topic="capital_gains", expertise=ExpertiseLevel.ADVANCED,
        provision_references=("sec_112a", "sec_111a"),
        related_articles=("edu_cg_basics",),
        estimated_read_minutes=8,
        keywords=("grandfathering", "corporate actions", "bonus", "split", "capital loss", "carry forward"),
    ))

    ec.register(EducationArticle(
        article_id="edu_nri_taxation",
        title="NRI Taxation: What You Need to Know",
        summary="As an NRI, you're taxed differently from residents. Understand residential status, India-source income, DTAA benefits, and Schedule FA requirements.",
        content="""## NRI Taxation Guide

### Residential Status (Section 6)
You are **Non-Resident (NR)** if:
- Days in India < 60 in the current FY, OR
- Days in India < 60 + <365 in previous 4 years

### What Income Is Taxable for NRIs?
- **Taxable in India**: Salary for services in India, rental income from Indian property, capital gains on Indian assets, interest from Indian bank accounts
- **Not taxable in India**: Foreign salary, foreign business income, foreign investments (unless received in India)

### DTAA (Double Taxation Avoidance Agreement)
India has DTAAs with 90+ countries. If tax is paid in both countries, DTAA provides relief either via:
- **Exemption method**: Income taxed in only one country
- **Credit method**: Foreign tax credited against Indian tax

### Schedule FA — Don't Miss This
Every NRI must disclose foreign assets in Schedule FA if held during the year. Penalty for non-disclosure: **₹10 lakh** under the Black Money Act.""",
        topic="filing", expertise=ExpertiseLevel.ADVANCED,
        provision_references=("sec_6",),
        related_articles=(),
        estimated_read_minutes=7,
        keywords=("NRI", "non-resident", "DTAA", "foreign assets", "Schedule FA", "residential status"),
    ))

    return ec


education_content = _build_education_content()
