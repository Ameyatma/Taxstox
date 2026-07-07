"""Enterprise Domain Services — Business workflows.

Tenant onboarding, user invitation, role assignment, client assignment.
All pure domain logic. No framework dependencies.

Traceability: C21.1, C21.2, C21.3
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from src.domain.enterprise.tenant import (
    Tenant,
    TenantStatus,
    TenantRepository,
    ClientAssignment,
    Permission,
    ResourceAction,
    Role,
)


@dataclass
class OnboardingResult:
    """Result of tenant onboarding."""
    tenant: Tenant
    admin_role: Role
    success: bool = True
    message: str = ""


class TenantOnboardingService:
    """Orchestrates new tenant creation with default roles and setup.

    Domain service — pure logic, no persistence (delegates to TenantRepository).
    """

    def __init__(self, repo: TenantRepository) -> None:
        self._repo = repo

    def onboard(
        self,
        name: str,
        slug: str,
        admin_user_id: Optional[UUID] = None,
    ) -> OnboardingResult:
        """Create a new tenant with default CA firm role structure.

        Default roles:
        - Admin (hierarchy 10): full access
        - Senior CA (hierarchy 20): manage clients, file returns
        - Junior CA (hierarchy 30): file returns, read clients
        - Taxpayer (hierarchy 100): read own data
        """
        if self._repo.get_by_slug(slug):
            return OnboardingResult(
                tenant=Tenant(tenant_id=uuid4(), name="", slug=""),
                admin_role=Role(role_id=uuid4(), name="", hierarchy_level=0),
                success=False,
                message=f"Tenant with slug '{slug}' already exists.",
            )

        tenant = Tenant.create(name=name, slug=slug)
        # Replace default Admin with properly structured roles
        tenant.roles.clear()

        admin = tenant.add_role("Admin", 10, "Full tenant access")
        admin.grant(Permission.create("filing", ResourceAction.MANAGE))
        admin.grant(Permission.create("client", ResourceAction.MANAGE))
        admin.grant(Permission.create("billing", ResourceAction.MANAGE))
        admin.grant(Permission.create("settings", ResourceAction.MANAGE))

        senior = tenant.add_role("Senior CA", 20, "Manage clients, file returns")
        senior.grant(Permission.create("filing", ResourceAction.WRITE))
        senior.grant(Permission.create("client", ResourceAction.WRITE))
        senior.grant(Permission.create("billing", ResourceAction.READ))

        junior = tenant.add_role("Junior CA", 30, "File returns, read clients")
        junior.grant(Permission.create("filing", ResourceAction.WRITE))
        junior.grant(Permission.create("client", ResourceAction.READ))

        taxpayer = tenant.add_role("Taxpayer", 100, "Read own data")
        taxpayer.grant(Permission.create("filing", ResourceAction.READ))

        self._repo.save(tenant)

        return OnboardingResult(tenant=tenant, admin_role=admin)


class ClientAssignmentService:
    """Manages client-to-tenant assignments. Domain service."""

    def __init__(self, repo: TenantRepository) -> None:
        self._repo = repo

    def assign(
        self,
        tenant: Tenant,
        client_user_id: UUID,
        assigned_by: UUID,
    ) -> Optional[ClientAssignment]:
        """Assign a taxpayer client to a CA firm tenant."""
        if not tenant.is_active:
            return None

        # Prevent duplicate assignment
        for existing in tenant.client_assignments:
            if existing.client_user_id == client_user_id:
                return existing

        assignment = tenant.assign_client(client_user_id, assigned_by)
        self._repo.save(tenant)
        return assignment

    def bulk_assign(
        self,
        tenant: Tenant,
        client_user_ids: list[UUID],
        assigned_by: UUID,
    ) -> int:
        """Bulk assign clients. Returns count of new assignments."""
        count = 0
        for uid in client_user_ids:
            if self.assign(tenant, uid, assigned_by):
                count += 1
        return count

    def unassign(
        self, tenant: Tenant, client_user_id: UUID,
    ) -> bool:
        """Remove a client from a tenant."""
        removed = tenant.remove_client(client_user_id)
        if removed:
            self._repo.save(tenant)
        return removed
