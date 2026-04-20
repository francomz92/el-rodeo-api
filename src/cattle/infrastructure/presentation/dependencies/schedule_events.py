from typing import Annotated

from fastapi import Depends

from src.cattle.application.uses_cases.schedule_events_use_cases.delete_schedule_event_case import DeleteScheduleEventCase
from src.cattle.application.uses_cases.schedule_events_use_cases.list_schedule_event_case import ListScheduleEventsCase
from src.cattle.application.uses_cases.schedule_events_use_cases.regiser_schedule_event_case import RegisterScheduleEventCase
from src.cattle.application.uses_cases.schedule_events_use_cases.update_schedule_event_case import UpdateScheduleEventCase
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork



def _get_register_event_case(uow: GetUnitOfWork):
    return RegisterScheduleEventCase(uow=uow)


def _get_update_event_case(uow: GetUnitOfWork):
    return UpdateScheduleEventCase(uow=uow)


def _get_delete_event_case(uow: GetUnitOfWork):
    return DeleteScheduleEventCase(uow=uow)


def _get_list_events_case(uow: GetUnitOfWork):
    return ListScheduleEventsCase(uow=uow)


GetRegisterScheduleEventCase = Annotated[RegisterScheduleEventCase, Depends(_get_register_event_case)]
GetUpdateScheduleEventCase = Annotated[UpdateScheduleEventCase, Depends(_get_update_event_case)]
GetDeleteScheduleEventCase = Annotated[DeleteScheduleEventCase, Depends(_get_delete_event_case)]
GetListScheduleEventsCase = Annotated[ListScheduleEventsCase, Depends(_get_list_events_case)]