"""Make business actor user_id columns nullable for GDPR offboarding.

Sets ``user_id`` nullable on seven business tables so controlled tenant
offboarding can unlink an account while keeping business rows and audit
history: ``sales``, ``purchases``, ``animals``, ``animal_protocols``,
``animal_supplies``, ``calendar_events`` and ``buyers``.

``calendar_event_participants.user_id`` intentionally stays NOT NULL because it
is part of the composite primary key; those association rows are deleted
instead of unlinked.

Revision ID: 3c7e91a4b6d2
Revises: ee522a9be72a
Create Date: 2026-09-20 10:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c7e91a4b6d2"
down_revision: Union[str, None] = "ee522a9be72a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Business tables whose ``user_id`` actor reference becomes nullable.
_UNLINKABLE_TABLES: tuple[str, ...] = (
    "sales",
    "purchases",
    "animals",
    "animal_protocols",
    "animal_supplies",
    "calendar_events",
    "buyers",
)


def upgrade() -> None:
    for table_name in _UNLINKABLE_TABLES:
        op.alter_column(
            table_name,
            "user_id",
            existing_type=sa.Uuid(),
            nullable=True,
        )


def downgrade() -> None:
    # Fail closed: never restore NOT NULL while unlinked rows exist.
    # Resolve those rows explicitly; this migration will not invent or reassign actors.
    bind = op.get_bind()
    tables_with_unlinked_rows = [
        table_name
        for table_name in _UNLINKABLE_TABLES
        if bind.execute(sa.text(f"SELECT 1 FROM {table_name} WHERE user_id IS NULL LIMIT 1")).first() is not None
    ]
    if tables_with_unlinked_rows:
        raise RuntimeError(
            "Cannot restore NOT NULL on business user_id columns: rows with NULL user_id exist in: "
            f"{', '.join(tables_with_unlinked_rows)}. "
            "Assign or remove those unlinked rows explicitly before downgrading; no actor will be invented or reassigned."
        )
    for table_name in _UNLINKABLE_TABLES:
        op.alter_column(
            table_name,
            "user_id",
            existing_type=sa.Uuid(),
            nullable=False,
        )
