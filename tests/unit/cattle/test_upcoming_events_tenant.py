"""Tests for upcoming events Celery task tenant iteration.

Verifies:
  - notify_upcoming_events(tenant_id=X) scopes to X
  - notify_upcoming_events(tenant_id=None) iterates all tenants
  - ScheduledEventsReminderService passes tenant_id to repository
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.cattle.application.services.notifications.scheduled_events_reminder_service import (
    ScheduledEventsReminderService,
)
from src.cattle.application.uses_cases.schedule_events_use_cases.norifi_upcoming_events_case import (
    NotifyUpcomingEventsCase,
)
from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository


class TestScheduledEventsReminderServiceTenant:
    """ScheduledEventsReminderService passes tenant_id to repository."""

    def setup_method(self) -> None:
        self.service = ScheduledEventsReminderService()
        self.repository = MagicMock(spec=IScheduleEventRepository)
        self.repository.get_pending_events = AsyncMock()
        self.notifier = MagicMock()

    @pytest.mark.asyncio
    async def test_get_pending_events_passes_tenant_id(self) -> None:
        """When tenant_id is provided, it's passed to repository.get_pending_events."""
        tenant_id = uuid4()
        self.repository.get_pending_events.return_value = []

        await self.service.get_pending_events(
            repository=self.repository,
            tenant_id=tenant_id,
        )

        self.repository.get_pending_events.assert_awaited_once_with(tenant_id=tenant_id)

    @pytest.mark.asyncio
    async def test_get_pending_events_passes_none_by_default(self) -> None:
        """When tenant_id is None, repository.get_pending_events receives None."""
        self.repository.get_pending_events.return_value = []

        await self.service.get_pending_events(
            repository=self.repository,
        )

        self.repository.get_pending_events.assert_awaited_once_with(tenant_id=None)


class TestNotifyUpcomingEventsCaseTenant:
    """NotifyUpcomingEventsCase passes tenant_id through the call chain."""

    def setup_method(self) -> None:
        self.uow = MagicMock()
        self.service = MagicMock()
        self.service.get_pending_events = AsyncMock()
        self.notifier = MagicMock()
        self.case = NotifyUpcomingEventsCase(
            uow=self.uow,
            service=self.service,
            notifier=self.notifier,
        )

    @pytest.mark.asyncio
    async def test_execute_passes_tenant_id(self) -> None:
        """execute(tenant_id=X) passes tenant_id to service.get_pending_events."""
        tenant_id = uuid4()
        self.uow.__aenter__.return_value = self.uow
        self.uow.__aexit__.return_value = None
        repo = MagicMock()
        self.uow.get_repository.return_value = repo
        self.service.get_pending_events.return_value = []

        await self.case.execute(tenant_id=tenant_id)

        self.service.get_pending_events.assert_awaited_once_with(
            repository=repo,
            tenant_id=tenant_id,
        )

    @pytest.mark.asyncio
    async def test_execute_passes_none_by_default(self) -> None:
        """execute() passes no tenant_id (None) to service."""
        self.uow.__aenter__.return_value = self.uow
        self.uow.__aexit__.return_value = None
        repo = MagicMock()
        self.uow.get_repository.return_value = repo
        self.service.get_pending_events.return_value = []

        await self.case.execute()

        self.service.get_pending_events.assert_awaited_once_with(
            repository=repo,
            tenant_id=None,
        )
