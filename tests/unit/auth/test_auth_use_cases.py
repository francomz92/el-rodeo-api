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
from src.auth.application.uses_cases.register_user_case import RegisterUserCase
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.services.change_password_service import ChangePasswordService
from src.auth.domain.services.login_user_service import LoginUserService
from src.auth.domain.services.register_user_service import RegisterUserService
from src.common.domain.exceptions import DuplicatedError, UnauthorizedError


class TestRegisterUserCase:
    """RegisterUserCase registers a new user via UoW."""

    def setup_method(self) -> None:
        self.service = RegisterUserService()
        self.uow = MockUoW()
        self.security = MagicMock()
        self.notifier = MagicMock()
        self.token_service = MagicMock()
        self.case = RegisterUserCase(
            uow=self.uow,
            security_service=self.security,
            register_service=self.service,
            notifier_service=self.notifier,
            token_service=self.token_service,
        )

    async def test_execute_creates_user_successfully(self) -> None:
        """Happy path: valid data -> user created, token generated, notified."""
        from src.auth.domain.value_objects.user_value_object import UserCreationValueObject

        data = UserCreationValueObject(
            name="Test User",
            dni="12345678",
            email="test@example.com",
        )
        expected_user = make_user_entity()
        repo = self.uow.get_repository(IUserRepository)
        repo.exists.return_value = False
        repo.create.return_value = expected_user
        self.token_service.generate = MagicMock(return_value="test-token")

        result = await self.case.execute(data, redirect_url="http://example.com/confirm")

        assert result == expected_user
        repo.exists.assert_awaited_once_with(dni="12345678", email="test@example.com")
        self.token_service.generate.assert_called_once()
        self.notifier.send.assert_called_once()
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_on_duplicate(self) -> None:
        """Raises DuplicatedError when user already exists."""
        from src.auth.domain.value_objects.user_value_object import UserCreationValueObject

        data = UserCreationValueObject(
            name="Test User",
            dni="12345678",
            email="test@example.com",
        )
        repo = self.uow.get_repository(IUserRepository)
        repo.exists.return_value = True

        with pytest.raises(DuplicatedError):
            await self.case.execute(data, redirect_url="http://example.com/confirm")

        repo.create.assert_not_called()
        self.uow.commit.assert_not_called()


class TestLoginUserCase:
    """LoginUserCase authenticates a user and returns a token."""

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
        """Happy path: valid DNI and password -> token returned."""
        expected_user = make_user_entity()
        expected_user.passwords_match = MagicMock(return_value=True)
        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_dni.return_value = expected_user
        self.token_service.generate.return_value = "access-token-123"

        result = await self.case.execute(dni="12345678", password="correct_password")

        assert result == "access-token-123"
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
        expected_user.passwords_match = MagicMock(return_value=False)
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
        self.auth_service = MagicMock()
        self.change_service = ChangePasswordService()
        self.case = ChangePasswordCase(
            uow=self.uow,
            security_service=self.security,
            auth_service=self.auth_service,
            change_password_service=self.change_service,
        )

    async def test_execute_changes_password_successfully(self) -> None:
        """Happy path: token valid -> password changed -> commit called."""
        expected_user = make_user_entity()
        expected_user.passwords_match = MagicMock(return_value=True)
        self.auth_service.get_authenticated_user = AsyncMock(return_value=expected_user)

        repo = self.uow.get_repository(IUserRepository)
        repo.update_password = AsyncMock()

        await self.case.execute(
            token="valid-token",
            password="old_pass",
            new_password="new_pass",
            confirmed_password="new_pass",
        )

        self.auth_service.get_authenticated_user.assert_awaited_once()
        repo.update_password.assert_awaited_once()
        self.uow.commit.assert_awaited_once()

    async def test_execute_raises_on_invalid_token(self) -> None:
        """Raises when the auth service cannot authenticate the token."""
        self.auth_service.get_authenticated_user = AsyncMock(side_effect=UnauthorizedError("Invalid token"))

        with pytest.raises(UnauthorizedError):
            await self.case.execute(
                token="invalid-token",
                password="old_pass",
                new_password="new_pass",
                confirmed_password="new_pass",
            )

        self.uow.commit.assert_not_called()
