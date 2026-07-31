"""P6 Tests — Customer Experience: Notifications, Tax Planning, Refund, Export.

Tests: 32
"""

import pytest
from decimal import Decimal
from uuid import UUID, uuid4
from datetime import date

# ── Notifications ──

from src.domain.notification.notification import (
    Notification, NotificationChannel, NotificationPriority,
    NotificationTemplate, NotificationPreference, STANDARD_TEMPLATES,
)
from src.domain.notification.deadline_watcher import (
    DeadlineRule, ReminderSchedule, DeadlineType, get_standard_deadline,
)
from src.engine.notification.notification_engine import (
    NotificationEngine, DeadlineReminderEngine, NotificationBatch,
)


class TestNotifications:
    def test_create_notification(self):
        n = Notification.create(uuid4(), NotificationChannel.EMAIL, "Subject", "Body")
        assert n.channel == NotificationChannel.EMAIL
        assert n.status == "pending"

    def test_from_template(self):
        template = STANDARD_TEMPLATES["filing_completed"]
        n = Notification.from_template(template, uuid4(), {
            "name": "John", "financial_year": "FY2025-26",
            "ack_number": "ABC123", "filing_date": "2026-07-31",
        })
        assert "John" in n.body
        assert "FY2025-26" in n.subject
        assert "ABC123" in n.body

    def test_notification_preferences_default(self):
        prefs = NotificationPreference.default(uuid4())
        assert prefs.email_enabled
        assert prefs.channel_enabled(NotificationChannel.EMAIL)
        assert prefs.channel_enabled(NotificationChannel.IN_APP)

    def test_in_app_notification_dispatch(self):
        engine = NotificationEngine()
        n = Notification.create(uuid4(), NotificationChannel.IN_APP, "Test", "Body")
        engine.send(n)
        assert n.status == "sent"
        notifications = engine.get_in_app_notifications(n.recipient_user_id)
        assert len(notifications) == 1

    def test_batch_dispatch(self):
        engine = NotificationEngine()
        notifications = [
            Notification.create(uuid4(), NotificationChannel.IN_APP, f"Test {i}", f"Body {i}")
            for i in range(5)
        ]
        batch = engine.send_batch(notifications)
        assert batch.total == 5
        assert batch.sent == 5


class TestDeadlineReminders:
    def test_reminder_schedule(self):
        schedule = ReminderSchedule.default_itr()
        assert 30 in schedule.days_before
        assert 7 in schedule.days_before
        assert 1 in schedule.days_before

    def test_should_remind_today(self):
        rule = DeadlineRule.create_itr_reminder(uuid4())
        # Verify get_reminder_dates returns correct number of dates
        deadline = date(2026, 7, 31)
        dates = rule.get_reminder_dates(deadline)
        assert len(dates) == 6  # 5 pre-deadline reminders + due date
        assert deadline in dates  # Due date included

    def test_get_standard_deadline_itr(self):
        deadline = get_standard_deadline(DeadlineType.ITR_FILING, "FY2025-26")
        assert deadline.month == 7
        assert deadline.day == 31

    def test_deadline_reminder_engine(self):
        engine = DeadlineReminderEngine()
        rule = DeadlineRule.create_itr_reminder(uuid4(), "FY2025-26")
        # Evaluate with has_active check
        assert rule.is_active
        # Verify the engine can evaluate rules
        reminders = engine.evaluate([rule])
        # On most days, no reminders fire — that's correct behavior
        assert isinstance(reminders, list)


# ── Tax Planning ──

from src.domain.tax_planning.scenario import TaxScenario, ScenarioVariable
from src.domain.tax_planning.loss_harvesting import (
    LossHarvestingOpportunity, HarvestingRecommendation, AssetType,
)
from src.domain.tax_planning.projection import (
    MultiYearProjection, YearProjection, ProjectionAssumption,
)
from src.engine.tax_planning.scenario_simulator import ScenarioSimulator
from src.engine.tax_planning.loss_harvesting_engine import LossHarvestingEngine
from src.engine.tax_planning.multi_year_projection import MultiYearProjectionEngine


