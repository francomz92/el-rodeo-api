from datetime import date
from uuid import UUID

from sqlalchemy import (
    Float,
    ForeignKey,
    String,
    Date,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, Relationship, mapped_column

from src.cattle.domain.constants.animal import AnimalStatus
from src.common.infrastructure.persistence.models import Model


class AnimalType(Model):
    __tablename__ = "animal_types"

    name: Mapped[str] = mapped_column(String(50), index=True, unique=True)

    animals: Mapped[list["Animal"]] = Relationship(back_populates="type")


class Animal(Model):
    __tablename__ = "animals"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type_id: Mapped[UUID] = mapped_column(ForeignKey("animal_types.id", ondelete="SET NULL"), nullable=True)
    caravana: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    tag: Mapped[str] = mapped_column(String(50), default=str)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    initial_weight: Mapped[float] = mapped_column(Float)
    initial_weight_date: Mapped[date] = mapped_column(Date)
    last_weight: Mapped[float] = mapped_column(Float)
    breed: Mapped[str] = mapped_column(String(50))
    status: Mapped[AnimalStatus] = mapped_column(SQLEnum(AnimalStatus), index=True)

    user: Mapped["User"] = Relationship(back_populates="animals")  # type: ignore
    type: Mapped["AnimalType"] = Relationship(back_populates="animals")
