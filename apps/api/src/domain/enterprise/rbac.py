"""RBAC Domain Service — Authorization independent of authentication.

JWT provides identity. This service determines permissions.
No framework dependencies. Pure domain logic.

Traceability: C1.3 (RBAC), C21.2 (CA Firm Hierarchy)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.domain.enterprise.tenant import (
    Tenant,
    TenantRepository,
    Role,
    Permission,
    ResourceAction,
)


class AuthorizationService:
    """Determines what a user can do within a tenant.

    Pure domain logic. No HTTP, no JWT parsing, no framework types.
    Consumes Tenant aggregate via repository.
    """

    def __init__(self, tenant_repo: TenantRepository) -> None:
        self._repo = tenant_repo

    def can(
        self,
        tenant_id: UUID,
        user_id: UUID,
        resource: str,
        action: ResourceAction,
        user_roles: list[str] | None = None,
    ) -> bool:
        """Check if user has permission within a tenant."""
        tenant = self._repo.get(tenant_id)
        if not tenant or not tenant.is_active:
            return False

        for role in tenant.roles:
            if user_roles and role.name not in user_roles:
                continue
            if role.has_permission(resource, action):
                return True

        return False

    def get_permissions(
        self, tenant_id: UUID, user_roles: list[str],
    ) -> set[Permission]:
        """Get all permissions for a user's roles within a tenant."""
        tenant = self._repo.get(tenant_id)
        if not tenant or not tenant.is_active:
            return set()

        perms: set[Permission] = set()
        for role in tenant.roles:
            if role.name in user_roles:
                perms |= role.permissions
        return perms

    def can_manage_clients(self, tenant_id: UUID, user_roles: list[str]) -> bool:
        return self.can(tenant_id, UUID("00000000-0000-0000-0000-000000000000"),
                       "client", ResourceAction.MANAGE, user_roles)


class RoleAssignmentService:
    """Assigns roles to users within a tenant. Domain service — no persistence."""

    @staticmethod
    def assign(
        tenant: Tenant, user_id: UUID, role_name: str,
    ) -> bool:
        """Assign a role to a user. Returns True if role exists in tenant."""
        for role in tenant.roles:
            if role.name == role_name:
                return True
        return False

    @staticmethod
    def resolve_hierarchy(tenant: Tenant, role_names: list[str]) -> int:
        """Get the highest authority level (lowest hierarchy_level number)."""
        min_level = 999
        for role in tenant.roles:
            if role.name in role_names:
                min_level = min(min_level, role.hierarchy_level)
        return min_level if min_level < 999 else 999
