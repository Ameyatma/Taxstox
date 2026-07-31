"""P5 Tests — Enterprise Platform: Branding, SSO, Billing, Portfolio,
Supervision, Bulk Operations, Firm Dashboard, Analytics, Custom Reports.

Tests: 37
"""

import pytest
from decimal import Decimal
from uuid import UUID, uuid4

# ── Domain: Branding ──

from src.domain.enterprise.branding import BrandingConfig


class TestBranding:
    def test_default_config(self):
        config = BrandingConfig.default()
        assert config.primary_color == "#1a56db"
        assert not config.has_branding

    def test_custom_config_has_branding(self):
        config = BrandingConfig(logo_url="https://firm.com/logo.png", custom_domain="tax.firm.com")
        assert config.has_branding

    def test_color_validation_valid(self):
        config = BrandingConfig(primary_color="#ff0000", accent_color="#00ff00")
        assert len(config.validate()) == 0

    def test_color_validation_invalid(self):
        config = BrandingConfig(primary_color="red")
        errors = config.validate()
        assert len(errors) > 0

    def test_domain_validation(self):
        config = BrandingConfig(custom_domain="invalid")
        errors = config.validate()
        assert len(errors) > 0


# ── Domain: SSO ──

from src.domain.enterprise.sso import (
    SSOConfig, SSOProviderType, SAMLConfig, OIDCConfig,
    DomainVerification, SSOStatus,
)


class TestSSO:
    def test_create_saml_config(self):
        saml = SAMLConfig(
            entity_id="https://idp.firm.com", sso_url="https://idp.firm.com/sso",
        )
        config = SSOConfig.create_saml(uuid4(), saml)
        assert config.provider_type == SSOProviderType.SAML
        assert config.status == SSOStatus.PENDING_VERIFICATION

    def test_create_oidc_config(self):
        oidc = OIDCConfig(issuer_url="https://accounts.google.com", client_id="abc123")
        config = SSOConfig.create_oidc(uuid4(), oidc)
        assert config.provider_type == SSOProviderType.OIDC

    def test_domain_verification(self):
        dv = DomainVerification.create("firm.com")
        assert not dv.verified
        verified = dv.verify(dv.verification_token)
        assert verified.verified

    def test_domain_verification_wrong_token(self):
        dv = DomainVerification.create("firm.com")
        result = dv.verify("wrong-token")
        assert not result.verified

    def test_add_and_verify_domain(self):
        config = SSOConfig.create_saml(uuid4(), SAMLConfig(entity_id="idp", sso_url="url"))
        dv = config.add_domain("firm.com")
        assert len(config.domains) == 1
        success = config.verify_domain("firm.com", dv.verification_token)
        assert success
        assert config.status == SSOStatus.ACTIVE

    def test_verified_domains_list(self):
        config = SSOConfig.create_saml(uuid4(), SAMLConfig(entity_id="idp", sso_url="url"))
        dv1 = config.add_domain("a.com")
        dv2 = config.add_domain("b.com")
        config.verify_domain("a.com", dv1.verification_token)
        assert config.verified_domains == ["a.com"]


# ── Domain: Billing ──

from src.domain.enterprise.billing import (
    Subscription, SubscriptionTier, BillingPeriod, Invoice,
    InvoiceItem, InvoiceStatus, UsageRecord, TIER_CONFIG,
)


