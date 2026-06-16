"""Unit tests for schedule event domain services."""

from datetime import timedelta
from uuid import UUID

import pytest
from tests.factories import (
    make_schedule_event_create,
    make_schedule_event_entity,
    make_schedule_event_list_params,
    make_schedule_event_update,
)

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
from src.common.domain.exceptions import BusinessValidationError, ConflictError, NotFoundError
from src.common.utils.date_utils import get_current_datetime


class TestRegisterScheduleEventService:
    """RegisterScheduleEventService creates schedule events."""

    def setup_method(self) -> None:
        self.service = RegisterScheduleEventService()

    def test_validate_event_date_passes_with_valid_date(self) -> None:
        """A past or today date passes validation."""
        today = get_current_datetime().date()
        # Should not raise
        self.service.validate_event_date(today)

    def test_validate_event_date_raises_when_not_a_date(self) -> None:
        """Non-date values raise BusinessValidationError."""
        with pytest.raises(BusinessValidationError):
            self.service.validate_event_date("not-a-date")

    def test_validate_event_date_raises_when_in_future(self) -> None:
        """Future dates raise BusinessValidationError."""
        future = get_current_datetime().date() + timedelta(days=1)
        with pytest.raises(BusinessValidationError):
            self.service.validate_event_date(future)

    async def test_create_new_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        data = make_schedule_event_create()
        expected_entity = make_schedule_event_entity()
        repo = AsyncMock()
        repo.create.return_value = expected_entity

        result = await self.service.create_new(data, repo)

        assert result == expected_entity
        repo.create.assert_awaited_once_with(data)


class TestListScheduleEventService:
    """ListScheduleEventService lists events."""

    def setup_method(self) -> None:
        self.service = ListScheduleEventService()

    async def test_get_events_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        user_id = UUID("00000000-0000-0000-0000-000000000001")
        filters = make_schedule_event_list_params()
        expected = [make_schedule_event_entity(), make_schedule_event_entity()]
        repo = AsyncMock()
        repo.list_for_user.return_value = expected

        result = await self.service.get_events(
            user_id=user_id,
            query=filters,
            limit=10,
            offset=0,
            order_by="event_date",
            repository=repo,
        )

        assert result == expected
        repo.list_for_user.assert_awaited_once_with(
            user_id=user_id,
            filters=filters,
            limit=10,
            offset=0,
            order_by="event_date",
        )


class TestUpdateScheduleEventService:
    """UpdateScheduleEventService updates events."""

    def setup_method(self) -> None:
        self.service = UpdateScheduleEventService()

    def test_validate_event_date_passes_with_past_date(self) -> None:
        today = get_current_datetime().date()
        self.service.validate_event_date(today)

    def test_validate_event_date_raises_when_in_past(self) -> None:
        yesterday = get_current_datetime().date() - timedelta(days=1)
        with pytest.raises(BusinessValidationError):
            self.service.validate_event_date(yesterday)

    async def test_validate_event_exists_passes(self) -> None:
        from unittest.mock import AsyncMock

        event = make_schedule_event_entity(pending=True)
        repo = AsyncMock()
        repo.get_by_id.return_value = event

        await self.service.validate_event_exists(
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            repo,
        )

    async def test_validate_event_exists_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.validate_event_exists(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )

    async def test_validate_event_exists_raises_when_not_pending(self) -> None:
        from unittest.mock import AsyncMock

        event = make_schedule_event_entity(pending=False)
        repo = AsyncMock()
        repo.get_by_id.return_value = event

        with pytest.raises(ConflictError):
            await self.service.validate_event_exists(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )

    async def test_update_event_data_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        event_id = UUID("00000000-0000-0000-0000-000000000001")
        data = make_schedule_event_update()
        expected_entity = make_schedule_event_entity(id=event_id)
        repo = AsyncMock()
        repo.update_data.return_value = expected_entity

        result = await self.service.update_event_data(event_id, data, repo)

        assert result == expected_entity
        repo.update_data.assert_awaited_once_with(event_id, data)


class TestDeleteScheduleEventService:
    """DeleteScheduleEventService deletes events."""

    def setup_method(self) -> None:
        self.service = DeleteScheduleEventService()

    async def test_validate_for_delete_passes(self) -> None:
        from unittest.mock import AsyncMock

        event = make_schedule_event_entity(pending=True)
        repo = AsyncMock()
        repo.get_by_id.return_value = event

        await self.service.validate_for_delete(
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            repo,
        )

    async def test_validate_for_delete_raises_not_found(self) -> None:
        from unittest.mock import AsyncMock

        repo = AsyncMock()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await self.service.validate_for_delete(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )

    async def test_validate_for_delete_raises_when_not_pending(self) -> None:
        from unittest.mock import AsyncMock

        event = make_schedule_event_entity(pending=False)
        repo = AsyncMock()
        repo.get_by_id.return_value = event

        with pytest.raises(ConflictError):
            await self.service.validate_for_delete(
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
                repo,
            )

    async def test_delete_event_delegates_to_repo(self) -> None:
        from unittest.mock import AsyncMock

        event_id = UUID("00000000-0000-0000-0000-000000000001")
        repo = AsyncMock()

        await self.service.delete_event(event_id, repo)

        repo.delete.assert_awaited_once_with(id=event_id)
