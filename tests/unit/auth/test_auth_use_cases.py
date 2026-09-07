"""Unit tests for auth use cases.

Use cases orchestrate domain services and repositories via the Unit of Work.
Here we mock the UoW to test the orchestration logic in isolation.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from tests.factories import make_user_entity
from tests.mocks import MockUoW

from src.auth.application.uses_cases.change_password_case import ChangePasswordCase
from src.auth.application.uses_cases.login_user_case import LoginUserCase
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.services.change_password_service import ChangePasswordService
from src.auth.domain.services.login_user_service import LoginUserService
from src.common.domain.exceptions import UnauthorizedError


class TestLoginUserCase:
    """LoginUserCase authenticates a user and returns a token pair."""

    def setup_method(self) -> None:
        self.login_service = LoginUserService()
        self.uow = MockUoW()
        self.security = MagicMock()
        self.token_service = MagicMock()
        self.case = LoginUserCase(
            uow=self.uow,
            security_service=self.security,
            token_service=self.token_service,
            login_service=self.login_service,
        )

    async def test_execute_returns_token_on_success(self) -> None:
        """Happy path: valid DNI and password -> token pair returned."""
        expected_user = make_user_entity()
        expected_user.passwords_match = AsyncMock(return_value=True)
        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_dni.return_value = expected_user
        self.token_service.generate.return_value = "access-token-123"
        self.token_service.generate_refresh_token.return_value = "refresh-jwt-456"
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        fake_family = "660e8400-e29b-41d4-a716-446655441111"
        self.token_service.decode_refresh_token.return_value = {
            "jti": fake_id,
            "refresh_token_id": fake_id,
            "family_id": fake_family,
        }

        access, refresh = await self.case.execute(dni="12345678", password="correct_password")

        assert access == "access-token-123"
        assert refresh == "refresh-jwt-456"
        repo.get_by_dni.assert_awaited_once_with("12345678")
        self.token_service.generate.assert_called_once()

    async def test_execute_raises_on_invalid_dni(self) -> None:
        """Raises UnauthorizedError when DNI is not found."""
        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_dni.return_value = None

        with pytest.raises(UnauthorizedError):
            await self.case.execute(dni="12345678", password="any_password")

        self.token_service.generate.assert_not_called()

    async def test_execute_raises_on_invalid_password(self) -> None:
        """Raises UnauthorizedError when password does not match."""
        expected_user = make_user_entity()
        expected_user.passwords_match = AsyncMock(return_value=False)
        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_dni.return_value = expected_user

        with pytest.raises(UnauthorizedError):
            await self.case.execute(dni="12345678", password="wrong_password")

        self.token_service.generate.assert_not_called()


class TestChangePasswordCase:
    """ChangePasswordCase changes a user's password via UoW."""

    def setup_method(self) -> None:
        self.uow = MockUoW()
        self.security = MagicMock()
        self.security.hash_password = AsyncMock(return_value="new_hashed_value")
        self.change_service = ChangePasswordService()
        self.case = ChangePasswordCase(
            uow=self.uow,
            security_service=self.security,
            change_password_service=self.change_service,
        )

    async def test_execute_changes_password_successfully(self) -> None:
        """Happy path: valid user -> password changed -> commit called."""
        expected_user = make_user_entity()
        expected_user.passwords_match = AsyncMock(return_value=True)

        repo = self.uow.get_repository(IUserRepository)
        repo.update_password = AsyncMock()

        await self.case.execute(
            user=expected_user,
            password="old_pass",
            new_password="new_pass",
            confirmed_password="new_pass",
        )

        repo.update_password.assert_awaited_once()
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_on_invalid_password(self) -> None:
        """Raises when current password does not match."""
        expected_user = make_user_entity()
        expected_user.passwords_match = AsyncMock(return_value=False)

        with pytest.raises(UnauthorizedError):
            await self.case.execute(
                user=expected_user,
                password="wrong_pass",
                new_password="new_pass",
                confirmed_password="new_pass",
            )

        self.uow.commit.assert_not_called()
