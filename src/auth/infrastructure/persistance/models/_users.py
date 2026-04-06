from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.common.infrastructure.persistence.models import Model


class User(Model):
    __tablename__ = "users"

    dni: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
