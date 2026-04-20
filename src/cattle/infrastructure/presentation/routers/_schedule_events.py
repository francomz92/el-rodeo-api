from uuid import UUID

from fastapi import APIRouter, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import GetCurrentUser
from src.cattle.application.ports.dtos.schedule_event_dtos import ScheduleEventCreationDTO, ScheduleEventUpdateDTO, ScheduleEventsListQueryParamsDTO
from src.cattle.infrastructure.adapters.http.input.schedule_event_schemas import ScheduleEventCreationSchema, ScheduleEventUpdateSchema, ScheduleEventsQueryParams
from src.cattle.infrastructure.adapters.http.output.schedule_events_schemas import ScheduleEventSchema
from src.cattle.infrastructure.presentation.dependencies.schedule_events import GetDeleteScheduleEventCase, GetListScheduleEventsCase, GetRegisterScheduleEventCase, GetUpdateScheduleEventCase



events_router = APIRouter(
    responses={401: {}, 403: {}},
)



@events_router.post(
    path="/schedule-events",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user schedule event in the database",
    response_model=ScheduleEventSchema,
)
async def create_schedule_event(
    current_user: GetCurrentUser,
    register_schedule_event_case: GetRegisterScheduleEventCase,
    data: ScheduleEventCreationSchema,
):
    event_data = ScheduleEventCreationDTO(
        **data.model_dump(exclude_unset=True),
        user_id=current_user.id,
    )
    return await register_schedule_event_case.excecue(data=event_data)


@events_router.put(
    path="/schedule-events/{id}",
    status_code=status.HTTP_200_OK,
    summary="Update an event data in the database",
    response_model=ScheduleEventSchema,
)
async def update_event(
    id: UUID,
    current_user: GetCurrentUser,
    update_schedule_event_case: GetUpdateScheduleEventCase,
    data: ScheduleEventUpdateSchema,
):
    payload = ScheduleEventUpdateDTO(
        **data.model_dump(exclude_unset=True),
        user_id=current_user.id,
    )
    return await update_schedule_event_case.excecute(id=id, data=payload)


@events_router.delete(
    path="/schedule-events/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scheduled event in the database",
)
async def delete_evetn(
    id: UUID,
    current_user: GetCurrentUser,
    delete_schedule_event_case: GetDeleteScheduleEventCase,
):
    return delete_schedule_event_case.excecute(id=id, user_id=current_user.id)


@events_router.get(
    path="/schedule-events",
    status_code=status.HTTP_200_OK,
    summary="List all scheduled events for a user",
    response_model=list[ScheduleEventSchema],
)
async def list_schedule_events(
    current_user: GetCurrentUser,
    list_schedule_events_case: GetListScheduleEventsCase,
    query_params: ScheduleEventsQueryParams,
):
    filters = ScheduleEventsListQueryParamsDTO(
        **query_params.model_dump(
            exclude_unset=True,
            exclude={"limit", "offset", "order_by"},
        ),
    )
    return await list_schedule_events_case.excecute(
        user_id=current_user.id,
        filters=filters,
        limit=query_params.limit,
        offset=query_params.offset,
        order_by=query_params.order_by,
    )