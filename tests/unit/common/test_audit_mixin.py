"""Tests for AuditableRepositoryMixin and Model base updated_at.

Covers PR 2 tasks: 2.1 (mixin) and 2.2 (updated_at on Model base).
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.common.infrastructure.persistence.models import Model

# ── 2.2 Model base updated_at ────────────────────────────────────────────────


class TestModelUpdatedAt:
    """Task 2.2: Model base should have updated_at column."""

    def test_updated_at_column_exists(self) -> None:
        """Model base should define an updated_at attribute."""
        # Will pass once updated_at is added to the Model class
        assert hasattr(Model, "updated_at"), (
            "Model must have updated_at attribute — add it to src/common/infrastructure/persistence/models/base.py"
        )

    def test_created_at_and_updated_at_are_distinct(self) -> None:
        """Both created_at and updated_at should be present and distinct."""
        assert hasattr(Model, "created_at")
        assert hasattr(Model, "updated_at")
        assert Model.created_at is not Model.updated_at

    def test_updated_at_inherited_by_concrete_model(self) -> None:
        """Concrete models inheriting from Model should have updated_at."""
        from src.auth.infrastructure.persistence.models import User

        assert hasattr(User, "updated_at")

    def test_updated_at_on_all_model_tables(self) -> None:
        """Every concrete model that inherits Model should have updated_at."""
        from src.auth.infrastructure.persistence.models import RefreshToken, Tenant, User
        from src.cattle.infrastructure.persistence.models import Animal, AnimalType
        from src.cattle.infrastructure.persistence.models._animal_models import AnimalProtocols
        from src.cattle.infrastructure.persistence.models._schedule_event_models import ScheduledEvent
        from src.finance.infrastructure.persistence.models import AnimalSupply, AnimalSupplyType, Purchase
        from src.market.infrastructure.persistence.models import Buyer, Sale

        for cls in [
            User,
            Tenant,
            RefreshToken,
            Animal,
            AnimalType,
            AnimalProtocols,
            ScheduledEvent,
            AnimalSupply,
            AnimalSupplyType,
            Purchase,
            Buyer,
            Sale,
        ]:
            assert hasattr(cls, "updated_at"), f"{cls.__name__} should have updated_at"


# ── 2.1 AuditableRepositoryMixin ─────────────────────────────────────────────


class TestAuditableRepositoryMixin:
    """Task 2.1: Mixin audit helper methods."""

    # ── Setup helpers ─────────────────────────────────────────────────────

    @pytest.fixture
    def mixin(self) -> "AuditableRepositoryMixin":
        from src.common.infrastructure.persistence.repositories._auditable_mixin import (
            AuditableRepositoryMixin,
        )

        return AuditableRepositoryMixin()

    @pytest.fixture
    def mock_audit(self) -> MagicMock:
        from unittest.mock import MagicMock

        return MagicMock()

    # ── Structural tests ──────────────────────────────────────────────────

    def test_mixin_is_importable(self) -> None:
        """Mixin module should exist with AuditableRepositoryMixin class."""
        from src.common.infrastructure.persistence.repositories._auditable_mixin import (
            AuditableRepositoryMixin,
        )

        assert AuditableRepositoryMixin is not None

    def test_mixin_has_audit_repository_attribute(self, mixin) -> None:
        """Mixin should have an audit_repository attribute defaulting to None."""
        assert hasattr(mixin, "audit_repository")
        assert mixin.audit_repository is None

    def test_mixin_has_audit_create_method(self, mixin) -> None:
        """Mixin should have _audit_create method."""
        assert hasattr(mixin, "_audit_create")
        assert callable(mixin._audit_create)

    def test_mixin_has_audit_update_method(self, mixin) -> None:
        """Mixin should have _audit_update method."""
        assert hasattr(mixin, "_audit_update")
        assert callable(mixin._audit_update)

    def test_mixin_has_audit_delete_method(self, mixin) -> None:
        """Mixin should have _audit_delete method."""
        assert hasattr(mixin, "_audit_delete")
        assert callable(mixin._audit_delete)

    # ── No-op behavior (audit_repository is None) ─────────────────────────

    def test_audit_create_is_noop_when_no_audit_repo(self, mixin) -> None:
        """_audit_create should not raise when audit_repository is None."""
        entity_id = uuid4()
        # Should not raise
        mixin._audit_create("TestEntity", entity_id, {"name": "test"})

    def test_audit_update_is_noop_when_no_audit_repo(self, mixin) -> None:
        """_audit_update should not raise when audit_repository is None."""
        entity_id = uuid4()
        mixin._audit_update("TestEntity", entity_id, {"name": "old"}, {"name": "new"})

    def test_audit_delete_is_noop_when_no_audit_repo(self, mixin) -> None:
        """_audit_delete should not raise when audit_repository is None."""
        entity_id = uuid4()
        mixin._audit_delete("TestEntity", entity_id, {"name": "old"})

    # ── Record behavior (audit_repository is set) ─────────────────────────

    def test_audit_create_calls_record_with_correct_params(self, mixin, mock_audit) -> None:
        """_audit_create should call audit_repository.record."""
        mixin.audit_repository = mock_audit
        entity_id = uuid4()

        mixin._audit_create("User", entity_id, {"name": "John"})

        mock_audit.record.assert_called_once()
        call_kwargs = mock_audit.record.call_args[1]
        assert call_kwargs["action"] == "create"
        assert call_kwargs["entity_type"] == "User"
        assert call_kwargs["entity_id"] == entity_id
        assert call_kwargs["new_values"] == {"name": "John"}

    def test_audit_update_calls_record_with_correct_params(self, mixin, mock_audit) -> None:
        """_audit_update should call audit_repository.record."""
        mixin.audit_repository = mock_audit
        entity_id = uuid4()

        mixin._audit_update("Animal", entity_id, {"name": "Old"}, {"name": "New"})

        mock_audit.record.assert_called_once()
        call_kwargs = mock_audit.record.call_args[1]
        assert call_kwargs["action"] == "update"
        assert call_kwargs["entity_type"] == "Animal"
        assert call_kwargs["entity_id"] == entity_id
        assert call_kwargs["old_values"] == {"name": "Old"}
        assert call_kwargs["new_values"] == {"name": "New"}

    def test_audit_delete_calls_record_with_correct_params(self, mixin, mock_audit) -> None:
        """_audit_delete should call audit_repository.record."""
        mixin.audit_repository = mock_audit
        entity_id = uuid4()

        mixin._audit_delete("Sale", entity_id, {"price": 100.0})

        mock_audit.record.assert_called_once()
        call_kwargs = mock_audit.record.call_args[1]
        assert call_kwargs["action"] == "delete"
        assert call_kwargs["entity_type"] == "Sale"
        assert call_kwargs["entity_id"] == entity_id
        assert call_kwargs["old_values"] == {"price": 100.0}

    # ── Triangulation ─────────────────────────────────────────────────────

    def test_audit_create_passes_extra_kwargs(self, mixin, mock_audit) -> None:
        """Extra keyword arguments should be forwarded to record()."""
        mixin.audit_repository = mock_audit
        entity_id = uuid4()

        mixin._audit_create(
            "Test",
            entity_id,
            {"x": 1},
            tenant_id=uuid4(),
            user_id=uuid4(),
        )

        call_kwargs = mock_audit.record.call_args[1]
        assert "tenant_id" in call_kwargs
        assert "user_id" in call_kwargs

    def test_audit_update_without_old_values(self, mixin, mock_audit) -> None:
        """_audit_update should work without old_values."""
        mixin.audit_repository = mock_audit
        entity_id = uuid4()

        mixin._audit_update("Test", entity_id, new_values={"x": 2})

        call_kwargs = mock_audit.record.call_args[1]
        assert call_kwargs["old_values"] is None
        assert call_kwargs["new_values"] == {"x": 2}

    def test_audit_delete_by_entity_type_only(self, mixin, mock_audit) -> None:
        """Entity type can differ from class name (passed explicitly)."""
        mixin.audit_repository = mock_audit
        entity_id = uuid4()

        mixin._audit_delete("purchase", entity_id)

        call_kwargs = mock_audit.record.call_args[1]
        assert call_kwargs["entity_type"] == "purchase"
        assert call_kwargs["old_values"] is None
