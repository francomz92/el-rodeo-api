"""Unit tests for TenantEntity domain object.

The TenantEntity is a pure dataclass with no behavior.
Tests verify construction, field types, and equality semantics.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.auth.domain.entities._tenant_entity import TenantEntity


class TestTenantEntityConstruction:
    """TenantEntity must accept all fields at construction."""

    def test_creates_with_all_fields(self) -> None:
        """A fully populated TenantEntity retains all values."""
        expected_id = uuid4()
        expected_created_at = datetime.now(tz=timezone.utc)
        expected_updated_at = datetime.now(tz=timezone.utc)

        entity = TenantEntity(
            id=expected_id,
            name="Acme Farm",
            slug="acme-farm",
            created_at=expected_created_at,
            updated_at=expected_updated_at,
        )

        assert entity.id == expected_id
        assert entity.name == "Acme Farm"
        assert entity.slug == "acme-farm"
        assert entity.created_at == expected_created_at
        assert entity.updated_at == expected_updated_at

    def test_fields_have_correct_types(self) -> None:
        """All fields must be proper UUID/datetime/str types."""
        now = datetime.now(tz=timezone.utc)
        entity = TenantEntity(
            id=uuid4(),
            name="Test",
            slug="test",
            created_at=now,
            updated_at=now,
        )

        assert isinstance(entity.id, UUID)
        assert isinstance(entity.name, str)
        assert isinstance(entity.slug, str)
        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.updated_at, datetime)

    def test_two_entities_with_same_fields_are_not_equal(self) -> None:
        """Dataclass default eq compares all fields — they are value objects."""
        now = datetime.now(tz=timezone.utc)
        e1 = TenantEntity(
            id=uuid4(),
            name="Acme",
            slug="acme",
            created_at=now,
            updated_at=now,
        )
        e2 = TenantEntity(
            id=uuid4(),
            name="Acme",
            slug="acme",
            created_at=now,
            updated_at=now,
        )

        # Different IDs → not equal (default dataclass eq)
        assert e1 != e2
