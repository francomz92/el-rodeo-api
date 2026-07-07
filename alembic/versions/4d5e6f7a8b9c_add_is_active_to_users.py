"""add is_active column to users table

Revision ID: 4d5e6f7a8b9c
Revises: 2d4a1c3b9e5f
Create Date: 2026-06-26 12:00:00.000000

Adds is_active BOOLEAN NOT NULL DEFAULT TRUE to the users table.
The model already has this field (added in PR 3's updated_at migration),
but the actual column migration was missed — this fills that gap.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d5e6f7a8b9c"
down_revision: Union[str, None] = "2d4a1c3b9e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Add is_active column if it doesn't exist (idempotent guard)
    conn.execute(
        sa.text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'users'
                    AND column_name = 'is_active'
                ) THEN
                    ALTER TABLE users
                    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
                END IF;
            END $$;
        """)
    )


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'users'
                    AND column_name = 'is_active'
                ) THEN
                    ALTER TABLE users DROP COLUMN is_active;
                END IF;
            END $$;
        """)
    )
