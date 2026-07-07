"""Unit tests for AuthService tenant_id propagation.

Verifies that get_authenticated_user sets uow.tenant_id from the JWT payload.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from tests.factories import make_user_entity
from tests.mocks import MockUoW

from src.auth.application.services.authentication_service import AuthService
from src.auth.domain.repositories.users_repository_port import IUserRepository


class TestAuthServiceTenant:
    """AuthService sets uow.tenant_id from JWT payload."""

    def setup_method(self) -> None:
        self.token_service = MagicMock()
        self.blacklist_service = MagicMock()
        self.blacklist_service.is_blacklisted = AsyncMock(return_value=False)
        self.service = AuthService(
            token_service=self.token_service,
            blacklist_service=self.blacklist_service,
        )

    @pytest.mark.asyncio
    async def test_sets_tenant_id_on_uow_from_jwt(self) -> None:
        """get_authenticated_user sets uow.tenant_id from JWT payload."""
        tenant_id = uuid4()
        user_id = uuid4()
        expected_user = make_user_entity(id=user_id, tenant_id=tenant_id)

        self.token_service.decode.return_value = {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "jti": "some-jti",
        }

        uow = MockUoW()
        repo = uow.get_repository(IUserRepository)
        repo.get_by_id.return_value = expected_user

        user = await self.service.get_authenticated_user(uow=uow, token="valid-token")

        assert user == expected_user
        assert hasattr(uow, "tenant_id")
        assert uow.tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_sets_none_when_no_tenant_id(self) -> None:
        """When JWT has no tenant_id, uow.tenant_id is set to None."""
        user_id = uuid4()
        expected_user = make_user_entity(id=user_id, tenant_id=None)

        self.token_service.decode.return_value = {
            "user_id": str(user_id),
            "jti": "some-jti",
        }

        uow = MockUoW()
        repo = uow.get_repository(IUserRepository)
        repo.get_by_id.return_value = expected_user

        user = await self.service.get_authenticated_user(uow=uow, token="valid-token")

        assert user == expected_user
        assert uow.tenant_id is None
