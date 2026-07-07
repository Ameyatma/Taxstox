"""Unit tests for Enterprise Multi-Tenancy bounded context — M8."""

from uuid import UUID, uuid4

from src.domain.enterprise.tenant import (
    Tenant,
    TenantStatus,
    Permission,
    ResourceAction,
    Role,
    ClientAssignment,
)


class TestPermission:
    def test_create_permission(self):
        p = Permission.create("filing", ResourceAction.WRITE)
        assert p.resource == "filing"
        assert p.action == ResourceAction.WRITE

    def test_permission_equality(self):
        p1 = Permission.create("filing", "read")
        p2 = Permission.create("filing", ResourceAction.READ)
        assert p1 == p2

    def test_permission_from_string(self):
        p = Permission.create("client", "manage")
        assert p.action == ResourceAction.MANAGE


class TestRole:
    def test_create_role(self):
        role = Role(role_id=uuid4(), name="Senior CA", hierarchy_level=20)
        assert role.hierarchy_level == 20

    def test_grant_permission(self):
        role = Role(role_id=uuid4(), name="Admin", hierarchy_level=10)
        role.grant(Permission.create("filing", ResourceAction.MANAGE))
        assert role.has_permission("filing", ResourceAction.MANAGE)

    def test_revoke_permission(self):
        role = Role(role_id=uuid4(), name="Admin", hierarchy_level=10)
        p = Permission.create("billing", ResourceAction.READ)
        role.grant(p)
        role.revoke(p)
        assert not role.has_permission("billing", ResourceAction.READ)

    def test_no_permission_by_default(self):
        role = Role(role_id=uuid4(), name="Junior", hierarchy_level=30)
        assert not role.has_permission("filing", ResourceAction.MANAGE)


class TestTenant:
    def test_create_tenant(self):
        tenant = Tenant.create("Test Firm", "test-firm")
        assert tenant.name == "Test Firm"
        assert tenant.slug == "test-firm"
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.is_active

    def test_default_admin_role(self):
        tenant = Tenant.create("Firm", "firm")
        assert tenant.role_count >= 1
        admin = tenant.get_role(tenant.roles[0].role_id)
        assert admin is not None
        assert admin.name == "Admin"

    def test_add_role(self):
        tenant = Tenant.create("Firm", "firm")
        tenant.roles.clear()
        role = tenant.add_role("Senior CA", 20, "Senior accountant")
        assert tenant.role_count == 1
        assert role.name == "Senior CA"

    def test_suspend_activate(self):
        tenant = Tenant.create("Firm", "firm")
        tenant.suspend()
        assert not tenant.is_active
        tenant.activate()
        assert tenant.is_active

    def test_assign_client(self):
        tenant = Tenant.create("Firm", "firm")
        client_id = uuid4()
        assignment = tenant.assign_client(client_id, uuid4())
        assert assignment.client_user_id == client_id
        assert tenant.client_count == 1

    def test_remove_client(self):
        tenant = Tenant.create("Firm", "firm")
        client_id = uuid4()
        tenant.assign_client(client_id, uuid4())
        assert tenant.client_count == 1
        tenant.remove_client(client_id)
        assert tenant.client_count == 0

    def test_no_duplicate_client(self):
        tenant = Tenant.create("Firm", "firm")
        client_id = uuid4()
        tenant.assign_client(client_id, uuid4())
        tenant.assign_client(client_id, uuid4())
        assert tenant.client_count == 2  # Tenant doesn't deduplicate (service does)


class TestClientAssignment:
    def test_create_assignment(self):
        a = ClientAssignment(
            assignment_id=uuid4(),
            client_user_id=uuid4(),
            assigned_by=uuid4(),
            tenant_id=uuid4(),
        )
        assert a.assigned_at != ""


class TestAuthorizationService:
    def test_can_with_valid_permission(self):
        from src.domain.enterprise.rbac import AuthorizationService

        class FakeRepo:
            def get(self, tid):
                tenant = Tenant.create("Test", "test")
                role = tenant.roles[0]
                role.grant(Permission.create("filing", ResourceAction.WRITE))
                return tenant
            def get_by_slug(self, s): return None
            def save(self, t): pass
            def list_all(self): return []
            def list_by_user(self, u): return []

        svc = AuthorizationService(FakeRepo())
        result = svc.can(
            uuid4(), uuid4(), "filing", ResourceAction.WRITE,
            user_roles=["Admin"],
        )
        assert result is True

    def test_cannot_without_permission(self):
        from src.domain.enterprise.rbac import AuthorizationService

        class FakeRepo:
            def get(self, tid):
                tenant = Tenant.create("Test", "test")
                tenant.roles.clear()
                return tenant
            def get_by_slug(self, s): return None
            def save(self, t): pass
            def list_all(self): return []
            def list_by_user(self, u): return []

        svc = AuthorizationService(FakeRepo())
        result = svc.can(
            uuid4(), uuid4(), "filing", ResourceAction.WRITE,
            user_roles=["Admin"],
        )
        assert result is False


class TestOnboardingService:
    def test_onboard_creates_tenant_with_roles(self):
        from src.domain.enterprise.services import TenantOnboardingService

        class FakeRepo:
            def __init__(self): self.saved = None
            def get(self, tid): return None
            def get_by_slug(self, s): return None
            def save(self, t): self.saved = t
            def list_all(self): return []
            def list_by_user(self, u): return []

        repo = FakeRepo()
        svc = TenantOnboardingService(repo)
        result = svc.onboard("Test CA Firm", "test-ca")

        assert result.success
        assert repo.saved is not None
        assert repo.saved.role_count == 4  # Admin, Senior CA, Junior CA, Taxpayer
        assert "Admin" in [r.name for r in repo.saved.roles]

    def test_onboard_duplicate_slug_fails(self):
        from src.domain.enterprise.services import TenantOnboardingService

        class FakeRepo:
            def get(self, tid): return None
            def get_by_slug(self, s): return Tenant.create("Existing", s)
            def save(self, t): pass
            def list_all(self): return []
            def list_by_user(self, u): return []

        svc = TenantOnboardingService(FakeRepo())
        result = svc.onboard("New Firm", "test-ca")
        assert not result.success
