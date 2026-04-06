from abc import ABC, abstractmethod
from typing import TypeVar

from .repository import IRepository


RepositoryType = TypeVar("RepositoryType", bound=IRepository)


class IUoW(ABC):
    @abstractmethod
    async def __aenter__(self) -> "IUoW":
        """Método de entrada para el context manager asíncrono."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Método de salida para el context manager asíncrono."""
        pass

    @abstractmethod
    def get_repository(self, repository_type: type[RepositoryType]) -> RepositoryType:
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
