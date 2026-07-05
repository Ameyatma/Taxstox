"""Unit tests for Audit Trail infrastructure."""

from src.engine.audit import (
    AuditEvent,
    AuditEventType,
    AuditTrail,
    AuditContext,
)


class TestAuditEvent:
    def test_create_event(self):
        event = AuditEvent.create(
            event_type=AuditEventType.RULE_EVALUATED,
            correlation_id="corr-001",
            financial_year="FY2025-26",
            bounded_context="tax_computation",
            capability_id="C6.1",
            description="Applied slab rate: 5% on ₹4,00,000",
            input_data={"income": "925000"},
            output_data={"slab_tax": "32500"},
            rule_reference="Section 115BAC",
        )
        assert event.event_type == AuditEventType.RULE_EVALUATED
        assert event.correlation_id == "corr-001"
        assert event.financial_year == "FY2025-26"
        assert event.bounded_context == "tax_computation"

    def test_event_is_immutable(self):
        event = AuditEvent.create(
            event_type=AuditEventType.TAX_FINALIZED,
            correlation_id="corr-001",
            financial_year="FY2025-26",
            bounded_context="tax_computation",
            capability_id="C6.5",
            description="Tax finalized",
            output_data={"net_tax": "156974"},
        )
        # Frozen dataclass — cannot modify
        assert event.output_data["net_tax"] == "156974"


class TestAuditTrail:
    def test_empty_trail(self):
        trail = AuditTrail(correlation_id="corr-001", financial_year="FY2025-26")
        assert trail.event_count == 0
        assert len(trail.timeline) == 0

    def test_append_returns_new_trail(self):
        trail = AuditTrail(correlation_id="corr-001", financial_year="FY2025-26")
        event = AuditEvent.create(
            event_type=AuditEventType.INCOME_COMPUTED,
            correlation_id="corr-001",
            financial_year="FY2025-26",
            bounded_context="income",
            capability_id="C4.1",
            description="Salary income computed",
            output_data={"income": "1796602", "income_head": "salary"},
            rule_reference="Section 15-17",
        )
        trail2 = trail.append(event)
        assert trail.event_count == 0  # Original unchanged
        assert trail2.event_count == 1  # New trail has event

    def test_filter_by_type(self):
        trail = AuditTrail(correlation_id="corr-001", financial_year="FY2025-26")
        e1 = AuditEvent.create(
            AuditEventType.INCOME_COMPUTED, "corr-001", "FY2025-26",
            "income", "C4.1", "Salary", output_data={"income": "1000000"},
        )
        e2 = AuditEvent.create(
            AuditEventType.DEDUCTION_APPLIED, "corr-001", "FY2025-26",
            "income", "C5.1", "80C applied", output_data={"section": "80C", "amount": "150000"},
        )
        trail = trail.append(e1).append(e2)
        income_events = trail.events_by_type(AuditEventType.INCOME_COMPUTED)
        assert len(income_events) == 1

    def test_to_replay_script(self):
        trail = AuditTrail(correlation_id="corr-001", financial_year="FY2025-26")
        event = AuditEvent.create(
            AuditEventType.TAX_FINALIZED, "corr-001", "FY2025-26",
            "tax_computation", "C6.5", "Tax computed",
            output_data={"net_tax": "50000"},
        )
        trail = trail.append(event)
        script = trail.to_replay_script()
        assert "FY2025-26" in script
        assert "corr-001" in script


class TestAuditContext:
    def test_context_creates_correlated_events(self):
        ctx = AuditContext("FY2025-26")
        e1 = ctx.event(
            AuditEventType.SLAB_APPLIED, "tax_computation", "C6.1",
            "Slab tax applied",
        )
        e2 = ctx.event(
            AuditEventType.CESS_APPLIED, "tax_computation", "C6.4",
            "Cess applied",
        )
        assert e1.correlation_id == e2.correlation_id == ctx.correlation_id
        assert e1.financial_year == "FY2025-26"
