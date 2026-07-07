"""Finance Act Change Analyzer — Detect and categorize changes between FYs.

Compares two TaxYearConfig instances and produces a structured delta
showing what changed, by how much, and which provisions are affected.

Traceability: C11.3 (Finance Act Change Analyzer — 0%→50%, P4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from src.engine.rules.config import TaxYearConfig, SlabBracket, RegimeConfig
from src.models.financial_year import FinancialYear


class ChangeType(str, Enum):
    SLAB_RATE_CHANGED = "slab_rate_changed"
    SLAB_BRACKET_ADDED = "slab_bracket_added"
    SLAB_BRACKET_REMOVED = "slab_bracket_removed"
    SLAB_THRESHOLD_CHANGED = "slab_threshold_changed"
    DEDUCTION_LIMIT_CHANGED = "deduction_limit_changed"
    DEDUCTION_ADDED = "deduction_added"
    DEDUCTION_REMOVED = "deduction_removed"
    REBATE_THRESHOLD_CHANGED = "rebate_threshold_changed"
    REBATE_MAX_CHANGED = "rebate_max_changed"
    STD_DEDUCTION_CHANGED = "std_deduction_changed"
    SURCHARGE_RATE_CHANGED = "surcharge_rate_changed"
    SURCHARGE_THRESHOLD_ADDED = "surcharge_threshold_added"
    SURCHARGE_THRESHOLD_REMOVED = "surcharge_threshold_removed"
    CESS_RATE_CHANGED = "cess_rate_changed"
    LTCG_EXEMPTION_CHANGED = "ltcg_exemption_changed"
    CAPITAL_GAINS_RATE_CHANGED = "capital_gains_rate_changed"
    REGIME_CONFIG_CHANGED = "regime_config_changed"
    NEW_PROVISION_ADDED = "new_provision_added"


@dataclass(frozen=True)
class FinanceActDelta:
    """A single detected change between two financial years."""

    change_type: ChangeType
    description: str                    # Human-readable description
    regime: str = ""                    # "old", "new", or "" for both
    old_value: str = ""
    new_value: str = ""
    provision_affected: str = ""        # provision_id
    taxpayer_impact: str = ""           # Plain-language impact on taxpayer
    magnitude: str = ""                 # "major", "moderate", "minor"


@dataclass
class FinanceActChangeReport:
    """Complete report of all changes between two FYs."""

    financial_year_from: str
    financial_year_to: str
    changes: list[FinanceActDelta] = field(default_factory=list)

    @property
    def major_changes(self) -> list[FinanceActDelta]:
        return [c for c in self.changes if c.magnitude == "major"]

    @property
    def slab_changes(self) -> list[FinanceActDelta]:
        return [c for c in self.changes if c.change_type.value.startswith("slab")]

    @property
    def deduction_changes(self) -> list[FinanceActDelta]:
        return [c for c in self.changes if c.change_type.value.startswith("deduction")]

    @property
    def change_count(self) -> int:
        return len(self.changes)

    @property
    def summary(self) -> str:
        parts = [f"Finance Act changes from {self.financial_year_from} to {self.financial_year_to}:"]
        for c in self.changes:
            parts.append(f"  [{c.magnitude.upper()}] {c.description}")
        return "\n".join(parts)


class FinanceActChangeAnalyzer:
    """Analyzes changes between two TaxYearConfig instances.

    Compares every dimension: slabs, deductions, rebates, surcharge,
    cess, standard deduction, capital gains rates, and more.

    Produces a structured, categorized change report suitable for
    CA review, taxpayer education, and automated impact analysis.
    """

    def analyze(
        self,
        config_from: TaxYearConfig,
        config_to: TaxYearConfig,
    ) -> FinanceActChangeReport:
        """Compare two FY configs and produce a change report."""
        report = FinanceActChangeReport(
            financial_year_from=config_from.financial_year.label,
            financial_year_to=config_to.financial_year.label,
        )

        self._compare_regime(config_from.old_regime, config_to.old_regime, "old", report)
        self._compare_regime(config_from.new_regime, config_to.new_regime, "new", report)
        self._compare_deductions(config_from, config_to, report)
        self._compare_surcharge(config_from, config_to, report)
        self._compare_cess(config_from, config_to, report)
        self._compare_capital_gains(config_from, config_to, report)
        self._compare_std_deduction(config_from, config_to, report)

        return report

    def _compare_regime(
        self,
        old_regime: RegimeConfig,
        new_regime: RegimeConfig,
        regime_label: str,
        report: FinanceActChangeReport,
    ) -> None:
        """Compare slab brackets between two regime configs."""
        old_slabs = old_regime.slabs
        new_slabs = new_regime.slabs

        # Detect slab changes
        if len(old_slabs) != len(new_slabs):
            report.changes.append(FinanceActDelta(
                change_type=ChangeType.SLAB_BRACKET_ADDED if len(new_slabs) > len(old_slabs)
                else ChangeType.SLAB_BRACKET_REMOVED,
                regime=regime_label,
                description=f"{regime_label.title()} Regime: {'Added' if len(new_slabs) > len(old_slabs) else 'Removed'} tax slab bracket (now {len(new_slabs)} brackets)",
                old_value=str(len(old_slabs)),
                new_value=str(len(new_slabs)),
                provision_affected="sec_115bac" if regime_label == "new" else "slab_old",
                taxpayer_impact="Tax brackets restructured — check new slabs",
                magnitude="major",
            ))

        # Compare each slab bracket
        for i, (old_s, new_s) in enumerate(zip(old_slabs, new_slabs)):
            if old_s.income_to != new_s.income_to:
                report.changes.append(FinanceActDelta(
                    change_type=ChangeType.SLAB_THRESHOLD_CHANGED,
                    regime=regime_label,
                    description=f"{regime_label.title()} Regime slab {i + 1}: threshold changed from ₹{old_s.income_to:,.0f} to ₹{new_s.income_to:,.0f}",
                    old_value=f"₹{old_s.income_to:,.0f}",
                    new_value=f"₹{new_s.income_to:,.0f}",
                    provision_affected="sec_115bac" if regime_label == "new" else "slab_old",
                    taxpayer_impact=f"Tax bracket boundary changed affecting income around ₹{old_s.income_to:,.0f}-₹{new_s.income_to:,.0f} range",
                    magnitude="moderate" if abs(new_s.income_to - old_s.income_to) < 200000 else "major",
                ))
            if old_s.rate != new_s.rate:
                report.changes.append(FinanceActDelta(
                    change_type=ChangeType.SLAB_RATE_CHANGED,
                    regime=regime_label,
                    description=f"{regime_label.title()} Regime slab {i + 1}: rate changed from {old_s.rate * 100:.0f}% to {new_s.rate * 100:.0f}%",
                    old_value=f"{old_s.rate * 100:.0f}%",
                    new_value=f"{new_s.rate * 100:.0f}%",
                    provision_affected="sec_115bac" if regime_label == "new" else "slab_old",
                    taxpayer_impact=f"Tax rate changed — {'lower' if new_s.rate < old_s.rate else 'higher'} tax for this bracket",
                    magnitude="major",
                ))

        # Compare rebate
        if old_regime.rebate_threshold != new_regime.rebate_threshold:
            report.changes.append(FinanceActDelta(
                change_type=ChangeType.REBATE_THRESHOLD_CHANGED,
                regime=regime_label,
                description=f"{regime_label.title()} Regime 87A rebate income threshold: ₹{old_regime.rebate_threshold:,.0f} → ₹{new_regime.rebate_threshold:,.0f}",
                old_value=f"₹{old_regime.rebate_threshold:,.0f}",
                new_value=f"₹{new_regime.rebate_threshold:,.0f}",
                provision_affected="sec_87a",
                taxpayer_impact=f"More taxpayers eligible for rebate" if new_regime.rebate_threshold > old_regime.rebate_threshold else "Fewer taxpayers eligible for rebate",
                magnitude="major",
            ))
        if old_regime.rebate_max != new_regime.rebate_max:
            report.changes.append(FinanceActDelta(
                change_type=ChangeType.REBATE_MAX_CHANGED,
                regime=regime_label,
                description=f"{regime_label.title()} Regime 87A rebate amount: ₹{old_regime.rebate_max:,.0f} → ₹{new_regime.rebate_max:,.0f}",
                old_value=f"₹{old_regime.rebate_max:,.0f}",
                new_value=f"₹{new_regime.rebate_max:,.0f}",
                provision_affected="sec_87a",
                taxpayer_impact=f"Maximum rebate {'increased' if new_regime.rebate_max > old_regime.rebate_max else 'decreased'}",
                magnitude="major",
            ))

    def _compare_deductions(
        self, cf: TaxYearConfig, ct: TaxYearConfig, report: FinanceActChangeReport,
    ) -> None:
        """Compare deduction limits between two configs."""
        old_deds = {dl.section: dl for dl in cf.deduction_limits}
        new_deds = {dl.section: dl for dl in ct.deduction_limits}

        # Check for changed limits
        for section, old_dl in old_deds.items():
            new_dl = new_deds.get(section)
            if new_dl and old_dl.limit != new_dl.limit:
                report.changes.append(FinanceActDelta(
                    change_type=ChangeType.DEDUCTION_LIMIT_CHANGED,
                    description=f"Section {section} limit: ₹{old_dl.limit:,.0f} → ₹{new_dl.limit:,.0f}",
                    old_value=f"₹{old_dl.limit:,.0f}",
                    new_value=f"₹{new_dl.limit:,.0f}",
                    provision_affected=f"sec_{section.lower().replace(' ', '_').replace('(', '').replace(')', '')}",
                    taxpayer_impact=f"{'Higher' if new_dl.limit > old_dl.limit else 'Lower'} deduction available under Section {section}",
                    magnitude="moderate" if abs(new_dl.limit - old_dl.limit) < 50000 else "major",
                ))

        # New deductions
        for section in new_deds:
            if section not in old_deds:
                report.changes.append(FinanceActDelta(
                    change_type=ChangeType.DEDUCTION_ADDED,
                    description=f"New deduction: Section {section} — ₹{new_deds[section].limit:,.0f}",
                    new_value=f"₹{new_deds[section].limit:,.0f}",
                    provision_affected=f"sec_{section.lower()}",
                    taxpayer_impact=f"New deduction available under Section {section}",
                    magnitude="moderate",
                ))

        # Removed deductions
        for section in old_deds:
            if section not in new_deds:
                report.changes.append(FinanceActDelta(
                    change_type=ChangeType.DEDUCTION_REMOVED,
                    description=f"Removed deduction: Section {section} (was ₹{old_deds[section].limit:,.0f})",
                    old_value=f"₹{old_deds[section].limit:,.0f}",
                    provision_affected=f"sec_{section.lower()}",
                    taxpayer_impact=f"Section {section} deduction no longer available",
                    magnitude="major",
                ))

    def _compare_surcharge(
        self, cf: TaxYearConfig, ct: TaxYearConfig, report: FinanceActChangeReport,
    ) -> None:
        """Compare surcharge thresholds between two configs."""
        old_st = {st.income_threshold: st.rate for st in cf.surcharge_thresholds}
        new_st = {st.income_threshold: st.rate for st in ct.surcharge_thresholds}

        for threshold, old_rate in old_st.items():
            new_rate = new_st.get(threshold)
            if new_rate and old_rate != new_rate:
                report.changes.append(FinanceActDelta(
                    change_type=ChangeType.SURCHARGE_RATE_CHANGED,
                    description=f"Surcharge rate at ₹{threshold:,.0f}: {old_rate * 100:.0f}% → {new_rate * 100:.0f}%",
                    old_value=f"{old_rate * 100:.0f}%",
                    new_value=f"{new_rate * 100:.0f}%",
                    provision_affected="surcharge",
                    taxpayer_impact=f"Surcharge {'increased' if new_rate > old_rate else 'decreased'} on income above ₹{threshold:,.0f}",
                    magnitude="major",
                ))

        for threshold in new_st:
            if threshold not in old_st:
                report.changes.append(FinanceActDelta(
                    change_type=ChangeType.SURCHARGE_THRESHOLD_ADDED,
                    description=f"New surcharge bracket at ₹{threshold:,.0f}: {new_st[threshold] * 100:.0f}%",
                    new_value=f"{new_st[threshold] * 100:.0f}%",
                    provision_affected="surcharge",
                    taxpayer_impact=f"New surcharge rate applies for income above ₹{threshold:,.0f}",
                    magnitude="moderate",
                ))

    def _compare_cess(self, cf: TaxYearConfig, ct: TaxYearConfig, report: FinanceActChangeReport) -> None:
        """Compare cess rates."""
        if cf.cess_rate != ct.cess_rate:
            report.changes.append(FinanceActDelta(
                change_type=ChangeType.CESS_RATE_CHANGED,
                description=f"HEC rate: {cf.cess_rate * 100:.0f}% → {ct.cess_rate * 100:.0f}%",
                old_value=f"{cf.cess_rate * 100:.0f}%",
                new_value=f"{ct.cess_rate * 100:.0f}%",
                provision_affected="cess",
                taxpayer_impact=f"Health & Education Cess rate {'increased' if ct.cess_rate > cf.cess_rate else 'decreased'}",
                magnitude="major" if cf.cess_rate != ct.cess_rate else "minor",
            ))

    def _compare_capital_gains(self, cf: TaxYearConfig, ct: TaxYearConfig, report: FinanceActChangeReport) -> None:
        """Compare capital gains rates and exemptions."""
        if cf.ltcg_112a_exemption != ct.ltcg_112a_exemption:
            report.changes.append(FinanceActDelta(
                change_type=ChangeType.LTCG_EXEMPTION_CHANGED,
                description=f"Section 112A exemption: ₹{cf.ltcg_112a_exemption:,.0f} → ₹{ct.ltcg_112a_exemption:,.0f}",
                old_value=f"₹{cf.ltcg_112a_exemption:,.0f}",
                new_value=f"₹{ct.ltcg_112a_exemption:,.0f}",
                provision_affected="sec_112a",
                taxpayer_impact=f"{'Higher' if ct.ltcg_112a_exemption > cf.ltcg_112a_exemption else 'Lower'} tax-free LTCG limit",
                magnitude="major",
            ))
        if cf.equity_stcg_rate != ct.equity_stcg_rate:
            report.changes.append(FinanceActDelta(
                change_type=ChangeType.CAPITAL_GAINS_RATE_CHANGED,
                description=f"Equity STCG rate: {cf.equity_stcg_rate * 100:.0f}% → {ct.equity_stcg_rate * 100:.0f}%",
                old_value=f"{cf.equity_stcg_rate * 100:.0f}%",
                new_value=f"{ct.equity_stcg_rate * 100:.0f}%",
                provision_affected="sec_111a",
                taxpayer_impact=f"Short-term capital gains tax rate changed",
                magnitude="major",
            ))
        if cf.equity_ltcg_rate != ct.equity_ltcg_rate:
            report.changes.append(FinanceActDelta(
                change_type=ChangeType.CAPITAL_GAINS_RATE_CHANGED,
                description=f"Equity LTCG rate: {cf.equity_ltcg_rate * 100:.0f}% → {ct.equity_ltcg_rate * 100:.0f}%",
                old_value=f"{cf.equity_ltcg_rate * 100:.0f}%",
                new_value=f"{ct.equity_ltcg_rate * 100:.0f}%",
                provision_affected="sec_112a",
                taxpayer_impact=f"Long-term capital gains tax rate changed",
                magnitude="major",
            ))

    def _compare_std_deduction(self, cf: TaxYearConfig, ct: TaxYearConfig, report: FinanceActChangeReport) -> None:
        """Compare standard deduction amounts."""
        for regime_label, old_config, new_config in [
            ("old", cf.old_regime, ct.old_regime),
            ("new", cf.new_regime, ct.new_regime),
        ]:
            if old_config.std_deduction != new_config.std_deduction:
                report.changes.append(FinanceActDelta(
                    change_type=ChangeType.STD_DEDUCTION_CHANGED,
                    regime=regime_label,
                    description=f"{regime_label.title()} Regime standard deduction: ₹{old_config.std_deduction:,.0f} → ₹{new_config.std_deduction:,.0f}",
                    old_value=f"₹{old_config.std_deduction:,.0f}",
                    new_value=f"₹{new_config.std_deduction:,.0f}",
                    provision_affected="std_deduction",
                    taxpayer_impact=f"Standard deduction {'increased' if new_config.std_deduction > old_config.std_deduction else 'decreased'} under {regime_label} regime",
                    magnitude="moderate",
                ))


# ── Convenience Functions ─────────────────────────────────────────────

def analyze_fy_transition(
    fy_from: str,
    fy_to: str,
) -> FinanceActChangeReport | None:
    """Analyze changes between two financial years using the rule_repository.

    Args:
        fy_from: Source FY label (e.g., "FY2024-25")
        fy_to: Target FY label (e.g., "FY2025-26")

    Returns:
        FinanceActChangeReport or None if either FY is unavailable
    """
    from src.engine.rules.config import rule_repository

    try:
        config_from = rule_repository.get(FinancialYear.from_string(fy_from))
        config_to = rule_repository.get(FinancialYear.from_string(fy_to))
    except (KeyError, ValueError):
        return None

    analyzer = FinanceActChangeAnalyzer()
    return analyzer.analyze(config_from, config_to)
