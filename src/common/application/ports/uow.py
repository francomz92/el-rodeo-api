from abc import ABC, abstractmethod

from .repository import IRepository, RepositoryType


class IUoW(ABC):
    @abstractmethod
    def get_repository(self, repository_type: RepositoryType) -> type[IRepository]:
        raise NotImplemented

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplemented

    @abstractmethod
    async def refresh(self, entity) -> None:
        raise NotImplemented

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplemented

    @abstractmethod
    async def dispose(self) -> None:
        raise NotImplemented
