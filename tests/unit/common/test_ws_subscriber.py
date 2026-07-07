"""Unit tests for RedisPubSubSubscriber.

Tests start/stop lifecycle and message forwarding via _handle_message.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.common.infrastructure.adapters.websocket.subscriber import (
    RedisPubSubSubscriber,
)


@pytest.fixture
def mock_redis() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_manager() -> MagicMock:
    mgr = MagicMock()
    mgr.broadcast = AsyncMock()
    return mgr


@pytest.fixture
def subscriber(mock_redis: MagicMock, mock_manager: MagicMock) -> RedisPubSubSubscriber:
    return RedisPubSubSubscriber(redis_client=mock_redis, manager=mock_manager)


class TestStart:
    """Subscriber.start behaviour."""

    @pytest.mark.asyncio
    async def test_start_creates_background_task(self, subscriber: RedisPubSubSubscriber) -> None:
        await subscriber.start()
        assert subscriber._task is not None
        assert not subscriber._task.done()
        await subscriber.stop()

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self, subscriber: RedisPubSubSubscriber) -> None:
        await subscriber.start()
        assert subscriber._running is True
        await subscriber.stop()


class TestStop:
    """Subscriber.stop behaviour."""

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, subscriber: RedisPubSubSubscriber) -> None:
        await subscriber.start()
        assert subscriber._task is not None
        await subscriber.stop()
        assert subscriber._task is None
        assert subscriber._running is False

    @pytest.mark.asyncio
    async def test_stop_safe_when_not_started(self, subscriber: RedisPubSubSubscriber) -> None:
        await subscriber.stop()  # Should not raise


class TestHandleMessage:
    """Subscriber._handle_message behaviour."""

    @pytest.mark.asyncio
    async def test_forwards_pmessage_to_manager_broadcast(self, subscriber: RedisPubSubSubscriber, mock_manager: MagicMock) -> None:
        message = {
            "type": "pmessage",
            "channel": "notifications:550e8400-e29b-41d4-a716-446655440000",
            "data": '{"event": "test"}',
        }

        await subscriber._handle_message(message)

        mock_manager.broadcast.assert_awaited_once_with(
            "550e8400-e29b-41d4-a716-446655440000",
            {"event": "test"},
        )

    @pytest.mark.asyncio
    async def test_ignores_subscribe_messages(self, subscriber: RedisPubSubSubscriber, mock_manager: MagicMock) -> None:
        message = {"type": "subscribe", "channel": "notifications:*", "data": 1}

        await subscriber._handle_message(message)

        mock_manager.broadcast.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ignores_psubscribe_messages(self, subscriber: RedisPubSubSubscriber, mock_manager: MagicMock) -> None:
        message = {"type": "psubscribe", "channel": "notifications:*", "data": 1}

        await subscriber._handle_message(message)

        mock_manager.broadcast.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_empty_channel_does_not_broadcast(self, subscriber: RedisPubSubSubscriber, mock_manager: MagicMock) -> None:
        message = {"type": "pmessage", "channel": "notifications:", "data": "{}"}

        await subscriber._handle_message(message)

        mock_manager.broadcast.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_invalid_json_does_not_broadcast(self, subscriber: RedisPubSubSubscriber, mock_manager: MagicMock) -> None:
        message = {
            "type": "pmessage",
            "channel": "notifications:550e8400-e29b-41d4-a716-446655440000",
            "data": "not-json",
        }

        await subscriber._handle_message(message)

        mock_manager.broadcast.assert_not_awaited()
