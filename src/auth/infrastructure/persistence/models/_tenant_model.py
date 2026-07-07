from uuid import UUID

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.common.infrastructure.persistence.models import Model


class Tenant(Model):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    plan_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=True,
    )
