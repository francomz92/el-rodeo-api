from src.common.application.ports.uow import IRepository, IUoW
from src.common.infrastructure.persistence.connections.db import AsyncSession

from .repositories import repositories_list


class UnitOfWork(IUoW):
    def __init__(self, session_maker: AsyncSession) -> None:
        self.session_maker = session_maker

    def get_repository(self, repository_type: type[IRepository]) -> IRepository:
        repository = repositories_list.get(repository_type, None)
        if not repository:
            raise ValueError(f"Repository of type {repository_type} not found.")
        return repository(self.db)  # type: ignore

    async def __aenter__(self):
        self.db: AsyncSession = self.session_maker
        return self

    async def __aexit__(self, exc_type, *args, **kwargs):
        if exc_type:
            await self.rollback()
        await self.dispose()

    async def commit(self):
        await self.db.commit()

    async def rollback(self):
        await self.db.rollback()

    async def refresh(self, entity):
        await self.db.refresh(entity)

    async def dispose(self):
        await self.db.close()
