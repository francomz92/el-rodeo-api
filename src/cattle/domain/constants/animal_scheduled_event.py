from enum import StrEnum


class AnimalEventType(StrEnum):
    VACCINATION = "vacunacion"
    AUCTION = "remate"
    MEETING = "reunion"
    VETERINARY = "veterinario"
    WEIGHING = "pesaje"
    TAGGING = "marcado"
    DEWORMING = "desparasitacion"
    TRANSPORT = "transporte"
    OTHER = "otro"
