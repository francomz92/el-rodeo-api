"""Row-to-entity builders for the market repositories."""

from decimal import Decimal

from sqlalchemy import RowMapping

from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.entities.sales import SaleEntity


def build_buyer(buyer_data: RowMapping) -> BuyerEntity:
    """Build a BuyerEntity from a SQLAlchemy RowMapping."""
    return BuyerEntity(
        id=buyer_data["id"],
        tenant_id=buyer_data["tenant_id"],
        created_at=buyer_data["created_at"],
        name=buyer_data["name"],
        description=buyer_data["description"],
        contact_number=buyer_data["contact_number"],
        contact_address=buyer_data["contact_address"],
    )


def build_sale(sale_data: RowMapping) -> SaleEntity:
    """Build a SaleEntity from a SQLAlchemy RowMapping (Sale columns only)."""
    return SaleEntity(
        id=sale_data["id"],
        tenant_id=sale_data["tenant_id"],
        sale_date=sale_data["sale_date"],
        price=Decimal(str(sale_data["price"])),
        price_per_kg=Decimal(str(sale_data["price_per_kg"])),
        weight=sale_data["weight"],
        description=sale_data["description"],
        buyer_id=sale_data["buyer_id"],
        animal_id=sale_data["animal_id"],
        created_at=sale_data.get("created_at"),
    )
