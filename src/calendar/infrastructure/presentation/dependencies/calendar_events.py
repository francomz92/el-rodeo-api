from typing import Annotated

from fastapi import Depends

from src.calendar.application.uses_cases.calendar_events_use_cases.delete_calendar_event_case import DeleteCalendarEventCase
from src.calendar.application.uses_cases.calendar_events_use_cases.list_calendar_event_case import ListCalendarEventsCase
from src.calendar.application.uses_cases.calendar_events_use_cases.register_calendar_event_case import RegisterCalendarEventCase
from src.calendar.application.uses_cases.calendar_events_use_cases.update_calendar_event_case import UpdateCalendarEventCase
from src.calendar.domain.services.calendar_events.delete_calendar_event_service import DeleteCalendarEventService
from src.calendar.domain.services.calendar_events.list_calendar_event_service import ListCalendarEventService
from src.calendar.domain.services.calendar_events.register_calendar_event_service import RegisterCalendarEventService
from src.calendar.domain.services.calendar_events.update_calendar_event_service import UpdateCalendarEventService
from src.common.infrastructure.presentation.dependencies.event_bus import GetEventBus
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_register_event_case(
    uow: GetUnitOfWork,
    service: Annotated[RegisterCalendarEventService, Depends()],
    event_bus: GetEventBus,
) -> RegisterCalendarEventCase:
    return RegisterCalendarEventCase(uow=uow, service=service, event_bus=event_bus)


def _get_update_event_case(
    uow: GetUnitOfWork,
    service: Annotated[UpdateCalendarEventService, Depends()],
    event_bus: GetEventBus,
) -> UpdateCalendarEventCase:
    return UpdateCalendarEventCase(uow=uow, service=service, event_bus=event_bus)


def _get_delete_event_case(
    uow: GetUnitOfWork,
    service: Annotated[DeleteCalendarEventService, Depends()],
) -> DeleteCalendarEventCase:
    return DeleteCalendarEventCase(uow=uow, service=service)


def _get_list_events_case(
    uow: GetUnitOfWork,
    service: Annotated[ListCalendarEventService, Depends()],
) -> ListCalendarEventsCase:
    return ListCalendarEventsCase(uow=uow, service=service)


GetRegisterCalendarEventCase = Annotated[RegisterCalendarEventCase, Depends(_get_register_event_case)]
GetUpdateCalendarEventCase = Annotated[UpdateCalendarEventCase, Depends(_get_update_event_case)]
GetDeleteCalendarEventCase = Annotated[DeleteCalendarEventCase, Depends(_get_delete_event_case)]
GetListCalendarEventsCase = Annotated[ListCalendarEventsCase, Depends(_get_list_events_case)]
