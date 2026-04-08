from enum import Enum


class AnimalStatus(Enum, str):
    AVAILABLE = "disponible"
    UNAVAILABLE = "no_disponible"
    SOLD = "vendido"
