"""Unit tests for animal supplies input schemas (Phase 8 — API Hardening).

Covers:
- AnimalSuppliesCreateSchema: name must have max_length=100
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.finance.domain.constants.animal_supplies import UnitOfMeasurement
from src.finance.infrastructure.adapters.http.input.animal_supplies_schemas import (
    AnimalSuppliesCreateSchema,
)


class TestAnimalSuppliesCreateSchemaConstraints:
    """AnimalSuppliesCreateSchema must enforce max_length=100 on name."""

    def test_name_within_limit_accepted(self) -> None:
        """Name up to 100 characters passes validation."""
        schema = AnimalSuppliesCreateSchema(
            type_id=uuid4(),
            name="a" * 100,
            amount=10.0,
            critical_amount=5.0,
            unit_of_measurement=UnitOfMeasurement.UNIT,
        )
        assert len(schema.name) == 100

    def test_name_exceeds_max_length_rejected(self) -> None:
        """Name longer than 100 characters raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AnimalSuppliesCreateSchema(
                type_id=uuid4(),
                name="a" * 101,
                amount=10.0,
                critical_amount=5.0,
                unit_of_measurement=UnitOfMeasurement.UNIT,
            )
        errors = exc_info.value.errors()
        assert any("name" in e["loc"] for e in errors)

    def test_short_name_accepted(self) -> None:
        """Short name (1 char) passes validation."""
        schema = AnimalSuppliesCreateSchema(
            type_id=uuid4(),
            name="X",
            amount=10.0,
            critical_amount=5.0,
            unit_of_measurement=UnitOfMeasurement.UNIT,
        )
        assert schema.name == "X"
