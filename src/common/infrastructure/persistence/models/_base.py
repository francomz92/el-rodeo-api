from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Uuid

from src.common.infrastructure.persistence.connections import db
from src.common.utils.date_utils import get_current_datetime


class Model(db.BaseDBModel):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_current_datetime)
