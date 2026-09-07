from dataclasses import dataclass, field
from uuid import UUID

from src.common.domain.exceptions import BusinessValidationError
from src.common.domain.types import Sentinel


@dataclass
class BuyerListQueryParamsValueObject:
    name: str | Sentinel = Sentinel.UNSET
    contact_number: str | Sentinel = Sentinel.UNSET


@dataclass
class BuyerCreateValueObject:
    user_id: UUID
    name: str
    description: str = field(default_factory=str)
    contact_number: str = field(default_factory=str)
    contact_address: str = field(default_factory=str)

    def __post_init__(self) -> None:
        if len(self.contact_number) > 10:
            raise BusinessValidationError(
                message="El número de contacto no puede tener más de 10 caracteres.",
                details=[{"field": "contact_number", "message": f"Se encontraron {len(self.contact_number)} caracteres, máximo 10."}],
            )
        if len(self.contact_address) > 100:
            raise BusinessValidationError(
                message="La dirección de contacto no puede tener más de 100 caracteres.",
                details=[{"field": "contact_address", "message": f"Se encontraron {len(self.contact_address)} caracteres, máximo 100."}],
            )


@dataclass
class BuyerUpdateValueObject:
    name: str | Sentinel = Sentinel.UNSET
    description: str | Sentinel = Sentinel.UNSET
    contact_number: str | Sentinel = Sentinel.UNSET
    contact_address: str | Sentinel = Sentinel.UNSET
