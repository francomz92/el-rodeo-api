"""Unit tests for RefreshTokenCase.

The use case orchestrates token validation and rotation through
TokenService and IRefreshTokenRepository (resolved via UoW).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from tests.mocks import MockUoW

from src.auth.application.exceptions.authentication import InvalidCredentialError
from src.auth.application.uses_cases.refresh_token_case import RefreshTokenCase
from src.auth.domain.repositories.refresh_token_repository_port import (
    IRefreshTokenRepository,
)


class TestRefreshTokenCase:
    def setup_method(self) -> None:
        self.token_service = MagicMock()
        self.uow = MockUoW()
        self.repo = self.uow.get_repository(IRefreshTokenRepository)
        self.case = RefreshTokenCase(
            token_service=self.token_service,
            uow=self.uow,
        )

    async def test_execute_returns_new_token_pair(self) -> None:
        """Happy path: valid refresh token -> new access + refresh tokens."""
        self.token_service.rotate_refresh_token = AsyncMock(return_value=("new-access-token", "new-refresh-token"))

        access, refresh = await self.case.execute("valid-refresh-token")

        assert access == "new-access-token"
        assert refresh == "new-refresh-token"
        self.token_service.rotate_refresh_token.assert_awaited_once_with("valid-refresh-token", self.repo)

    async def test_execute_raises_on_invalid_token(self) -> None:
        """Invalid refresh token raises InvalidCredentialError."""
        self.token_service.rotate_refresh_token = AsyncMock(side_effect=InvalidCredentialError("invalid_refresh_token"))

        with pytest.raises(InvalidCredentialError):
            await self.case.execute("invalid-token")

    async def test_execute_raises_on_reuse_detection(self) -> None:
        """Reuse of rotated token propagates token_family_revoked."""
        self.token_service.rotate_refresh_token = AsyncMock(side_effect=InvalidCredentialError("token_family_revoked"))

        with pytest.raises(InvalidCredentialError) as exc:
            await self.case.execute("reused-token")

        assert "token_family_revoked" in str(exc.value)
