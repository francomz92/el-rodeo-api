"""Unit tests for the Celery outbox_forwarder_task.

Tests that the forwarder:
- Queries PENDING outbox events
- Finds matching active WebhookSubscriptions
- POSTs signed payloads to subscriber URLs
- Marks events SENT on success
- Marks events FAILED on partial failure
- Deactivates subscriptions after 5 failures
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.common.infrastructure.persistence.models.event_outbox import (
    EventOutbox,
    OutboxStatus,
)
from src.common.infrastructure.persistence.models.webhook_subscription import (
    WebhookSubscription,
)


class _MockAsyncSession:
    """Custom async context manager mock that returns self from __aenter__."""

    def __init__(self) -> None:
        self.execute = AsyncMock()
        self.commit = AsyncMock()

    async def __aenter__(self) -> "_MockAsyncSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


class TestOutboxForwarderTask:
    """Outbox forwarder processes pending events and delivers to subscribers."""

    def setup_method(self) -> None:
        self.event_id = uuid4()
        self.aggregate_id = uuid4()
        self.tenant_id = uuid4()
        self.subscription_id = uuid4()
        self.webhook_url = "https://example.com/webhook"
        self.secret = "test-secret-123"

    def _make_outbox_event(
        self,
        event_type: str = "payment.received",
        status: str = OutboxStatus.PENDING,
        retry_count: int = 0,
    ) -> EventOutbox:
        return EventOutbox(
            event_id=self.event_id,
            event_type=event_type,
            aggregate_id=self.aggregate_id,
            payload={
                "event_id": str(self.event_id),
                "aggregate_id": str(self.aggregate_id),
                "event_type": event_type,
            },
            status=status,
            retry_count=retry_count,
        )

    def _make_subscription(
        self,
        subscribed_events: list[str] | None = None,
        is_active: bool = True,
        failure_count: int = 0,
    ) -> WebhookSubscription:
        return WebhookSubscription(
            id=self.subscription_id,
            tenant_id=self.tenant_id,
            url=self.webhook_url,
            secret=self.secret,
            subscribed_events=subscribed_events or ["payment.received"],
            is_active=is_active,
            failure_count=failure_count,
        )

    def _setup_mock_session(
        self,
        events: list[EventOutbox],
        subscriptions: list[WebhookSubscription] | None = None,
    ) -> _MockAsyncSession:
        """Create a mock session that returns *events* and optionally *subscriptions*."""
        session = _MockAsyncSession()

        mock_event_result = MagicMock()
        mock_event_result.scalars.return_value.all.return_value = events

        if subscriptions is not None:
            mock_sub_result = MagicMock()
            mock_sub_result.scalars.return_value.all.return_value = subscriptions
            session.execute.side_effect = [mock_event_result, mock_sub_result]
        else:
            session.execute.return_value = mock_event_result

        return session

    def test_forwarder_processes_pending_events(self) -> None:
        """Forwarder queries PENDING events and delivers them."""
        event = self._make_outbox_event()
        sub = self._make_subscription()
        session = self._setup_mock_session(events=[event], subscriptions=[sub])

        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch = AsyncMock(return_value=True)

        with (
            patch(
                "src.common.infrastructure.workers.event_tasks.AsyncSessionMaker",
                return_value=session,
            ),
            patch(
                "src.common.infrastructure.workers.event_tasks.WebhookDispatcher",
                return_value=mock_dispatcher,
            ),
        ):
            from src.common.infrastructure.workers.event_tasks import (
                outbox_forwarder_task,
            )

            result = outbox_forwarder_task()

        assert result["processed"] == 1
        assert result["succeeded"] == 1
        assert result["failed"] == 0
        assert event.status == OutboxStatus.SENT
        mock_dispatcher.dispatch.assert_called_once_with(
            url=self.webhook_url,
            secret=self.secret,
            payload=event.payload,
        )

    def test_forwarder_skips_non_matching_subscriptions(self) -> None:
        """Events only go to subscribers who registered for that event type."""
        event = self._make_outbox_event(event_type="animal.created")
        sub = self._make_subscription(subscribed_events=["payment.received"])
        session = self._setup_mock_session(events=[event], subscriptions=[sub])

        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch = AsyncMock()

        with (
            patch(
                "src.common.infrastructure.workers.event_tasks.AsyncSessionMaker",
                return_value=session,
            ),
            patch(
                "src.common.infrastructure.workers.event_tasks.WebhookDispatcher",
                return_value=mock_dispatcher,
            ),
        ):
            from src.common.infrastructure.workers.event_tasks import (
                outbox_forwarder_task,
            )

            result = outbox_forwarder_task()

        assert result["processed"] == 1
        assert result["succeeded"] == 1
        assert result["failed"] == 0
        mock_dispatcher.dispatch.assert_not_called()

    def test_forwarder_marks_failed_on_dispatch_failure(self) -> None:
        """When dispatch fails, the event increments retry_count and stays PENDING."""
        event = self._make_outbox_event()
        sub = self._make_subscription()
        session = self._setup_mock_session(events=[event], subscriptions=[sub])

        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch = AsyncMock(return_value=False)

        with (
            patch(
                "src.common.infrastructure.workers.event_tasks.AsyncSessionMaker",
                return_value=session,
            ),
            patch(
                "src.common.infrastructure.workers.event_tasks.WebhookDispatcher",
                return_value=mock_dispatcher,
            ),
        ):
            from src.common.infrastructure.workers.event_tasks import (
                outbox_forwarder_task,
            )

            result = outbox_forwarder_task()

        assert result["processed"] == 1
        assert result["succeeded"] == 0
        assert result["failed"] == 1
        # First failure — retry_count incremented, stays PENDING for retry
        assert event.retry_count == 1
        assert event.status == OutboxStatus.PENDING

    def test_forwarder_deactivates_subscription_after_5_failures(self) -> None:
        """Subscription is deactivated after 5 consecutive failures."""
        event = self._make_outbox_event()
        sub = self._make_subscription(failure_count=4)
        session = self._setup_mock_session(events=[event], subscriptions=[sub])

        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch = AsyncMock(return_value=False)

        with (
            patch(
                "src.common.infrastructure.workers.event_tasks.AsyncSessionMaker",
                return_value=session,
            ),
            patch(
                "src.common.infrastructure.workers.event_tasks.WebhookDispatcher",
                return_value=mock_dispatcher,
            ),
        ):
            from src.common.infrastructure.workers.event_tasks import (
                outbox_forwarder_task,
            )

            result = outbox_forwarder_task()

        assert result["processed"] == 1
        assert result["failed"] == 1
        assert sub.is_active is False
        assert sub.failure_count == 5
        # Event retried but not yet exhausted (MAX_OUTBOX_RETRIES=5)
        assert event.retry_count == 1
        assert event.status == OutboxStatus.PENDING

    def test_forwarder_does_not_deactivate_before_5_failures(self) -> None:
        """Subscription stays active at < 5 failures."""
        event = self._make_outbox_event()
        sub = self._make_subscription(failure_count=2)
        session = self._setup_mock_session(events=[event], subscriptions=[sub])

        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch = AsyncMock(return_value=False)

        with (
            patch(
                "src.common.infrastructure.workers.event_tasks.AsyncSessionMaker",
                return_value=session,
            ),
            patch(
                "src.common.infrastructure.workers.event_tasks.WebhookDispatcher",
                return_value=mock_dispatcher,
            ),
        ):
            from src.common.infrastructure.workers.event_tasks import (
                outbox_forwarder_task,
            )

            result = outbox_forwarder_task()

        assert result["failed"] == 1
        assert sub.is_active is True
        assert sub.failure_count == 3
        # Event gets a retry, stays PENDING
        assert event.retry_count == 1
        assert event.status == OutboxStatus.PENDING

    def test_forwarder_handles_no_pending_events(self) -> None:
        """No pending events is a no-op returning zero counts."""
        session = self._setup_mock_session(events=[])

        with patch(
            "src.common.infrastructure.workers.event_tasks.AsyncSessionMaker",
            return_value=session,
        ):
            from src.common.infrastructure.workers.event_tasks import (
                outbox_forwarder_task,
            )

            result = outbox_forwarder_task()

        assert result["processed"] == 0
        assert result["succeeded"] == 0
        assert result["failed"] == 0

    def test_forwarder_respects_limit(self) -> None:
        """Forwarder fetches at most 50 events at a time."""
        session = self._setup_mock_session(events=[])

        with patch(
            "src.common.infrastructure.workers.event_tasks.AsyncSessionMaker",
            return_value=session,
        ):
            from src.common.infrastructure.workers.event_tasks import (
                outbox_forwarder_task,
            )

            outbox_forwarder_task()

        call_stmt = session.execute.call_args[0][0]
        assert hasattr(call_stmt, "_limit")
        assert call_stmt._limit == 50
