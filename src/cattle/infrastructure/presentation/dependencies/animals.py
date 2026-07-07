from typing import Annotated

from fastapi import Depends

from src.cattle.application.uses_cases.animals_use_cases.delete_animal_case import DeleteAnimalCase
from src.cattle.application.uses_cases.animals_use_cases.get_animal_case import ObtainAnimalCase
from src.cattle.application.uses_cases.animals_use_cases.list_animals_case import ListAnimalsCase
from src.cattle.application.uses_cases.animals_use_cases.register_animal_case import RegisterAnimalCase
from src.cattle.application.uses_cases.animals_use_cases.update_animal_case import UpdateAnimalCase
from src.cattle.domain.services.animal_protocols.create_animal_protocol_service import CreateAnimalProtocolService
from src.cattle.domain.services.animals.delete_animal_service import DeleteAnimalService
from src.cattle.domain.services.animals.get_animal_service import GetAnimalService
from src.cattle.domain.services.animals.list_animal_service import ListAnimalService
from src.cattle.domain.services.animals.register_animal_service import RegisterAnimalService
from src.cattle.domain.services.animals.update_animal_service import UpdateAnimalService
from src.cattle.infrastructure.events.handlers.cache_invalidation import (
    AnimalCacheInvalidationHandler,
)
from src.common.domain.ports.cache_service import ICacheService
from src.common.domain.ports.event_bus import IEventBus
from src.common.infrastructure.adapters.cache_service import RedisCacheService
from src.common.infrastructure.events.bus import InMemoryEventBus
from src.common.infrastructure.events.handlers.outbox_scheduler import OutboxScheduler
from src.common.infrastructure.events.handlers.ws_broadcast import (
    WebSocketBroadcastHandler,
)
from src.common.infrastructure.persistence.connections.redis import _redis_client
from src.common.infrastructure.presentation.dependencies.redis import GetRedisClient
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_cache_service(redis: GetRedisClient) -> ICacheService:  # type: ignore[reportInvalidTypeForm]
    """Build a Redis-backed cache service."""
    return RedisCacheService(redis=redis)


GetCacheService = Annotated[ICacheService, Depends(_get_cache_service)]


def _get_event_bus(
    uow: GetUnitOfWork,
    cache_service: GetCacheService,
) -> IEventBus:
    """Build a request-scoped event bus with handler registrations."""
    bus = InMemoryEventBus()
    bus.register("*", OutboxScheduler(uow))
    bus.register("*", WebSocketBroadcastHandler(_redis_client))
    bus.register("animal.created", AnimalCacheInvalidationHandler(cache_service))
    return bus


GetEventBus = Annotated[IEventBus, Depends(_get_event_bus)]


def _get_register_animals_case(
    uow: GetUnitOfWork,
    service: Annotated[RegisterAnimalService, Depends()],
    create_animal_protocol_service: Annotated[
        CreateAnimalProtocolService,
        Depends(),
    ],
    event_bus: GetEventBus,
):
    return RegisterAnimalCase(
        uow=uow,
        service=service,
        create_animal_protocol_service=create_animal_protocol_service,
        event_bus=event_bus,
    )


def _get_update_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[UpdateAnimalService, Depends()],
):
    return UpdateAnimalCase(uow, service)


def _get_delete_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[DeleteAnimalService, Depends()],
):
    return DeleteAnimalCase(uow=uow, service=service)


def _get_list_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[ListAnimalService, Depends()],
):
    return ListAnimalsCase(uow=uow, service=service)


def _get_obtain_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[GetAnimalService, Depends()],
):
    return ObtainAnimalCase(uow, service)


GetAnimalRegisterCase = Annotated[RegisterAnimalCase, Depends(_get_register_animals_case)]
GetAnimalUpdateCase = Annotated[UpdateAnimalCase, Depends(_get_update_animal_case)]
GetAnimalDeleteCase = Annotated[DeleteAnimalCase, Depends(_get_delete_animal_case)]
GetAnimalListCase = Annotated[ListAnimalsCase, Depends(_get_list_animal_case)]
GetObtainAnimalCase = Annotated[ObtainAnimalCase, Depends(_get_obtain_animal_case)]
