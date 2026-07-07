"""Unit tests for _get_current_tenant dependency.

Verifies that the dependency resolves a TenantEntity from the JWT payload.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.auth.domain.entities._tenant_entity import TenantEntity
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.common.domain.exceptions import UnauthorizedError


class _MockUoW:
    """Minimal UoW mock that supports async context manager protocol."""

    def __init__(self):
        self.tenant_id = None
        self._tenant_repo = MagicMock()
        self._tenant_repo.get_by_id = AsyncMock()

    def get_repository(self, repo_type):
        if repo_type == ITenantRepository:
            return self._tenant_repo
        return MagicMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.mark.asyncio
async def test_get_current_tenant_returns_tenant() -> None:
    """_get_current_tenant returns TenantEntity from JWT tenant_id."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        _get_current_tenant,
    )

    tenant_id = uuid4()
    uow = _MockUoW()
    auth_service = MagicMock()
    auth_service.token_service.decode.return_value = {
        "tenant_id": str(tenant_id),
    }
    token = MagicMock()
    token.credentials = "valid-token"

    expected_tenant = TenantEntity(
        id=tenant_id,
        name="Test",
        slug="test",
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    uow._tenant_repo.get_by_id.return_value = expected_tenant

    result = await _get_current_tenant(
        uow=uow,
        auth_service=auth_service,
        token=token,
    )

    assert result == expected_tenant
    uow._tenant_repo.get_by_id.assert_awaited_once_with(tenant_id)


@pytest.mark.asyncio
async def test_get_current_tenant_raises_when_no_token() -> None:
    """_get_current_tenant raises UnauthorizedError when no token."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        _get_current_tenant,
    )

    uow = _MockUoW()
    auth_service = MagicMock()

    with pytest.raises(UnauthorizedError):
        await _get_current_tenant(uow=uow, auth_service=auth_service, token=None)


@pytest.mark.asyncio
async def test_get_current_tenant_raises_when_no_tenant_id() -> None:
    """_get_current_tenant raises when JWT has no tenant_id."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        _get_current_tenant,
    )

    uow = _MockUoW()
    auth_service = MagicMock()
    auth_service.token_service.decode.return_value = {}
    token = MagicMock()
    token.credentials = "valid-token"

    with pytest.raises(UnauthorizedError):
        await _get_current_tenant(uow=uow, auth_service=auth_service, token=token)


@pytest.mark.asyncio
async def test_get_current_tenant_raises_when_tenant_not_found() -> None:
    """_get_current_tenant raises when tenant_id from JWT is not in DB."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        _get_current_tenant,
    )

    tenant_id = uuid4()
    uow = _MockUoW()
    auth_service = MagicMock()
    auth_service.token_service.decode.return_value = {
        "tenant_id": str(tenant_id),
    }
    token = MagicMock()
    token.credentials = "valid-token"
    uow._tenant_repo.get_by_id.return_value = None

    with pytest.raises(UnauthorizedError):
        await _get_current_tenant(uow=uow, auth_service=auth_service, token=token)
