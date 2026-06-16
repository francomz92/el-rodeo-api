"""Unit tests for sale domain services.

Domain services contain pure business logic with no infrastructure dependencies.
"""

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
        """price_per_kg * weight >= price should pass validation."""
        data = type("Data", (), {"price_per_kg": 20.0, "price": 1000.0, "weight": 100.0})()

        # Should not raise
        self.service.validate_data(data)

    def test_raises_error_when_price_per_kg_times_weight_higher_than_price(self) -> None:
        """price_per_kg * weight < price is inconsistent and must be rejected."""
        data = type("Data", (), {"price_per_kg": 5000.0, "price": 1000.0, "weight": 1.0})()

        with pytest.raises(BusinessValidationError) as exc_info:
            self.service.validate_data(data)

        assert "inconsistent" in exc_info.value.message.lower() or "inconsistente" in exc_info.value.message.lower()
        assert any(d.get("field") == "price_per_kg" for d in exc_info.value.details)

    def test_equal_price_and_price_per_kg_passes(self) -> None:
        """price_per_kg * weight == price passes because the condition is strict `<`."""
        data = type("Data", (), {"price_per_kg": 10.0, "price": 1000.0, "weight": 100.0})()

        # Should not raise (condition is `<`, not `<=`)
        self.service.validate_data(data)

    async def test_create_new_returns_entity(self) -> None:
        """create_new delegates to the repository and returns the result."""
        from unittest.mock import AsyncMock

        from tests.factories import make_sale_create, make_sale_entity

        data = make_sale_create()
        expected_entity = make_sale_entity()
        repo = AsyncMock()
        repo.create = AsyncMock(return_value=expected_entity)

        result = await self.service.create_new(data, repo)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(data)