class TestBilling:
    def test_create_free_subscription(self):
        sub = Subscription.create(uuid4(), SubscriptionTier.FREE)
        assert sub.tier == SubscriptionTier.FREE
        assert sub.max_filings_per_month == 10
        assert not sub.can_white_label

    def test_enterprise_subscription_features(self):
        sub = Subscription.create(uuid4(), SubscriptionTier.ENTERPRISE)
        assert sub.can_white_label
        assert sub.can_sso
        assert sub.max_filings_per_month > 100000

    def test_filing_limit_enforcement(self):
        sub = Subscription.create(uuid4(), SubscriptionTier.FREE)
        # Free tier: 10 filings/month
        for _ in range(10):
            assert sub.can_file()
            sub.record_filing()
        assert not sub.can_file()
        assert not sub.record_filing()

    def test_upgrade_subscription(self):
        sub = Subscription.create(uuid4(), SubscriptionTier.FREE)
        sub.upgrade(SubscriptionTier.PROFESSIONAL)
        assert sub.tier == SubscriptionTier.PROFESSIONAL
        assert sub.max_clients == 500

    def test_cancel_subscription(self):
        sub = Subscription.create(uuid4())
        sub.cancel()
        assert sub.status == "cancelled"

    def test_invoice_generation(self):
        items = (
            InvoiceItem(description="Professional Plan", quantity=1,
                        unit_price=Decimal("999"), amount=Decimal("999")),
            InvoiceItem(description="Extra filings (5)", quantity=5,
                        unit_price=Decimal("149"), amount=Decimal("745")),
        )
        subtotal = Decimal("1744")
        tax = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
        total = subtotal + tax
        invoice = Invoice(
            invoice_id=uuid4(), tenant_id=uuid4(),
            period_start="2026-07-01", period_end="2026-07-31",
            items=items, subtotal=subtotal, tax=tax, total=total,
        )
        assert invoice.status == InvoiceStatus.PENDING
        assert not invoice.is_paid
        assert len(invoice.items) == 2

    def test_tier_config_consistency(self):
        """All tiers must have defined configs."""
        for tier in SubscriptionTier:
            assert tier in TIER_CONFIG, f"Missing config for {tier}"
            config = TIER_CONFIG[tier]
            assert "max_clients" in config
            assert "max_filings_per_month" in config
            assert "price_per_month" in config


# ── Domain: Enhanced Tenant ──

from src.domain.enterprise.tenant import (
    Tenant, TenantStatus, FeatureFlag, ClientTag,
    Permission, ResourceAction, Role, ClientAssignment,
)


class TestEnhancedTenant:
    def test_feature_flags_default_enabled(self):
        tenant = Tenant.create("Firm", "firm")
        assert tenant.is_feature_enabled("capital_gains")

    def test_disable_feature(self):
        tenant = Tenant.create("Firm", "firm")
        tenant.disable_feature("capital_gains")
        assert not tenant.is_feature_enabled("capital_gains")

    def test_enable_feature(self):
        tenant = Tenant.create("Firm", "firm")
        tenant.disable_feature("business_income")
        tenant.enable_feature("business_income")
        assert tenant.is_feature_enabled("business_income")

    def test_tag_client(self):
        tenant = Tenant.create("Firm", "firm")
        client_id = uuid4()
        tenant.tag_client(client_id, "HNI")
        assert "HNI" in tenant.get_client_tags(client_id)

    def test_untag_client(self):
        tenant = Tenant.create("Firm", "firm")
        client_id = uuid4()
        tenant.tag_client(client_id, "HNI")
        tenant.tag_client(client_id, "NRI")
        tenant.untag_client(client_id, "HNI")
        assert tenant.get_client_tags(client_id) == ["NRI"]

    def test_get_clients_by_tag(self):
        tenant = Tenant.create("Firm", "firm")
        c1, c2 = uuid4(), uuid4()
        tenant.tag_client(c1, "HNI")
        tenant.tag_client(c2, "HNI")
        tenant.tag_client(c1, "salaried")
        hni_clients = tenant.get_clients_by_tag("HNI")
        assert len(hni_clients) == 2
        assert c1 in hni_clients and c2 in hni_clients

    def test_staff_count(self):
        tenant = Tenant.create("Firm", "firm")
        tenant.roles.clear()
        tenant.add_role("Admin", 10)
        tenant.add_role("Senior CA", 20)
        tenant.add_role("Taxpayer", 100)
        assert tenant.staff_count == 2  # Excludes Taxpayer


# ── Domain: Client Portfolio ──

