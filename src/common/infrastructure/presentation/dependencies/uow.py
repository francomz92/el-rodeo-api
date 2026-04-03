from typing import Annotated

from fastapi import Depends

from src.common.application.ports.uow import IUoW
from src.common.infrastructure.persistence.connections.db import AsyncSessionMaker, async_sessionmaker
from src.common.infrastructure.persistence.uow import UnitOfWork


def _get_uow(
    session_maker: async_sessionmaker = Depends(lambda: AsyncSessionMaker),
) -> IUoW:
    return UnitOfWork(session_maker=session_maker)


GetUnitOfWork = Annotated[IUoW, Depends(_get_uow)]
