"""Enterprise Platform — Alembic migration P5.

Creates: subscriptions, branding_configs, sso_configs, domain_verifications,
         client_tags, activity_log, document_vault, client_filing_status,
         review_requests, report_schedules tables.

Backward compatible: all tables are additive. No data migration needed.
"""

from alembic import op
import sqlalchemy as sa

revision = "003_enterprise_platform"
down_revision = "002_enterprise_tenants"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, unique=True),
        sa.Column("tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("period", sa.String(20), nullable=False, server_default="monthly"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("current_period_start", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("filings_this_period", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # 2. Branding configs table
    op.create_table(
        "branding_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, unique=True),
        sa.Column("logo_url", sa.String(500), server_default=""),
        sa.Column("favicon_url", sa.String(500), server_default=""),
        sa.Column("primary_color", sa.String(7), server_default="#1a56db"),
        sa.Column("accent_color", sa.String(7), server_default="#16a34a"),
        sa.Column("custom_domain", sa.String(255), server_default=""),
        sa.Column("custom_css_url", sa.String(500), server_default=""),
        sa.Column("company_name_display", sa.String(255), server_default=""),
        sa.Column("support_email", sa.String(255), server_default=""),
        sa.Column("support_phone", sa.String(20), server_default=""),
        sa.Column("powered_by_visible", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # 3. SSO configs table
    op.create_table(
        "sso_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, unique=True),
        sa.Column("provider_type", sa.String(10), nullable=False, server_default="oidc"),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending_verification"),
        sa.Column("saml_entity_id", sa.String(500), server_default=""),
        sa.Column("saml_sso_url", sa.String(500), server_default=""),
        sa.Column("saml_x509_cert", sa.Text(), server_default=""),
        sa.Column("oidc_issuer_url", sa.String(500), server_default=""),
        sa.Column("oidc_client_id", sa.String(255), server_default=""),
        sa.Column("oidc_client_secret_encrypted", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # 4. Domain verifications (for SSO)
    op.create_table(
        "domain_verifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sso_config_id", sa.String(36), sa.ForeignKey("sso_configs.id"), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("verification_token", sa.String(255), nullable=False),
        sa.Column("verified", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # 5. Client tags
    op.create_table(
        "client_tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("client_user_id", sa.String(36), nullable=False, index=True),
        sa.Column("tag", sa.String(100), nullable=False),
        sa.Column("applied_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "client_user_id", "tag", name="uq_client_tag"),
    )

    # 6. Activity log
    op.create_table(
        "activity_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("activity_type", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("target_user_id", sa.String(36), nullable=True),
        sa.Column("target_resource", sa.String(255), server_default=""),
        sa.Column("metadata_json", sa.Text(), server_default="{}"),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), index=True),
    )

    # 7. Document vault
    op.create_table(
        "document_vault",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("client_user_id", sa.String(36), nullable=False, index=True),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("financial_year", sa.String(10), server_default=""),
        sa.Column("uploaded_by", sa.String(36), nullable=True),
        sa.Column("expiry_date", sa.DateTime(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # 8. Client filing statuses (portfolio)
    op.create_table(
        "client_filing_statuses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("client_user_id", sa.String(36), nullable=False, index=True),
        sa.Column("financial_year", sa.String(10), nullable=False),
        sa.Column("itr_type", sa.String(10), server_default=""),
        sa.Column("status", sa.String(30), nullable=False, server_default="not_started"),
        sa.Column("priority", sa.String(20), server_default="normal"),
        sa.Column("assigned_to", sa.String(36), nullable=True),
        sa.Column("due_date", sa.String(10), nullable=True),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.Column("last_updated", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "client_user_id", "financial_year", name="uq_client_filing"),
    )

    # 9. Review requests (supervision workflow)
    op.create_table(
        "review_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("submitted_by", sa.String(36), nullable=False),
        sa.Column("submitted_for", sa.String(36), nullable=False),
        sa.Column("reviewer_id", sa.String(36), nullable=True),
        sa.Column("financial_year", sa.String(10), server_default=""),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("comments", sa.Text(), server_default=""),
        sa.Column("reviewer_comments", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
    )

    # 10. Report schedules
    op.create_table(
        "report_schedules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("template_id", sa.String(36), nullable=False),
        sa.Column("frequency", sa.String(20), nullable=False, server_default="once"),
        sa.Column("format", sa.String(10), nullable=False, server_default="csv"),
        sa.Column("recipients_json", sa.Text(), server_default="[]"),
        sa.Column("parameters_json", sa.Text(), server_default="{}"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("report_schedules")
    op.drop_table("review_requests")
    op.drop_table("client_filing_statuses")
    op.drop_table("document_vault")
    op.drop_table("activity_log")
    op.drop_table("client_tags")
    op.drop_table("domain_verifications")
    op.drop_table("sso_configs")
    op.drop_table("branding_configs")
    op.drop_table("subscriptions")
