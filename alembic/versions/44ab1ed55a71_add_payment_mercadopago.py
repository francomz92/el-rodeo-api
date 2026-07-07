"""add MercadoPago payments table, subscription columns, and seed prices

Revision ID: 44ab1ed55a71
Revises: 7a5e3f1d2c8b
Create Date: 2026-06-30 11:49:46.470134

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "44ab1ed55a71"
down_revision: Union[str, None] = "7a5e3f1d2c8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create payments table
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("subscription_id", sa.Uuid(), nullable=False),
        sa.Column("mp_payment_id", sa.String(), nullable=True),
        sa.Column("mp_preference_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="ARS"),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("payment_method", sa.String(), nullable=True),
        sa.Column("installments", sa.Integer(), nullable=True),
        sa.Column(
            "paid_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mp_payment_id"),
    )
    op.create_index(op.f("ix_payments_id"), "payments", ["id"], unique=False)
    op.create_index(op.f("ix_payments_tenant_id"), "payments", ["tenant_id"], unique=False)
    op.create_index(
        op.f("ix_payments_subscription_id"),
        "payments",
        ["subscription_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_payments_tenant_id",
        "payments",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_payments_subscription_id",
        "payments",
        "subscriptions",
        ["subscription_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 2. Add MercadoPago columns to subscriptions
    op.add_column(
        "subscriptions",
        sa.Column("mp_preference_id", sa.String(), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("mp_subscription_id", sa.String(), nullable=True),
    )

    # 3. Update plan seed prices
    op.execute(
        sa.text(
            """
            UPDATE plans SET
                price_monthly = 0.00,
                price_yearly = NULL
            WHERE plan_type = 'free'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE plans SET
                price_monthly = 15.00,
                price_yearly = 150.00
            WHERE plan_type = 'pro'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE plans SET
                price_monthly = 50.00,
                price_yearly = 500.00
            WHERE plan_type = 'enterprise'
            """
        )
    )


def downgrade() -> None:
    # 1. Revert plan prices to original seed values
    op.execute(
        sa.text(
            """
            UPDATE plans SET
                price_monthly = NULL,
                price_yearly = NULL
            WHERE plan_type = 'free'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE plans SET
                price_monthly = 29.99,
                price_yearly = 299.99
            WHERE plan_type = 'pro'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE plans SET
                price_monthly = 99.99,
                price_yearly = 999.99
            WHERE plan_type = 'enterprise'
            """
        )
    )

    # 2. Drop MercadoPago columns from subscriptions
    op.drop_column("subscriptions", "mp_subscription_id")
    op.drop_column("subscriptions", "mp_preference_id")

    # 3. Drop payments table
    op.drop_constraint("fk_payments_subscription_id", "payments", type_="foreignkey")
    op.drop_constraint("fk_payments_tenant_id", "payments", type_="foreignkey")
    op.drop_index(op.f("ix_payments_subscription_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_tenant_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_id"), table_name="payments")
    op.drop_table("payments")