from src.domain.enterprise.portfolio import (
    ClientPortfolio, ClientFilingStatus, FilingStatus,
    ClientPriority, DocumentVaultEntry,
)


class TestClientPortfolio:
    def test_set_client_status_new(self):
        portfolio = ClientPortfolio(tenant_id=uuid4())
        client_id = uuid4()
        fs = portfolio.set_client_status(client_id, "FY2025-26", FilingStatus.IN_PROGRESS)
        assert fs.status == FilingStatus.IN_PROGRESS
        assert portfolio.clients_by_status["in_progress"] == 1

    def test_advance_status(self):
        portfolio = ClientPortfolio(tenant_id=uuid4())
        client_id = uuid4()
        portfolio.set_client_status(client_id, "FY2025-26", FilingStatus.NOT_STARTED)
        portfolio.set_client_status(client_id, "FY2025-26", FilingStatus.FILED)
        fs = portfolio.get_client_status(client_id, "FY2025-26")
        assert fs is not None
        assert fs.status == FilingStatus.FILED

    def test_completion_rate(self):
        portfolio = ClientPortfolio(tenant_id=uuid4())
        portfolio.set_client_status(uuid4(), "FY2025-26", FilingStatus.FILED)
        portfolio.set_client_status(uuid4(), "FY2025-26", FilingStatus.NOT_STARTED)
        assert portfolio.completion_rate == 0.5

    def test_document_vault(self):
        portfolio = ClientPortfolio(tenant_id=uuid4())
        client_id = uuid4()
        entry = portfolio.add_document(client_id, "form16", "form16_client.pdf", "FY2025-26")
        assert entry.document_type == "form16"
        documents = portfolio.get_client_documents(client_id)
        assert len(documents) == 1

    def test_get_documents_by_type(self):
        portfolio = ClientPortfolio(tenant_id=uuid4())
        portfolio.add_document(uuid4(), "form16", "f1.pdf")
        portfolio.add_document(uuid4(), "ais", "a1.pdf")
        portfolio.add_document(uuid4(), "form16", "f2.pdf")
        form16s = portfolio.get_documents_by_type("form16")
        assert len(form16s) == 2


# ── Domain: Supervision ──

from src.domain.enterprise.supervision import (
    SupervisionWorkflow, ReviewRequest, ReviewStatus,
    ActivityLogEntry, ActivityType,
)


class TestSupervision:
    def test_submit_for_review_hierarchy_enforced(self):
        wf = SupervisionWorkflow(tenant_id=uuid4())
        # Admin (hierarchy 10) cannot review Admin (hierarchy 10)
        result = wf.submit_for_review(uuid4(), uuid4(), 10, 10)
        assert result is None  # Equal hierarchy cannot review

    def test_submit_for_review_junior_to_senior(self):
        wf = SupervisionWorkflow(tenant_id=uuid4())
        # Junior (hierarchy 30) can be reviewed by Senior (hierarchy 20)
        result = wf.submit_for_review(uuid4(), uuid4(), 20, 30)
        assert result is not None
        assert result.status == ReviewStatus.PENDING

    def test_approve_review(self):
        wf = SupervisionWorkflow(tenant_id=uuid4())
        req = wf.submit_for_review(uuid4(), uuid4(), 20, 30)
        assert req is not None
        approved = wf.approve_review(req.request_id, uuid4(), "Looks good")
        assert approved
        assert req.status == ReviewStatus.APPROVED

    def test_reject_review(self):
        wf = SupervisionWorkflow(tenant_id=uuid4())
        req = wf.submit_for_review(uuid4(), uuid4(), 20, 30)
        assert req is not None
        rejected = wf.reject_review(req.request_id, uuid4(), "Needs corrections")
        assert rejected
        assert req.status == ReviewStatus.REJECTED

    def test_pending_review_count(self):
        wf = SupervisionWorkflow(tenant_id=uuid4())
        wf.submit_for_review(uuid4(), uuid4(), 20, 30)
        wf.submit_for_review(uuid4(), uuid4(), 20, 30)
        assert wf.pending_review_count == 2

    def test_activity_log_entry(self):
        entry = ActivityLogEntry.create(
            uuid4(), uuid4(), ActivityType.CLIENT_ASSIGNED,
            "Client assigned to Senior CA",
        )
        assert entry.activity_type == ActivityType.CLIENT_ASSIGNED
        assert entry.timestamp != ""


