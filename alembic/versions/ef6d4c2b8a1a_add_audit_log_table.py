"""add_audit_log_table

Revision ID: ef6d4c2b8a1a
Revises: c094cf8c4003
Create Date: 2026-06-25 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ef6d4c2b8a1a"
down_revision: Union[str, None] = "c094cf8c4003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create partitioned audit_log table
    op.execute(
        sa.text("""
            CREATE TABLE audit_log (
                id UUID NOT NULL,
                tenant_id UUID,
                user_id UUID,
                action VARCHAR(20) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id UUID NOT NULL,
                old_values JSONB,
                new_values JSONB,
                ip_address VARCHAR(45),
                metadata JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, created_at)
            ) PARTITION BY RANGE (created_at)
        """)
    )

    # 2. Create initial monthly partitions
    #    Past catch-all + current month + 11 future months = 13 partitions
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_past PARTITION OF audit_log
            FOR VALUES FROM (MINVALUE) TO ('2026-06-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2026_06 PARTITION OF audit_log
            FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2026_07 PARTITION OF audit_log
            FOR VALUES FROM ('2026-07-01') TO ('2026-08-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2026_08 PARTITION OF audit_log
            FOR VALUES FROM ('2026-08-01') TO ('2026-09-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2026_09 PARTITION OF audit_log
            FOR VALUES FROM ('2026-09-01') TO ('2026-10-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2026_10 PARTITION OF audit_log
            FOR VALUES FROM ('2026-10-01') TO ('2026-11-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2026_11 PARTITION OF audit_log
            FOR VALUES FROM ('2026-11-01') TO ('2026-12-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2026_12 PARTITION OF audit_log
            FOR VALUES FROM ('2026-12-01') TO ('2027-01-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2027_01 PARTITION OF audit_log
            FOR VALUES FROM ('2027-01-01') TO ('2027-02-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2027_02 PARTITION OF audit_log
            FOR VALUES FROM ('2027-02-01') TO ('2027-03-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2027_03 PARTITION OF audit_log
            FOR VALUES FROM ('2027-03-01') TO ('2027-04-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2027_04 PARTITION OF audit_log
            FOR VALUES FROM ('2027-04-01') TO ('2027-05-01')
        """)
    )
    op.execute(
        sa.text("""
            CREATE TABLE audit_log_2027_05 PARTITION OF audit_log
            FOR VALUES FROM ('2027-05-01') TO ('2027-06-01')
        """)
    )

    # 3. Create indexes
    op.create_index(
        "ix_audit_log_tenant_entity",
        "audit_log",
        ["tenant_id", "entity_type", "entity_id"],
    )
    op.execute(sa.text("CREATE INDEX ix_audit_log_tenant_created_at ON audit_log (tenant_id, created_at DESC)"))
    op.create_index(
        "ix_audit_log_user_id",
        "audit_log",
        ["user_id"],
    )

    # 4. Add foreign key constraints
    op.create_foreign_key(
        "fk_audit_log_tenant_id",
        "audit_log",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_audit_log_user_id",
        "audit_log",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Drop FKs first, then indexes, then table (cascades to partitions)
    op.drop_constraint("fk_audit_log_user_id", "audit_log", type_="foreignkey")
    op.drop_constraint("fk_audit_log_tenant_id", "audit_log", type_="foreignkey")
    op.drop_index("ix_audit_log_user_id", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_entity", table_name="audit_log")
    op.drop_table("audit_log")
