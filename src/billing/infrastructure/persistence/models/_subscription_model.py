from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from src.common.infrastructure.persistence.models.base import Model


class Subscription(Model):
    __tablename__ = "subscriptions"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    subscription_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=True, default=dict)
    gateway_preference_id: Mapped[str | None] = mapped_column("mp_preference_id", VARCHAR(255), nullable=True, default=None)
    gateway_subscription_id: Mapped[str | None] = mapped_column("mp_subscription_id", VARCHAR(255), nullable=True, default=None)
    billing_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    next_billing_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    gateway_card_id: Mapped[str | None] = mapped_column("mp_card_id", VARCHAR(50), nullable=True, default=None)
