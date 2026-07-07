"""add multi-tenancy foundation

Revision ID: 26b6bc7b0176
Revises: f3079648712b
Create Date: 2026-06-22 04:59:31.908377

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "26b6bc7b0176"
down_revision: Union[str, None] = "f3079648712b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create tenants table
    op.create_table(
        "tenants",
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tenants_id"), "tenants", ["id"], unique=False)
    op.create_index(op.f("ix_tenants_name"), "tenants", ["name"], unique=False)
    op.create_index(op.f("ix_tenants_slug"), "tenants", ["slug"], unique=True)

    # 2. Add tenant_id to users (nullable for backfill phase)
    op.add_column(
        "users",
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
    )
    op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"], unique=False)

    # 3. Backfill: create a tenant for every existing user
    #    Use email prefix as slug placeholder (user can edit later).
    conn = op.get_bind()

    # Get existing users
    users = conn.execute(sa.text("SELECT id, name, email FROM users WHERE tenant_id IS NULL")).fetchall()

    for user_id, name, email in users:
        slug = email.split("@")[0] if email and "@" in email else "user"
        slug = slug.lower().replace(" ", "-").replace(".", "-").replace("_", "-")[:90]

        # Insert tenant
        tenant_id = conn.execute(
            sa.text("INSERT INTO tenants (id, name, slug, created_at) VALUES (gen_random_uuid(), :name, :slug, NOW()) RETURNING id"),
            {"name": name, "slug": slug},
        ).scalar_one()

        # Update user's tenant_id
        conn.execute(
            sa.text("UPDATE users SET tenant_id = :tid WHERE id = :uid"),
            {"tid": tenant_id, "uid": user_id},
        )

    # 4. Add FK constraint
    op.create_foreign_key(
        "fk_users_tenant_id",
        "users",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_tenant_id", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_tenant_id"), table_name="users")
    op.drop_column("users", "tenant_id")
    op.drop_index(op.f("ix_tenants_slug"), table_name="tenants")
    op.drop_index(op.f("ix_tenants_name"), table_name="tenants")
    op.drop_index(op.f("ix_tenants_id"), table_name="tenants")
    op.drop_table("tenants")
