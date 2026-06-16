"""Unit tests for schedule event use cases."""

from uuid import UUID

from tests.factories import (
    make_schedule_event_create,
    make_schedule_event_entity,
    make_schedule_event_list_params,
    make_schedule_event_update,
)
from tests.mocks import MockUoW

from src.cattle.application.uses_cases.schedule_events_use_cases.delete_schedule_event_case import (
    DeleteScheduleEventCase,
)
from src.cattle.application.uses_cases.schedule_events_use_cases.list_schedule_event_case import (
    ListScheduleEventsCase,
)
from src.cattle.application.uses_cases.schedule_events_use_cases.register_schedule_event_case import (
    RegisterScheduleEventCase,
)
from src.cattle.application.uses_cases.schedule_events_use_cases.update_schedule_event_case import (
    UpdateScheduleEventCase,
)
from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.services.schedule_events.delete_schedule_event_service import (
    DeleteScheduleEventService,
)
from src.cattle.domain.services.schedule_events.list_schedule_event_service import (
    ListScheduleEventService,
)
from src.cattle.domain.services.schedule_events.register_schedule_event_service import (
    RegisterScheduleEventService,
)
from src.cattle.domain.services.schedule_events.update_schedule_event_service import (
    UpdateScheduleEventService,
)
from src.common.utils.date_utils import get_current_datetime


class TestRegisterScheduleEventCase:
    """RegisterScheduleEventCase creates an event via UoW."""

    def setup_method(self) -> None:
        self.service = RegisterScheduleEventService()
        self.uow = MockUoW()
        self.case = RegisterScheduleEventCase(uow=self.uow, service=self.service)

    async def test_execute_creates_event_successfully(self) -> None:
        data = make_schedule_event_create(event_date=get_current_datetime().date())
        expected_entity = make_schedule_event_entity()
        repo = self.uow.get_repository(IScheduleEventRepository)
        repo.create.return_value = expected_entity

        await self.case.execute(data)

        repo.create.assert_awaited_once()
        self.uow.commit.assert_awaited_once()


class TestListScheduleEventsCase:
    """ListScheduleEventsCase lists events."""

    def setup_method(self) -> None:
        self.service = ListScheduleEventService()
        self.uow = MockUoW()
        self.case = ListScheduleEventsCase(uow=self.uow, service=self.service)

    async def test_execute_returns_events(self) -> None:
        user_id = UUID("00000000-0000-0000-0000-000000000001")
        filters = make_schedule_event_list_params()
        expected = [make_schedule_event_entity(), make_schedule_event_entity()]
        repo = self.uow.get_repository(IScheduleEventRepository)
        repo.list_for_user.return_value = expected

        result = await self.case.execute(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="event_date",
        )

        assert result == expected
        repo.list_for_user.assert_awaited_once_with(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="event_date",
        )


class TestUpdateScheduleEventCase:
    """UpdateScheduleEventCase updates an event."""

    def setup_method(self) -> None:
        self.service = UpdateScheduleEventService()
        self.uow = MockUoW()
        self.case = UpdateScheduleEventCase(uow=self.uow, service=self.service)

    async def test_execute_updates_successfully(self) -> None:
        event_id = UUID("00000000-0000-0000-0000-000000000001")
        today = get_current_datetime().date()
        data = make_schedule_event_update(event_date=today)
        existing = make_schedule_event_entity(id=event_id, pending=True)
        updated = make_schedule_event_entity(id=event_id)
        repo = self.uow.get_repository(IScheduleEventRepository)
        repo.get_by_id.return_value = existing
        repo.update_data.return_value = updated

        await self.case.execute(id=event_id, data=data)

        repo.update_data.assert_awaited_once()
        self.uow.commit.assert_awaited_once()


class TestDeleteScheduleEventCase:
    """DeleteScheduleEventCase deletes an event."""

    def setup_method(self) -> None:
        self.service = DeleteScheduleEventService()
        self.uow = MockUoW()
        self.case = DeleteScheduleEventCase(uow=self.uow, service=self.service)

    async def test_execute_deletes_event(self) -> None:
        event_id = UUID("00000000-0000-0000-0000-000000000001")
        user_id = UUID("00000000-0000-0000-0000-000000000002")
        existing = make_schedule_event_entity(id=event_id, pending=True)
        repo = self.uow.get_repository(IScheduleEventRepository)
        repo.get_by_id.return_value = existing

        await self.case.execute(id=event_id, user_id=user_id)

        repo.delete.assert_awaited_once_with(id=event_id)
        self.uow.commit.assert_awaited_once()
