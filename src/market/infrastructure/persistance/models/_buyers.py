from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, Relationship

from src.common.infrastructure.persistence.models import Model


class Buyer(Model):
    __tablename__ = "buyers"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), default=str)
    contact_number: Mapped[str] = mapped_column(String(10), default=str)
    contact_address: Mapped[str] = mapped_column(String(100), default=str)

    user: Mapped["User"] = Relationship()  # type: ignore  # noqa: F821