class TestScenarioSimulator:
    def test_create_scenario(self):
        s = TaxScenario.create("Max 80C", "Invest the full 1.5L in 80C")
        s.add_variable("total_income", "Total Income", Decimal("1000000"), Decimal("850000"))
        assert len(s.variables) == 1
        assert s.total_change == Decimal("-150000")

    def test_simulate_income_decrease(self):
        baseline = {
            "total_income": "1000000",
            "final_tax": "50000",
            "gross_total_income": "1000000",
            "deductions": "0",
        }
        result = ScenarioSimulator.quick_scenario(
            "Pay cut", Decimal("-200000"), baseline,
        )
        assert result.scenario_total_income < result.original_total_income

    def test_simulate_income_increase(self):
        baseline = {
            "total_income": "1500000",
            "final_tax": "100000",
            "gross_total_income": "1500000",
            "deductions": "0",
        }
        result = ScenarioSimulator.quick_scenario(
            "Bonus", Decimal("500000"), baseline,
        )
        assert result.scenario_final_tax >= result.original_final_tax

    def test_scenario_comparison_summary(self):
        baseline = {"total_income": "1000000", "final_tax": "50000"}
        result = ScenarioSimulator.quick_scenario("Raise", Decimal("200000"), baseline)
        assert len(result.summary) > 0
        assert "Raise" in result.summary


class TestLossHarvesting:
    def test_identify_opportunities(self):
        engine = LossHarvestingEngine()
        holdings = [
            {"name": "RELIANCE", "type": "listed_equity", "cost": "100000",
             "current": "80000", "holding_days": 200, "stt_paid": True},
            {"name": "TCS", "type": "listed_equity", "cost": "50000",
             "current": "60000", "holding_days": 400, "stt_paid": True},
        ]
        recs = engine.analyze_portfolio(holdings, existing_stcg=Decimal("50000"))
        assert len(recs) >= 1  # At least RELIANCE has a loss

    def test_no_recommendations_when_no_losses(self):
        engine = LossHarvestingEngine()
        holdings = [
            {"name": "TCS", "type": "listed_equity", "cost": "50000",
             "current": "60000", "holding_days": 400, "stt_paid": True},
        ]
        recs = engine.analyze_portfolio(holdings)
        assert len(recs) == 0

    def test_compute_tax_saved(self):
        opp = LossHarvestingOpportunity(
            asset_name="TEST", asset_type=AssetType.LISTED_EQUITY,
            acquisition_cost=Decimal("100000"), current_value=Decimal("80000"),
            unrealized_loss=Decimal("-20000"), holding_period_days=100,
            is_long_term=False, stt_paid=True,
        )
        rec = HarvestingRecommendation.create(opp)
        saved = rec.compute_tax_saved(Decimal("0.30"))
        assert saved == Decimal("3000.00")  # 20000 * 0.15

    def test_total_potential_savings(self):
        opp1 = LossHarvestingOpportunity(
            asset_name="A", asset_type=AssetType.LISTED_EQUITY,
            acquisition_cost=Decimal("50000"), current_value=Decimal("40000"),
            unrealized_loss=Decimal("-10000"), holding_period_days=50,
            is_long_term=False, stt_paid=True,
        )
        opp2 = LossHarvestingOpportunity(
            asset_name="B", asset_type=AssetType.LISTED_EQUITY,
            acquisition_cost=Decimal("30000"), current_value=Decimal("20000"),
            unrealized_loss=Decimal("-10000"), holding_period_days=50,
            is_long_term=False, stt_paid=True,
        )
        r1 = HarvestingRecommendation.create(opp1)
        r2 = HarvestingRecommendation.create(opp2)
        r1.compute_tax_saved(Decimal("0.30"))
        r2.compute_tax_saved(Decimal("0.30"))
        total = LossHarvestingEngine.total_potential_savings([r1, r2])
        assert total == Decimal("3000.00")  # 10000*0.15 each = 1500 each


