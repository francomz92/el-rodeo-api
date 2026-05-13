from typing import Annotated

from fastapi import Depends

from src.common.application.ports.uow import IUoW
from src.common.infrastructure.persistence.uow import UnitOfWork

from .db import GetSession


def _get_uow(session_maker: GetSession) -> IUoW:
    return UnitOfWork(session=session_maker)


GetUnitOfWork = Annotated[IUoW, Depends(_get_uow)]
