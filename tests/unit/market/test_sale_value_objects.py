"""Unit tests for sale value objects.

These tests validate the creation and default behaviour of sale-related
value objects without any infrastructure dependency.
"""

from datetime import date
from uuid import UUID

from src.common.domain.types import Sentinel
from src.market.domain.value_objects.sale_value_objects import (
    SaleCreateValueObject,
    SaleListQueryParamsValueObject,
)


class TestSaleCreateValueObject:
    """SaleCreateValueObject is the input data for creating a sale."""

    def test_constructs_with_all_fields(self, any_uuid: UUID) -> None:
        """All required fields are set correctly."""
        sale_date = date(2024, 6, 15)

        vo = SaleCreateValueObject(
            user_id=any_uuid,
            animal_id=any_uuid,
            buyer_id=any_uuid,
            sale_date=sale_date,
            price=1500.00,
            price_per_kg=12.50,
            weight=120.0,
            description="Venta de novillo",
        )

        assert vo.user_id == any_uuid
        assert vo.animal_id == any_uuid
        assert vo.buyer_id == any_uuid
        assert vo.sale_date == sale_date
        assert vo.price == 1500.00
        assert vo.price_per_kg == 12.50
        assert vo.weight == 120.0
        assert vo.description == "Venta de novillo"

    def test_default_description_is_empty_string(self, any_uuid: UUID) -> None:
        """Description defaults to empty string when not provided."""
        vo = SaleCreateValueObject(
            user_id=any_uuid,
            animal_id=any_uuid,
            buyer_id=any_uuid,
            sale_date=date.today(),
            price=1000.0,
            price_per_kg=10.0,
            weight=100.0,
        )

        assert vo.description == ""

    def test_can_set_description_to_none(self, any_uuid: UUID) -> None:
        """Description accepts None (for nullable DB column compatibility)."""
        vo = SaleCreateValueObject(
            user_id=any_uuid,
            animal_id=any_uuid,
            buyer_id=any_uuid,
            sale_date=date.today(),
            price=1000.0,
            price_per_kg=10.0,
            weight=100.0,
            description="",
        )

        assert vo.description == ""

    def test_negative_price_is_allowed_at_this_layer(self, any_uuid: UUID) -> None:
        """Value objects don't validate business rules — domain services do."""
        vo = SaleCreateValueObject(
            user_id=any_uuid,
            animal_id=any_uuid,
            buyer_id=any_uuid,
            sale_date=date.today(),
            price=-100.0,
            price_per_kg=10.0,
            weight=100.0,
        )

        assert vo.price == -100.0


class TestSaleListQueryParamsValueObject:
    """SaleListQueryParamsValueObject carries optional filters for listing sales."""

    def test_defaults_to_unset_for_all_filters(self, unset: Sentinel) -> None:
        """All filter fields default to Sentinel.UNSET — meaning 'no filter'."""
        params = SaleListQueryParamsValueObject()

        assert params.buyer_id is unset
        assert params.sale_date is unset
        assert params.price is unset

    def test_with_buyer_id_filter(self, any_uuid: UUID, unset: Sentinel) -> None:
        """Sets buyer_id and leaves others as unset."""
        params = SaleListQueryParamsValueObject(buyer_id=any_uuid)

        assert params.buyer_id == any_uuid
        assert params.sale_date is unset
        assert params.price is unset

    def test_with_sale_date_filter(self, unset: Sentinel) -> None:
        """Sets sale_date and leaves others as unset."""
        sale_date = date(2024, 6, 1)
        params = SaleListQueryParamsValueObject(sale_date=sale_date)

        assert params.sale_date == sale_date
        assert params.buyer_id is unset
        assert params.price is unset

    def test_with_price_filter(self, unset: Sentinel) -> None:
        """Sets price (max price filter) and leaves others as unset."""
        params = SaleListQueryParamsValueObject(price=5000.0)

        assert params.price == 5000.0
        assert params.buyer_id is unset
        assert params.sale_date is unset

    def test_with_all_filters_set(self, any_uuid: UUID) -> None:
        """All filters can be set simultaneously."""
        sale_date = date(2024, 6, 1)
        params = SaleListQueryParamsValueObject(
            buyer_id=any_uuid,
            sale_date=sale_date,
            price=3000.0,
        )

        assert params.buyer_id == any_uuid
        assert params.sale_date == sale_date
        assert params.price == 3000.0
