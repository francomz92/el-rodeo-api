from typing import Annotated

from fastapi import Depends

from src.common.infrastructure.persistence.uow import UnitOfWork

from .db import GetSession


def _get_uow(session_maker: GetSession) -> UnitOfWork:  # type: ignore[reportInvalidTypeForm]
    return UnitOfWork(session=session_maker)


GetUnitOfWork = Annotated[UnitOfWork, Depends(_get_uow)]
