"""Unit tests for LoginUserCase dual-mode (access + refresh tokens).

The use case now returns a tuple of (access_token, refresh_token) and
persists the refresh token via IRefreshTokenRepository (resolved via UoW).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from tests.factories import make_user_entity
from tests.mocks import MockUoW

from src.auth.application.uses_cases.login_user_case import LoginUserCase
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.services.login_user_service import LoginUserService
from src.common.domain.exceptions import UnauthorizedError


class TestLoginUserCaseDualMode:
    """LoginUserCase now returns both access and refresh tokens."""

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

    async def test_execute_returns_token_pair(self) -> None:
        """Happy path: valid credentials -> (access_token, refresh_token)."""
        expected_user = make_user_entity()
        expected_user.passwords_match = AsyncMock(return_value=True)
        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_dni.return_value = expected_user

        fake_refresh_token_id = "550e8400-e29b-41d4-a716-446655440000"
        fake_family_id = "660e8400-e29b-41d4-a716-446655441111"

        self.token_service.generate.return_value = "access-token-123"
        self.token_service.generate_refresh_token.return_value = "raw-refresh-jwt-456"
        self.token_service.decode_refresh_token.return_value = {
            "jti": fake_refresh_token_id,
            "refresh_token_id": fake_refresh_token_id,
            "family_id": fake_family_id,
        }

        access, refresh = await self.case.execute(dni="12345678", password="correct_password")

        assert access == "access-token-123"
        assert refresh == "raw-refresh-jwt-456"
        repo.get_by_dni.assert_awaited_once_with("12345678")
        self.token_service.generate.assert_called_once()
        self.token_service.generate_refresh_token.assert_called_once_with(
            user_id=str(expected_user.id),
            tenant_id=str(expected_user.tenant_id),
        )

    async def test_execute_raises_on_invalid_dni(self) -> None:
        """Raises UnauthorizedError when DNI is not found."""
        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_dni.return_value = None

        with pytest.raises(UnauthorizedError):
            await self.case.execute(dni="12345678", password="any_password")

        self.token_service.generate.assert_not_called()
        self.token_service.generate_refresh_token.assert_not_called()

    async def test_execute_raises_on_invalid_password(self) -> None:
        """Raises UnauthorizedError when password does not match."""
        expected_user = make_user_entity()
        expected_user.passwords_match = AsyncMock(return_value=False)
        repo = self.uow.get_repository(IUserRepository)
        repo.get_by_dni.return_value = expected_user

        with pytest.raises(UnauthorizedError):
            await self.case.execute(dni="12345678", password="wrong_password")

        self.token_service.generate.assert_not_called()
        self.token_service.generate_refresh_token.assert_not_called()
