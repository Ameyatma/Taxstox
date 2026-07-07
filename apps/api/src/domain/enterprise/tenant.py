"""Enterprise Tenant — Aggregate Root.

Tenant owns: Roles, Permissions, ClientAssignments.
All mutations flow through the Tenant aggregate to enforce invariants.

Traceability: C21.1 (Tenant Management), C21.2 (CA Firm Hierarchy)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Protocol
from uuid import UUID, uuid4


# ── Value Objects ─────────────────────────────────────────────────────

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class ResourceAction(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE = "manage"


@dataclass(frozen=True)
class Permission:
    """A single permission: resource + action. Value object — immutable, shareable."""
    resource: str              # e.g., "filing", "client", "billing"
    action: ResourceAction     # read, write, delete, manage

    @staticmethod
    def create(resource: str, action: ResourceAction | str) -> Permission:
        action = ResourceAction(action) if isinstance(action, str) else action
        return Permission(resource=resource, action=action)


# ── Role Entity ───────────────────────────────────────────────────────

@dataclass
class Role:
    """A role with a hierarchy level and permissions. Owned by Tenant."""

    role_id: UUID
    name: str                            # "SuperAdmin", "Senior CA", "Taxpayer"
    hierarchy_level: int                 # Lower = more authority (0 = SuperAdmin)
    permissions: set[Permission] = field(default_factory=set)
    description: str = ""

    def has_permission(self, resource: str, action: ResourceAction) -> bool:
        """Check if this role grants the given permission."""
        return Permission(resource=resource, action=action) in self.permissions

    def grant(self, permission: Permission) -> None:
        self.permissions.add(permission)

    def revoke(self, permission: Permission) -> None:
        self.permissions.discard(permission)


# ── Tenant Aggregate Root ─────────────────────────────────────────────

@dataclass
class Tenant:
    """Enterprise tenant — CA firm, enterprise, or individual.

    Aggregate Root. All mutations to Roles, Clients, and tenant state
    flow through this aggregate to enforce consistency.
    """

    tenant_id: UUID
    name: str
    slug: str                            # URL-safe identifier
    status: TenantStatus = TenantStatus.ACTIVE
    roles: list[Role] = field(default_factory=list)
    client_assignments: list[ClientAssignment] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    @staticmethod
    def create(name: str, slug: str) -> Tenant:
        """Factory: create a new tenant with default roles."""
        tenant = Tenant(tenant_id=uuid4(), name=name, slug=slug)
        # Every tenant gets a default Admin role
        admin = Role(
            role_id=uuid4(), name="Admin", hierarchy_level=10,
            permissions={
                Permission.create("filing", ResourceAction.MANAGE),
                Permission.create("client", ResourceAction.MANAGE),
                Permission.create("billing", ResourceAction.READ),
            },
            description="Default tenant administrator",
        )
        tenant.roles.append(admin)
        return tenant

    def add_role(self, name: str, hierarchy_level: int, description: str = "") -> Role:
        """Create and add a new role to this tenant."""
        role = Role(
            role_id=uuid4(), name=name, hierarchy_level=hierarchy_level,
            description=description,
        )
        self.roles.append(role)
        self._touch()
        return role

    def get_role(self, role_id: UUID) -> Optional[Role]:
        for r in self.roles:
            if r.role_id == role_id:
                return r
        return None

    def assign_client(self, user_id: UUID, assigned_by: UUID) -> ClientAssignment:
        """Assign a taxpayer client to this tenant."""
        assignment = ClientAssignment(
            assignment_id=uuid4(),
            client_user_id=user_id,
            assigned_by=assigned_by,
            tenant_id=self.tenant_id,
        )
        self.client_assignments.append(assignment)
        self._touch()
        return assignment

    def remove_client(self, user_id: UUID) -> bool:
        before = len(self.client_assignments)
        self.client_assignments = [
            a for a in self.client_assignments if a.client_user_id != user_id
        ]
        self._touch()
        return len(self.client_assignments) < before

    def suspend(self) -> None:
        self.status = TenantStatus.SUSPENDED
        self._touch()

    def activate(self) -> None:
        self.status = TenantStatus.ACTIVE
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    @property
    def client_count(self) -> int:
        return len(self.client_assignments)

    @property
    def role_count(self) -> int:
        return len(self.roles)

    @property
    def is_active(self) -> bool:
        return self.status == TenantStatus.ACTIVE


# ── ClientAssignment (Entity within Tenant aggregate) ─────────────────

@dataclass(frozen=True)
class ClientAssignment:
    """A taxpayer client assigned to a tenant (CA firm)."""
    assignment_id: UUID
    client_user_id: UUID
    assigned_by: UUID
    tenant_id: UUID
    assigned_at: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.assigned_at:
            object.__setattr__(self, "assigned_at",
                              datetime.now(timezone.utc).isoformat())


# ── Tenant Repository (Abstract Interface) ────────────────────────────

class TenantRepository(Protocol):
    """Aggregate-oriented repository for Tenant. Implementation in infrastructure."""

    def get(self, tenant_id: UUID) -> Optional[Tenant]: ...

    def get_by_slug(self, slug: str) -> Optional[Tenant]: ...

    def save(self, tenant: Tenant) -> None: ...

    def list_all(self) -> list[Tenant]: ...

    def list_by_user(self, user_id: UUID) -> list[Tenant]: ...


# ── Tenant Context Abstraction (Domain side) ──────────────────────────

class TenantContextProvider(Protocol):
    """Abstract access to current tenant context. Infrastructure provides
    the implementation via TenantContextMiddleware."""

    def current_tenant_id(self) -> Optional[UUID]: ...
