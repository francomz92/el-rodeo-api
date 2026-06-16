from datetime import date
from uuid import UUID

from sqlalchemy import (
    Date,
    Enum as SQLEnum,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.infrastructure.persistence.models import Model
from src.finance.domain.constants.animal_supplies import UnitOfMeasurement


class Purchase(Model):
    __tablename__ = "purchases"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    supply_id: Mapped[UUID] = mapped_column(ForeignKey("animal_supplies.id", ondelete="RESTRICT"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    purchase_date: Mapped[date] = mapped_column(Date)
    unit_price: Mapped[float] = mapped_column(Float)
    unit_of_measurement: Mapped[UnitOfMeasurement] = mapped_column(SQLEnum(UnitOfMeasurement))

    user: Mapped["User"] = relationship()  # type: ignore  # noqa: F821
    supply: Mapped["AnimalSupply"] = relationship()  # type: ignore  # noqa: F821
