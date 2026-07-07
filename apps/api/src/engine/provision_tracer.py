"""Legal Provision Tracer — Links every computation to specific IT Act sections.

Provides end-to-end traceability from a tax computation result back to
the specific legal provisions that produced each value.

Traceability: C10.3 (Legal Provision Tracer — 40%→70%, P1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ProvisionReference:
    """A reference to a specific legal provision."""
    section: str            # e.g., "115BAC", "80C", "87A"
    sub_section: str = ""   # e.g., "(1A)", "(2)"
    description: str = ""   # Plain-language description
    finance_act: str = ""   # e.g., "Finance Act 2025"


# ── Standard Provision Map ───────────────────────────────────────────

PROVISION_MAP: dict[str, ProvisionReference] = {
    # Salary
    "salary_171": ProvisionReference("17(1)", "", "Salary income", "IT Act 1961"),
    "salary_172": ProvisionReference("17(2)", "", "Perquisites", "IT Act 1961"),
    "salary_173": ProvisionReference("17(3)", "", "Profits in lieu of salary", "IT Act 1961"),
    "std_deduction": ProvisionReference("16(ia)", "", "Standard deduction from salary", "Finance Act 2018"),
    "professional_tax": ProvisionReference("16(iii)", "", "Professional tax deduction", "IT Act 1961"),
    "entertainment": ProvisionReference("16(ii)", "", "Entertainment allowance", "IT Act 1961"),

    # Exemptions
    "hra_1013a": ProvisionReference("10(13A)", "", "House Rent Allowance exemption", "IT Act 1961"),
    "lta_105": ProvisionReference("10(5)", "", "Leave Travel Concession exemption", "IT Act 1961"),
    "gratuity_1010": ProvisionReference("10(10)", "", "Gratuity exemption", "IT Act 1961"),

    # Deductions
    "80c": ProvisionReference("80C", "", "Aggregate deduction — investments/expenditure (₹1.5L)", "IT Act 1961"),
    "80ccc": ProvisionReference("80CCC", "", "Pension fund contribution", "IT Act 1961"),
    "80ccd1": ProvisionReference("80CCD(1)", "", "NPS employee contribution (within 80C)", "IT Act 1961"),
    "80ccd1b": ProvisionReference("80CCD(1B)", "", "Additional NPS deduction (₹50K)", "Finance Act 2015"),
    "80ccd2": ProvisionReference("80CCD(2)", "", "Employer NPS contribution (no limit)", "IT Act 1961"),
    "80d": ProvisionReference("80D", "", "Health insurance premium", "IT Act 1961"),
    "80dd": ProvisionReference("80DD", "", "Disabled dependent maintenance", "IT Act 1961"),
    "80ddb": ProvisionReference("80DDB", "", "Medical treatment for specified diseases", "IT Act 1961"),
    "80e": ProvisionReference("80E", "", "Education loan interest", "IT Act 1961"),
    "80ee": ProvisionReference("80EE", "", "First home loan interest (₹50K)", "Finance Act 2016"),
    "80eea": ProvisionReference("80EEA", "", "Affordable housing loan interest (₹1.5L)", "Finance Act 2019"),
    "80eeb": ProvisionReference("80EEB", "", "Electric vehicle loan interest (₹1.5L)", "Finance Act 2019"),
    "80g": ProvisionReference("80G", "", "Donations to charitable institutions", "IT Act 1961"),
    "80gg": ProvisionReference("80GG", "", "Rent paid (no HRA received)", "IT Act 1961"),
    "80tta": ProvisionReference("80TTA", "", "Savings account interest (₹10K)", "IT Act 1961"),
    "80ttb": ProvisionReference("80TTB", "", "Senior citizen interest income (₹50K)", "Finance Act 2018"),
    "80u": ProvisionReference("80U", "", "Self-disability deduction", "IT Act 1961"),
    "24b": ProvisionReference("24(b)", "", "Interest on housing loan", "IT Act 1961"),

    # Capital Gains
    "112a": ProvisionReference("112A", "", "Equity LTCG (12.5%, ₹1.25L exemption)", "Finance Act 2018"),
    "111a": ProvisionReference("111A", "", "Equity STCG (15%)", "Finance Act 2018"),
    "stcg_other": ProvisionReference("Slab rate", "", "Non-equity STCG — taxed at slab rates", "IT Act 1961"),
    "ltcg_other": ProvisionReference("112", "", "Non-equity LTCG (12.5% without indexation)", "Finance Act 2024"),
    "115bbh": ProvisionReference("115BBH", "", "Crypto/VDA income (30%)", "Finance Act 2022"),

    # Tax Computation
    "slab_old": ProvisionReference("Slab rates (Old)", "", "Progressive tax rates — Old Regime", "Finance Act 2025"),
    "slab_new": ProvisionReference("115BAC", "(1A)", "Progressive tax rates — New Regime", "Finance Act 2025"),
    "87a": ProvisionReference("87A", "", "Rebate for low-income taxpayers", "Finance Act 2025"),
    "surcharge": ProvisionReference("Surcharge", "", "Surcharge on high-income taxpayers", "Finance Act 2025"),
    "cess": ProvisionReference("2(11)", "", "Health & Education Cess (4%)", "Finance Act 2018"),

    # Interest
    "234a": ProvisionReference("234A", "", "Interest for late filing (1%/month)", "IT Act 1961"),
    "234b": ProvisionReference("234B", "", "Interest for advance tax default (1%/month)", "IT Act 1961"),
    "234c": ProvisionReference("234C", "", "Interest for advance tax deferment (1%/month)", "IT Act 1961"),
    "234f": ProvisionReference("234F", "", "Late filing fee (₹1K/₹5K/₹10K)", "Finance Act 2017"),
}


class ProvisionTracer:
    """Traces computation values to their legal provisions.

    Given a computation result, produces a human-readable trace showing
    which provision produced each value and the chain of dependencies.
    """

    def trace(self, computation: dict) -> list[dict]:
        """Trace computation values to provisions.

        Returns list of {value_name, value, provision_section, provision_description}
        """
        traces: list[dict] = []

        mappings = [
            ("gross_salary", "salary_171"),
            ("std_deduction", "std_deduction"),
            ("hra_exemption", "hra_1013a"),
            ("lta_exemption", "lta_105"),
            ("income_salary", "salary_171"),
            ("rebate_87a", "87a"),
            ("surcharge", "surcharge"),
            ("cess", "cess"),
            ("net_tax", "slab_new"),
        ]

        for value_key, provision_key in mappings:
            if value_key in computation:
                prov = PROVISION_MAP.get(provision_key)
                if prov:
                    traces.append({
                        "value": value_key,
                        "amount": str(computation.get(value_key, "0")),
                        "section": prov.section,
                        "description": prov.description,
                    })

        return traces

    @staticmethod
    def lookup(provision_key: str) -> Optional[ProvisionReference]:
        """Look up a provision by key."""
        return PROVISION_MAP.get(provision_key)
