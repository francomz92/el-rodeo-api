"""Unit tests for auth use cases.

Use cases orchestrate domain services and repositories via the Unit of Work.
Here we mock the UoW to test the orchestration logic in isolation.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from tests.factories import make_user_entity
from tests.mocks import MockUoW

from src.auth.application.uses_cases.change_password_case import ChangePasswordCase
from src.auth.application.uses_cases.login_user_case import LoginUserCase
from src.auth.application.uses_cases.register_user_case import RegisterUserCase
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.services.change_password_service import ChangePasswordService
from src.auth.domain.services.login_user_service import LoginUserService
from src.auth.domain.services.register_user_service import RegisterUserService
from src.billing.application.services._trial_management_service import (
    TrialManagementService,
)
from src.common.domain.exceptions import DuplicatedError, UnauthorizedError


class TestRegisterUserCase:
    """RegisterUserCase registers a new user via UoW."""

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

        tenant_repo = self.uow.get_repository(ITenantRepository)
        tenant_repo.get_by_slug.return_value = None  # no duplicate slug
        fake_tenant_id = uuid4()
        from datetime import datetime, timezone

        from src.auth.domain.entities._tenant_entity import TenantEntity

        tenant_repo.create.return_value = TenantEntity(
            id=fake_tenant_id,
            name="Test User",
            slug="test-user",
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

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

    async def test_execute_starts_trial_when_trial_service_injected(self) -> None:
        """When trial_service is injected, start_trial is called after tenant creation."""
        from unittest.mock import AsyncMock

        from src.auth.domain.value_objects.user_value_object import (
            UserCreationValueObject,
        )

        trial_service = MagicMock(spec=TrialManagementService)
        trial_service.start_trial = AsyncMock()

        case = RegisterUserCase(
            uow=self.uow,
            security_service=self.security,
            register_service=self.service,
            notifier_service=self.notifier,
            token_service=self.token_service,
            trial_service=trial_service,
        )

        data = UserCreationValueObject(
            name="Test User",
            dni="87654321",
            email="trial@example.com",
        )
        expected_user = make_user_entity()
        repo = self.uow.get_repository(IUserRepository)
        repo.exists.return_value = False
        repo.create.return_value = expected_user

        tenant_repo = self.uow.get_repository(ITenantRepository)
        tenant_repo.get_by_slug.return_value = None

        from datetime import datetime, timezone

        from src.auth.domain.entities._tenant_entity import TenantEntity

        fake_tenant_id = uuid4()
        tenant_repo.create.return_value = TenantEntity(
            id=fake_tenant_id,
            name="Test User",
            slug="test-user",
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        self.token_service.generate = MagicMock(return_value="test-token")

        await case.execute(data, redirect_url="http://example.com/confirm")

        trial_service.start_trial.assert_awaited_once_with(fake_tenant_id)

    async def test_execute_skips_trial_when_trial_service_is_none(self) -> None:
        """When trial_service is None, no trial is started (backward compat)."""
        from src.auth.domain.value_objects.user_value_object import (
            UserCreationValueObject,
        )

        data = UserCreationValueObject(
            name="Test User",
            dni="11223344",
            email="notrial@example.com",
        )
        expected_user = make_user_entity()
        repo = self.uow.get_repository(IUserRepository)
        repo.exists.return_value = False
        repo.create.return_value = expected_user

        tenant_repo = self.uow.get_repository(ITenantRepository)
        tenant_repo.get_by_slug.return_value = None

        from datetime import datetime, timezone

        from src.auth.domain.entities._tenant_entity import TenantEntity

        fake_tenant_id = uuid4()
        tenant_repo.create.return_value = TenantEntity(
            id=fake_tenant_id,
            name="Test User",
            slug="test-user",
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        self.token_service.generate = MagicMock(return_value="test-token")

        result = await self.case.execute(data, redirect_url="http://example.com/confirm")

        assert result == expected_user


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
