"""add billing models — plans, subscriptions, plan_id on tenants

Revision ID: 7a5e3f1d2c8b
Revises: 4d5e6f7a8b9c
Create Date: 2026-06-26 15:13:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7a5e3f1d2c8b"
down_revision: Union[str, None] = "4d5e6f7a8b9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create plans table
    op.create_table(
        "plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "plan_type",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("features", postgresql.JSONB(), nullable=True),
        sa.Column("quotas", postgresql.JSONB(), nullable=True),
        sa.Column(
            "price_monthly",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "price_yearly",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="t"),
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
        sa.UniqueConstraint("plan_type"),
    )
    op.create_index(op.f("ix_plans_id"), "plans", ["id"], unique=False)

    # 2. Seed FREE plan
    op.execute(
        sa.text(
            """
            INSERT INTO plans (id, plan_type, name, description, features, quotas,
                               price_monthly, price_yearly, is_active)
            VALUES (gen_random_uuid(), 'free', 'Free', 'Free tier — para pequeños productores',
                    '[]'::jsonb,
                    '[]'::jsonb,
                    NULL, NULL, TRUE)
            """
        )
    )

    # 3. Seed PRO plan
    op.execute(
        sa.text(
            """
            INSERT INTO plans (id, plan_type, name, description, features, quotas,
                               price_monthly, price_yearly, is_active)
            VALUES (gen_random_uuid(), 'pro', 'Pro', 'Plan profesional para medianos productores',
                    '[]'::jsonb,
                    '[]'::jsonb,
                    29.99, 299.99, TRUE)
            """
        )
    )

    # 4. Seed ENTERPRISE plan
    op.execute(
        sa.text(
            """
            INSERT INTO plans (id, plan_type, name, description, features, quotas,
                               price_monthly, price_yearly, is_active)
            VALUES (gen_random_uuid(), 'enterprise', 'Enterprise',
                    'Plan empresarial — acceso completo',
                    '[]'::jsonb,
                    '[]'::jsonb,
                    99.99, 999.99, TRUE)
            """
        )
    )

    # 5. Create subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "current_period_start",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "current_period_end",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "trial_end",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "canceled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index(op.f("ix_subscriptions_id"), "subscriptions", ["id"], unique=False)
    op.create_index(
        op.f("ix_subscriptions_tenant_id"),
        "subscriptions",
        ["tenant_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_subscriptions_tenant_id",
        "subscriptions",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_subscriptions_plan_id",
        "subscriptions",
        "plans",
        ["plan_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # 6. Add plan_id to tenants
    op.add_column(
        "tenants",
        sa.Column("plan_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_tenants_plan_id",
        "tenants",
        "plans",
        ["plan_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # 7. Backfill: create FREE subscription for existing tenants
    conn = op.get_bind()

    # Get the FREE plan ID
    free_plan = conn.execute(sa.text("SELECT id FROM plans WHERE plan_type = 'free'")).fetchone()
    if free_plan:
        free_plan_id = free_plan[0]
        tenants = conn.execute(sa.text("SELECT id FROM tenants WHERE plan_id IS NULL")).fetchall()

        for (tenant_id,) in tenants:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO subscriptions (id, tenant_id, plan_id, status,
                                               current_period_start, current_period_end,
                                               metadata)
                    VALUES (gen_random_uuid(), :tid, :pid, 'active',
                            NOW(), NULL, '{}'::jsonb)
                    """
                ),
                {"tid": tenant_id, "pid": free_plan_id},
            )
            conn.execute(
                sa.text("UPDATE tenants SET plan_id = :pid WHERE id = :tid"),
                {"pid": free_plan_id, "tid": tenant_id},
            )


def downgrade() -> None:
    # Remove FK constraints
    op.drop_constraint("fk_tenants_plan_id", "tenants", type_="foreignkey")
    op.drop_column("tenants", "plan_id")

    op.drop_constraint("fk_subscriptions_plan_id", "subscriptions", type_="foreignkey")
    op.drop_constraint("fk_subscriptions_tenant_id", "subscriptions", type_="foreignkey")
    op.drop_index(op.f("ix_subscriptions_tenant_id"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_id"), table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index(op.f("ix_plans_id"), table_name="plans")
    op.drop_table("plans")
