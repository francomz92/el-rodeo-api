"""Row-to-entity builders for the finance repositories."""

from typing import cast

from sqlalchemy import RowMapping

from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity, SupplyTypeEntity
from src.finance.domain.entities.purchases import PurchaseEntity


def build_animal_supply_with_type(supply_data: RowMapping) -> AnimalSupplyEntity:
    """Build an AnimalSupplyEntity from an animal-supply row mapping.

    The mapping is expected to contain the AnimalSupply columns plus the
    outer-joined AnimalSupplyType columns (``type_id``/``type_name``).
    """
    return AnimalSupplyEntity(
        id=supply_data["id"],
        tenant_id=supply_data["tenant_id"],
        created_at=supply_data["created_at"],
        name=supply_data["name"],
        amount=supply_data["amount"],
        critical_amount=supply_data["critical_amount"],
        unit_of_measurement=supply_data["unit_of_measurement"],
        description=supply_data["description"],
        type=SupplyTypeEntity(
            id=supply_data["type_id"],
            name=supply_data["type_name"],
        ),
    )


def build_supply_type(supply_data: RowMapping) -> SupplyTypeEntity:
    """Build a SupplyTypeEntity from a SQLAlchemy RowMapping."""
    return SupplyTypeEntity(
        id=supply_data["id"],
        name=supply_data["name"],
    )


def build_purchase_with_supply(purchase_data: RowMapping) -> PurchaseEntity:
    """Build a PurchaseEntity from a purchase row mapping.

    The mapping is expected to contain the Purchase columns plus the
    outer-joined AnimalSupply columns (``supply_id``/``supply_name``).
    """
    return PurchaseEntity(
        id=purchase_data["id"],
        tenant_id=purchase_data["tenant_id"],
        amount=purchase_data["amount"],
        price=purchase_data["price"],
        purchase_date=purchase_data["purchase_date"],
        unit_price=purchase_data["unit_price"],
        unit_of_measurement=purchase_data["unit_of_measurement"],
        user_id=purchase_data["user_id"],
        user_name=cast(str, None),
        supply_id=purchase_data["supply_id"],
        supply_name=purchase_data["supply_name"],
        status=purchase_data["status"],
        confirmed_at=purchase_data["confirmed_at"],
        confirmed_by=purchase_data["confirmed_by"],
    )
