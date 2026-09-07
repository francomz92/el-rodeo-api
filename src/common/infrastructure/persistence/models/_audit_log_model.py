from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.common.infrastructure.persistence.models.base import Model
from src.common.utils.date_utils import get_current_datetime


class AuditLog(Model):
    """Immutable audit log table for CUD event tracking.

    Data retention uses batch DELETE via the purge task
    (``retention_purge`` module) rather than partition DROP.
    """

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_tenant_entity", "tenant_id", "entity_type", "entity_id"),
        Index("ix_audit_log_tenant_created_at", "tenant_id", text("created_at DESC")),
        Index("ix_audit_log_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_current_datetime,
        index=True,
    )
    # Override base Model.updated_at to remove onupdate — AuditLog is
    # immutable and should never silently set updated_at on UPDATE.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_current_datetime,
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("tenants.id", ondelete="SET NULL"),
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
