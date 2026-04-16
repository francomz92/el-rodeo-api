from dataclasses import dataclass

from src.common.application.types import UNSET


@dataclass
class UserCreationDTO:
    name: str
    dni: str


@dataclass
class UserUpdateDTO:
    name: str | type[UNSET] = UNSET
    password: str | type[UNSET] = UNSET
