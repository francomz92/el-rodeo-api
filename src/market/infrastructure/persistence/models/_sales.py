from datetime import date
from uuid import UUID

from sqlalchemy import Date, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.infrastructure.persistence.models.base import Model


class Sale(Model):
    __tablename__ = "sales"

    tenant_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    buyer_id: Mapped[UUID] = mapped_column(ForeignKey("buyers.id", ondelete="SET NULL"), index=True)
    animal_id: Mapped[UUID] = mapped_column(ForeignKey("animals.id", ondelete="CASCADE"), index=True)
    sale_date: Mapped[date] = mapped_column(Date)
    # TODO: Migrate these columns to Numeric (instead of Float) for full Decimal precision.
    #       Float works with Decimal via conversion but can introduce rounding errors
    #       in edge cases. Requires an Alembic migration.
    price: Mapped[float] = mapped_column(Float)
    price_per_kg: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String(500), default=str)

    user: Mapped["User"] = relationship()  # type: ignore  # noqa: F821
    buyer: Mapped["Buyer"] = relationship()  # type: ignore  # noqa: F821
    animal: Mapped["Animal"] = relationship()  # type: ignore # noqa: F821
