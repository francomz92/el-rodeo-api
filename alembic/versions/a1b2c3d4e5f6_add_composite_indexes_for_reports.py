"""Add composite indexes for report queries.

Adds ``ix_animals_tenant_status`` on ``animals(tenant_id, status)`` for
inventory summary queries, and ``ix_sales_tenant_sale_date`` on
``sales(tenant_id, sale_date)`` for sales summary date-range aggregations.

Revision ID: a1b2c3d4e5f6
Revises: 5fdb829b56a6
Create Date: 2026-07-23 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "5fdb829b56a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite index for inventory summary: WHERE tenant_id = ? GROUP BY status
    op.create_index(
        "ix_animals_tenant_status",
        "animals",
        ["tenant_id", "status"],
        unique=False,
    )
    # Composite index for sales summary: WHERE tenant_id = ? AND sale_date BETWEEN ?
    op.create_index(
        "ix_sales_tenant_sale_date",
        "sales",
        ["tenant_id", "sale_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_animals_tenant_status", table_name="animals")
    op.drop_index("ix_sales_tenant_sale_date", table_name="sales")
