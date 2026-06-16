"""Unit tests for UserEntity domain logic.

The entity encapsulates password verification and update logic.
We mock the security service to avoid hashing dependencies.
"""

from unittest.mock import MagicMock

import pytest

from src.auth.domain.entities import UserEntity
from src.common.domain.services.security import ISecurityService


class TestUserEntityPasswordMatching:
    """UserEntity.passwords_match delegates to the security service."""

    def setup_method(self) -> None:
        self.security = MagicMock(spec=ISecurityService)

    def test_returns_true_when_passwords_match(self) -> None:
        """Delegates to security_service.verify_password and returns True."""
        user = _make_user()
        self.security.verify_password.return_value = True

        result = user.passwords_match(self.security, "correct_password")

        assert result is True
        self.security.verify_password.assert_called_once_with(
            "correct_password",
            user._hashed_password,
        )

    def test_returns_false_when_passwords_dont_match(self) -> None:
        """Returns False when the security service says no."""
        user = _make_user()
        self.security.verify_password.return_value = False

        result = user.passwords_match(self.security, "wrong_password")

        assert result is False


class TestUserEntityUpdatePassword:
    """UserEntity.update_password validates and delegates to the security service."""

    def setup_method(self) -> None:
        self.security = MagicMock(spec=ISecurityService)

    def test_updates_password_successfully(self) -> None:
        """Hashes the new password and stores it."""
        user = _make_user()
        self.security.hash_password.return_value = "new_hashed_value"

        user.update_password(self.security, "old_pass", "new_pass", "new_pass")

        self.security.hash_password.assert_called_once_with("new_pass")
        assert user._hashed_password == "new_hashed_value"

    def test_raises_when_new_passwords_dont_match(self) -> None:
        """Raises ValueError when confirm does not match the new password."""
        user = _make_user()

        with pytest.raises(ValueError, match="deben coincidir"):
            user.update_password(self.security, "old_pass", "new_pass", "different_confirm")

    def test_raises_when_new_password_equals_old(self) -> None:
        """Raises ValueError when new password is the same as the old one."""
        user = _make_user()

        with pytest.raises(ValueError, match="diferente"):
            user.update_password(self.security, "same_pass", "same_pass", "same_pass")


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
        is_admin=False,
        _hashed_password="old_hashed_value",
    )
