from datetime import date
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.cattle.domain.constants.animal import AnimalStatus
from src.common.infrastructure.persistence.models import Model


class AnimalType(Model):
    __tablename__ = "animal_types"

    name: Mapped[str] = mapped_column(String(50), index=True, unique=True)

    animals: Mapped[list["Animal"]] = relationship(back_populates="type")


class Animal(Model):
    __tablename__ = "animals"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type_id: Mapped[UUID] = mapped_column(ForeignKey("animal_types.id", ondelete="SET NULL"), nullable=True)
    caravana: Mapped[str] = mapped_column(String(50), unique=True)
    tag: Mapped[str] = mapped_column(String(50), default=str)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    initial_weight: Mapped[float] = mapped_column(Float)
    initial_weight_date: Mapped[date] = mapped_column(Date)
    last_weight: Mapped[float] = mapped_column(Float)
    breed: Mapped[str] = mapped_column(String(50))
    status: Mapped[AnimalStatus] = mapped_column(SQLEnum(AnimalStatus), index=True)

    user: Mapped["User"] = relationship()  # type: ignore  # noqa: F821
    type: Mapped["AnimalType"] = relationship(back_populates="animals")


class AnimalProtocols(Model):
    __tablename__ = "animal_protocols"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    animal_id: Mapped[UUID] = mapped_column(ForeignKey("animals.id", ondelete="CASCADE"))
    vaccinated: Mapped[bool] = mapped_column(Boolean, default=False)
    vaccinated_date: Mapped[date] = mapped_column(Date, nullable=True)
    sale_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    sale_permission_date: Mapped[date] = mapped_column(Date, nullable=True)

    animal: Mapped[Animal] = relationship()
