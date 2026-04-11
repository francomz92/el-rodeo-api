from datetime import date
from uuid import UUID

from sqlalchemy import (
    Date,
    Float,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, Relationship, mapped_column

from src.common.infrastructure.persistence.models import Model
from src.finance.domain.constatns.animal_supplies import UnitOfMeasurement


class Purchase(Model):
    __tablename__ = "purchases"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    supplie_id: Mapped[UUID] = mapped_column(ForeignKey("animal_supplies.id", ondelete="SET NULL"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    purchase_date: Mapped[date] = mapped_column(Date)
    unit_price: Mapped[float] = mapped_column(Float)
    unit_of_measurement: Mapped[UnitOfMeasurement] = mapped_column(SQLEnum(UnitOfMeasurement))

    user: Mapped["Users"] = Relationship(back_populates="purchases")  # type: ignore
    supplie: Mapped["AnimalSupplies"] = Relationship(back_populates="purchases")  # type: ignore
