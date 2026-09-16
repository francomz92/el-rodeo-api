from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.auth.domain.entities._user_role import UserRole
from src.common.infrastructure.persistence.models.base import Model


class User(Model):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    dni: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        String(20),
        nullable=False,
        default=UserRole.VIEWER,
    )
    tenant_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    event_links: Mapped[list["CalendarEventParticipant"]] = relationship(  # type: ignore  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan",
    )

    events: Mapped[list["CalendarEvent"]] = relationship(  # type: ignore  # noqa: F821
        secondary="calendar_event_participants",
        back_populates="participants",
    )
