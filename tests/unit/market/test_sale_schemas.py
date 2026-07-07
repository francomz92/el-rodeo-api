"""Unit tests for sale input schemas (Phase 8 — API Hardening).

Covers:
- SaleCreateSchema: price, price_per_kg, weight must be gt=0
"""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.market.infrastructure.adapters.http.input.sale_schemas import (
    SaleCreateSchema,
)


class TestSaleCreateSchemaConstraints:
    """SaleCreateSchema must enforce gt=0 on price, price_per_kg, weight."""

    def test_positive_values_accepted(self) -> None:
        """All positive numeric fields pass validation."""
        schema = SaleCreateSchema(
            animal_id=uuid4(),
            buyer_id=uuid4(),
            sale_date=date(2024, 6, 15),
            price=1500.00,
            price_per_kg=15.50,
            weight=100.0,
        )
        assert schema.price == 1500.00
        assert schema.price_per_kg == 15.50
        assert schema.weight == 100.0

    def test_zero_price_rejected(self) -> None:
        """Zero price raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            SaleCreateSchema(
                animal_id=uuid4(),
                buyer_id=uuid4(),
                sale_date=date(2024, 6, 15),
                price=0,
                price_per_kg=15.50,
                weight=100.0,
            )
        errors = exc_info.value.errors()
        assert any("price" in e["loc"] for e in errors)

    def test_zero_price_per_kg_rejected(self) -> None:
        """Zero price_per_kg raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            SaleCreateSchema(
                animal_id=uuid4(),
                buyer_id=uuid4(),
                sale_date=date(2024, 6, 15),
                price=1500.00,
                price_per_kg=0,
                weight=100.0,
            )
        errors = exc_info.value.errors()
        assert any("price_per_kg" in e["loc"] for e in errors)

    def test_zero_weight_rejected(self) -> None:
        """Zero weight raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            SaleCreateSchema(
                animal_id=uuid4(),
                buyer_id=uuid4(),
                sale_date=date(2024, 6, 15),
                price=1500.00,
                price_per_kg=15.50,
                weight=0,
            )
        errors = exc_info.value.errors()
        assert any("weight" in e["loc"] for e in errors)

    def test_negative_price_rejected(self) -> None:
        """Negative price raises validation error."""
        with pytest.raises(ValidationError):
            SaleCreateSchema(
                animal_id=uuid4(),
                buyer_id=uuid4(),
                sale_date=date(2024, 6, 15),
                price=-100.00,
                price_per_kg=15.50,
                weight=100.0,
            )

    def test_negative_price_per_kg_rejected(self) -> None:
        """Negative price_per_kg raises validation error."""
        with pytest.raises(ValidationError):
            SaleCreateSchema(
                animal_id=uuid4(),
                buyer_id=uuid4(),
                sale_date=date(2024, 6, 15),
                price=1500.00,
                price_per_kg=-5.0,
                weight=100.0,
            )

    def test_negative_weight_rejected(self) -> None:
        """Negative weight raises validation error."""
        with pytest.raises(ValidationError):
            SaleCreateSchema(
                animal_id=uuid4(),
                buyer_id=uuid4(),
                sale_date=date(2024, 6, 15),
                price=1500.00,
                price_per_kg=15.50,
                weight=-50.0,
            )
