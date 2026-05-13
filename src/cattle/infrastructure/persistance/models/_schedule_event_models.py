from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, Relationship

from src.common.infrastructure.persistence.models import Model


class ScheduledEvent(Model):
    __tablename__ = "scheduled_events"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(String(255))
    event_date: Mapped[date] = mapped_column(Date, index=True)
    pending: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = Relationship()  # type: ignore  # noqa: F821