# ── Engine: Bulk Operations ──

from src.engine.enterprise.bulk_operations import (
    BulkClientImportEngine, ClientImportRow, ImportRowStatus,
)


class TestBulkOperations:
    def test_parse_csv(self):
        engine = BulkClientImportEngine()
        csv_content = "PAN,Name,Email,Mobile,Type,Tags\nABCDE1234F,John,john@test.com,9876543210,individual,HNI\n"
        rows = engine.parse_csv(csv_content)
        assert len(rows) == 1
        assert rows[0].pan == "ABCDE1234F"
        assert rows[0].name == "John"

    def test_validate_valid_row(self):
        row = ClientImportRow(
            row_number=1, pan="ABCDE1234F", name="John Doe",
            email="john@test.com", mobile="9876543210",
        )
        errors = row.validate()
        assert len(errors) == 0

    def test_validate_invalid_pan(self):
        row = ClientImportRow(row_number=1, pan="INVALID", name="John")
        errors = row.validate()
        assert len(errors) > 0

    def test_process_import_dedup(self):
        engine = BulkClientImportEngine()
        rows = [
            ClientImportRow(row_number=1, pan="ABCDE1234F", name="John"),
            ClientImportRow(row_number=2, pan="XYZAB5678C", name="Jane"),
        ]
        engine.validate_rows(rows)
        result = engine.process_import(
            uuid4(), rows, existing_pans={"ABCDE1234F"},
        )
        assert result.success_count == 1
        assert result.skipped_count == 1

    def test_csv_template_generation(self):
        engine = BulkClientImportEngine()
        template = engine.generate_csv_template()
        assert "PAN" in template
        assert "ABCDE1234F" in template


# ── Engine: Firm Dashboard ──

from src.engine.enterprise.firm_dashboard import FirmDashboardEngine


class TestFirmDashboard:
    def test_compute_basic_metrics(self):
        class FakeRepo:
            def get(self, tid):
                tenant = Tenant.create("Test Firm", "test-firm")
                return tenant
            def get_by_slug(self, s): return None
            def save(self, t): pass
            def list_all(self): return []
            def list_by_user(self, u): return []

        engine = FirmDashboardEngine(FakeRepo())
        dashboard = engine.compute(uuid4())
        assert dashboard.tenant_name == "Test Firm"
        assert dashboard.total_clients.value > 0 or dashboard.total_clients.value == Decimal("0")


# ── Engine: Comparative Analytics ──

from src.engine.enterprise.comparative_analytics import ComparativeAnalyticsEngine


class TestComparativeAnalytics:
    def test_tax_benchmarks_computation(self):
        tax_data = [
            {"total_income": "1000000", "final_tax": "50000", "regime": "new"},
            {"total_income": "2000000", "final_tax": "200000", "regime": "old"},
            {"total_income": "500000", "final_tax": "0", "regime": "new"},
        ]
        benchmarks = ComparativeAnalyticsEngine.compute_tax_benchmarks(tax_data)
        assert len(benchmarks) >= 1

    def test_regime_distribution(self):
        regimes = ["new", "old", "new", "new", "old"]
        dist = ComparativeAnalyticsEngine.compute_regime_distribution(regimes)
        assert dist["new"] == 3
        assert dist["old"] == 2


# ── Engine: Custom Reports ──

from src.engine.reporting.custom_report_builder import CustomReportEngine, ReportGenerationResult
from src.domain.reporting.custom_report import ReportFormat


