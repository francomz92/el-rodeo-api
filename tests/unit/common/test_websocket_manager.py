"""Unit tests for ConnectionManager.

Tests connect/disconnect, broadcast (tenant isolation, stale cleanup),
get_connections, and close_all.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocket

from src.common.infrastructure.adapters.websocket.manager import ConnectionManager


@pytest.fixture
def ws1() -> MagicMock:
    ws = MagicMock(spec=WebSocket)
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    ws.accept = AsyncMock()
    ws.receive_text = AsyncMock()
    return ws


@pytest.fixture
def ws2() -> MagicMock:
    ws = MagicMock(spec=WebSocket)
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    ws.accept = AsyncMock()
    return ws


@pytest.fixture
def manager() -> ConnectionManager:
    return ConnectionManager()


class TestConnect:
    """ConnectionManager.connect behaviour."""

    @pytest.mark.asyncio
    async def test_connect_adds_websocket_to_tenant_set(self, manager: ConnectionManager, ws1: MagicMock) -> None:
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"

        await manager.connect(tenant_id, ws1)

        assert ws1 in manager.get_connections(tenant_id)

    @pytest.mark.asyncio
    async def test_connect_accepts_multiple_connections_per_tenant(
        self, manager: ConnectionManager, ws1: MagicMock, ws2: MagicMock
    ) -> None:
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"

        await manager.connect(tenant_id, ws1)
        await manager.connect(tenant_id, ws2)

        conns = manager.get_connections(tenant_id)
        assert ws1 in conns
        assert ws2 in conns
        assert len(conns) == 2


class TestDisconnect:
    """ConnectionManager.disconnect behaviour."""

    @pytest.mark.asyncio
    async def test_disconnect_removes_websocket(self, manager: ConnectionManager, ws1: MagicMock) -> None:
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        await manager.connect(tenant_id, ws1)

        manager.disconnect(tenant_id, ws1)

        assert ws1 not in manager.get_connections(tenant_id)

    @pytest.mark.asyncio
    async def test_disconnect_removes_tenant_key_when_empty(self, manager: ConnectionManager, ws1: MagicMock) -> None:
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        await manager.connect(tenant_id, ws1)

        manager.disconnect(tenant_id, ws1)

        assert tenant_id not in manager._connections

    @pytest.mark.asyncio
    async def test_disconnect_other_tenant_not_affected(self, manager: ConnectionManager, ws1: MagicMock, ws2: MagicMock) -> None:
        t1 = "550e8400-e29b-41d4-a716-446655440000"
        t2 = "660e8400-e29b-41d4-a716-446655440001"
        await manager.connect(t1, ws1)
        await manager.connect(t2, ws2)

        manager.disconnect(t1, ws1)

        assert ws2 in manager.get_connections(t2)


class TestBroadcast:
    """ConnectionManager.broadcast behaviour."""

    @pytest.mark.asyncio
    async def test_broadcast_sends_json_to_all_connections(self, manager: ConnectionManager, ws1: MagicMock, ws2: MagicMock) -> None:
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        await manager.connect(tenant_id, ws1)
        await manager.connect(tenant_id, ws2)
        message = {"type": "notification", "event": "test"}

        await manager.broadcast(tenant_id, message)

        ws1.send_text.assert_awaited_once_with('{"type": "notification", "event": "test"}')
        ws2.send_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcast_does_not_send_to_other_tenants(self, manager: ConnectionManager, ws1: MagicMock, ws2: MagicMock) -> None:
        t1 = "550e8400-e29b-41d4-a716-446655440000"
        t2 = "660e8400-e29b-41d4-a716-446655440001"
        await manager.connect(t1, ws1)
        await manager.connect(t2, ws2)
        message = {"type": "notification"}

        await manager.broadcast(t1, message)

        ws1.send_text.assert_awaited_once()
        ws2.send_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_broadcast_noop_for_unknown_tenant(self, manager: ConnectionManager, ws1: MagicMock) -> None:
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"

        # Should not raise
        await manager.broadcast(tenant_id, {"type": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_removes_stale_connections(self, manager: ConnectionManager, ws1: MagicMock, ws2: MagicMock) -> None:
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        ws1.send_text = AsyncMock(side_effect=Exception("Connection closed"))
        ws2.send_text = AsyncMock()
        await manager.connect(tenant_id, ws1)
        await manager.connect(tenant_id, ws2)

        await manager.broadcast(tenant_id, {"type": "test"})

        # ws1 should be removed (stale)
        assert ws1 not in manager.get_connections(tenant_id)
        # ws2 should still be there
        assert ws2 in manager.get_connections(tenant_id)
        ws2.send_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcast_removes_tenant_when_all_stale(self, manager: ConnectionManager, ws1: MagicMock) -> None:
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        ws1.send_text = AsyncMock(side_effect=Exception("Closed"))
        await manager.connect(tenant_id, ws1)

        await manager.broadcast(tenant_id, {"type": "test"})

        assert tenant_id not in manager._connections


class TestGetConnections:
    """ConnectionManager.get_connections behaviour."""

    def test_get_connections_returns_empty_set_for_unknown_tenant(self, manager: ConnectionManager) -> None:
        tenant_id = "unknown-tenant-id"

        conns = manager.get_connections(tenant_id)

        assert conns == set()

    @pytest.mark.asyncio
    async def test_get_connections_returns_connections_for_tenant(self, manager: ConnectionManager, ws1: MagicMock) -> None:
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        await manager.connect(tenant_id, ws1)

        conns = manager.get_connections(tenant_id)

        assert ws1 in conns


class TestCloseAll:
    """ConnectionManager.close_all behaviour."""

    @pytest.mark.asyncio
    async def test_close_all_closes_all_connections(self, manager: ConnectionManager, ws1: MagicMock, ws2: MagicMock) -> None:
        t1 = "550e8400-e29b-41d4-a716-446655440000"
        t2 = "660e8400-e29b-41d4-a716-446655440001"
        await manager.connect(t1, ws1)
        await manager.connect(t2, ws2)

        await manager.close_all()

        ws1.close.assert_awaited_once_with(code=1001, reason="Server shutting down")
        ws2.close.assert_awaited_once_with(code=1001, reason="Server shutting down")
        assert manager._connections == {}

    @pytest.mark.asyncio
    async def test_close_all_safe_when_no_connections(self, manager: ConnectionManager) -> None:
        await manager.close_all()  # Should not raise

    @pytest.mark.asyncio
    async def test_close_all_continues_on_close_error(self, manager: ConnectionManager, ws1: MagicMock, ws2: MagicMock) -> None:
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        ws1.close = AsyncMock(side_effect=Exception("Close failed"))
        ws2.close = AsyncMock()
        await manager.connect(tenant_id, ws1)
        await manager.connect(tenant_id, ws2)

        await manager.close_all()

        ws2.close.assert_awaited_once()
        assert manager._connections == {}
