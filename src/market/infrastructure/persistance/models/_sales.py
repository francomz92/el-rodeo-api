from datetime import date
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, Relationship

from src.common.infrastructure.persistence.models import Model


class Sale(Model):
    __tablename__ = "sales"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    buyer_id: Mapped[UUID] = mapped_column(ForeignKey("buyers.id", ondelete="SET NULL"), index=True)
    animal_id: Mapped[UUID] = mapped_column(ForeignKey("animals.id", ondelete="CASCADE"), index=True)
    sale_date: Mapped[date] = mapped_column(DateTime)
    price: Mapped[float] = mapped_column(Float)
    price_per_kg: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String(500), default=str)

    user: Mapped["User"] = Relationship()  # type: ignore  # noqa: F821
    buyer: Mapped["Buyer"] = Relationship()  # type: ignore  # noqa: F821
    animal: Mapped["Animal"] = Relationship()  # type: ignore # noqa: F821
