"""Unit tests for ITenantRepository port and TenantRepository impl.

Port contract tests verify the interface methods exist.
Implementation tests verify CRUD with a mocked DB session.
"""

from abc import ABC
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.auth.domain.entities._tenant_entity import TenantEntity
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.auth.infrastructure.persistence.repositories.tenant_repository import (
    TenantRepository,
)


class TestITenantRepositoryPort:
    """ITenantRepository is an abstract port (interface)."""

    def test_interface_is_abstract(self) -> None:
        """Port must be an abstract class."""
        assert issubclass(ITenantRepository, ABC)

    def test_interface_defines_create(self) -> None:
        """Port must declare async create method."""
        assert hasattr(ITenantRepository, "create")

    def test_interface_defines_get_by_id(self) -> None:
        """Port must declare get_by_id method."""
        assert hasattr(ITenantRepository, "get_by_id")

    def test_interface_defines_get_by_slug(self) -> None:
        """Port must declare get_by_slug method."""
        assert hasattr(ITenantRepository, "get_by_slug")

    def test_interface_defines_list_all(self) -> None:
        """Port must declare list_all method."""
        assert hasattr(ITenantRepository, "list_all")


class TestTenantRepository:
    """TenantRepository CRUD with mocked session."""

    def setup_method(self) -> None:
        self.session = MagicMock()
        self.session.execute = AsyncMock()
        self.repo = TenantRepository(session=self.session)

    @pytest.mark.asyncio
    async def test_create_returns_tenant_entity(self) -> None:
        """create() persists a tenant and returns TenantEntity."""
        from datetime import datetime, timezone

        fake_id = uuid4()
        now = datetime.now(tz=timezone.utc)

        # Mock the execute to return a row with the new id
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = fake_id
        self.session.execute.return_value = result_mock

        # Mock get_by_id to return the entity
        expected_entity = TenantEntity(
            id=fake_id,
            name="Acme Farm",
            slug="acme-farm",
            created_at=now,
            updated_at=now,
        )
        self.repo.get_by_id = AsyncMock(return_value=expected_entity)  # type: ignore

        entity = await self.repo.create(name="Acme Farm", slug="acme-farm")

        assert entity.id == fake_id
        assert entity.name == "Acme Farm"
        assert entity.slug == "acme-farm"
        self.session.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self) -> None:
        """get_by_id returns None for non-existent ID."""
        result_mock = MagicMock()
        result_mock.mappings.return_value.one_or_none.return_value = None
        self.session.execute.return_value = result_mock

        entity = await self.repo.get_by_id(uuid4())

        assert entity is None

    @pytest.mark.asyncio
    async def test_get_by_slug_returns_none_when_not_found(self) -> None:
        """get_by_slug returns None for non-existent slug."""
        result_mock = MagicMock()
        result_mock.mappings.return_value.one_or_none.return_value = None
        self.session.execute.return_value = result_mock

        entity = await self.repo.get_by_slug("non-existent")

        assert entity is None

    @pytest.mark.asyncio
    async def test_list_all_returns_empty_when_no_tenants(self) -> None:
        """list_all returns empty list when no tenants exist."""
        result_mock = MagicMock()
        result_mock.mappings.return_value.all.return_value = []
        self.session.execute.return_value = result_mock

        entities = await self.repo.list_all()

        assert entities == []
