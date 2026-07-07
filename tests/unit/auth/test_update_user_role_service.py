"""Unit tests for UpdateUserRoleService.

Tests all business rules:
- Only OWNER can change roles
- No self-escalation (user cannot change own role)
- Last OWNER protection (cannot demote last OWNER)
- Non-last OWNER demotion succeeds
- Same-role preservation always allowed
- SUPER_ADMIN cannot be assigned via this service
"""

import pytest
from tests.factories import make_user_entity

from src.auth.domain.entities._user_role import UserRole
from src.common.domain.exceptions import NotPermissionError


class TestUpdateUserRoleService:
    """UpdateUserRoleService validates role change business rules."""

    def setup_method(self) -> None:
        from src.auth.domain.services.update_user_role_service import (
            UpdateUserRoleService,
        )

        self.service = UpdateUserRoleService()

    # ── Happy path: OWNER can change other users ───────────────────────

    @pytest.mark.asyncio
    async def test_owner_can_promote_viewer_to_editor(self) -> None:
        """OWNER can promote a VIEWER to EDITOR."""
        actor = make_user_entity(role=UserRole.OWNER)
        target = make_user_entity(role=UserRole.VIEWER)
        result = await self.service.can_update_role(
            actor=actor,
            target=target,
            new_role=UserRole.EDITOR,
            owners_in_tenant=2,
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_owner_can_promote_viewer_to_owner(self) -> None:
        """OWNER can promote a VIEWER all the way to OWNER."""
        actor = make_user_entity(role=UserRole.OWNER)
        target = make_user_entity(role=UserRole.VIEWER)
        result = await self.service.can_update_role(
            actor=actor,
            target=target,
            new_role=UserRole.OWNER,
            owners_in_tenant=1,
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_owner_can_downgrade_admin_to_viewer(self) -> None:
        """OWNER can downgrade another user."""
        actor = make_user_entity(role=UserRole.OWNER)
        target = make_user_entity(role=UserRole.ADMIN)
        result = await self.service.can_update_role(
            actor=actor,
            target=target,
            new_role=UserRole.VIEWER,
            owners_in_tenant=2,
        )
        assert result is True

    # ── Self-escalation prevention ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_owner_cannot_change_own_role(self) -> None:
        """OWNER cannot change their OWN role (self-escalation prevention)."""
        user = make_user_entity(role=UserRole.OWNER)
        with pytest.raises(
            NotPermissionError,
            match="No puedes modificar tu propio rol",
        ):
            await self.service.can_update_role(
                actor=user,
                target=user,
                new_role=UserRole.ADMIN,
                owners_in_tenant=2,
            )

    @pytest.mark.asyncio
    async def test_admin_cannot_change_own_role(self) -> None:
        """ADMIN cannot change their OWN role — fails OWNER check first."""
        user = make_user_entity(role=UserRole.ADMIN)
        with pytest.raises(
            NotPermissionError,
            match="Solo los propietarios",
        ):
            await self.service.can_update_role(
                actor=user,
                target=user,
                new_role=UserRole.EDITOR,
                owners_in_tenant=2,
            )

    # ── Last OWNER protection ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_last_owner_demotion_denied(self) -> None:
        """Cannot demote the last remaining OWNER in a tenant."""
        actor = make_user_entity(role=UserRole.OWNER)
        target = make_user_entity(role=UserRole.OWNER)
        with pytest.raises(
            NotPermissionError,
            match="Debe haber al menos un propietario",
        ):
            await self.service.can_update_role(
                actor=actor,
                target=target,
                new_role=UserRole.ADMIN,
                owners_in_tenant=1,
            )

    @pytest.mark.asyncio
    async def test_last_owner_downgrade_to_viewer_denied(self) -> None:
        """Cannot downgrade the last OWNER even to the lowest role."""
        actor = make_user_entity(role=UserRole.OWNER)
        target = make_user_entity(role=UserRole.OWNER)
        with pytest.raises(NotPermissionError):
            await self.service.can_update_role(
                actor=actor,
                target=target,
                new_role=UserRole.VIEWER,
                owners_in_tenant=1,
            )

    @pytest.mark.asyncio
    async def test_non_last_owner_demotion_allowed(self) -> None:
        """Can demote an OWNER when at least one other OWNER remains."""
        actor = make_user_entity(role=UserRole.OWNER)
        target = make_user_entity(role=UserRole.OWNER)
        result = await self.service.can_update_role(
            actor=actor,
            target=target,
            new_role=UserRole.ADMIN,
            owners_in_tenant=2,
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_owner_keeps_same_role_allowed_even_last(self) -> None:
        """Can keep another OWNER at OWNER role even if last OWNER."""
        actor = make_user_entity(role=UserRole.OWNER)
        target = make_user_entity(role=UserRole.OWNER)
        result = await self.service.can_update_role(
            actor=actor,
            target=target,
            new_role=UserRole.OWNER,
            owners_in_tenant=1,
        )
        assert result is True

    # ── Non-OWNER access denied ────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_viewer_cannot_change_roles(self) -> None:
        """VIEWER cannot change any user's role."""
        actor = make_user_entity(role=UserRole.VIEWER)
        target = make_user_entity(role=UserRole.VIEWER)
        with pytest.raises(
            NotPermissionError,
            match="Solo los propietarios",
        ):
            await self.service.can_update_role(
                actor=actor,
                target=target,
                new_role=UserRole.EDITOR,
                owners_in_tenant=2,
            )

    @pytest.mark.asyncio
    async def test_editor_cannot_change_roles(self) -> None:
        """EDITOR cannot change any user's role."""
        actor = make_user_entity(role=UserRole.EDITOR)
        target = make_user_entity(role=UserRole.VIEWER)
        with pytest.raises(
            NotPermissionError,
            match="Solo los propietarios",
        ):
            await self.service.can_update_role(
                actor=actor,
                target=target,
                new_role=UserRole.EDITOR,
                owners_in_tenant=2,
            )

    @pytest.mark.asyncio
    async def test_admin_cannot_change_roles(self) -> None:
        """ADMIN (non-OWNER) cannot change any user's role."""
        actor = make_user_entity(role=UserRole.ADMIN)
        target = make_user_entity(role=UserRole.VIEWER)
        with pytest.raises(
            NotPermissionError,
            match="Solo los propietarios",
        ):
            await self.service.can_update_role(
                actor=actor,
                target=target,
                new_role=UserRole.EDITOR,
                owners_in_tenant=2,
            )

    # ── SUPER_ADMIN rejection ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_owner_cannot_assign_super_admin(self) -> None:
        """OWNER cannot assign SUPER_ADMIN role via the service."""
        actor = make_user_entity(role=UserRole.OWNER)
        target = make_user_entity(role=UserRole.VIEWER)
        with pytest.raises(
            NotPermissionError,
            match="SUPER_ADMIN",
        ):
            await self.service.can_update_role(
                actor=actor,
                target=target,
                new_role=UserRole.SUPER_ADMIN,
                owners_in_tenant=2,
            )
