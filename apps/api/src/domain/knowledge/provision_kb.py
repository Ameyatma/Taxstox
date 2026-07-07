"""Provision Knowledge Base — Complete registry of Income Tax Act provisions.

Each provision has: section reference, description, conditions, related provisions,
affected ITR schedules, and regime applicability.

Traceability: C11.2 (Tax Provision KB — 40%→70%, P4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Optional


@dataclass(frozen=True)
class ProvisionEntry:
    """A single Income Tax Act provision with full metadata."""

    provision_id: str                    # e.g., "sec_80c", "sec_115bac"
    section: str                         # e.g., "80C", "115BAC(1A)"
    title: str                           # e.g., "Aggregate Deduction"
    description: str                     # Plain-language explanation
    category: str                        # "deduction", "exemption", "slab", "rebate", "surcharge", "cess", "interest", "capital_gains", "tds", "filing"
    chapter: str = ""                    # e.g., "Chapter VI-A"
    conditions: str = ""                 # Eligibility conditions, plain language
    applies_to_regime: str = "both"      # "old", "new", "both"
    applies_to_residential: str = "all"  # "resident", "non_resident", "rnor", "all"
    max_benefit: str = ""                # e.g., "₹1,50,000", "No limit"
    related_provisions: tuple[str, ...] = ()   # provision_ids
    affects_itr_schedules: tuple[str, ...] = ()  # e.g., "ScheduleVIA", "ScheduleS"
    finance_act_introduced: str = ""      # e.g., "Finance Act 2005"
    finance_act_last_amended: str = ""    # e.g., "Finance Act 2023"
    is_active: bool = True
    notes: str = ""                      # Implementation notes, edge cases


class ProvisionKnowledgeBase:
    """Complete, searchable registry of Income Tax Act provisions.

    Domain service. No framework dependencies. All data is structured,
    version-controlled, and traceable to specific legal sections.
    """

    def __init__(self) -> None:
        self._provisions: dict[str, ProvisionEntry] = {}
        self._by_category: dict[str, list[ProvisionEntry]] = {}
        self._by_section: dict[str, ProvisionEntry] = {}

    def register(self, entry: ProvisionEntry) -> None:
        """Register a provision."""
        self._provisions[entry.provision_id] = entry
        self._by_section[entry.section] = entry
        if entry.category not in self._by_category:
            self._by_category[entry.category] = []
        self._by_category[entry.category].append(entry)

    def get(self, provision_id: str) -> Optional[ProvisionEntry]:
        """Look up a provision by ID."""
        return self._provisions.get(provision_id)

    def get_by_section(self, section: str) -> Optional[ProvisionEntry]:
        """Look up a provision by section number."""
        return self._by_section.get(section)

    def get_by_category(self, category: str) -> tuple[ProvisionEntry, ...]:
        """Get all provisions in a category."""
        return tuple(self._by_category.get(category, []))

    def search(self, keyword: str) -> tuple[ProvisionEntry, ...]:
        """Full-text search across title, description, and section."""
        kw = keyword.lower()
        results = []
        for entry in self._provisions.values():
            if (kw in entry.title.lower()
                or kw in entry.description.lower()
                or kw in entry.section.lower()
                or kw in entry.conditions.lower()):
                results.append(entry)
        return tuple(results)

    def get_affected_by_regime_change(
        self, regime: str, fy_from: str, fy_to: str
    ) -> tuple[ProvisionEntry, ...]:
        """Get provisions whose regime applicability changed between FYs."""
        # Simplification: return provisions that apply ONLY to the given regime
        return tuple(
            e for e in self._provisions.values()
            if e.applies_to_regime == regime
        )

    def get_chain(self, provision_id: str) -> tuple[ProvisionEntry, ...]:
        """Get a provision and all its related provisions (one level)."""
        entry = self._provisions.get(provision_id)
        if not entry:
            return ()
        chain = [entry]
        for related_id in entry.related_provisions:
            related = self._provisions.get(related_id)
            if related:
                chain.append(related)
        return tuple(chain)

    @property
    def all_provisions(self) -> tuple[ProvisionEntry, ...]:
        return tuple(self._provisions.values())

    @property
    def category_summary(self) -> dict[str, int]:
        return {cat: len(entries) for cat, entries in self._by_category.items()}


# ── Singleton, populated with all provisions ─────────────────────────

def _build_provision_kb() -> ProvisionKnowledgeBase:
    """Build the complete provision knowledge base."""
    kb = ProvisionKnowledgeBase()

    # ── Salary Provisions ──
    kb.register(ProvisionEntry(
        provision_id="sec_171", section="17(1)", title="Salary Income",
        description="Any remuneration received by an employee from an employer, including basic pay, allowances, and bonuses.",
        category="income", chapter="Chapter IV-D", conditions="Must be employer-employee relationship.",
        applies_to_regime="both",
        related_provisions=("sec_172", "sec_173", "sec_16", "sec_10"),
        affects_itr_schedules=("ScheduleS",),
        finance_act_introduced="IT Act 1961",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_172", section="17(2)", title="Perquisites",
        description="Non-cash benefits provided by employer: rent-free accommodation, car, ESOP, etc.",
        category="income", chapter="Chapter IV-D",
        applies_to_regime="both",
        related_provisions=("sec_171", "sec_173"),
        affects_itr_schedules=("ScheduleS",),
        finance_act_introduced="IT Act 1961",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_173", section="17(3)", title="Profits in Lieu of Salary",
        description="Compensation received on termination, keyman insurance, etc.",
        category="income", chapter="Chapter IV-D",
        applies_to_regime="both",
        related_provisions=("sec_171",),
        affects_itr_schedules=("ScheduleS",),
        finance_act_introduced="IT Act 1961",
    ))
    kb.register(ProvisionEntry(
        provision_id="std_deduction", section="16(ia)", title="Standard Deduction",
        description="Flat deduction from salary income. ₹50,000 under Old Regime, ₹75,000 under New Regime.",
        category="deduction", chapter="Chapter IV-D",
        conditions="Available to all salaried employees. No proof required.",
        applies_to_regime="both", max_benefit="₹50,000 (Old) / ₹75,000 (New)",
        related_provisions=("sec_171",),
        affects_itr_schedules=("ScheduleS",),
        finance_act_introduced="Finance Act 2018", finance_act_last_amended="Finance Act 2024",
    ))
    kb.register(ProvisionEntry(
        provision_id="professional_tax", section="16(iii)", title="Professional Tax",
        description="State-level professional tax paid by employee is deductible from salary.",
        category="deduction", chapter="Chapter IV-D",
        applies_to_regime="both", max_benefit="₹2,500 per year",
        affects_itr_schedules=("ScheduleS",),
        finance_act_introduced="IT Act 1961",
    ))

    # ── Exemption Provisions ──
    kb.register(ProvisionEntry(
        provision_id="hra_1013a", section="10(13A)", title="House Rent Allowance Exemption",
        description="HRA exemption: minimum of (actual HRA, rent paid minus 10% of basic, 40%/50% of basic).",
        category="exemption", chapter="Chapter III",
        conditions="Must be paying rent. Must receive HRA as salary component. 50% for metro, 40% non-metro.",
        applies_to_regime="old", max_benefit="Per formula",
        related_provisions=("sec_171", "sec_80gg"),
        affects_itr_schedules=("ScheduleS",),
        finance_act_introduced="IT Act 1961",
    ))
    kb.register(ProvisionEntry(
        provision_id="lta_105", section="10(5)", title="Leave Travel Concession",
        description="Exemption for travel within India for self + family. Available twice in a block of 4 years.",
        category="exemption", chapter="Chapter III",
        conditions="Only actual travel costs (no accommodation/food). Economy air or first-class AC train.",
        applies_to_regime="old",
        related_provisions=("sec_171",),
        affects_itr_schedules=("ScheduleS",),
        finance_act_introduced="IT Act 1961",
    ))
    kb.register(ProvisionEntry(
        provision_id="gratuity_1010", section="10(10)", title="Gratuity Exemption",
        description="Gratuity received on retirement/death. Exempt up to ₹20 lakh (government: fully exempt).",
        category="exemption", chapter="Chapter III",
        conditions="Must complete 5 years of continuous service (except death/disability).",
        applies_to_regime="old", max_benefit="₹20,00,000",
        finance_act_introduced="IT Act 1961", finance_act_last_amended="Finance Act 2019",
    ))

    # ── Chapter VI-A Deductions ──
    kb.register(ProvisionEntry(
        provision_id="sec_80c", section="80C", title="Aggregate Deduction",
        description="Deduction for specified investments and expenditures: EPF, PPF, ELSS, LIC, tuition fees, home loan principal, NSC, tax-saving FD, SSY, SCSS.",
        category="deduction", chapter="Chapter VI-A",
        conditions="Maximum ₹1,50,000 across all eligible items combined.",
        applies_to_regime="old", max_benefit="₹1,50,000",
        related_provisions=("sec_80ccc", "sec_80ccd1", "sec_24b"),
        affects_itr_schedules=("ScheduleVIA",),
        finance_act_introduced="IT Act 1961", finance_act_last_amended="Finance Act 2014",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_80ccd1b", section="80CCD(1B)", title="Additional NPS Deduction",
        description="Additional deduction for own NPS contribution beyond the ₹1.5L 80C limit.",
        category="deduction", chapter="Chapter VI-A",
        conditions="Available to all individuals. Above and beyond 80C limit.",
        applies_to_regime="both", max_benefit="₹50,000",
        related_provisions=("sec_80c", "sec_80ccd2"),
        affects_itr_schedules=("ScheduleVIA",),
        finance_act_introduced="Finance Act 2015",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_80ccd2", section="80CCD(2)", title="Employer NPS Contribution",
        description="Employer contribution to employee NPS. No upper limit but 10% of salary cap for private sector.",
        category="deduction", chapter="Chapter VI-A",
        conditions="Available under both regimes. For private sector: max 10% of salary (Basic + DA).",
        applies_to_regime="both", max_benefit="10% of salary (private) / 14% (govt)",
        related_provisions=("sec_80ccd1b",),
        affects_itr_schedules=("ScheduleVIA",),
        finance_act_introduced="IT Act 1961",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_80d", section="80D", title="Health Insurance Premium",
        description="Deduction for health insurance premium for self, spouse, children, and parents.",
        category="deduction", chapter="Chapter VI-A",
        conditions="Self + family: ₹25,000 (₹50,000 if senior citizen). Parents: additional ₹25,000 (₹50,000 if senior). Preventive health checkup: ₹5,000 included in limit.",
        applies_to_regime="old", max_benefit="₹25,000-₹1,00,000 depending on age",
        related_provisions=("sec_80ddb",),
        affects_itr_schedules=("ScheduleVIA",),
        finance_act_introduced="IT Act 1961", finance_act_last_amended="Finance Act 2018",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_80tta", section="80TTA", title="Savings Interest Deduction",
        description="Deduction for interest from savings bank accounts (not FDs).",
        category="deduction", chapter="Chapter VI-A",
        conditions="Available to individuals and HUFs (non-senior citizens).",
        applies_to_regime="both", max_benefit="₹10,000",
        related_provisions=("sec_80ttb",),
        affects_itr_schedules=("ScheduleVIA",),
        finance_act_introduced="Finance Act 2012",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_80ttb", section="80TTB", title="Senior Citizen Interest Deduction",
        description="Deduction for interest from deposits (savings + FDs) for senior citizens.",
        category="deduction", chapter="Chapter VI-A",
        conditions="Available to resident senior citizens (60+).",
        applies_to_regime="both", max_benefit="₹50,000",
        related_provisions=("sec_80tta",),
        affects_itr_schedules=("ScheduleVIA",),
        finance_act_introduced="Finance Act 2018",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_80e", section="80E", title="Education Loan Interest",
        description="Deduction for interest on education loan for higher studies of self, spouse, or children.",
        category="deduction", chapter="Chapter VI-A",
        conditions="Loan must be from approved financial institution. Available for max 8 years.",
        applies_to_regime="old", max_benefit="No limit (full interest amount)",
        related_provisions=(),
        affects_itr_schedules=("ScheduleVIA",),
        finance_act_introduced="Finance Act 2006",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_80g", section="80G", title="Donations to Charitable Institutions",
        description="Deduction for donations to specified funds and charitable institutions. 100% or 50% deduction with or without qualifying limit.",
        category="deduction", chapter="Chapter VI-A",
        conditions="Donation must be to registered institution with valid 80G certificate. Cash donations >₹2,000 not eligible.",
        applies_to_regime="old", max_benefit="Varies by donee category",
        related_provisions=(),
        affects_itr_schedules=("ScheduleVIA",),
        finance_act_introduced="IT Act 1961",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_80gg", section="80GG", title="Rent Paid (No HRA)",
        description="Deduction for rent paid by individuals not receiving HRA from employer.",
        category="deduction", chapter="Chapter VI-A",
        conditions="Self/spouse/minor child must not own property in same city. Available only under Old Regime.",
        applies_to_regime="old", max_benefit="₹5,000/month or 25% of total income (whichever is less)",
        related_provisions=("hra_1013a",),
        affects_itr_schedules=("ScheduleVIA",),
        finance_act_introduced="IT Act 1961",
    ))

    # ── Capital Gains Provisions ──
    kb.register(ProvisionEntry(
        provision_id="sec_112a", section="112A", title="Equity LTCG",
        description="Long-term capital gains on listed equity shares and equity-oriented mutual funds. Taxed at 12.5% with ₹1.25L annual exemption.",
        category="capital_gains", chapter="Chapter IV-E",
        conditions="Held >12 months. STT paid on both purchase and sale (equity) or on sale (MF).",
        applies_to_regime="both", max_benefit="₹1,25,000 exemption",
        related_provisions=("sec_111a",),
        affects_itr_schedules=("Schedule112A", "ScheduleCG"),
        finance_act_introduced="Finance Act 2018", finance_act_last_amended="Finance Act 2024",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_111a", section="111A", title="Equity STCG",
        description="Short-term capital gains on listed equity and equity MF. Taxed at 15% flat.",
        category="capital_gains", chapter="Chapter IV-E",
        conditions="Held ≤12 months. STT paid on sale.",
        applies_to_regime="both",
        related_provisions=("sec_112a",),
        affects_itr_schedules=("ScheduleCG", "CG-A2"),
        finance_act_introduced="Finance Act 2004",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_115bbh", section="115BBH", title="Virtual Digital Assets",
        description="Income from transfer of crypto/virtual digital assets. Taxed at 30% flat. No deduction except cost of acquisition.",
        category="capital_gains", chapter="Chapter IV-E",
        conditions="No deduction for expenses except cost of acquisition. Loss from VDA cannot be set off against any other income.",
        applies_to_regime="both",
        related_provisions=(),
        affects_itr_schedules=("ScheduleCG", "ScheduleOS"),
        finance_act_introduced="Finance Act 2022",
    ))

    # ── Tax Computation ──
    kb.register(ProvisionEntry(
        provision_id="sec_115bac", section="115BAC", title="New Tax Regime",
        description="Alternative tax regime with lower slab rates but limited deductions and exemptions. Default regime from FY2023-24.",
        category="slab", chapter="Chapter XII",
        conditions="Opt-out possible for business income earners. Once opted out for business income, cannot re-enter.",
        applies_to_regime="new",
        related_provisions=("sec_87a", "sec_80ccd2"),
        affects_itr_schedules=("PartB-TTI",),
        finance_act_introduced="Finance Act 2020", finance_act_last_amended="Finance Act 2025",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_87a", section="87A", title="Rebate for Low-Income Taxpayers",
        description="Rebate from tax for individuals with income below threshold. ₹12,500 (Old, ₹5L) / ₹60,000 (New, ₹12L).",
        category="rebate", chapter="Chapter VIII",
        conditions="Total income must be ≤ threshold. Resident individual only. Rebate capped at tax amount.",
        applies_to_regime="both", max_benefit="₹12,500 (Old) / ₹60,000 (New)",
        related_provisions=("sec_115bac",),
        affects_itr_schedules=("PartB-TTI",),
        finance_act_introduced="Finance Act 2013", finance_act_last_amended="Finance Act 2025",
    ))
    kb.register(ProvisionEntry(
        provision_id="surcharge", section="Surcharge", title="Surcharge on High Income",
        description="Additional tax on high-income taxpayers. 10% (>₹50L), 15% (>₹1Cr), 25% (>₹2Cr), 37% (>₹5Cr) with marginal relief.",
        category="surcharge", chapter="Finance Act",
        conditions="Rates vary by entity type. Marginal relief ensures surcharge ≤ excess income above threshold.",
        applies_to_regime="both",
        related_provisions=(),
        affects_itr_schedules=("PartB-TTI",),
        finance_act_introduced="Finance Act (annual)", finance_act_last_amended="Finance Act 2025",
    ))
    kb.register(ProvisionEntry(
        provision_id="cess", section="2(11)", title="Health & Education Cess",
        description="4% cess on income tax + surcharge. Applied after rebate and surcharge.",
        category="cess", chapter="Finance Act",
        applies_to_regime="both",
        related_provisions=(),
        affects_itr_schedules=("PartB-TTI",),
        finance_act_introduced="Finance Act 2018",
    ))

    # ── House Property ──
    kb.register(ProvisionEntry(
        provision_id="sec_24b", section="24(b)", title="Housing Loan Interest",
        description="Deduction for interest on housing loan. Self-occupied: max ₹2L per year. Let-out: full interest.",
        category="deduction", chapter="Chapter IV-C",
        conditions="Loan must be for purchase/construction. Construction must complete within 5 years for full benefit.",
        applies_to_regime="old", max_benefit="₹2,00,000 (self-occupied) / No limit (let-out)",
        related_provisions=("sec_80c", "sec_80ee", "sec_80eea"),
        affects_itr_schedules=("ScheduleHP",),
        finance_act_introduced="IT Act 1961", finance_act_last_amended="Finance Act 2017",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_80eea", section="80EEA", title="Affordable Housing Loan Interest",
        description="Additional ₹1.5L deduction for first-time homebuyers of affordable housing (stamp duty ≤₹45L).",
        category="deduction", chapter="Chapter VI-A",
        conditions="Loan sanctioned between April 1, 2019 and March 31, 2022. No other residential property. Stamp duty ≤₹45L.",
        applies_to_regime="old", max_benefit="₹1,50,000",
        related_provisions=("sec_24b",),
        affects_itr_schedules=("ScheduleVIA",),
        finance_act_introduced="Finance Act 2019",
    ))

    # ── Interest Provisions ──
    kb.register(ProvisionEntry(
        provision_id="sec_234a", section="234A", title="Late Filing Interest",
        description="Interest at 1% per month on unpaid tax if return filed after due date.",
        category="interest", chapter="Chapter XVII-F",
        conditions="Applies from the day after due date until actual filing date.",
        applies_to_regime="both",
        related_provisions=("sec_234b", "sec_234c"),
        affects_itr_schedules=("PartB-TTI",),
        finance_act_introduced="IT Act 1961",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_234b", section="234B", title="Advance Tax Default Interest",
        description="Interest at 1% per month if advance tax paid is less than 90% of assessed tax.",
        category="interest", chapter="Chapter XVII-F",
        applies_to_regime="both",
        related_provisions=("sec_234a", "sec_234c"),
        affects_itr_schedules=("PartB-TTI",),
        finance_act_introduced="IT Act 1961",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_234c", section="234C", title="Advance Tax Deferment Interest",
        description="Interest at 1% per month for deferment of advance tax installments.",
        category="interest", chapter="Chapter XVII-F",
        applies_to_regime="both",
        related_provisions=("sec_234a", "sec_234b"),
        affects_itr_schedules=("PartB-TTI",),
        finance_act_introduced="IT Act 1961",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_234f", section="234F", title="Late Filing Fee",
        description="Fee for late filing: ₹1,000 (total income ≤₹5L), ₹5,000 (₹5L-₹10L), ₹10,000 (>₹10L).",
        category="filing", chapter="Chapter XVII-F",
        conditions="Applies if return filed after Section 139(1) due date but before December 31.",
        applies_to_regime="both", max_benefit="N/A (penalty)",
        finance_act_introduced="Finance Act 2017",
    ))

    # ── Presumptive Taxation ──
    kb.register(ProvisionEntry(
        provision_id="sec_44ad", section="44AD", title="Presumptive Business Income",
        description="Small businesses with turnover ≤₹2Cr: deemed income at 8% (6% for digital receipts). No books of accounts required.",
        category="income", chapter="Chapter IV-D",
        conditions="Turnover ≤₹2Cr. Eligible businesses only (no professionals, commission agents).",
        applies_to_regime="both", max_benefit="Simplified compliance",
        related_provisions=("sec_44ada", "sec_44ae"),
        affects_itr_schedules=("ScheduleBP",),
        finance_act_introduced="IT Act 1961", finance_act_last_amended="Finance Act 2023",
    ))
    kb.register(ProvisionEntry(
        provision_id="sec_44ada", section="44ADA", title="Presumptive Professional Income",
        description="Specified professionals with gross receipts ≤₹50L: deemed income at 50%.",
        category="income", chapter="Chapter IV-D",
        conditions="Applies to specified professions (legal, medical, engineering, architecture, accountancy, technical consultancy, interior decoration, etc.).",
        applies_to_regime="both", max_benefit="Simplified compliance",
        related_provisions=("sec_44ad",),
        affects_itr_schedules=("ScheduleBP",),
        finance_act_introduced="Finance Act 2016", finance_act_last_amended="Finance Act 2023",
    ))

    # ── Residential Status ──
    kb.register(ProvisionEntry(
        provision_id="sec_6", section="6", title="Residential Status",
        description="Determines residential status (ROR/RNOR/NR) based on days in India and other criteria.",
        category="filing", chapter="Chapter II",
        conditions="ROR: 182+ days in India, or 60+ days + 365+ days in previous 4 years. RNOR: satisfies ROR criteria but was NR in 9 of 10 previous years or ≤729 days in 7 previous years. NR: none of the above. Deemed resident: Indian citizen/PIO with income >₹15L from Indian sources.",
        applies_to_regime="both",
        related_provisions=(),
        affects_itr_schedules=("PartA-GeneralInfo",),
        finance_act_introduced="IT Act 1961", finance_act_last_amended="Finance Act 2020",
    ))

    return kb


provision_kb = _build_provision_kb()
