from uuid import UUID

from sqlalchemy import (
    Enum as SQLEnum,
    Float,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.infrastructure.persistence.models import Model
from src.finance.domain.constants.animal_supplies import UnitOfMeasurement


class AnimalSupplyType(Model):
    __tablename__ = "animal_supply_types"

    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False, unique=True)


class AnimalSupply(Model):
    __tablename__ = "animal_supplies"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type_id: Mapped[UUID] = mapped_column(ForeignKey("animal_supply_types.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), default=str)
    amount: Mapped[float] = mapped_column(Float)
    critical_amount: Mapped[float] = mapped_column(Float)
    unit_of_measurement: Mapped[UnitOfMeasurement] = mapped_column(SQLEnum(UnitOfMeasurement))

    user: Mapped["User"] = relationship()  # type: ignore  # noqa: F821
    type: Mapped["AnimalSupplyType"] = relationship()
