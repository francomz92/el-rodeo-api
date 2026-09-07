"""Mapper functions for SalesRepository.

Builds SaleEntity from Sale table columns (no joins).
"""

from decimal import Decimal

from sqlalchemy import RowMapping

from src.market.domain.entities.sales import SaleEntity


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
