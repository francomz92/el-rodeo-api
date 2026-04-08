from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.common.infrastructure.persistence.models import Model


class User(Model):
    __tablename__ = "users"

    dni: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
