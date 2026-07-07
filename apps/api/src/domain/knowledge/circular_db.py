"""CBDT Circular Database — Structured registry of CBDT circulars, notifications,
and clarifications with provision mapping.

Traceability: C11.5 (CBDT Circular Database — 0%→50%, P4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Circular:
    """A single CBDT circular or notification."""

    circular_number: str                # e.g., "2/2025", "Notification 37/2024"
    circular_type: str                  # "circular", "notification", "press_release", "clarification"
    title: str                          # Official title
    summary: str                        # Plain-language summary of what it means
    issued_date: str                    # ISO date string
    effective_from: str = ""            # FY label, e.g., "FY2025-26"
    provisions_affected: tuple[str, ...] = ()  # provision_ids (e.g., "sec_80c")
    key_changes: tuple[str, ...] = ()    # Bullet-point key changes
    url: str = ""                       # Official CBDT URL
    is_active: bool = True
    superseded_by: str = ""             # Circular number that supersedes this one


class CBDTCircularDatabase:
    """Searchable registry of CBDT circulars and notifications.

    Domain service. Maps circulars to the provisions they affect.
    Enables impact analysis: "What circulars affect Section 80C?"
    """

    def __init__(self) -> None:
        self._circulars: list[Circular] = []

    def register(self, circular: Circular) -> None:
        """Register a circular."""
        self._circulars.append(circular)

    def get_by_number(self, number: str) -> Optional[Circular]:
        """Look up a circular by its number."""
        for c in self._circulars:
            if c.circular_number.lower() == number.lower():
                return c
        return None

    def get_by_provision(self, provision_id: str) -> tuple[Circular, ...]:
        """Get all circulars affecting a specific provision."""
        return tuple(
            c for c in self._circulars
            if provision_id in c.provisions_affected
        )

    def get_active(self, fy: str | None = None) -> tuple[Circular, ...]:
        """Get all currently active circulars, optionally for a specific FY."""
        active = [c for c in self._circulars if c.is_active]
        if fy:
            active = [c for c in active if c.effective_from == fy]
        return tuple(active)

    def search(self, keyword: str) -> tuple[Circular, ...]:
        """Search circulars by keyword in title or summary."""
        kw = keyword.lower()
        return tuple(
            c for c in self._circulars
            if kw in c.title.lower() or kw in c.summary.lower()
        )

    @property
    def all_circulars(self) -> tuple[Circular, ...]:
        return tuple(self._circulars)

    @property
    def count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for c in self._circulars:
            counts[c.circular_type] = counts.get(c.circular_type, 0) + 1
        return counts


# ── Build with key circulars ──────────────────────────────────────────

def _build_circular_db() -> CBDTCircularDatabase:
    """Build the CBDT circular database with key circulars affecting individual taxpayers."""
    db = CBDTCircularDatabase()

    # Key circulars relevant to individual taxpayers
    db.register(Circular(
        circular_number="Notification 25/2025",
        circular_type="notification",
        title="Income-Tax (Second Amendment) Rules, 2025 — New Regime Default",
        summary="Clarifies that the New Tax Regime under Section 115BAC is the default regime from FY2024-25. Taxpayers must explicitly opt for Old Regime.",
        issued_date="2025-02-01",
        effective_from="FY2025-26",
        provisions_affected=("sec_115bac",),
        key_changes=(
            "New Regime confirmed as default for FY2025-26",
            "Old Regime requires explicit opt-out",
        ),
    ))
    db.register(Circular(
        circular_number="Circular 1/2025",
        circular_type="circular",
        title="Explanatory Notes to Finance Act 2025",
        summary="Comprehensive explanatory notes on all provisions of Finance Act 2025 including new slab rates, rebate enhancement, and deduction changes.",
        issued_date="2025-02-01",
        effective_from="FY2025-26",
        provisions_affected=("sec_115bac", "sec_87a", "std_deduction", "surcharge"),
        key_changes=(
            "New Regime slabs revised for FY2025-26",
            "87A rebate increased to ₹60,000 for New Regime",
            "Standard deduction under New Regime increased to ₹75,000",
            "Surcharge thresholds updated",
        ),
    ))
    db.register(Circular(
        circular_number="Circular 18/2024",
        circular_type="circular",
        title="Clarification on Capital Gains — Section 112A Grandfathering",
        summary="Explains the methodology for computing cost of acquisition for equity shares acquired before January 31, 2018 under the grandfathering provisions of Section 112A.",
        issued_date="2024-09-15",
        effective_from="FY2018-19",
        provisions_affected=("sec_112a",),
        key_changes=(
            "Fair Market Value as on Jan 31, 2018, is used as deemed cost for shares acquired before that date",
            "Step-by-step computation methodology provided with examples",
        ),
    ))
    db.register(Circular(
        circular_number="Notification 37/2024",
        circular_type="notification",
        title="Cost Inflation Index for FY2024-25",
        summary="Notifies the Cost Inflation Index (CII) for FY2024-25 as 363, applicable for computing indexed cost of acquisition.",
        issued_date="2024-06-01",
        effective_from="FY2024-25",
        provisions_affected=("sec_112a",),
        key_changes=("CII for FY2024-25: 363",),
    ))
    db.register(Circular(
        circular_number="Circular 2/2024",
        circular_type="circular",
        title="Clarification on Virtual Digital Assets (Crypto) — Section 115BBH",
        summary="Clarifies that Section 115BBH applies to all Virtual Digital Assets including cryptocurrencies, NFTs, and tokens. 30% tax + 4% cess. No deduction for expenses except cost of acquisition.",
        issued_date="2024-04-15",
        effective_from="FY2022-23",
        provisions_affected=("sec_115bbh",),
        key_changes=(
            "All VDA types covered including NFTs and tokens",
            "Loss from one VDA cannot offset gain from another VDA",
            "1% TDS under Section 194S on VDA transfers",
        ),
    ))
    db.register(Circular(
        circular_number="Circular 14/2023",
        circular_type="circular",
        title="Clarification on 80D Deduction for Preventive Health Checkup",
        summary="Preventive health checkup up to ₹5,000 is included within the overall 80D limit (₹25,000/₹50,000), not an additional deduction.",
        issued_date="2023-12-10",
        effective_from="FY2023-24",
        provisions_affected=("sec_80d",),
        key_changes=("₹5,000 preventive checkup is within limit, not additional",),
    ))
    db.register(Circular(
        circular_number="Press Release 12/2024",
        circular_type="press_release",
        title="ITD Advisory: AIS-TIS Discrepancy Resolution Before ITR Filing",
        summary="Taxpayers should verify all transactions in AIS before filing ITR. Discrepancies between AIS and taxpayer records must be resolved using the AIS feedback mechanism.",
        issued_date="2024-06-15",
        effective_from="FY2024-25",
        provisions_affected=(),
        key_changes=("AIS-TIS reconciliation mandatory before filing",),
    ))

    return db


circular_db = _build_circular_db()
