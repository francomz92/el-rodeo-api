"""Background asyncio task that subscribes to Redis Pub/Sub and forwards
messages to local WebSocket connections.
"""

from __future__ import annotations

import asyncio
import json

from src.common.infrastructure.adapters.websocket.manager import ConnectionManager
from src.common.utils import log


class RedisPubSubSubscriber:
    """Background asyncio task that listens to Redis Pub/Sub channels
    and broadcasts messages to local WebSocket connections.

    One instance per app process. Subscribes to ``notifications:*`` channels
    and forwards messages to the appropriate tenant's connections.
    """

    def __init__(
        self,
        redis_client,
        manager: ConnectionManager,
    ) -> None:
        self._redis = redis_client
        self._manager = manager
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the background subscriber task."""
        self._running = True
        self._task = asyncio.create_task(self._run())
        log.info("Redis Pub/Sub subscriber started")

    async def stop(self) -> None:
        """Stop the background subscriber task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        log.info("Redis Pub/Sub subscriber stopped")

    async def _run(self) -> None:
        """Subscribe to ``notifications:*`` channels and forward messages."""
        while self._running:
            pubsub = None
            try:
                pubsub = self._redis.pubsub()
                await pubsub.psubscribe("notifications:*")
                async for message in pubsub.listen():
                    if not self._running:
                        break
                    await self._handle_message(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(
                    "Redis Pub/Sub error: {} — reconnecting in 5s",
                    e,
                )
                await asyncio.sleep(5)
            finally:
                if pubsub is not None:
                    await pubsub.close()

    async def _handle_message(self, message: dict) -> None:
        """Process a single Pub/Sub message and forward to the manager."""
        if message["type"] != "pmessage":
            return
        channel: str = message["channel"]
        # Extract tenant_id from channel "notifications:{tenant_id}"
        tenant_id_str = channel.split(":", 1)[1] if ":" in channel else ""
        if not tenant_id_str:
            log.warning("Empty tenant_id in channel: {}", channel)
            return
        try:
            data = json.loads(message["data"])
            await self._manager.broadcast(tenant_id_str, data)
        except (ValueError, json.JSONDecodeError) as e:
            log.warning("Invalid Pub/Sub message: {}", e)
