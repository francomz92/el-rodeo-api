"""Unit tests for user management use cases.

Tests:
- GetUserProfileCase returns current_user unchanged
- UpdateUserProfileCase: email uniqueness conflict, happy path
- ListUsersCase: pagination passthrough, role guard
- SoftDeleteUserCase: self-block, last-OWNER block, cross-tenant block
- LoginUserService: inactive user raises 401
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from tests.factories import make_user_entity
from tests.mocks import MockUoW

from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.common.domain.exceptions import ConflictError, DomainError, NotFoundError, NotPermissionError, UnauthorizedError


class TestGetUserProfileCase:
    """GetUserProfileCase returns the current user unchanged."""

    def setup_method(self) -> None:
        from src.auth.application.uses_cases.get_user_profile_case import (
            GetUserProfileCase,
        )

        self.case = GetUserProfileCase()

    @pytest.mark.asyncio
    async def test_execute_returns_current_user(self) -> None:
        """Returns the same user entity passed in."""
        user = make_user_entity()
        result = await self.case.execute(user)

        assert result is user
        assert result.id == user.id
        assert result.name == user.name
        assert result.email == user.email


class TestUpdateUserProfileCase:
    """UpdateUserProfileCase handles email update and uniqueness validation."""

    def setup_method(self) -> None:
        from src.auth.application.uses_cases.update_user_profile_case import (
            UpdateUserProfileCase,
        )

        self.uow = MockUoW()
        self.case = UpdateUserProfileCase(uow=self.uow)

    @pytest.mark.asyncio
    async def test_execute_updates_name_successfully(self) -> None:
        """Happy path: name update succeeds."""
        user = make_user_entity()
        repo = self.uow.get_repository(IUserRepository)
        repo.exists_by_email_excluding_user = AsyncMock(return_value=False)
        repo.update_data = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=user)

        result = await self.case.execute(
            current_user=user,
            name="New Name",
        )

        assert result.name == user.name  # Returned from mock is same entity
        repo.update_data.assert_awaited_once()
        self.uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_raises_on_duplicate_email(self) -> None:
        """Raises ConflictError when email is already taken by another user."""
        user = make_user_entity()
        repo = self.uow.get_repository(IUserRepository)
        repo.exists_by_email_excluding_user = AsyncMock(return_value=True)

        with pytest.raises(ConflictError, match="email ya está en uso"):
            await self.case.execute(
                current_user=user,
                email="taken@example.com",
            )

        repo.update_data.assert_not_called()
        self.uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_updates_email_successfully(self) -> None:
        """Happy path: email update succeeds when email is unique."""
        user = make_user_entity()
        repo = self.uow.get_repository(IUserRepository)
        repo.exists_by_email_excluding_user = AsyncMock(return_value=False)
        repo.update_data = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=user)

        result = await self.case.execute(
            current_user=user,
            email="new@example.com",
        )

        assert result is not None
        repo.update_data.assert_awaited_once()
        self.uow.commit.assert_awaited_once()


class TestListUsersCase:
    """ListUsersCase enforces role guard and delegates to repo."""

    def setup_method(self) -> None:
        from src.auth.application.uses_cases.list_users_case import (
            ListUsersCase,
        )

        self.uow = MockUoW()
        self.case = ListUsersCase(uow=self.uow)

    @pytest.mark.asyncio
    async def test_admin_can_list_users(self) -> None:
        """ADMIN can list users with pagination."""
        common_tid = uuid4()
        admin = make_user_entity(role=UserRole.ADMIN, tenant_id=common_tid)
        repo = self.uow.get_repository(IUserRepository)
        expected_users = [make_user_entity(tenant_id=common_tid) for _ in range(3)]
        repo.list = AsyncMock(return_value=(expected_users, 10, False))

        users, total, next_cursor = await self.case.execute(
            current_user=admin,
            page=1,
            per_page=20,
            search=None,
            role=None,
        )

        assert len(users) == 3
        assert total == 10
        assert next_cursor is None  # no cursor param → no next_cursor
        repo.list.assert_awaited_once_with(
            tenant_id=common_tid,
            page=1,
            per_page=20,
            search=None,
            role=None,
            cursor=None,
        )

    @pytest.mark.asyncio
    async def test_viewer_cannot_list_users(self) -> None:
        """VIEWER gets NotPermissionError."""
        viewer = make_user_entity(role=UserRole.VIEWER)

        with pytest.raises(NotPermissionError, match="No tienes permisos"):
            await self.case.execute(
                current_user=viewer,
                page=1,
                per_page=20,
            )

    @pytest.mark.asyncio
    async def test_pagination_and_filters_passed_through(self) -> None:
        """Pagination and filter params are passed to repo.list."""
        common_tid = uuid4()
        admin = make_user_entity(role=UserRole.ADMIN, tenant_id=common_tid)
        repo = self.uow.get_repository(IUserRepository)
        repo.list = AsyncMock(return_value=([], 0, False))

        await self.case.execute(
            current_user=admin,
            page=2,
            per_page=10,
            search="alice",
            role=UserRole.EDITOR,
        )

        repo.list.assert_awaited_once_with(
            tenant_id=common_tid,
            page=2,
            per_page=10,
            search="alice",
            role=UserRole.EDITOR,
            cursor=None,
        )


class TestSoftDeleteUserCase:
    """SoftDeleteUserCase enforces all guards before deactivation."""

    def setup_method(self) -> None:
        from src.auth.application.uses_cases.soft_delete_user_case import (
            SoftDeleteUserCase,
        )

        self.uow = MockUoW()
        self.case = SoftDeleteUserCase(uow=self.uow)

    @pytest.mark.asyncio
    async def test_self_deactivation_blocked(self) -> None:
        """Cannot deactivate yourself."""
        user = make_user_entity(role=UserRole.ADMIN)

        with pytest.raises(DomainError, match="No puedes desactivarte"):
            await self.case.execute(
                current_user=user,
                target_user_id=user.id,
            )

        self.uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_admin_cannot_deactivate(self) -> None:
        """VIEWER cannot deactivate any user."""
        viewer = make_user_entity(role=UserRole.VIEWER)
        target = make_user_entity()

        with pytest.raises(NotPermissionError, match="No tienes permisos"):
            await self.case.execute(
                current_user=viewer,
                target_user_id=target.id,
            )

        self.uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_last_owner_deactivation_blocked(self) -> None:
        """Cannot deactivate the last OWNER in the tenant."""
        common_tid = uuid4()
        admin = make_user_entity(role=UserRole.ADMIN, tenant_id=common_tid)
        owner = make_user_entity(role=UserRole.OWNER, tenant_id=common_tid)

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=owner)
        repo.count_owners_by_tenant = AsyncMock(return_value=1)

        with pytest.raises(DomainError, match="único propietario"):
            await self.case.execute(
                current_user=admin,
                target_user_id=owner.id,
            )

        repo.update_data.assert_not_called()
        self.uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_cross_tenant_deactivation_blocked(self) -> None:
        """Cannot deactivate a user from a different tenant."""
        admin = make_user_entity(role=UserRole.ADMIN, tenant_id=uuid4())
        target = make_user_entity(tenant_id=uuid4())  # Different tenant

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=target)

        with pytest.raises(NotPermissionError, match="no pertenece"):
            await self.case.execute(
                current_user=admin,
                target_user_id=target.id,
            )

        repo.update_data.assert_not_called()
        self.uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_target_not_found_raises(self) -> None:
        """Raises DomainError when target user does not exist."""
        admin = make_user_entity(role=UserRole.ADMIN)
        target_id = uuid4()

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(DomainError, match="Usuario no encontrado"):
            await self.case.execute(
                current_user=admin,
                target_user_id=target_id,
            )

        repo.update_data.assert_not_called()
        self.uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_successful_soft_delete(self) -> None:
        """Happy path: admin deactivates a viewer successfully."""
        common_tid = uuid4()
        admin = make_user_entity(role=UserRole.ADMIN, tenant_id=common_tid)
        target = make_user_entity(role=UserRole.VIEWER, tenant_id=common_tid)

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=target)
        repo.update_data = AsyncMock()

        await self.case.execute(
            current_user=admin,
            target_user_id=target.id,
        )

        repo.update_data.assert_awaited_once()
        self.uow.commit.assert_awaited_once()


class TestGetUserByIdCase:
    """GetUserByIdCase handles admin user retrieval with tenant isolation."""

    def setup_method(self) -> None:
        from src.auth.application.uses_cases.get_user_by_id_case import (
            GetUserByIdCase,
        )

        self.uow = MockUoW()
        self.case = GetUserByIdCase(uow=self.uow)

    @pytest.mark.asyncio
    async def test_admin_can_get_user_by_id(self) -> None:
        """Happy path: admin retrieves a user within the same tenant."""
        common_tid = uuid4()
        admin = make_user_entity(role=UserRole.ADMIN, tenant_id=common_tid)
        target = make_user_entity(role=UserRole.VIEWER, tenant_id=common_tid)

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id_with_tenant_check = AsyncMock(return_value=target)

        result = await self.case.execute(
            current_user=admin,
            target_user_id=target.id,
        )

        assert result.id == target.id
        assert result.tenant_id == common_tid
        repo.get_by_id_with_tenant_check.assert_awaited_once_with(
            user_id=target.id,
            tenant_id=common_tid,
        )

    @pytest.mark.asyncio
    async def test_viewer_cannot_get_user_by_id(self) -> None:
        """VIEWER role raises NotPermissionError."""
        common_tid = uuid4()
        viewer = make_user_entity(role=UserRole.VIEWER, tenant_id=common_tid)
        target = make_user_entity(role=UserRole.VIEWER, tenant_id=common_tid)

        with pytest.raises(NotPermissionError):
            await self.case.execute(
                current_user=viewer,
                target_user_id=target.id,
            )

    @pytest.mark.asyncio
    async def test_cross_tenant_user_not_found(self) -> None:
        """Getting a user from another tenant returns NotFoundError."""
        admin = make_user_entity(role=UserRole.ADMIN, tenant_id=uuid4())
        target_id = uuid4()

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id_with_tenant_check = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError, match="Usuario no encontrado"):
            await self.case.execute(
                current_user=admin,
                target_user_id=target_id,
            )

        repo.get_by_id_with_tenant_check.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_super_admin_can_get_user_by_id(self) -> None:
        """SUPER_ADMIN role can retrieve any user."""
        common_tid = uuid4()
        admin = make_user_entity(role=UserRole.SUPER_ADMIN, tenant_id=common_tid)
        target = make_user_entity(role=UserRole.VIEWER, tenant_id=common_tid)

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id_with_tenant_check = AsyncMock(return_value=target)

        result = await self.case.execute(
            current_user=admin,
            target_user_id=target.id,
        )

        assert result.id == target.id


class TestLoginServiceWithInactiveUser:
    """LoginUserService blocks inactive users."""

    def setup_method(self) -> None:
        from src.auth.domain.services.login_user_service import LoginUserService

        self.service = LoginUserService()

    @pytest.mark.asyncio
    async def test_active_user_passes_check(self) -> None:
        """Active user passes the is_active check."""
        from unittest.mock import AsyncMock, MagicMock

        user = make_user_entity(is_active=True)
        user.passwords_match = AsyncMock(return_value=True)
        security = MagicMock()

        # Should not raise
        await self.service.validate_credentials(
            user=user,
            password="any_password",
            security_service=security,
        )

    @pytest.mark.asyncio
    async def test_inactive_user_raises_unauthorized(self) -> None:
        """Inactive user raises UnauthorizedError."""
        from unittest.mock import MagicMock

        user = make_user_entity(is_active=False)
        security = MagicMock()

        with pytest.raises(UnauthorizedError):
            await self.service.validate_credentials(
                user=user,
                password="any_password",
                security_service=security,
            )
