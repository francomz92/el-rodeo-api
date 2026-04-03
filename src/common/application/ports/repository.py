from abc import ABC
from enum import Enum


class IRepository(ABC): ...


class RepositoryType(str, Enum):
    pass
