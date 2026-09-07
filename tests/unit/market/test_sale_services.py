"""Unit tests for sale domain services.

Domain services contain pure business logic with no infrastructure dependencies.
"""

from decimal import Decimal

import pytest

from src.common.domain.exceptions import BusinessValidationError
from src.market.domain.services.sale_services.create_sale_service import (
    CreateSaleService,
)


class TestCreateSaleService:
    """Business rules for creating a sale."""

    def setup_method(self) -> None:
        self.service = CreateSaleService()

    def test_valid_data_passes_validation(self) -> None:
        """price_per_kg * weight consistent with price passes validation."""
        # 10.0 * 100 = 1000, matches price exactly
        data = type("Data", (), {"price_per_kg": Decimal("10.0"), "price": Decimal("1000.0"), "weight": 100.0})()

        # Should not raise
        self.service.validate_data(data)

    def test_raises_error_when_price_per_kg_times_weight_inconsistent(self) -> None:
        """price_per_kg * weight off by >10% raises BusinessValidationError."""
        # 5000.0 * 1 = 5000, |5000 - 1000|/1000 = 4.0 > 0.1 → off by >10%
        data = type("Data", (), {"price_per_kg": Decimal("5000.0"), "price": Decimal("1000.0"), "weight": 1.0})()

        with pytest.raises(BusinessValidationError) as exc_info:
            self.service.validate_data(data)

        assert "inconsistent" in exc_info.value.message.lower() or "inconsistente" in exc_info.value.message.lower()
        assert any(d.get("field") == "price_per_kg" for d in exc_info.value.details)

    def test_within_tolerance_passes(self) -> None:
        """price_per_kg * weight within 10% tolerance passes (<= 10% deviation)."""
        # 15.0 * 100 = 1500, |1500 - 1600|/1600 = 0.0625 < 0.1 → within 10% tolerance
        data = type("Data", (), {"price_per_kg": Decimal("15.0"), "price": Decimal("1600.0"), "weight": 100.0})()

        # Should not raise
        self.service.validate_data(data)

    def test_raises_when_price_is_zero(self) -> None:
        """Price <= 0 raises BusinessValidationError."""
        data = type("Data", (), {"price_per_kg": Decimal("10.0"), "price": Decimal("0"), "weight": 100.0})()

        with pytest.raises(BusinessValidationError):
            self.service.validate_data(data)

    def test_raises_when_price_per_kg_is_zero(self) -> None:
        """Price_per_kg <= 0 raises BusinessValidationError."""
        data = type("Data", (), {"price_per_kg": Decimal("0"), "price": Decimal("1000.0"), "weight": 100.0})()

        with pytest.raises(BusinessValidationError):
            self.service.validate_data(data)

    def test_raises_when_weight_is_zero(self) -> None:
        """Weight <= 0 raises BusinessValidationError."""
        data = type("Data", (), {"price_per_kg": Decimal("10.0"), "price": Decimal("1000.0"), "weight": 0.0})()

        with pytest.raises(BusinessValidationError):
            self.service.validate_data(data)

    async def test_create_new_returns_entity(self) -> None:
        """create_new delegates to the repository and returns the result."""
        from unittest.mock import AsyncMock

        from tests.factories import make_animal_entity, make_animal_protocol_entity, make_sale_create, make_sale_entity

        data = make_sale_create()
        expected_entity = make_sale_entity()
        repo = AsyncMock()
        repo.create = AsyncMock(return_value=expected_entity)
        animal_repo = AsyncMock()
        animal_repo.get_by_id = AsyncMock(return_value=make_animal_entity())
        from datetime import date

        protocol_repo = AsyncMock()
        protocol_repo.get_by_animal_id = AsyncMock(
            return_value=make_animal_protocol_entity(
                animal=make_animal_entity(),
                vaccinated=True,
                vaccinated_date=date.today(),
                sale_permission=True,
                sale_permission_date=date.today(),
            )
        )

        result = await self.service.create_new(data, repo, animal_repo, protocol_repo)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(data)
