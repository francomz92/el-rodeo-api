from dataclasses import dataclass

from src.common.domain.types import Sentinel


@dataclass
class UserCreationValueObject:
    name: str
    dni: str
    email: str


@dataclass
class UserUpdateValueObject:
    name: str | type[Sentinel] = Sentinel
    password: str | type[Sentinel] = Sentinel
