"""Unit tests for buyer value objects."""

from uuid import UUID

from src.common.domain.types import Sentinel
from src.market.domain.value_objects.buyer_value_objects import (
    BuyerCreateValueObject,
    BuyerListQueryParamsValueObject,
    BuyerUpdateValueObject,
)


class TestBuyerCreateValueObject:
    """BuyerCreateValueObject is the input data for creating a buyer."""

    def test_constructs_with_all_fields(self, any_uuid: UUID) -> None:
        """All required fields and defaults are set correctly."""
        vo = BuyerCreateValueObject(
            user_id=any_uuid,
            name="Comprador Test",
            description="Comprador de prueba",
            contact_number="+54 11 1234-5678",
            contact_address="Calle Falsa 123",
        )

        assert vo.user_id == any_uuid
        assert vo.name == "Comprador Test"
        assert vo.description == "Comprador de prueba"
        assert vo.contact_number == "+54 11 1234-5678"
        assert vo.contact_address == "Calle Falsa 123"

    def test_defaults_are_empty_strings(self, any_uuid: UUID) -> None:
        """Optional fields default to empty string."""
        vo = BuyerCreateValueObject(
            user_id=any_uuid,
            name="Comprador Test",
        )

        assert vo.description == ""
        assert vo.contact_number == ""
        assert vo.contact_address == ""


class TestBuyerUpdateValueObject:
    """BuyerUpdateValueObject carries partial updates for a buyer."""

    def test_all_fields_default_to_unset(self, unset: Sentinel) -> None:
        """Every field is UNSET when no value is provided — partial update."""
        vo = BuyerUpdateValueObject()

        assert vo.name is unset
        assert vo.description is unset
        assert vo.contact_number is unset
        assert vo.contact_address is unset

    def test_partial_update_only_name(self, unset: Sentinel) -> None:
        """Only the provided field is set; the rest remain UNSET."""
        vo = BuyerUpdateValueObject(name="Nuevo Nombre")

        assert vo.name == "Nuevo Nombre"
        assert vo.description is unset
        assert vo.contact_number is unset
        assert vo.contact_address is unset


class TestBuyerListQueryParamsValueObject:
    """BuyerListQueryParamsValueObject carries optional filters for listing buyers."""

    def test_defaults_to_unset(self, unset: Sentinel) -> None:
        """All filter fields default to UNSET."""
        params = BuyerListQueryParamsValueObject()

        assert params.name is unset
        assert params.contact_number is unset

    def test_with_name_filter(self, unset: Sentinel) -> None:
        """Only name is set."""
        params = BuyerListQueryParamsValueObject(name="Test")

        assert params.name == "Test"
        assert params.contact_number is unset
