"""Unit tests for auth domain services.

Domain services contain pure business logic with no infrastructure dependencies.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.auth.domain.services.change_password_service import ChangePasswordService
from src.auth.domain.services.login_user_service import LoginUserService
from src.auth.domain.services.register_user_service import RegisterUserService
from src.common.domain.exceptions import DuplicatedError, UnauthorizedError


class TestRegisterUserService:
    """RegisterUserService validates duplicates and creates new users."""

    def setup_method(self) -> None:
        self.service = RegisterUserService()

    async def test_validate_duplicated_passes_when_no_user(self) -> None:
        """Does not raise when repository.exists returns False."""
        repo = AsyncMock()
        repo.exists = AsyncMock(return_value=False)

        # Should not raise
        await self.service.validate_duplicated(
            dni="12345678",
            email="test@example.com",
            repository=repo,
        )

        repo.exists.assert_awaited_once_with(dni="12345678", email="test@example.com")

    async def test_validate_duplicated_raises_when_user_exists(self) -> None:
        """Raises DuplicatedError when repository.exists returns True."""
        repo = AsyncMock()
        repo.exists = AsyncMock(return_value=True)

        with pytest.raises(DuplicatedError):
            await self.service.validate_duplicated(
                dni="12345678",
                email="test@example.com",
                repository=repo,
            )

    async def test_create_new_returns_user_and_password(self) -> None:
        """create_new generates a password, hashes it, and returns user + password."""
        from tests.factories import make_user_entity

        security = MagicMock()
        security.generate_random_str = MagicMock(return_value="randompass12")
        security.hash_password = MagicMock(return_value="hashed_value")

        data = MagicMock()
        expected_user = make_user_entity()
        repo = AsyncMock()
        repo.create = AsyncMock(return_value=expected_user)

        user, password = await self.service.create_new(data, security, repo)

        assert user == expected_user
        assert password == "randompass12"
        security.generate_random_str.assert_called_once_with(10)
        security.hash_password.assert_called_once_with("randompass12")
        repo.create.assert_awaited_once_with(data=data, password="hashed_value")


class TestLoginUserService:
    """LoginUserService validates credentials and fetches users."""

    def setup_method(self) -> None:
        self.service = LoginUserService()

    async def test_validate_duplicate_and_get_user_returns_user(self) -> None:
        """Returns the user when found by DNI."""
        from tests.factories import make_user_entity

        expected_user = make_user_entity()
        repo = AsyncMock()
        repo.get_by_dni = AsyncMock(return_value=expected_user)

        result = await self.service.validate_duplicate_and_get_user(
            dni="12345678",
            repository=repo,
        )

        assert result == expected_user
        repo.get_by_dni.assert_awaited_once_with("12345678")

    async def test_validate_duplicate_and_get_user_raises_when_not_found(self) -> None:
        """Raises UnauthorizedError when the DNI is not found."""
        repo = AsyncMock()
        repo.get_by_dni = AsyncMock(return_value=None)

        with pytest.raises(UnauthorizedError):
            await self.service.validate_duplicate_and_get_user(
                dni="12345678",
                repository=repo,
            )

    async def test_validate_credentials_passes_when_passwords_match(self) -> None:
        """Does not raise when passwords_match returns True."""
        from tests.factories import make_user_entity

        user = make_user_entity()
        security = MagicMock()
        user.passwords_match = MagicMock(return_value=True)

        # Should not raise
        await self.service.validate_credentials(user, "correct_password", security)

        user.passwords_match.assert_called_once_with(security, "correct_password")

    async def test_validate_credentials_raises_when_passwords_dont_match(self) -> None:
        """Raises UnauthorizedError when passwords_match returns False."""
        from tests.factories import make_user_entity

        user = make_user_entity()
        security = MagicMock()
        user.passwords_match = MagicMock(return_value=False)

        with pytest.raises(UnauthorizedError):
            await self.service.validate_credentials(user, "wrong_password", security)


class TestChangePasswordService:
    """ChangePasswordService validates and changes passwords."""

    def setup_method(self) -> None:
        self.service = ChangePasswordService()

    def test_validate_passwords_passes_when_match(self) -> None:
        """Does not raise when passwords_match returns True."""
        from tests.factories import make_user_entity

        user = make_user_entity()
        security = MagicMock()
        user.passwords_match = MagicMock(return_value=True)

        # Should not raise
        self.service.validate_passwords(user, "current_password", security)

    def test_validate_passwords_raises_when_mismatch(self) -> None:
        """Raises UnauthorizedError when passwords_match returns False."""
        from tests.factories import make_user_entity

        user = make_user_entity()
        security = MagicMock()
        user.passwords_match = MagicMock(return_value=False)

        with pytest.raises(UnauthorizedError):
            self.service.validate_passwords(user, "wrong_password", security)

    async def test_change_password_updates_and_persists(self) -> None:
        """change_password calls user.update_password and repository.update_password."""
        from tests.factories import make_user_entity

        user = make_user_entity(_hashed_password="old_hash")
        security = MagicMock()
        repo = AsyncMock()
        repo.update_password = AsyncMock()

        await self.service.change_password(
            user=user,
            password="old_pass",
            new_password="new_pass",
            confirmed_password="new_pass",
            security_service=security,
            repository=repo,
        )

        repo.update_password.assert_awaited_once_with(user.id, user._hashed_password)
