from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.auth.domain.entities._user_role import UserRole
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    require_role,
)
from src.calendar.domain.value_objects.calendar_event_value_object import (
    CalendarEventCreationValueObject,
    CalendarEventsListQueryParamsValueObject,
    CalendarEventUpdateValueObject,
)
from src.common.domain.exceptions import NotPermissionError

from ...adapters.http.input.calendar_event_schemas import (
    CalendarEventCreationSchema,
    CalendarEventsQueryParams,
    CalendarEventUpdateSchema,
)
from ...adapters.http.output.calendar_events_schemas import CalendarEventSchema
from ..dependencies.calendar_events import (
    GetDeleteCalendarEventCase,
    GetListCalendarEventsCase,
    GetRegisterCalendarEventCase,
    GetUpdateCalendarEventCase,
)


def _get_calendar_tenant_id(current_user: GetCurrentUser) -> UUID:
    """Require a tenant for calendar operations and return its identifier."""
    if current_user.tenant_id is None:
        raise NotPermissionError("Se requiere un tenant para acceder a los eventos del calendario.")
    return current_user.tenant_id


GetCalendarTenantId = Annotated[UUID, Depends(_get_calendar_tenant_id)]

events_router = APIRouter(
    prefix="/events",
    responses={401: {}, 403: {}},
    dependencies=[require_role(UserRole.VIEWER)],
)


@events_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user calendar event in the database",
    response_model=CalendarEventSchema,
    dependencies=[require_role(UserRole.EDITOR)],
)
async def create_calendar_event(
    current_user: GetCurrentUser,
    calendar_event_case: GetRegisterCalendarEventCase,
    data: CalendarEventCreationSchema,
    tenant_id: GetCalendarTenantId,
):
    event_data = CalendarEventCreationValueObject(
        **data.model_dump(exclude_unset=True),
        user_id=current_user.id,
    )
    return await calendar_event_case.execute(data=event_data, tenant_id=tenant_id)


@events_router.put(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    summary="Update an event data in the database",
    response_model=CalendarEventSchema,
    dependencies=[require_role(UserRole.EDITOR)],
)
async def update_event(
    id: UUID,
    current_user: GetCurrentUser,
    calendar_event_case: GetUpdateCalendarEventCase,
    data: CalendarEventUpdateSchema,
    tenant_id: GetCalendarTenantId,
):
    payload = CalendarEventUpdateValueObject(
        **data.model_dump(exclude_unset=True),
        user_id=current_user.id,
    )
    return await calendar_event_case.execute(
        id=id,
        data=payload,
        tenant_id=tenant_id,
    )


@events_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a calendar event in the database",
    dependencies=[require_role(UserRole.ADMIN)],
)
async def delete_event(
    id: UUID,
    current_user: GetCurrentUser,
    calendar_event_case: GetDeleteCalendarEventCase,
    _tenant_id: GetCalendarTenantId,
):
    return await calendar_event_case.execute(
        id=id,
    )


@events_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    summary="List all calendar events for a user",
    response_model=list[CalendarEventSchema],
)
async def list_calendar_events(
    current_user: GetCurrentUser,
    calendar_event_case: GetListCalendarEventsCase,
    query_params: Annotated[CalendarEventsQueryParams, Query()],
    _tenant_id: GetCalendarTenantId,
):
    filters = CalendarEventsListQueryParamsValueObject(
        **query_params.model_dump(
            exclude_unset=True,
            exclude={"limit", "offset", "order_by"},
        ),
    )
    return await calendar_event_case.execute(filters=filters, order_by=query_params.order_by)
