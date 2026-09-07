from uuid import UUID

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.infrastructure.persistence.models.base import Model


class Buyer(Model):
    __tablename__ = "buyers"

    tenant_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    contact_number: Mapped[str] = mapped_column(String(10), default="")
    contact_address: Mapped[str] = mapped_column(String(100), default="")

    user: Mapped["User"] = relationship()  # type: ignore  # noqa: F821
