"""subscriptions tenant_id unique index (one subscription per tenant)

Revision ID: dbde2e447abe
Revises: b8f2d6a9c4e7
Create Date: 2026-10-25 21:12:01.841895

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dbde2e447abe"
down_revision: Union[str, None] = "b8f2d6a9c4e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enforce one subscription per tenant with a unique index.

    Replaces the plain index on tenant_id; the table held no duplicates
    at migration time (verified), so the swap is safe.
    """
    op.drop_index("ix_subscriptions_tenant_id", table_name="subscriptions")
    op.create_index(
        "ix_subscriptions_tenant_id",
        "subscriptions",
        ["tenant_id"],
        unique=True,
    )


def downgrade() -> None:
    """Restore the plain (non-unique) index on tenant_id."""
    op.drop_index("ix_subscriptions_tenant_id", table_name="subscriptions")
    op.create_index("ix_subscriptions_tenant_id", "subscriptions", ["tenant_id"])
