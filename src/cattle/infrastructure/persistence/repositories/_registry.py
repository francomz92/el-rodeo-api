from src.cattle.infrastructure.persistence.repositories.animal_protocol_repository import (
    AnimalProtocolsRepository,
    IAnimalProtocolsRepository,
)
from src.cattle.infrastructure.persistence.repositories.animal_repository import (
    AnimalRepository,
    IAnimalsRepository,
)
from src.cattle.infrastructure.persistence.repositories.animal_type_repository import (
    AnimalTypeRepository,
    IAnimalTypesRepository,
)
from src.cattle.infrastructure.persistence.repositories.schedule_event_repository import (
    IScheduleEventRepository,
    ScheduleEventRepository,
)
from src.common.domain.repository import IRepository

repositories_list: dict[type[IRepository], type[IRepository]] = {
    IAnimalsRepository: AnimalRepository,
    IAnimalTypesRepository: AnimalTypeRepository,
    IScheduleEventRepository: ScheduleEventRepository,
    IAnimalProtocolsRepository: AnimalProtocolsRepository,
}
