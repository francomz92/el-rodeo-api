"""Per-tenant WebSocket connection manager.

Maintains an in-memory mapping of tenant_id → set of active WebSocket
connections for real-time notification delivery.
"""

from __future__ import annotations

import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections per tenant.

    Maintains an in-memory mapping of tenant_id → set of active WebSocket
    connections. Used by both the WebSocket endpoint (connect/disconnect)
    and the Redis Pub/Sub subscriber (broadcast).
    """

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, tenant_id: str, websocket: WebSocket) -> None:
        """Accept and register a WebSocket for *tenant_id*."""
        await websocket.accept()
        if tenant_id not in self._connections:
            self._connections[tenant_id] = set()
        self._connections[tenant_id].add(websocket)
        logger.info(
            "WebSocket connected: tenant=%s total=%d",
            tenant_id,
            self._total(),
        )

    def disconnect(self, tenant_id: str, websocket: WebSocket) -> None:
        """Remove *websocket* from *tenant_id*'s connection set."""
        if tenant_id in self._connections:
            self._connections[tenant_id].discard(websocket)
            if not self._connections[tenant_id]:
                del self._connections[tenant_id]
        logger.info(
            "WebSocket disconnected: tenant=%s total=%d",
            tenant_id,
            self._total(),
        )

    async def broadcast(self, tenant_id: str, message: dict) -> None:
        """Send *message* (serialized as JSON) to all connections for *tenant_id*.

        Stale connections (sending failed) are removed automatically.
        """
        if tenant_id not in self._connections:
            return
        stale: set[WebSocket] = set()
        payload = json.dumps(message, default=str)
        for ws in self._connections[tenant_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                stale.add(ws)
        for ws in stale:
            self._connections[tenant_id].discard(ws)
        if not self._connections[tenant_id]:
            del self._connections[tenant_id]

    def get_connections(self, tenant_id: str) -> set[WebSocket]:
        """Return the set of active connections for *tenant_id* (may be empty)."""
        return self._connections.get(tenant_id, set())

    async def close_all(self) -> None:
        """Close all connections (used during shutdown)."""
        for tenant_id, conns in list(self._connections.items()):
            for ws in conns:
                try:
                    await ws.close(code=1001, reason="Server shutting down")
                except Exception:
                    pass
            del self._connections[tenant_id]

    def _total(self) -> int:
        return sum(len(conns) for conns in self._connections.values())
