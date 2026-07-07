"""Unit tests for UpdateUserRoleCase.

Tests use case orchestration: loading target user, cross-tenant isolation,
service validation, and repository update.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from tests.factories import make_user_entity
from tests.mocks import MockUoW

from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.common.domain.exceptions import NotPermissionError


class TestUpdateUserRoleCase:
    """UpdateUserRoleCase orchestrates service + repository via UoW."""

    def setup_method(self) -> None:
        from src.auth.application.uses_cases.update_user_role_case import (
            UpdateUserRoleCase,
        )
        from src.auth.domain.services.update_user_role_service import (
            UpdateUserRoleService,
        )

        self.uow = MockUoW()
        self.service = UpdateUserRoleService()
        self.case = UpdateUserRoleCase(
            uow=self.uow,
            update_user_role_service=self.service,
        )

    # ── Happy path ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_execute_successfully_updates_role(self) -> None:
        """OWNER can update another user's role successfully."""
        common_tid = uuid4()
        actor = make_user_entity(role=UserRole.OWNER, tenant_id=common_tid)
        target = make_user_entity(role=UserRole.VIEWER, tenant_id=common_tid)
        target_id = target.id
        new_role = UserRole.EDITOR

        repo = self.uow.get_repository(IUserRepository)
        updated_target = make_user_entity(
            role=UserRole.EDITOR,
            id=target_id,
            tenant_id=common_tid,
        )

        call_count = 0

        async def get_by_id_side_effect(uid):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return target
            return updated_target

        repo.get_by_id = AsyncMock(side_effect=get_by_id_side_effect)
        repo.count_owners_by_tenant = AsyncMock(return_value=2)
        repo.update_role = AsyncMock()

        result = await self.case.execute(
            actor=actor,
            target_user_id=target_id,
            new_role=new_role,
        )

        assert result is not None
        assert result.role == UserRole.EDITOR
        repo.update_role.assert_awaited_once_with(target_id, new_role)
        self.uow.commit.assert_awaited_once()

    # ── Target user not found ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_execute_raises_when_target_not_found(self) -> None:
        """Raises ValueError when target user does not exist."""
        actor = make_user_entity(role=UserRole.OWNER)
        target_id = uuid4()

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="no encontrado"):
            await self.case.execute(
                actor=actor,
                target_user_id=target_id,
                new_role=UserRole.EDITOR,
            )

        repo.update_role.assert_not_called()
        self.uow.commit.assert_not_called()

    # ── Cross-tenant isolation ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_cross_tenant_role_change_denied(self) -> None:
        """Actor cannot change role of user in a different tenant."""
        actor = make_user_entity(role=UserRole.OWNER, tenant_id=uuid4())
        target = make_user_entity(role=UserRole.VIEWER, tenant_id=uuid4())
        # Both have different tenant_ids already from make_user_entity

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=target)

        with pytest.raises(
            NotPermissionError,
            match="otro tenant",
        ):
            await self.case.execute(
                actor=actor,
                target_user_id=target.id,
                new_role=UserRole.EDITOR,
            )

        repo.update_role.assert_not_called()
        self.uow.commit.assert_not_called()

    # ── Service validation failure ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_self_escalation_raises(self) -> None:
        """Self-escalation raises NotPermissionError."""
        actor = make_user_entity(role=UserRole.OWNER)

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=actor)
        repo.count_owners_by_tenant = AsyncMock(return_value=2)

        with pytest.raises(
            NotPermissionError,
            match="No puedes modificar tu propio rol",
        ):
            await self.case.execute(
                actor=actor,
                target_user_id=actor.id,
                new_role=UserRole.ADMIN,
            )

        repo.update_role.assert_not_called()
        self.uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_last_owner_demotion_raises(self) -> None:
        """Last OWNER demotion raises NotPermissionError."""
        common_tid = uuid4()
        actor = make_user_entity(role=UserRole.OWNER, tenant_id=common_tid)
        target = make_user_entity(role=UserRole.OWNER, tenant_id=common_tid)

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=target)
        repo.count_owners_by_tenant = AsyncMock(return_value=1)

        with pytest.raises(
            NotPermissionError,
            match="Debe haber al menos un propietario",
        ):
            await self.case.execute(
                actor=actor,
                target_user_id=target.id,
                new_role=UserRole.ADMIN,
            )

        repo.update_role.assert_not_called()
        self.uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_owner_cannot_change_roles(self) -> None:
        """Non-OWNER user raises NotPermissionError."""
        common_tid = uuid4()
        actor = make_user_entity(role=UserRole.ADMIN, tenant_id=common_tid)
        target = make_user_entity(role=UserRole.VIEWER, tenant_id=common_tid)

        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_id = AsyncMock(return_value=target)

        with pytest.raises(
            NotPermissionError,
            match="Solo los propietarios",
        ):
            await self.case.execute(
                actor=actor,
                target_user_id=target.id,
                new_role=UserRole.EDITOR,
            )

        repo.update_role.assert_not_called()
        self.uow.commit.assert_not_called()
