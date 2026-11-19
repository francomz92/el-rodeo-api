from typing import Annotated

from fastapi import Depends

from src.common.application.ports.uow import IUoWFactory
from src.common.infrastructure.persistence.uow import UnitOfWork, UnitOfWorkFactory
from src.common.infrastructure.presentation.dependencies.db import GetSession


def _get_uow(session: GetSession) -> UnitOfWork:  # type: ignore[reportInvalidTypeForm]
    return UnitOfWork(session=session)


def _get_uow_factory() -> IUoWFactory:
    return UnitOfWorkFactory()


GetUnitOfWork = Annotated[UnitOfWork, Depends(_get_uow)]
GetUoWFactory = Annotated[IUoWFactory, Depends(_get_uow_factory)]
