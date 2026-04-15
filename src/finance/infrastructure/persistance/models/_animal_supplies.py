from uuid import UUID

from sqlalchemy import (
    Float,
    ForeignKey,
    String,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, Relationship, mapped_column

from src.common.infrastructure.persistence.models import Model
from src.finance.domain.constatns.animal_supplies import UnitOfMeasurement


class AnimalSupplieType(Model):
    __tablename__ = "animal_supplie_types"

    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False, unique=True)


class AnimalSupplie(Model):
    __tablename__ = "animal_supplies"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type_id: Mapped[UUID] = mapped_column(ForeignKey("animals_supplie_types", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), default=str)
    amount: Mapped[float] = mapped_column(Float)
    critical_amount: Mapped[float] = mapped_column(Float)
    unit_of_measurement: Mapped[UnitOfMeasurement] = mapped_column(SQLEnum(UnitOfMeasurement))

    user: Mapped["Users"] = Relationship(back_populates="animal_supplies")  # type: ignore
    type: Mapped["AnimalSupplieType"] = Relationship(back_populates="animal_supplies")
