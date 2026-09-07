"""Unit tests for TenantAwareRepository base class.

Verifies that _filter_tenant adds the correct WHERE clause and
that bypass_filter mode skips tenant filtering.
"""

from abc import ABC
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import declarative_base

from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)

# Build a minimal test model
TestBase = declarative_base()


class TestModel(TestBase):  # type: ignore
    __tablename__ = "test_table"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String)
    name = Column(String)


class TestTenantAwareRepositoryInterface:
    """TenantAwareRepository is an abstract base class."""

    def test_is_abstract(self) -> None:
        """TenantAwareRepository must be abstract."""
        assert issubclass(TenantAwareRepository, ABC)

    def test_cannot_instantiate_directly(self) -> None:
        """Cannot instantiate TenantAwareRepository without _model."""
        with pytest.raises(TypeError):
            TenantAwareRepository(session=MagicMock(), tenant_id=uuid4())  # type: ignore


class TestFilterTenant:
    """_filter_tenant adds WHERE tenant_id = X clause."""

    def setup_method(self) -> None:
        self.tenant_id = uuid4()
        self.concrete_repo = _make_concrete_repo(self.tenant_id)

    def test_adds_tenant_filter(self) -> None:
        """_filter_tenant adds WHERE tenant_id = self._tenant_id."""
        stmt = select(TestModel)
        filtered = self.concrete_repo._filter_tenant(stmt)

        compiled = str(filtered.compile(compile_kwargs={"literal_binds": True}))
        # SQLAlchemy renders UUIDs as hex without dashes
        assert self.tenant_id.hex in compiled
        assert "tenant_id" in compiled

    def test_bypass_flag_skips_filter(self) -> None:
        """When bypass_filter=True, _filter_tenant returns statement unchanged."""
        repo = _make_concrete_repo(self.tenant_id, bypass=True)
        stmt = select(TestModel)
        filtered = repo._filter_tenant(stmt)

        compiled = str(filtered.compile(compile_kwargs={"literal_binds": True}))
        # No WHERE clause should be added
        assert "WHERE" not in compiled.upper() or "tenant_id" not in compiled

    def test_bypass_false_adds_filter(self) -> None:
        """When bypass_filter=False (default), filter IS added."""
        stmt = select(TestModel)
        filtered = self.concrete_repo._filter_tenant(stmt)

        compiled = str(filtered.compile(compile_kwargs={"literal_binds": True}))
        assert "WHERE" in compiled.upper()
        assert "tenant_id" in compiled

    def test_filter_uses_correct_tenant_id(self) -> None:
        """The WHERE clause references the correct tenant UUID hex."""
        stmt = select(TestModel)
        filtered = self.concrete_repo._filter_tenant(stmt)

        compiled = str(filtered.compile(compile_kwargs={"literal_binds": True}))
        assert self.tenant_id.hex in compiled


class TestTenantIdNone:
    """TenantAwareRepository tolerates tenant_id=None (no-op filter)."""

    def test_tenant_id_none_does_not_raise(self) -> None:
        """tenant_id=None should NOT raise ValueError."""
        repo = _make_concrete_repo(tenant_id=None)
        assert repo._tenant_id is None  # type: ignore[attr-defined]

    def test_filter_tenant_noop_when_tenant_id_none(self) -> None:
        """_filter_tenant returns stmt unchanged when tenant_id=None."""
        repo = _make_concrete_repo(tenant_id=None)
        stmt = select(TestModel)
        filtered = repo._filter_tenant(stmt)

        compiled = str(filtered.compile(compile_kwargs={"literal_binds": True}))
        assert "WHERE" not in compiled.upper() or "tenant_id" not in compiled

    def test_filter_tenant_noop_even_without_bypass(self) -> None:
        """tenant_id=None means no filtering even when bypass_filter=False."""
        repo = _make_concrete_repo(tenant_id=None, bypass=False)
        stmt = select(TestModel)
        filtered = repo._filter_tenant(stmt)

        compiled = str(filtered.compile(compile_kwargs={"literal_binds": True}))
        assert "WHERE" not in compiled.upper() or "tenant_id" not in compiled


class TestConcreteRepository:
    """Concrete subclass must define _model property."""

    def test_model_property_is_required(self) -> None:
        """Subclass must implement the _model abstract property."""

        class MissingModel(TenantAwareRepository):
            pass

        with pytest.raises(TypeError):
            MissingModel(session=MagicMock(), tenant_id=uuid4())  # type: ignore

    def test_model_property_returns_type(self) -> None:
        """_model returns the SQLAlchemy model class."""
        repo = _make_concrete_repo(uuid4())
        assert repo._model == TestModel  # type: ignore[comparison-overlap]


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_concrete_repo(tenant_id: UUID | None, bypass: bool = False) -> TenantAwareRepository:
    """Build a concrete tenant-aware repository for testing."""

    class ConcreteRepo(TenantAwareRepository):
        _model = TestModel

    return ConcreteRepo(session=MagicMock(), tenant_id=tenant_id, bypass_filter=bypass)
