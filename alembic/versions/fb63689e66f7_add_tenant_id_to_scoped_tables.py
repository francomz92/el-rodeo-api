"""add tenant_id to all tenant-scoped tables

Revision ID: fb63689e66f7
Revises: 26b6bc7b0176
Create Date: 2026-06-23 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fb63689e66f7"
down_revision: Union[str, None] = "26b6bc7b0176"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables that need tenant_id added (all have user_id FK → users.id → users.tenant_id)
TENANT_SCOPED_TABLES = [
    "animals",
    "animal_protocols",
    "scheduled_events",
    "animal_supplies",
    "purchases",
    "buyers",
    "sales",
]


def upgrade() -> None:
    conn = op.get_bind()

    for table in TENANT_SCOPED_TABLES:
        # 1. Add tenant_id as nullable
        op.add_column(
            table,
            sa.Column("tenant_id", sa.Uuid(), nullable=True),
        )

        # 2. Backfill: copy tenant_id from the owning user
        conn.execute(
            sa.text(
                f"""
                UPDATE {table}
                SET tenant_id = u.tenant_id
                FROM users u
                WHERE {table}.user_id = u.id
                """
            )
        )

        # 3. Set NOT NULL
        op.alter_column(table, "tenant_id", nullable=False)

        # 4. Add FK constraint
        op.create_foreign_key(
            f"fk_{table}_tenant_id",
            table,
            "tenants",
            ["tenant_id"],
            ["id"],
            ondelete="CASCADE",
        )

        # 5. Add index
        op.create_index(
            op.f(f"ix_{table}_tenant_id"),
            table,
            ["tenant_id"],
            unique=False,
        )


def downgrade() -> None:
    for table in reversed(TENANT_SCOPED_TABLES):
        op.drop_index(op.f(f"ix_{table}_tenant_id"), table_name=table)
        op.drop_constraint(f"fk_{table}_tenant_id", table, type_="foreignkey")
        op.drop_column(table, "tenant_id")