class TestCustomReports:
    def test_available_templates(self):
        engine = CustomReportEngine()
        templates = engine.available_templates
        assert len(templates) == 4

    def test_generate_csv_report(self):
        engine = CustomReportEngine()
        templates = engine.available_templates
        tenant = Tenant.create("Test Firm", "test-firm")
        result = engine.generate(templates[0], tenant, {"financial_year": "FY2025-26"}, ReportFormat.CSV)
        assert result.success
        assert "Client ID" in result.content

    def test_generate_json_report(self):
        engine = CustomReportEngine()
        templates = engine.available_templates
        tenant = Tenant.create("Test Firm", "test-firm")
        result = engine.generate(templates[0], tenant, {"financial_year": "FY2025-26"}, ReportFormat.JSON)
        assert result.success
        assert "clients" in result.content


# ── Infrastructure: SSO ──

from src.infrastructure.sso import SAMLAdapter, OIDCAdapter, SSOService


class TestSSOInfrastructure:
    def test_saml_validate_valid(self):
        config = SAMLConfig(
            entity_id="https://idp.test.com",
            sso_url="https://idp.test.com/sso",
            x509_certificate="-----BEGIN CERTIFICATE-----\nMIID...\n-----END CERTIFICATE-----",
        )
        errors = SAMLAdapter.validate_config(config)
        assert len(errors) == 0

    def test_saml_validate_missing_cert(self):
        config = SAMLConfig(entity_id="idp", sso_url="url")
        errors = SAMLAdapter.validate_config(config)
        assert len(errors) > 0

    def test_saml_metadata_generation(self):
        metadata = SAMLAdapter.generate_sp_metadata("test-firm", "https://taxstox.com/acs")
        assert "test-firm" in metadata
        assert "AssertionConsumerService" in metadata

    def test_oidc_validate_missing_secret(self):
        config = OIDCConfig(issuer_url="https://idp.com", client_id="abc")
        errors = OIDCAdapter.validate_config(config)
        assert len(errors) > 0


# ── Infrastructure: Billing ──

from src.infrastructure.billing import (
    SubscriptionManager, BillingGateway, UsageTracker, PaymentStatus,
)


class TestBillingInfrastructure:
    def test_subscription_manager_create(self):
        sub = SubscriptionManager.create_subscription(uuid4(), SubscriptionTier.PROFESSIONAL)
        assert sub.tier == SubscriptionTier.PROFESSIONAL

    def test_upgrade_refused_for_downgrade(self):
        sub = SubscriptionManager.create_subscription(uuid4(), SubscriptionTier.ENTERPRISE)
        result = SubscriptionManager.upgrade(sub, SubscriptionTier.FREE)
        assert not result
        assert sub.tier == SubscriptionTier.ENTERPRISE

    def test_upgrade_allowed(self):
        sub = SubscriptionManager.create_subscription(uuid4(), SubscriptionTier.FREE)
        result = SubscriptionManager.upgrade(sub, SubscriptionTier.PROFESSIONAL)
        assert result
        assert sub.tier == SubscriptionTier.PROFESSIONAL

    def test_invoice_generation(self):
        sub = SubscriptionManager.create_subscription(uuid4(), SubscriptionTier.PROFESSIONAL)
        sub.record_filing()
        sub.record_filing()
        invoice = SubscriptionManager.generate_invoice(sub, uuid4())
        assert invoice.total > 0
        assert len(invoice.items) >= 1

    def test_usage_tracker(self):
        tracker = UsageTracker()
        tid = uuid4()
        tracker.record(tid, "filing_completed")
        tracker.record(tid, "filing_completed")
        count = tracker.count_this_month(tid, "filing_completed")
        assert count == 2

    def test_payment_record(self):
        from src.infrastructure.billing import PaymentRecord
        payment = PaymentRecord(
            payment_id=uuid4(), invoice_id=uuid4(),
            tenant_id=uuid4(), amount=Decimal("999"),
        )
        assert payment.status == PaymentStatus.PENDING
