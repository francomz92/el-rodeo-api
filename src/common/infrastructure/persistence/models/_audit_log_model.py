from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, PrimaryKeyConstraint, String, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.common.infrastructure.persistence.models import Model
from src.common.utils.date_utils import get_current_datetime


class AuditLog(Model):
    """Partitioned audit log table for immutable CUD event tracking.

    Partitioned by RANGE on created_at (monthly) to support efficient
    data retention purges. The primary key includes created_at because
    PostgreSQL requires the partition key to be part of the PK.
    """

    __tablename__ = "audit_log"
    __table_args__ = (
        PrimaryKeyConstraint("id", "created_at"),
        Index("ix_audit_log_tenant_entity", "tenant_id", "entity_type", "entity_id"),
        Index("ix_audit_log_tenant_created_at", "tenant_id", text("created_at DESC")),
        Index("ix_audit_log_user_id", "user_id"),
        {
            "postgresql_partition_by": "RANGE (created_at)",
        },
    )

    # Override inherited id/created_at to control PK — composite PK
    # (id, created_at) is required for partitioning.
    id: Mapped[UUID] = mapped_column(
        Uuid,
        default=uuid4,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_current_datetime,
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    old_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
