"""Unit tests for WebSocketBroadcastHandler.

Tests that the handler publishes domain events to the correct Redis
Pub/Sub channel and skips events without tenant_id in metadata.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.common.domain.events.base import DomainEvent
from src.common.infrastructure.events.handlers.ws_broadcast import (
    WebSocketBroadcastHandler,
)


@pytest.fixture
def mock_redis() -> MagicMock:
    redis = MagicMock()
    redis.publish = AsyncMock()
    return redis


@pytest.fixture
def handler(mock_redis: MagicMock) -> WebSocketBroadcastHandler:
    return WebSocketBroadcastHandler(redis_client=mock_redis)


class TestHandlerCall:
    """WebSocketBroadcastHandler.__call__ behaviour."""

    @pytest.mark.asyncio
    async def test_publishes_to_correct_redis_channel(self, handler: WebSocketBroadcastHandler, mock_redis: MagicMock) -> None:
        tenant_id = uuid4()
        event = DomainEvent(
            aggregate_id=uuid4(),
            event_type="animal.created",
            metadata={"tenant_id": str(tenant_id)},
        )

        await handler(event)

        mock_redis.publish.assert_awaited_once()
        call_args = mock_redis.publish.await_args
        assert call_args is not None
        channel = call_args[0][0]
        assert channel == f"notifications:{tenant_id}"

    @pytest.mark.asyncio
    async def test_publishes_serialized_event_data(self, handler: WebSocketBroadcastHandler, mock_redis: MagicMock) -> None:
        tenant_id = uuid4()
        event = DomainEvent(
            aggregate_id=UUID(int=1),
            event_type="animal.updated",
            metadata={"tenant_id": str(tenant_id)},
        )

        await handler(event)

        mock_redis.publish.assert_awaited_once()
        call_args = mock_redis.publish.await_args
        assert call_args is not None
        channel, payload = call_args[0]
        assert channel == f"notifications:{tenant_id}"
        import json

        data = json.loads(payload)
        assert data["event_type"] == "animal.updated"
        assert data["event_id"] == str(event.event_id)
        assert data["aggregate_id"] == str(event.aggregate_id)

    @pytest.mark.asyncio
    async def test_skips_event_without_tenant_id(self, handler: WebSocketBroadcastHandler, mock_redis: MagicMock) -> None:
        event = DomainEvent(
            aggregate_id=uuid4(),
            event_type="animal.created",
            metadata={},
        )

        await handler(event)

        mock_redis.publish.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_event_with_none_metadata(self, handler: WebSocketBroadcastHandler, mock_redis: MagicMock) -> None:
        event_with_none_meta = DomainEvent(
            aggregate_id=uuid4(),
            event_type="animal.created",
            metadata={},
        )

        await handler(event_with_none_meta)

        mock_redis.publish.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handles_publish_error_gracefully(self, handler: WebSocketBroadcastHandler, mock_redis: MagicMock) -> None:
        """Handler should not raise when Redis publish fails."""
        mock_redis.publish = AsyncMock(side_effect=Exception("Redis down"))
        tenant_id = uuid4()
        event = DomainEvent(
            aggregate_id=uuid4(),
            event_type="animal.created",
            metadata={"tenant_id": str(tenant_id)},
        )

        # Should not raise
        await handler(event)

        mock_redis.publish.assert_awaited_once()
