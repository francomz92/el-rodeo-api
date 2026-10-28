from typing import Annotated

from fastapi import Depends

from src.cattle.application.uses_cases.animal_cases.delete_animal_case import DeleteAnimalCase
from src.cattle.application.uses_cases.animal_cases.get_animal_case import ObtainAnimalCase
from src.cattle.application.uses_cases.animal_cases.list_animals_case import ListAnimalsCase
from src.cattle.application.uses_cases.animal_cases.register_animal_case import RegisterAnimalCase
from src.cattle.application.uses_cases.animal_cases.update_animal_case import UpdateAnimalCase
from src.cattle.domain.services.animal_protocol_services.create_animal_protocol_service import CreateAnimalProtocolService
from src.cattle.domain.services.animal_services.delete_animal_service import DeleteAnimalService
from src.cattle.domain.services.animal_services.get_animal_service import GetAnimalService
from src.cattle.domain.services.animal_services.list_animal_service import ListAnimalService
from src.cattle.domain.services.animal_services.register_animal_service import RegisterAnimalService
from src.cattle.domain.services.animal_services.update_animal_service import UpdateAnimalService
from src.cattle.infrastructure.events.handlers.cache_invalidation import (
    AnimalCacheInvalidationHandler,
)
from src.common.domain.ports.event_bus import IEventBus
from src.common.infrastructure.events.handlers.ws_broadcast import (
    WebSocketBroadcastHandler,
)
from src.common.infrastructure.presentation.dependencies.cache import GetCacheService
from src.common.infrastructure.presentation.dependencies.event_bus import GetEventBus
from src.common.infrastructure.presentation.dependencies.redis import GetRedisClient
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_event_bus(
    bus: GetEventBus,
    cache_service: GetCacheService,
    redis_client: GetRedisClient,
) -> IEventBus:
    """Decorate the request-scoped event bus with cattle handlers."""
    bus.register("*", WebSocketBroadcastHandler(redis_client))
    bus.register("animal.created", AnimalCacheInvalidationHandler(cache_service))
    bus.register("animal.updated", AnimalCacheInvalidationHandler(cache_service))
    bus.register("animal.deleted", AnimalCacheInvalidationHandler(cache_service))
    return bus


GetAnimalEventBus = Annotated[IEventBus, Depends(_get_event_bus)]


def _get_register_animals_case(
    uow: GetUnitOfWork,
    service: Annotated[RegisterAnimalService, Depends()],
    create_animal_protocol_service: Annotated[
        CreateAnimalProtocolService,
        Depends(),
    ],
    event_bus: GetAnimalEventBus,
) -> RegisterAnimalCase:
    return RegisterAnimalCase(
        uow=uow,
        service=service,
        create_animal_protocol_service=create_animal_protocol_service,
        event_bus=event_bus,
    )


def _get_update_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[UpdateAnimalService, Depends()],
    event_bus: GetAnimalEventBus,
) -> UpdateAnimalCase:
    return UpdateAnimalCase(uow=uow, service=service, event_bus=event_bus)


def _get_delete_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[DeleteAnimalService, Depends()],
    event_bus: GetAnimalEventBus,
) -> DeleteAnimalCase:
    return DeleteAnimalCase(uow=uow, service=service, event_bus=event_bus)


def _get_list_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[ListAnimalService, Depends()],
) -> ListAnimalsCase:
    return ListAnimalsCase(uow=uow, service=service)


def _get_obtain_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[GetAnimalService, Depends()],
) -> ObtainAnimalCase:
    return ObtainAnimalCase(uow, service)


GetRegisterAnimalCase = Annotated[RegisterAnimalCase, Depends(_get_register_animals_case)]
GetUpdateAnimalCase = Annotated[UpdateAnimalCase, Depends(_get_update_animal_case)]
GetDeleteAnimalCase = Annotated[DeleteAnimalCase, Depends(_get_delete_animal_case)]
GetListAnimalsCase = Annotated[ListAnimalsCase, Depends(_get_list_animal_case)]
GetObtainAnimalCase = Annotated[ObtainAnimalCase, Depends(_get_obtain_animal_case)]
