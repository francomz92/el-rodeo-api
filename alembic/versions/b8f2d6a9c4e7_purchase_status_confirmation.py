"""Purchase confirmation lifecycle: stock moves only when confirming.

Adds ``status`` (``PENDING``/``CONFIRMED``), ``confirmed_at`` and
``confirmed_by`` to ``purchases``. Legacy rows are marked ``CONFIRMED``
because their stock was already summed under the old behaviour
(create used to increase stock immediately); new purchases start as
``PENDING`` and only a confirm action adds stock.

Revision ID: b8f2d6a9c4e7
Revises: 3c7e91a4b6d2
Create Date: 2026-10-23 10:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b8f2d6a9c4e7"
down_revision: Union[str, None] = "3c7e91a4b6d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS_ENUM = postgresql.ENUM("PENDING", "CONFIRMED", name="purchasestatus")


def upgrade() -> None:
    _STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    op.add_column("purchases", sa.Column("status", _STATUS_ENUM, nullable=True))
    op.add_column(
        "purchases",
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("purchases", sa.Column("confirmed_by", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_purchases_confirmed_by_users",
        "purchases",
        "users",
        ["confirmed_by"],
        ["id"],
        ondelete="CASCADE",
    )
    # Legacy purchases already added their stock on creation: mark them confirmed.
    op.execute("UPDATE purchases SET status = 'CONFIRMED' WHERE status IS NULL")
    op.alter_column(
        "purchases",
        "status",
        existing_type=_STATUS_ENUM,
        nullable=False,
        server_default=sa.text("'PENDING'"),
    )


def downgrade() -> None:
    # Confirmation history is lost by design when downgrading.
    op.drop_constraint("fk_purchases_confirmed_by_users", "purchases", type_="foreignkey")
    op.drop_column("purchases", "confirmed_by")
    op.drop_column("purchases", "confirmed_at")
    op.drop_column("purchases", "status")
    _STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
