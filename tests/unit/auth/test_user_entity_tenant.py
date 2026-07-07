"""Unit tests for UserEntity with tenant_id field.

Verifies that UserEntity accepts and stores tenant_id after the field is added.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from src.auth.domain.entities._user_entity import UserEntity


class TestUserEntityTenantId:
    """UserEntity must carry an optional tenant_id."""

    def test_accepts_tenant_id(self) -> None:
        """UserEntity can be constructed with tenant_id."""
        tenant_id = uuid4()
        user = UserEntity(
            id=uuid4(),
            name="Test User",
            dni="12345678",
            email="test@example.com",
            created_at=datetime.now(tz=timezone.utc),
            _hashed_password="hashed_value",
            tenant_id=tenant_id,
        )

        assert user.tenant_id == tenant_id
        assert isinstance(user.tenant_id, UUID)

    def test_tenant_id_defaults_to_none(self) -> None:
        """UserEntity can be constructed without tenant_id (backward compat)."""
        user = UserEntity(
            id=uuid4(),
            name="Test User",
            dni="12345678",
            email="test@example.com",
            created_at=datetime.now(tz=timezone.utc),
            _hashed_password="hashed_value",
        )

        assert user.tenant_id is None

    @pytest.mark.asyncio
    async def test_tenant_id_survives_password_operations(self) -> None:
        """Password operations don't affect tenant_id."""
        tenant_id = uuid4()
        user = UserEntity(
            id=uuid4(),
            name="Test User",
            dni="12345678",
            email="test@example.com",
            created_at=datetime.now(tz=timezone.utc),
            _hashed_password="old_hash",
            tenant_id=tenant_id,
        )

        security = AsyncMock()
        security.hash_password.return_value = "new_hash"

        await user.update_password(security, "old", "new", "new")
        assert user.tenant_id == tenant_id