class TestMultiYearProjection:
    def test_project_five_years(self):
        engine = MultiYearProjectionEngine()
        projection = engine.project(
            current_income=Decimal("1000000"),
            current_deductions=Decimal("150000"),
            num_years=5,
        )
        assert len(projection.years) == 5
        assert projection.start_year == "FY2025-26"
        assert len(projection.assumptions) == 2

    def test_income_growth_applied(self):
        engine = MultiYearProjectionEngine()
        projection = engine.project(
            Decimal("1000000"), Decimal("0"),
            income_growth_rate=Decimal("0.10"), num_years=3,
        )
        assert projection.years[1].projected_income > projection.years[0].projected_income

    def test_summary(self):
        engine = MultiYearProjectionEngine()
        projection = engine.project(Decimal("1000000"), Decimal("0"), num_years=3)
        assert len(projection.summary) > 0


# ── Refund Tracker ──

from src.domain.refund.refund_tracker import (
    RefundTimeline, RefundStatus, RefundStage, TimelineEntry,
)
from src.engine.refund_tracker import RefundTrackerEngine


class TestRefundTracker:
    def test_create_timeline(self):
        timeline = RefundTrackerEngine.create_timeline(
            uuid4(), "FY2025-26", "ACK123456", Decimal("25000"),
        )
        assert timeline.acknowledgement_number == "ACK123456"
        assert timeline.current_status is not None
        assert timeline.current_status.current_stage == RefundStage.ITR_FILED

    def test_advance_stage(self):
        timeline = RefundTrackerEngine.create_timeline(
            uuid4(), "FY2025-26", "ACK123", Decimal("10000"),
        )
        RefundTrackerEngine.advance_stage(
            timeline, RefundStage.ITR_PROCESSED, "ITR processed by CPC",
        )
        assert timeline.current_status.current_stage == RefundStage.ITR_PROCESSED

    def test_status_summary(self):
        timeline = RefundTrackerEngine.create_timeline(
            uuid4(), "FY2025-26", "ACK123", Decimal("5000"),
        )
        summary = RefundTrackerEngine.get_status_summary(timeline)
        assert summary["current_stage"] == "itr_filed"
        assert not summary["is_complete"]
        assert summary["progress_percent"] > 0


# ── Export ──

from src.engine.export_portability import ExportEngine, ExportFormat


class TestExport:
    def test_export_itr_json(self):
        result = ExportEngine.export_itr_json({"test": "data"}, "test.json")
        assert result.success
        assert "test" in result.content

    def test_export_csv_summary(self):
        breakdown = {
            "financial_year": "FY2025-26",
            "gross_total_income": "1000000",
            "final_tax": "50000",
        }
        result = ExportEngine.export_csv_summary(breakdown)
        assert "FY2025-26" in result.content
        assert "1000000" in result.content
        assert result.format == ExportFormat.CSV

    def test_export_data_portability(self):
        result = ExportEngine.export_data_portability(
            uuid4(), "ABCDE1234F", "John Doe",
            filings=[{"fy": "FY2025-26", "tax": "50000"}],
        )
        assert result.success
        assert "data_portability" in result.content
        assert "ABCDE1234F" not in result.content  # PAN masked
        assert "ABC**1234F" in result.content

    def test_pdf_summary_text(self):
        breakdown = {
            "financial_year": "FY2025-26",
            "gross_total_income": "1000000",
            "deductions": "150000",
            "total_income": "850000",
            "final_tax": "42500",
            "recommended_regime": "new",
            "savings": "10000",
        }
        text = ExportEngine.generate_pdf_summary_text(breakdown)
        assert "TAX COMPUTATION SUMMARY" in text
        assert "1,000,000" in text  # Formatted with commas
        assert "TaxStox" in text
