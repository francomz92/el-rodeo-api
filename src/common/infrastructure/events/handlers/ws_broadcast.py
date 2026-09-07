"""EventBus handler that publishes domain events to Redis Pub/Sub
for cross-instance WebSocket delivery.
"""

from __future__ import annotations

import json

from src.common.domain.events.base import DomainEvent
from src.common.utils import log


class WebSocketBroadcastHandler:
    """EventBus handler that publishes domain events to Redis Pub/Sub
    for cross-instance WebSocket delivery.

    The Redis Pub/Sub subscriber in each app instance picks up these
    messages and broadcasts them to local WebSocket connections.
    """

    def __init__(self, redis_client) -> None:
        self._redis = redis_client

    async def __call__(self, event: DomainEvent) -> None:
        """Publish *event* to Redis Pub/Sub for WebSocket delivery."""
        # Extract tenant_id from event metadata
        metadata = event.metadata or {}
        tenant_id = metadata.get("tenant_id")
        if tenant_id is None:
            log.debug("No tenant_id in event metadata — skipping WS broadcast")
            return

        message = {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "aggregate_id": str(event.aggregate_id),
            "timestamp": event.timestamp.isoformat(),
        }

        channel = f"notifications:{tenant_id}"
        await self._publish(channel, message)

    async def _publish(self, channel: str, message: dict) -> None:
        """Publish *message* to Redis *channel*."""
        try:
            await self._redis.publish(
                channel,
                json.dumps(message, default=str),
            )
        except Exception as e:
            log.error("Failed to publish to {}: {}", channel, e)
