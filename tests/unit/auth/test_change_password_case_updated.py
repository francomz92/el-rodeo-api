"""Unit tests for updated ChangePasswordCase.

The use case no longer accepts a token parameter — the authenticated user
is passed directly (resolved by the auth dependency). On success, it
revokes all refresh tokens for the user via UoW-resolved repo.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from tests.factories import make_user_entity
from tests.mocks import MockUoW

from src.auth.application.uses_cases.change_password_case import ChangePasswordCase
from src.auth.domain.repositories.refresh_token_repository_port import (
    IRefreshTokenRepository,
)
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.services.change_password_service import ChangePasswordService
from src.common.domain.exceptions import UnauthorizedError


class TestChangePasswordCaseUpdated:
    """ChangePasswordCase no longer accepts token param."""

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

    async def test_execute_changes_password_and_revokes_refresh_tokens(self) -> None:
        """Happy path: password changed, refresh tokens revoked."""
        user = make_user_entity()
        user.passwords_match = AsyncMock(return_value=True)

        repo = self.uow.get_repository(IUserRepository)
        repo.update_password = AsyncMock()

        await self.case.execute(
            user=user,
            password="old_pass",
            new_password="new_pass",
            confirmed_password="new_pass",
        )

        repo.update_password.assert_awaited_once()
        self.uow.commit.assert_awaited_once()

        # Verify refresh tokens were revoked
        refresh_repo = self.uow.get_repository(IRefreshTokenRepository)
        refresh_repo.revoke_all_user_tokens.assert_awaited_once_with(user.id)

    async def test_execute_raises_on_invalid_password(self) -> None:
        """Invalid current password raises and does not revoke tokens."""
        user = make_user_entity()
        user.passwords_match = AsyncMock(return_value=False)

        repo = self.uow.get_repository(IUserRepository)
        repo.update_password = AsyncMock()

        with pytest.raises(UnauthorizedError):
            await self.case.execute(
                user=user,
                password="wrong_pass",
                new_password="new_pass",
                confirmed_password="new_pass",
            )

        repo.update_password.assert_not_called()
        self.uow.commit.assert_not_called()
