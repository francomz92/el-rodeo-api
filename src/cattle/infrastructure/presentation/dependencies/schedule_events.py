from typing import Annotated

from fastapi import Depends

from src.cattle.application.uses_cases.schedule_events_use_cases.delete_schedule_event_case import DeleteScheduleEventCase
from src.cattle.application.uses_cases.schedule_events_use_cases.list_schedule_event_case import ListScheduleEventsCase
from src.cattle.application.uses_cases.schedule_events_use_cases.regiser_schedule_event_case import RegisterScheduleEventCase
from src.cattle.application.uses_cases.schedule_events_use_cases.update_schedule_event_case import UpdateScheduleEventCase
from src.cattle.domain.services.schedule_events.delete_schedule_event_service import DeleteScheduleEventService
from src.cattle.domain.services.schedule_events.list_schedule_event_service import ListScheduleEventService
from src.cattle.domain.services.schedule_events.register_schedule_event_service import RegisterScheduleEventService
from src.cattle.domain.services.schedule_events.update_schedule_event_service import UpdateScheduleEventService
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_register_event_case(
    uow: GetUnitOfWork,
    service: Annotated[RegisterScheduleEventService, Depends()],
):
    return RegisterScheduleEventCase(uow=uow, service=service)


def _get_update_event_case(
    uow: GetUnitOfWork,
    service: Annotated[UpdateScheduleEventService, Depends()],
):
    return UpdateScheduleEventCase(uow=uow, service=service)


def _get_delete_event_case(
    uow: GetUnitOfWork,
    service: Annotated[DeleteScheduleEventService, Depends()],
):
    return DeleteScheduleEventCase(uow=uow, service=service)


def _get_list_events_case(
    uow: GetUnitOfWork,
    service: Annotated[ListScheduleEventService, Depends()],
):
    return ListScheduleEventsCase(uow=uow, service=service)


GetRegisterScheduleEventCase = Annotated[RegisterScheduleEventCase, Depends(_get_register_event_case)]
GetUpdateScheduleEventCase = Annotated[UpdateScheduleEventCase, Depends(_get_update_event_case)]
GetDeleteScheduleEventCase = Annotated[DeleteScheduleEventCase, Depends(_get_delete_event_case)]
GetListScheduleEventsCase = Annotated[ListScheduleEventsCase, Depends(_get_list_events_case)]
