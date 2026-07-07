"""add user role column

Revision ID: a54adbe62ca3
Revises: fb63689e66f7
Create Date: 2026-06-23 07:00:35.442402

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a54adbe62ca3"
down_revision: Union[str, None] = "fb63689e66f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Add role column (nullable for migration, will be set NOT NULL after backfill)
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=True, server_default="viewer"),
    )

    # 2. Backfill: copy is_admin value to role (is_admin=True → admin, is_admin=False → viewer)
    conn.execute(sa.text("UPDATE users SET role = 'admin' WHERE is_admin = TRUE"))
    conn.execute(sa.text("UPDATE users SET role = 'viewer' WHERE is_admin = FALSE"))

    # 3. Set NOT NULL constraint
    op.alter_column("users", "role", existing_type=sa.String(20), nullable=False)

    # 4. Add CHECK constraint
    op.create_check_constraint("ck_users_role", "users", "role IN ('viewer', 'editor', 'admin', 'owner')")


def downgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
