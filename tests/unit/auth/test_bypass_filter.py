"""Unit tests for bypass_filter production fix in AuthService.

AuthService.get_authenticated_user() must set uow.bypass_filter based on
user.role == UserRole.SUPER_ADMIN after loading the user, so that
TenantAwareRepository queries bypass tenant scoping for cross-tenant
super-admin users.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from tests.factories import make_user_entity
from tests.mocks import MockUoW

from src.auth.application.services.authentication_service import AuthService
from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository


class TestBypassFilter:
    """AuthService.get_authenticated_user sets bypass_filter based on role."""

    def setup_method(self) -> None:
        self.token_service = MagicMock()
        self.blacklist_service = MagicMock()
        self.blacklist_service.is_blacklisted = AsyncMock(return_value=False)
        self.service = AuthService(
            token_service=self.token_service,
            blacklist_service=self.blacklist_service,
        )

    async def test_activates_bypass_when_user_is_super_admin(self) -> None:
        """When user.role is SUPER_ADMIN, uow.bypass_filter becomes True."""
        admin_user = make_user_entity(role=UserRole.SUPER_ADMIN)
        self.token_service.decode.return_value = {
            "user_id": str(admin_user.id),
            "tenant_id": str(admin_user.tenant_id),
            "jti": str(uuid4()),
        }
        uow = MockUoW()
        repo = uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=admin_user)

        user = await self.service.get_authenticated_user(uow, "valid-token")

        assert user == admin_user
        assert uow.bypass_filter is True

    async def test_bypass_stays_false_for_non_super_admin(self) -> None:
        """When user.role is not SUPER_ADMIN, uow.bypass_filter remains False."""
        viewer_user = make_user_entity(role=UserRole.VIEWER)
        self.token_service.decode.return_value = {
            "user_id": str(viewer_user.id),
            "tenant_id": str(viewer_user.tenant_id),
            "jti": str(uuid4()),
        }
        uow = MockUoW(tenant_id=viewer_user.tenant_id)
        repo = uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=viewer_user)

        user = await self.service.get_authenticated_user(uow, "valid-token")

        assert user == viewer_user
        assert uow.bypass_filter is False

    async def test_editor_does_not_activate_bypass(self) -> None:
        """EDITOR role does NOT activate bypass_filter."""
        editor_user = make_user_entity(role=UserRole.EDITOR)
        self.token_service.decode.return_value = {
            "user_id": str(editor_user.id),
            "tenant_id": str(editor_user.tenant_id),
            "jti": str(uuid4()),
        }
        uow = MockUoW(tenant_id=editor_user.tenant_id)
        repo = uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=editor_user)

        user = await self.service.get_authenticated_user(uow, "valid-token")

        assert user == editor_user
        assert uow.bypass_filter is False

    async def test_admin_does_not_activate_bypass(self) -> None:
        """ADMIN role does NOT activate bypass_filter."""
        admin_user = make_user_entity(role=UserRole.ADMIN)
        self.token_service.decode.return_value = {
            "user_id": str(admin_user.id),
            "tenant_id": str(admin_user.tenant_id),
            "jti": str(uuid4()),
        }
        uow = MockUoW(tenant_id=admin_user.tenant_id)
        repo = uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=admin_user)

        user = await self.service.get_authenticated_user(uow, "valid-token")

        assert user == admin_user
        assert uow.bypass_filter is False

    async def test_owner_does_not_activate_bypass(self) -> None:
        """OWNER role does NOT activate bypass_filter."""
        owner_user = make_user_entity(role=UserRole.OWNER)
        self.token_service.decode.return_value = {
            "user_id": str(owner_user.id),
            "tenant_id": str(owner_user.tenant_id),
            "jti": str(uuid4()),
        }
        uow = MockUoW(tenant_id=owner_user.tenant_id)
        repo = uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=owner_user)

        user = await self.service.get_authenticated_user(uow, "valid-token")

        assert user == owner_user
        assert uow.bypass_filter is False

    async def test_bypass_filter_does_not_affect_returned_user(self) -> None:
        """The returned UserEntity should have correct fields regardless of bypass."""
        super_admin_user = make_user_entity(role=UserRole.SUPER_ADMIN)
        self.token_service.decode.return_value = {
            "user_id": str(super_admin_user.id),
            "tenant_id": str(super_admin_user.tenant_id),
            "jti": str(uuid4()),
        }
        uow = MockUoW(tenant_id=super_admin_user.tenant_id)
        repo = uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=super_admin_user)

        user = await self.service.get_authenticated_user(uow, "valid-token")

        assert user.role == UserRole.SUPER_ADMIN
