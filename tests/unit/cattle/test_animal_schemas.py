"""Unit tests for animal input schemas (Phase 8 — API Hardening).

Covers:
- AnimalCreationSchema: initial_weight must be gt=0
- AnimalUpdateSchema: initial_weight, last_weight must be gt=0 when provided
"""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.cattle.infrastructure.adapters.http.input.animal_schemas import (
    AnimalCreationSchema,
    AnimalUpdateSchema,
)


class TestAnimalCreationSchemaConstraints:
    """AnimalCreationSchema must enforce gt=0 on weight fields."""

    def test_positive_initial_weight_accepted(self) -> None:
        """Positive initial_weight passes validation."""
        schema = AnimalCreationSchema(
            type_id=uuid4(),
            caravana="ABC123",
            breed="Angus",
            date_of_birth=date(2020, 1, 1),
            initial_weight=250.5,
            initial_weight_date=date(2020, 1, 1),
        )
        assert schema.initial_weight == 250.5

    def test_zero_initial_weight_rejected(self) -> None:
        """Zero initial_weight raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AnimalCreationSchema(
                type_id=uuid4(),
                caravana="ABC123",
                breed="Angus",
                date_of_birth=date(2020, 1, 1),
                initial_weight=0,
                initial_weight_date=date(2020, 1, 1),
            )
        errors = exc_info.value.errors()
        assert any("initial_weight" in e["loc"] for e in errors)

    def test_negative_initial_weight_rejected(self) -> None:
        """Negative initial_weight raises validation error."""
        with pytest.raises(ValidationError):
            AnimalCreationSchema(
                type_id=uuid4(),
                caravana="ABC123",
                breed="Angus",
                date_of_birth=date(2020, 1, 1),
                initial_weight=-10.0,
                initial_weight_date=date(2020, 1, 1),
            )


class TestAnimalUpdateSchemaConstraints:
    """AnimalUpdateSchema must enforce gt=0 on optional weight fields."""

    def test_positive_initial_weight_accepted(self) -> None:
        """Positive initial_weight passes validation."""
        schema = AnimalUpdateSchema(
            type_id=uuid4(),
            initial_weight=300.0,
        )
        assert schema.initial_weight == 300.0

    def test_zero_initial_weight_rejected(self) -> None:
        """Zero initial_weight raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AnimalUpdateSchema(
                type_id=uuid4(),
                initial_weight=0,
            )
        errors = exc_info.value.errors()
        assert any("initial_weight" in e["loc"] for e in errors)

    def test_negative_initial_weight_rejected(self) -> None:
        """Negative initial_weight raises validation error."""
        with pytest.raises(ValidationError):
            AnimalUpdateSchema(
                type_id=uuid4(),
                initial_weight=-5.0,
            )

    def test_initial_weight_none_accepted(self) -> None:
        """Omitting initial_weight is allowed (optional)."""
        schema = AnimalUpdateSchema(type_id=uuid4())
        assert schema.initial_weight is None

    def test_positive_last_weight_accepted(self) -> None:
        """Positive last_weight passes validation."""
        schema = AnimalUpdateSchema(
            type_id=uuid4(),
            last_weight=350.0,
        )
        assert schema.last_weight == 350.0

    def test_zero_last_weight_rejected(self) -> None:
        """Zero last_weight raises validation error."""
        with pytest.raises(ValidationError):
            AnimalUpdateSchema(
                type_id=uuid4(),
                last_weight=0,
            )

    def test_negative_last_weight_rejected(self) -> None:
        """Negative last_weight raises validation error."""
        with pytest.raises(ValidationError):
            AnimalUpdateSchema(
                type_id=uuid4(),
                last_weight=-1.0,
            )

    def test_last_weight_none_accepted(self) -> None:
        """Omitting last_weight is allowed (optional)."""
        schema = AnimalUpdateSchema(type_id=uuid4())
        assert schema.last_weight is None
