from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.common.utils.date_utils import get_current_datetime


class Model(DeclarativeBase):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_current_datetime)
