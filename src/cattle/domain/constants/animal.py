from enum import StrEnum


class AnimalStatus(StrEnum):
    READY = "disponible"
    NOT_READY = "no_disponible"
    SOLD = "vendido"
