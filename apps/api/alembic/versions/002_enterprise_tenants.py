"""Enterprise Multi-Tenancy — Alembic migration M8.

Creates: tenants, roles, permissions tables.
Modifies: users (+tenant_id, +role_id), filings (+tenant_id).

Backward compatible: default tenant for existing users. Reversible.
"""

from alembic import op
import sqlalchemy as sa
from uuid import uuid4

revision = "002_enterprise_tenants"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create tenants table
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid4())),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # 2. Create roles table (scoped to tenant)
    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid4())),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("hierarchy_level", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("description", sa.String(500), server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # 3. Create permissions table (scoped to role)
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: str(uuid4())),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("resource", sa.String(100), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
    )

    # 4. Add tenant_id and role_id to users (nullable initially for backfill)
    op.add_column("users", sa.Column("tenant_id", sa.String(36), nullable=True))
    op.add_column("users", sa.Column("role_id", sa.String(36), nullable=True))

    # 5. Create a default tenant for existing users
    default_tenant_id = str(uuid4())
    op.execute(f"""
        INSERT INTO tenants (id, name, slug, status)
        VALUES ('{default_tenant_id}', 'Default', 'default', 'active')
    """)

    # 6. Backfill existing users with default tenant
    op.execute(f"""
        UPDATE users SET tenant_id = '{default_tenant_id}' WHERE tenant_id IS NULL
    """)

    # 7. Add tenant_id to filings (nullable, backfill from user)
    op.add_column("filings", sa.Column("tenant_id", sa.String(36), nullable=True))
    op.execute(f"""
        UPDATE filings SET tenant_id = (
            SELECT tenant_id FROM users WHERE users.id = filings.user_id
        ) WHERE tenant_id IS NULL
    """)

    # 8. Create indexes
    op.create_index("idx_users_tenant", "users", ["tenant_id"])
    op.create_index("idx_filings_tenant", "filings", ["tenant_id"])
    op.create_index("idx_roles_tenant", "roles", ["tenant_id"])
    op.create_index("idx_permissions_role", "permissions", ["role_id"])


def downgrade():
    op.drop_index("idx_permissions_role")
    op.drop_index("idx_roles_tenant")
    op.drop_index("idx_filings_tenant")
    op.drop_index("idx_users_tenant")
    op.drop_column("filings", "tenant_id")
    op.drop_column("users", "role_id")
    op.drop_column("users", "tenant_id")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("tenants")
