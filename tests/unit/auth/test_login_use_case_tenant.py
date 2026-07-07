"""Unit tests for LoginUserCase tenant_id inclusion.

Verifies that when login_user_case.execute() is called, the JWT token
data dict includes the user's tenant_id.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from tests.factories import make_user_entity
from tests.mocks import MockUoW

from src.auth.application.uses_cases.login_user_case import LoginUserCase
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.services.login_user_service import LoginUserService


class TestLoginUserCaseTenantId:
    """LoginUserCase includes tenant_id in JWT data."""

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

    @pytest.mark.asyncio
    async def test_execute_passes_tenant_id_to_generate(self) -> None:
        """Access token data includes tenant_id when user has one."""
        tenant_id = uuid4()
        expected_user = make_user_entity(tenant_id=tenant_id)
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

        # Verify generate was called with tenant_id in data
        call_args = self.token_service.generate.call_args
        # generate() is called with positional args: (data, exp_minutes)
        data_arg = call_args[0][0]
        assert "tenant_id" in data_arg
        assert data_arg["tenant_id"] == str(tenant_id)
