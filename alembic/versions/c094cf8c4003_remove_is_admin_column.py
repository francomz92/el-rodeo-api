"""remove_is_admin_column

Revision ID: c094cf8c4003
Revises: a54adbe62ca3
Create Date: 2026-06-24 07:32:39.358375

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c094cf8c4003"
down_revision: Union[str, None] = "a54adbe62ca3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Backfill: is_admin=True → role='super_admin' (overwrites existing role)
    conn.execute(sa.text("UPDATE users SET role = 'super_admin' WHERE is_admin = TRUE"))

    # 2. Update CHECK constraint to include super_admin
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('viewer', 'editor', 'admin', 'owner', 'super_admin')",
    )

    # 3. Drop is_admin column
    op.drop_column("users", "is_admin")


def downgrade() -> None:
    conn = op.get_bind()

    # 1. Recreate is_admin column
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.alter_column("users", "is_admin", server_default=None)

    # 2. Backfill: role='super_admin' → is_admin=True
    conn.execute(sa.text("UPDATE users SET is_admin = TRUE WHERE role = 'super_admin'"))

    # 3. Restore original CHECK constraint (without super_admin)
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('viewer', 'editor', 'admin', 'owner')",
    )
