"""WebhookSubscription SQLAlchemy model for tenant webhook forwarding."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.common.infrastructure.persistence.models import Model


class WebhookSubscription(Model):
    """Tenant-scoped webhook subscription for forwarding domain events."""

    __tablename__ = "webhook_subscriptions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(100), nullable=False)
    subscribed_events: Mapped[list[str]] = mapped_column(ARRAY(String(100)), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
