from dataclasses import dataclass

from src.common.application.types import Sentinel


@dataclass
class UserCreationValueObject:
    name: str
    dni: str


@dataclass
class UserUpdateValueObject:
    name: str | type[Sentinel] = Sentinel
    password: str | type[Sentinel] = Sentinel
