from datetime import date
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, Relationship, mapped_column

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
    description: Mapped[str] = mapped_column(String(500), default_factory=str)

    user: Mapped["Users"] = Relationship(back_populates="sales")  # type: ignore
    buyer: Mapped["Buyers"] = Relationship(back_populates="purchases")  # type: ignore
    animal: Mapped["Animals"] = Relationship(back_populates="sales")  # type: ignore
