"""Unit tests for RegisterUserCase tenant creation.

Verifies that registration creates a tenant first, then creates the user
with the tenant_id from the new tenant.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from tests.factories import make_user_entity
from tests.mocks import MockUoW

from src.auth.application.uses_cases.register_user_case import RegisterUserCase
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.auth.domain.repositories.users_repository_port import (
    IUserRepository,
    UserCreationValueObject,
)
from src.auth.domain.services.register_user_service import RegisterUserService


class TestRegisterUserCaseTenant:
    """RegisterUserCase creates tenant then user."""

    def setup_method(self) -> None:
        self.service = RegisterUserService()
        self.uow = MockUoW()
        self.security = MagicMock()
        self.security.hash_password = AsyncMock(return_value="hashed_value")
        self.notifier = MagicMock()
        self.token_service = MagicMock()
        self.case = RegisterUserCase(
            uow=self.uow,
            security_service=self.security,
            register_service=self.service,
            notifier_service=self.notifier,
            token_service=self.token_service,
        )

    @pytest.mark.asyncio
    async def test_execute_creates_tenant_and_user(self) -> None:
        """Registration creates a tenant, then creates user with tenant_id."""
        from datetime import datetime, timezone

        data = UserCreationValueObject(
            name="Test Farm SRL",
            dni="12345678",
            email="test@acme.com",
        )
        expected_user = make_user_entity()
        user_repo = self.uow.get_repository(IUserRepository)
        user_repo.exists.return_value = False
        user_repo.create.return_value = expected_user

        tenant_repo = self.uow.get_repository(ITenantRepository)
        tenant_repo.get_by_slug.return_value = None  # no duplicate slug
        fake_tenant_id = uuid4()
        from src.auth.domain.entities._tenant_entity import TenantEntity

        tenant_repo.create.return_value = TenantEntity(
            id=fake_tenant_id,
            name="Test Farm SRL",
            slug="test-farm-srl",
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        self.token_service.generate = MagicMock(return_value="test-token")

        result = await self.case.execute(data, redirect_url="http://example.com/confirm")

        assert result == expected_user
        user_repo.exists.assert_awaited_once()
        tenant_repo.create.assert_awaited_once()
        # Verify token was generated with tenant context
        self.token_service.generate.assert_called_once()
        self.notifier.send.assert_called_once()
        self.uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_raises_on_duplicate_slug(self) -> None:
        """Registration raises DuplicatedError when slug already exists."""
        from datetime import datetime, timezone

        from src.auth.domain.entities._tenant_entity import TenantEntity
        from src.common.domain.exceptions import DuplicatedError

        data = UserCreationValueObject(
            name="Existing Farm",
            dni="87654321",
            email="existing@acme.com",
        )
        expected_user = make_user_entity()
        user_repo = self.uow.get_repository(IUserRepository)
        user_repo.exists.return_value = False
        user_repo.create.return_value = expected_user

        tenant_repo = self.uow.get_repository(ITenantRepository)
        # Simulate existing slug by returning a tenant from get_by_slug
        existing_tenant = TenantEntity(
            id=uuid4(),
            name="Existing Farm",
            slug="existing-farm",
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        tenant_repo.get_by_slug.return_value = existing_tenant

        self.token_service.generate = MagicMock(return_value="test-token")

        with pytest.raises(DuplicatedError):
            await self.case.execute(data, redirect_url="http://example.com/confirm")

        tenant_repo.get_by_slug.assert_awaited_once_with("existing-farm")
        tenant_repo.create.assert_not_called()
