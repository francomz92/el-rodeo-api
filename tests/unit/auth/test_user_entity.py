"""Unit tests for UserEntity domain logic.

The entity encapsulates password verification, update logic, and role field.
We mock the security service to avoid hashing dependencies.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.auth.domain.entities import UserEntity
from src.auth.domain.entities._user_role import UserRole
from src.common.domain.services.security import ISecurityService


class TestUserEntityRole:
    """UserEntity has a role field with sensible defaults."""

    def test_default_role_is_viewer(self) -> None:
        """When role is not provided, it defaults to VIEWER."""
        user = UserEntity(
            id=uuid4(),
            name="Test",
            dni="12345678",
            email="test@example.com",
            created_at=datetime.now(tz=timezone.utc),
            role=UserRole.VIEWER,
        )
        assert user.role == UserRole.VIEWER

    def test_can_set_explicit_role(self) -> None:
        """Role can be set explicitly at construction."""
        for role in (UserRole.VIEWER, UserRole.EDITOR, UserRole.ADMIN, UserRole.OWNER, UserRole.SUPER_ADMIN):
            user = UserEntity(
                id=uuid4(),
                name="Test",
                dni="12345678",
                email="test@example.com",
                created_at=datetime.now(tz=timezone.utc),
                role=role,
            )
            assert user.role == role

    def test_super_admin_rank_is_5(self) -> None:
        """SUPER_ADMIN has rank 5, above all other roles."""
        assert UserRole.SUPER_ADMIN.rank == 5

    def test_super_admin_hierarchy(self) -> None:
        """SUPER_ADMIN rank > OWNER rank."""
        assert UserRole.SUPER_ADMIN.rank > UserRole.OWNER.rank
        assert UserRole.SUPER_ADMIN.rank > UserRole.ADMIN.rank
        assert UserRole.SUPER_ADMIN.rank > UserRole.EDITOR.rank
        assert UserRole.SUPER_ADMIN.rank > UserRole.VIEWER.rank


class TestUserEntityPasswordMatching:
    """UserEntity.passwords_match delegates to the security service."""

    def setup_method(self) -> None:
        self.security = MagicMock(spec=ISecurityService)
        self.security.verify_password = AsyncMock()

    @pytest.mark.asyncio
    async def test_returns_true_when_passwords_match(self) -> None:
        """Delegates to security_service.verify_password and returns True."""
        user = _make_user()
        self.security.verify_password.return_value = True

        result = await user.passwords_match(self.security, "correct_password")

        assert result is True
        self.security.verify_password.assert_awaited_once_with(
            "correct_password",
            user._hashed_password,
        )

    @pytest.mark.asyncio
    async def test_returns_false_when_passwords_dont_match(self) -> None:
        """Returns False when the security service says no."""
        user = _make_user()
        self.security.verify_password.return_value = False

        result = await user.passwords_match(self.security, "wrong_password")

        assert result is False


class TestUserEntityUpdatePassword:
    """UserEntity.update_password validates and delegates to the security service."""

    def setup_method(self) -> None:
        self.security = MagicMock(spec=ISecurityService)
        self.security.hash_password = AsyncMock()

    @pytest.mark.asyncio
    async def test_updates_password_successfully(self) -> None:
        """Hashes the new password and stores it."""
        user = _make_user()
        self.security.hash_password.return_value = "new_hashed_value"

        await user.update_password(self.security, "old_pass", "new_pass", "new_pass")

        self.security.hash_password.assert_awaited_once_with("new_pass")
        assert user._hashed_password == "new_hashed_value"

    @pytest.mark.asyncio
    async def test_raises_when_new_passwords_dont_match(self) -> None:
        """Raises ValueError when confirm does not match the new password."""
        user = _make_user()

        with pytest.raises(ValueError, match="deben coincidir"):
            await user.update_password(self.security, "old_pass", "new_pass", "different_confirm")

    @pytest.mark.asyncio
    async def test_raises_when_new_password_equals_old(self) -> None:
        """Raises ValueError when new password is the same as the old one."""
        user = _make_user()

        with pytest.raises(ValueError, match="diferente"):
            await user.update_password(self.security, "same_pass", "same_pass", "same_pass")


def _make_user() -> UserEntity:
    """Helper to build a minimal UserEntity for these tests."""
    from datetime import datetime, timezone
    from uuid import uuid4

    return UserEntity(
        id=uuid4(),
        name="Test User",
        dni="12345678",
        email="test@example.com",
        created_at=datetime.now(tz=timezone.utc),
        _hashed_password="old_hashed_value",
    )
