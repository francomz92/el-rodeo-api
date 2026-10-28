from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.infrastructure.persistence.models.base import Model
from src.common.infrastructure.persistence.models.enum_types import values_enum
from src.finance.domain.constants.animal_supplies import UnitOfMeasurement
from src.finance.domain.constants.purchases import PurchaseStatus


class Purchase(Model):
    __tablename__ = "purchases"

    tenant_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    supply_id: Mapped[UUID] = mapped_column(ForeignKey("animal_supplies.id", ondelete="RESTRICT"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    purchase_date: Mapped[date] = mapped_column(Date)
    unit_price: Mapped[float] = mapped_column(Float)
    unit_of_measurement: Mapped[UnitOfMeasurement] = mapped_column(values_enum(UnitOfMeasurement))
    status: Mapped[PurchaseStatus] = mapped_column(
        values_enum(PurchaseStatus),
        nullable=False,
        default=PurchaseStatus.PENDING,
        # Native PG enum labels are the enum VALUES (backend-conventions-parity S6)
        server_default=PurchaseStatus.PENDING.value,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    user: Mapped["User | None"] = relationship(foreign_keys=[user_id])  # type: ignore  # noqa: F821
    supply: Mapped["AnimalSupply"] = relationship(foreign_keys=[supply_id])  # type: ignore  # noqa: F821
