"""add updated_at column to all application tables

Revision ID: 2d4a1c3b9e5f
Revises: ef6d4c2b8a1a
Create Date: 2026-06-26 10:00:00.000000

Adds updated_at TIMESTAMPTZ NOT NULL DEFAULT now() to every table whose
model inherits from the base Model (which now defines updated_at).

For the audit_log partitioned table, the column propagates to all
existing monthly partitions automatically (PG12+ behavior).

Backfills existing rows: updated_at = created_at for rows where
updated_at IS NULL (e.g., rows created before updated_at existed).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2d4a1c3b9e5f"
down_revision: Union[str, None] = "ef6d4c2b8a1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# All tables whose model inherits from Model (now has updated_at).
# Listed explicitly because some tables may have been created before
# updated_at was added to the base Model.
TABLES = [
    "animals",
    "animal_protocols",
    "animal_types",
    "scheduled_events",
    "animal_supplies",
    "animal_supply_types",
    "purchases",
    "buyers",
    "sales",
    "users",
    "tenants",
    "refresh_tokens",
    "audit_log",
]


def upgrade() -> None:
    conn = op.get_bind()

    for table in TABLES:
        # Add column if it doesn't exist
        conn.execute(
            sa.text(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = '{table}'
                        AND column_name = 'updated_at'
                    ) THEN
                        ALTER TABLE {table}
                        ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
                    END IF;
                END $$;
                """
            )
        )

        # Backfill: set updated_at = created_at for existing rows
        conn.execute(
            sa.text(
                f"""
                UPDATE {table}
                SET updated_at = created_at
                WHERE updated_at IS NULL
                """
            )
        )


def downgrade() -> None:
    for table in TABLES:
        conn = op.get_bind()
        conn.execute(
            sa.text(
                f"""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = '{table}'
                        AND column_name = 'updated_at'
                    ) THEN
                        ALTER TABLE {table} DROP COLUMN updated_at;
                    END IF;
                END $$;
                """
            )
        )
