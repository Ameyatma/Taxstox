"""Explanation Engine — human-readable narratives from audit trails.

Consumes AuditTrail events and produces deterministic, multi-level
explanations: summary (taxpayer), detail (CA), technical (auditor).

Traceability: C10.2 (Explanation Engine — 20%→60%),
             Constitution I4 (Explainability invariant)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from src.engine.audit import AuditTrail, AuditEventType


@dataclass(frozen=True)
class Explanation:
    """A single explanation for one computation step."""

    step: int
    title: str
    summary: str       # Plain language for taxpayer
    detail: str = ""   # Technical detail for CA
    provision: str = ""  # Legal provision reference
    amount: str = ""   # Monetary impact if applicable


@dataclass(frozen=True)
class ComputationNarrative:
    """Complete human-readable computation narrative."""

    financial_year: str
    correlation_id: str
    steps: tuple[Explanation, ...]
    total_tax: str = ""
    effective_rate: str = ""

    @property
    def summary_text(self) -> str:
        """One-paragraph summary for taxpayer."""
        parts = [f"Tax computation for {self.financial_year}:"]
        for s in self.steps:
            parts.append(s.summary)
        if self.total_tax:
            parts.append(f"Total tax: ₹{self.total_tax}")
        return "\n".join(parts)

    @property
    def detail_text(self) -> str:
        """Full detail for CA review."""
        parts = [f"Detailed Tax Computation — {self.financial_year}", ""]
        for s in self.steps:
            parts.append(f"Step {s.step}: {s.title}")
            parts.append(f"  {s.detail}")
            if s.provision:
                parts.append(f"  Provision: {s.provision}")
            if s.amount:
                parts.append(f"  Amount: ₹{s.amount}")
            parts.append("")
        return "\n".join(parts)


class ExplanationEngine:
    """Generates human-readable explanations from audit trails.

    Deterministic. Consumes AuditTrail, produces ComputationNarrative.
    Never performs tax computation — only explains what was computed.
    """

    def explain(self, trail: AuditTrail) -> ComputationNarrative:
        """Generate narrative from audit trail events."""
        explanations: list[Explanation] = []
        step = 0
        total_tax = ""

        for event in trail.events:
            step += 1
            exp = self._explain_event(step, event)
            if exp:
                explanations.append(exp)
                if event.event_type == AuditEventType.TAX_FINALIZED:
                    total_tax = event.output_data.get("net_tax", "")

        return ComputationNarrative(
            financial_year=trail.financial_year,
            correlation_id=trail.correlation_id,
            steps=tuple(explanations),
            total_tax=total_tax,
        )

    def _explain_event(self, step: int, event) -> Explanation | None:
        """Explain a single audit event."""
        handlers = {
            AuditEventType.INCOME_COMPUTED: self._explain_income,
            AuditEventType.DEDUCTION_APPLIED: self._explain_deduction,
            AuditEventType.RULE_EVALUATED: self._explain_rule,
            AuditEventType.SLAB_APPLIED: self._explain_slab,
            AuditEventType.REBATE_APPLIED: self._explain_rebate,
            AuditEventType.SURCHARGE_APPLIED: self._explain_surcharge,
            AuditEventType.CESS_APPLIED: self._explain_cess,
            AuditEventType.TAX_FINALIZED: self._explain_final,
            AuditEventType.REGIME_COMPARED: self._explain_regime,
        }
        handler = handlers.get(event.event_type)
        if handler:
            return handler(step, event)
        return Explanation(
            step=step,
            title=event.event_type.value.replace(".", " ").title(),
            summary=event.description,
        )

    @staticmethod
    def _explain_income(step: int, e) -> Explanation:
        income = e.output_data.get("income", "0")
        head = e.output_data.get("income_head", "salary")
        return Explanation(
            step=step, title=f"Income: {head.title()}",
            summary=f"₹{income} from {head}.",
            detail=e.description,
            amount=income,
            provision=e.rule_reference,
        )

    @staticmethod
    def _explain_deduction(step: int, e) -> Explanation:
        section = e.output_data.get("section", "")
        amount = e.output_data.get("amount", "0")
        return Explanation(
            step=step, title=f"Deduction: {section}",
            summary=f"₹{amount} deducted under Section {section}.",
            detail=e.description,
            amount=amount,
            provision=e.rule_reference or f"Section {section}",
        )

    @staticmethod
    def _explain_rule(step: int, e) -> Explanation:
        return Explanation(
            step=step, title="Rule Applied",
            summary=e.description,
            detail=f"Input: {e.input_data}, Output: {e.output_data}",
            provision=e.rule_reference,
        )

    @staticmethod
    def _explain_slab(step: int, e) -> Explanation:
        return Explanation(
            step=step, title="Slab Tax Applied",
            summary=e.description,
            detail=str(e.output_data),
            provision=e.rule_reference or "Section 115BAC",
        )

    @staticmethod
    def _explain_rebate(step: int, e) -> Explanation:
        amount = e.output_data.get("rebate", "0")
        return Explanation(
            step=step, title="Rebate u/s 87A",
            summary=f"Rebate of ₹{amount} applied." if amount != "0" else "No rebate applicable.",
            amount=amount,
            provision="Section 87A",
        )

    @staticmethod
    def _explain_surcharge(step: int, e) -> Explanation:
        amount = e.output_data.get("surcharge", "0")
        return Explanation(
            step=step, title="Surcharge",
            summary=f"Surcharge of ₹{amount} applied." if amount != "0" else "No surcharge applicable.",
            amount=amount,
            provision="Finance Act",
        )

    @staticmethod
    def _explain_cess(step: int, e) -> Explanation:
        amount = e.output_data.get("cess", "0")
        return Explanation(
            step=step, title="Health & Education Cess",
            summary=f"Cess of ₹{amount} (4% of tax + surcharge).",
            amount=amount,
            provision="Section 2(11) of Finance Act",
        )

    @staticmethod
    def _explain_final(step: int, e) -> Explanation:
        net_tax = e.output_data.get("net_tax", "0")
        return Explanation(
            step=step, title="Final Tax Liability",
            summary=f"Your total tax liability is ₹{net_tax}.",
            detail=e.description,
            amount=net_tax,
        )

    @staticmethod
    def _explain_regime(step: int, e) -> Explanation:
        recommended = e.output_data.get("recommended", "")
        savings = e.output_data.get("savings", "0")
        return Explanation(
            step=step, title="Regime Comparison",
            summary=f"{recommended} Regime recommended — saves ₹{savings}.",
            detail=e.description,
            amount=savings,
        )
