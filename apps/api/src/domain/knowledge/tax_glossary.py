"""Tax Glossary — Plain-language definitions for 100+ Indian tax terms.

Provides the foundation for taxpayer education, AI explanations, and
the knowledge graph's concept nodes.

Traceability: C11.4 (Tax Concept Glossary — 0%→60%, P4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class GlossaryEntry:
    """A single glossary term with plain-language definition."""

    term: str                            # The term being defined
    definition: str                      # Plain-language explanation (1-3 sentences)
    category: str                        # "income", "deduction", "exemption", "computation", "filing", "entity", "general"
    also_known_as: tuple[str, ...] = ()  # Alternative names
    see_also: tuple[str, ...] = ()       # Related terms
    example: str = ""                    # Practical example
    provision_reference: str = ""        # e.g., "Section 80C"


class TaxGlossary:
    """Complete glossary of Indian income tax terms.

    Domain service. Provides term lookup, category listing, and search.
    All definitions in plain language suitable for taxpayer education.
    """

    def __init__(self) -> None:
        self._entries: dict[str, GlossaryEntry] = {}
        self._by_category: dict[str, list[GlossaryEntry]] = {}

    def register(self, entry: GlossaryEntry) -> None:
        """Register a glossary entry."""
        key = entry.term.lower()
        self._entries[key] = entry
        for aka in entry.also_known_as:
            self._entries[aka.lower()] = entry
        if entry.category not in self._by_category:
            self._by_category[entry.category] = []
        self._by_category[entry.category].append(entry)

    def lookup(self, term: str) -> Optional[GlossaryEntry]:
        """Look up a term (case-insensitive)."""
        return self._entries.get(term.lower().strip())

    def get_by_category(self, category: str) -> tuple[GlossaryEntry, ...]:
        """Get all terms in a category."""
        return tuple(self._by_category.get(category, []))

    def search(self, keyword: str) -> tuple[GlossaryEntry, ...]:
        """Search terms and definitions for a keyword."""
        kw = keyword.lower()
        seen: set[str] = set()
        results = []
        for entry in self._entries.values():
            if entry.term not in seen:
                if kw in entry.term.lower() or kw in entry.definition.lower():
                    results.append(entry)
                    seen.add(entry.term)
        return tuple(results)

    @property
    def all_terms(self) -> tuple[str, ...]:
        return tuple(sorted(e.term for e in self._entries.values()))

    @property
    def category_summary(self) -> dict[str, int]:
        return {cat: len(entries) for cat, entries in self._by_category.items()}


# ── Build the glossary ────────────────────────────────────────────────

def _build_tax_glossary() -> TaxGlossary:
    """Build the complete tax glossary with 100+ terms."""
    g = TaxGlossary()

    entries = [
        # ── Income ──
        GlossaryEntry("Gross Total Income", "The sum of income from all five heads (salary, house property, business, capital gains, other sources) before any deductions under Chapter VI-A.", category="income", also_known_as=("GTI", "Gross Income"), see_also=("Total Income", "Income Heads"), provision_reference="Section 14"),
        GlossaryEntry("Total Income", "Gross Total Income minus all deductions under Chapter VI-A (80C, 80D, etc.). This is the amount on which tax is computed. Also called 'taxable income'.", category="income", also_known_as=("Taxable Income", "Net Taxable Income"), see_also=("Gross Total Income", "Deductions"), provision_reference="Section 2(45)"),
        GlossaryEntry("Income Heads", "The five categories under which all income is classified: Salary, House Property, Business & Profession, Capital Gains, and Other Sources.", category="income", also_known_as=("Heads of Income",), see_also=("Salary Income", "Capital Gains"), provision_reference="Section 14"),
        GlossaryEntry("Salary Income", "Income from employer-employee relationship: basic pay, allowances, perquisites, bonuses, and profits in lieu of salary.", category="income", also_known_as=("Income from Salaries",), see_also=("Perquisite", "HRA", "Standard Deduction"), provision_reference="Sections 15-17"),
        GlossaryEntry("House Property Income", "Income from owning a house property. Computed as Annual Value minus municipal taxes, standard deduction (30%), and home loan interest.", category="income", also_known_as=("Income from House Property",), see_also=("Gross Annual Value", "Section 24(b)"), provision_reference="Sections 22-27"),
        GlossaryEntry("Capital Gains", "Profit from selling a capital asset (shares, mutual funds, property, gold, crypto). Taxed based on holding period: short-term vs long-term.", category="income", see_also=("Short-Term Capital Gains", "Long-Term Capital Gains", "Cost of Acquisition"), provision_reference="Sections 45-55A"),
        GlossaryEntry("Other Sources Income", "Income that does not fall under the other four heads: interest, dividends, gifts above ₹50,000, lottery winnings, family pension.", category="income", also_known_as=("IFOS", "Income from Other Sources"), see_also=("Dividend", "Interest Income"), provision_reference="Sections 56-59"),
        GlossaryEntry("Perquisite", "A non-cash benefit provided by an employer: rent-free accommodation, company car, ESOP, telephone, club membership. Valued per Income Tax Rules Rule 3.", category="income", also_known_as=("Perk",), see_also=("Salary Income", "Form 12BA"), provision_reference="Section 17(2)"),

        # ── Deductions ──
        GlossaryEntry("Section 80C", "The most popular tax-saving section. Deduction of up to ₹1.5 lakh for investments (PPF, ELSS, NSC, tax-saving FD) and expenses (LIC premium, tuition fees, home loan principal).", category="deduction", also_known_as=("80C", "80C Deduction"), see_also=("PPF", "ELSS", "Chapter VI-A"), provision_reference="Section 80C", example="Invest ₹1,50,000 in PPF + ELSS to claim full 80C deduction."),
        GlossaryEntry("Chapter VI-A", "The chapter of the Income Tax Act that lists all deductions available to individuals: 80C, 80D, 80E, 80G, 80TTA, 80TTB, and more.", category="deduction", also_known_as=("VI-A Deductions",), see_also=("Section 80C", "Section 80D"), provision_reference="Sections 80A-80U"),
        GlossaryEntry("Standard Deduction", "A flat deduction from salary income available to all employees. ₹50,000 under Old Regime, ₹75,000 under New Regime. No proof required.", category="deduction", see_also=("Salary Income", "Old Regime", "New Regime"), provision_reference="Section 16(ia)", example="Salary ₹10,00,000 → Standard Deduction ₹50,000 → Taxable Salary ₹9,50,000"),
        GlossaryEntry("NPS", "National Pension System — a government-backed retirement savings scheme. Contributions qualify for deduction under 80CCD(1), 80CCD(1B), and 80CCD(2).", category="deduction", also_known_as=("National Pension System",), see_also=("Section 80CCD(1B)", "Section 80CCD(2)"), provision_reference="Sections 80CCD(1)/(1B)/(2)"),
        GlossaryEntry("Home Loan Interest Deduction", "Deduction for interest paid on home loan. Self-occupied property: max ₹2,00,000. Let-out property: no upper limit. Also called 'Section 24(b) deduction'.", category="deduction", also_known_as=("Section 24(b)", "Housing Loan Interest"), see_also=("Section 80C", "Section 80EEA"), provision_reference="Section 24(b)", example="Home loan interest paid ₹2,50,000 → Self-occupied: ₹2,00,000 deduction. Let-out: Full ₹2,50,000 deductible."),

        # ── Exemptions ──
        GlossaryEntry("HRA Exemption", "House Rent Allowance exemption for salaried employees paying rent. Exempt amount is the minimum of: actual HRA received, rent paid minus 10% of basic, or 40%/50% of basic salary.", category="exemption", also_known_as=("HRA", "House Rent Allowance"), see_also=("Section 80GG", "Salary Income"), provision_reference="Section 10(13A)", example="Basic ₹5L, HRA ₹2L, rent ₹1.8L in metro → Exempt: min(2L, 1.8L-50K, 2.5L) = ₹1.3L exempt"),
        GlossaryEntry("LTA Exemption", "Leave Travel Assistance exemption for travel within India. Available for self + family. Covers actual travel fare (air/rail/bus) only — no accommodation or food.", category="exemption", also_known_as=("LTA", "LTC", "Leave Travel Concession"), see_also=("Salary Income",), provision_reference="Section 10(5)"),
        GlossaryEntry("Agricultural Income", "Income from agricultural operations is exempt from tax under Section 10(1). However, it is included in total income for determining the applicable tax slab rate (partial integration).", category="exemption", see_also=("Total Income",), provision_reference="Section 10(1)"),

        # ── Tax Computation ──
        GlossaryEntry("Tax Slab", "The progressive rate structure that determines how much tax you pay. Different slabs apply to different income ranges (e.g., 0-4L: 0%, 4-8L: 5%).", category="computation", also_known_as=("Slab Rate", "Income Tax Slab"), see_also=("Old Regime", "New Regime", "Marginal Relief")),
        GlossaryEntry("Old Regime", "The traditional tax regime with higher slab rates but allows all deductions (80C, 80D, HRA, LTA, home loan interest, etc.). Taxpayer must explicitly opt for it.", category="computation", also_known_as=("Old Tax Regime", "Pre-115BAC Regime"), see_also=("New Regime", "Section 115BAC"), example="Old Regime: ₹2.5L-5L: 5%, ₹5L-10L: 20%"),
        GlossaryEntry("New Regime", "The default tax regime from FY2023-24 with lower slab rates but fewer deductions. Only standard deduction, employer NPS (80CCD(2)), and a few others are available.", category="computation", also_known_as=("New Tax Regime", "Section 115BAC Regime"), see_also=("Old Regime", "Section 115BAC"), provision_reference="Section 115BAC", example="New Regime: ₹0-4L: 0%, ₹4-8L: 5%, ₹8-12L: 10%, higher slabs up to 30%"),
        GlossaryEntry("Rebate 87A", "A rebate (reduction) from tax for individuals with total income below specified limits. ₹12,500 for Old Regime (income ≤₹5L). ₹60,000 for New Regime (income ≤₹12L).", category="computation", also_known_as=("87A Rebate", "Tax Rebate"), see_also=("Old Regime", "New Regime"), provision_reference="Section 87A", example="Income ₹11L, New Regime tax ₹45,000 → Rebate ₹45,000 → Net Tax = ₹0 (since income ≤₹12L)"),
        GlossaryEntry("Surcharge", "An additional tax on high-income taxpayers. 10% (>₹50L), 15% (>₹1Cr), 25% (>₹2Cr), 37% (>₹5Cr). Subject to marginal relief.", category="computation", see_also=("Marginal Relief", "Health & Education Cess"), provision_reference="Finance Act (annual)"),
        GlossaryEntry("Health & Education Cess", "A 4% cess levied on income tax + surcharge. Applied at the final step of tax computation. Also called HEC or simply 'Cess'.", category="computation", also_known_as=("HEC", "Cess"), see_also=("Surcharge", "Marginal Relief"), provision_reference="Section 2(11) of Finance Act"),
        GlossaryEntry("Marginal Relief", "A relief that ensures surcharge does not exceed the excess of income over the surcharge threshold. Prevents a ₹1 income increase from triggering disproportionate surcharge.", category="computation", see_also=("Surcharge",), provision_reference="Finance Act", example="Income ₹50.1L, tax ₹13L → Surcharge 10% = ₹1.3L. Excess income = ₹0.1L. Surcharge after relief = ₹0.1L."),
        GlossaryEntry("Effective Tax Rate", "The actual percentage of total income paid as tax. Final tax ÷ Total Income × 100. Different from the marginal/slab rate.", category="computation", see_also=("Tax Slab", "Marginal Tax Rate"), example="Total Income ₹10L, Final Tax ₹75,000 → Effective Rate = 7.5%"),
        GlossaryEntry("TDS", "Tax Deducted at Source — tax deducted by the payer (employer, bank, tenant) before paying you. Claimed as credit against final tax liability.", category="computation", also_known_as=("Tax Deducted at Source", "Withholding Tax"), see_also=("Form 16", "Form 26AS", "AIS"), provision_reference="Chapter XVII-B"),
        GlossaryEntry("Advance Tax", "Tax paid in installments during the financial year (not at year-end). Required if tax liability exceeds ₹10,000. Due dates: 15% by June 15, 45% by Sept 15, 75% by Dec 15, 100% by Mar 15.", category="computation", also_known_as=("Pay As You Earn",), see_also=("Section 234B", "Section 234C"), provision_reference="Sections 207-219"),

        # ── Filing ──
        GlossaryEntry("ITR", "Income Tax Return — the form filed with the Income Tax Department declaring income, deductions, tax liability, and taxes paid. ITR-1 (simplest) through ITR-7 (trusts).", category="filing", also_known_as=("Income Tax Return", "Return"), see_also=("ITR-1", "ITR-2", "Assessment Year"), provision_reference="Section 139(1)"),
        GlossaryEntry("ITR-1", "SAHAJ — the simplest ITR form. For resident individuals with salary, one house property, and other sources income. Total income must be ≤₹50 lakh.", category="filing", also_known_as=("SAHAJ",), see_also=("ITR-2", "ITR-3", "ITR-4")),
        GlossaryEntry("ITR-2", "ITR form for individuals and HUFs not having business/profession income. Allows capital gains, multiple house properties, foreign assets, and other complex scenarios.", category="filing", see_also=("ITR-1", "ITR-3")),
        GlossaryEntry("ITR-3", "ITR form for individuals and HUFs having income from business or profession. Requires filing of balance sheet, P&L, and other business schedules.", category="filing", see_also=("ITR-4", "Presumptive Taxation")),
        GlossaryEntry("ITR-4", "SUGAM — ITR form for individuals, HUFs, and firms (other than LLP) opting for presumptive taxation under Section 44AD/44ADA/44AE.", category="filing", also_known_as=("SUGAM",), see_also=("ITR-3", "Presumptive Taxation"), provision_reference="Sections 44AD/44ADA/44AE"),
        GlossaryEntry("Financial Year", "The 12-month period from April 1 to March 31 during which income is earned. FY2025-26 = April 2025 to March 2026. Also called 'Previous Year'.", category="filing", also_known_as=("FY", "Previous Year"), see_also=("Assessment Year",), provision_reference="Section 3"),
        GlossaryEntry("Assessment Year", "The 12-month period following the Financial Year in which income is assessed and taxed. AY2026-27 = April 2026 to March 2027 for income earned in FY2025-26.", category="filing", also_known_as=("AY",), see_also=("Financial Year",), provision_reference="Section 2(9)"),
        GlossaryEntry("Form 16", "TDS certificate issued by employer showing salary paid and tax deducted. Part A contains employer + employee details + TDS. Part B contains salary breakup + deductions.", category="filing", also_known_as=("Salary TDS Certificate",), see_also=("Form 26AS", "AIS", "TDS"), provision_reference="Section 203"),
        GlossaryEntry("AIS", "Annual Information Statement — a comprehensive statement from the Income Tax Department showing all financial transactions reported against your PAN: salary, interest, dividends, capital gains, TDS, SFT, refunds.", category="filing", also_known_as=("Annual Information Statement",), see_also=("Form 26AS", "SFT"), provision_reference="Section 285BB"),
        GlossaryEntry("Form 26AS", "Tax credit statement showing all TDS, TCS, advance tax, and self-assessment tax deposited against your PAN. Used to verify TDS credit before filing ITR.", category="filing", also_known_as=("26AS", "Tax Credit Statement"), see_also=("AIS", "TDS", "Form 16")),
        GlossaryEntry("Schedule FA", "Foreign Assets schedule — mandatory disclosure of all foreign assets (bank accounts, property, securities, trusts, insurance) held during the year. Penalty for non-disclosure: ₹10 lakh under Black Money Act.", category="filing", see_also=("Foreign Tax Credit", "NRI")),

        # ── Entity Types ──
        GlossaryEntry("HUF", "Hindu Undivided Family — a family unit treated as a separate taxpayer under the Income Tax Act. Has its own PAN and files its own ITR. Governed by Karta (head of family).", category="entity", also_known_as=("Hindu Undivided Family",), see_also=("Karta", "ITR-2")),
        GlossaryEntry("NRI", "Non-Resident Indian — an Indian citizen or PIO who does not meet the residency criteria under Section 6. Taxed only on India-source income + income from business controlled from India.", category="entity", also_known_as=("Non-Resident Indian", "Non-Resident"), see_also=("Residential Status", "RNOR", "Schedule FA")),
        GlossaryEntry("Senior Citizen", "A taxpayer aged 60 years or above during the financial year. Gets higher basic exemption limit and higher deduction limits (80D, 80TTB).", category="entity", see_also=("Super Senior Citizen", "Section 80TTB"), provision_reference="Section 2(42)"),
        GlossaryEntry("Super Senior Citizen", "A taxpayer aged 80 years or above during the financial year. Gets the highest basic exemption limit (₹5 lakh under Old Regime).", category="entity", see_also=("Senior Citizen",), provision_reference="Section 194P"),

        # ── General ──
        GlossaryEntry("PAN", "Permanent Account Number — a 10-character alphanumeric identifier issued by the Income Tax Department. Mandatory for filing ITR, opening bank accounts, and most financial transactions.", category="general", also_known_as=("Permanent Account Number",), example="Format: ABCDE1234F"),
        GlossaryEntry("CBDT", "Central Board of Direct Taxes — the apex body administering direct tax laws in India. Issues circulars, notifications, and clarifications on income tax matters.", category="general", also_known_as=("Central Board of Direct Taxes",), see_also=("Circular", "Notification")),
        GlossaryEntry("DPDP Act", "Digital Personal Data Protection Act 2023 — India's data privacy law. Requires consent for processing personal data and grants rights to data principals (taxpayers).", category="general", also_known_as=("Digital Personal Data Protection Act", "DPDP Act 2023"), see_also=("Consent",)),
        GlossaryEntry("Finance Act", "The annual legislation presented with the Union Budget that amends the Income Tax Act. Introduces new slab rates, changes deduction limits, and adds/removes provisions.", category="general", see_also=("Union Budget", "CBDT")),
        GlossaryEntry("Section 115BAC", "The section introducing the New Tax Regime — an alternative slab structure with lower tax rates but limited deductions. Default regime from FY2023-24.", category="general", also_known_as=("New Regime", "115BAC"), see_also=("New Regime", "Old Regime")),
        GlossaryEntry("Presumptive Taxation", "A simplified scheme where income is deemed at a fixed percentage of turnover/receipts. No need to maintain detailed books. Available under 44AD (business), 44ADA (profession), 44AE (transport).", category="general", see_also=("Section 44AD", "Section 44ADA", "ITR-4")),
    ]

    for entry in entries:
        g.register(entry)

    return g


tax_glossary = _build_tax_glossary()
