from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID

from src.cattle.domain.constants.animal import AnimalStatus
from src.common.domain.exceptions import BusinessValidationError

from .animal_entity import AnimalEntity


@dataclass
class AnimalProtocolEntity:
    id: UUID
    tenant_id: UUID
    animal: AnimalEntity
    vaccinated: bool
    vaccinated_date: date | None
    sale_permission: bool
    sale_permission_date: date | None

    def __post_init__(self) -> None:
        """Validate consistency at construction time."""
        self.validate_updated_dates(
            vaccinated=self.vaccinated,
            vaccinated_date=self.vaccinated_date,
            sale_permission=self.sale_permission,
            sale_permission_date=self.sale_permission_date,
        )

    def validate_updated_dates(
        self,
        vaccinated: bool,
        vaccinated_date: date | None,
        sale_permission: bool,
        sale_permission_date: date | None,
    ):
        if vaccinated_date and vaccinated_date > datetime.now(timezone.utc).date():
            raise BusinessValidationError(
                message="Fecha de vacunación inválida.",
                details=[
                    {
                        "field": "vaccinated_date",
                        "message": "La fecha de vacunación no puede ser posterior a la fecha actual.",
                    }
                ],
            )
        if vaccinated and not vaccinated_date:
            raise BusinessValidationError(
                message="Fecha de vacunación requerida.",
                details=[
                    {
                        "field": "vaccinated_date",
                        "message": "La fecha de vacunación es requerida cuando el animal está vacunado.",
                    }
                ],
            )
        # if not vaccinated and vaccinated_date:
        #     raise BusinessValidationError(
        #         message="La información de vacunación es inconsistente.",
        #         details=[
        #             {
        #                 "field": "vaccinated_date",
        #                 "message": "No puede proporcionar una fecha de vacunación para un animal no vacunado.",
        #             }
        #         ],
        #     )
        if sale_permission and not sale_permission_date:
            raise BusinessValidationError(
                message="Fecha de permiso de venta requerida.",
                details=[
                    {
                        "field": "sale_permission_date",
                        "message": "Debe ingresar una fecha para el permiso de venta aprobado.",
                    }
                ],
            )
        # if not sale_permission and sale_permission_date:
        #     raise BusinessValidationError(
        #         message="La información de permiso de venta es inconsistente.",
        #         details=[
        #             {
        #                 "field": "sale_permission_date",
        #                 "message": "No puede proporcionar una fecha de permiso de venta para un animal sin permiso.",
        #             }
        #         ],
        #     )

    def can_be_sold(self) -> bool:
        return all(
            (
                self.sale_permission,
                self.vaccinated,
                self.animal.status != AnimalStatus.SOLD,
            )
        )

    def can_update(self) -> bool:
        return self.animal.status != AnimalStatus.SOLD

    def can_delete(self) -> bool:
        return self.animal.status != AnimalStatus.SOLD
