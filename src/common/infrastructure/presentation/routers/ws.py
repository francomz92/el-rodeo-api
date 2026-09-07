"""WebSocket notification endpoint.

Provides a ``/ws/notifications`` WebSocket endpoint that validates JWT
tokens and manages per-tenant connections via ``ConnectionManager``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from src.common.infrastructure.adapters.websocket.manager import ConnectionManager
from src.common.infrastructure.presentation.dependencies.websocket import (
    GetWsManager,
)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...),
    manager: ConnectionManager = Depends(GetWsManager),
) -> None:
    """Accept a WebSocket connection for real-time notifications.

    Validates a short-lived WS-specific token (not the REST access token).
    Closes with code 4001 on invalid, expired, or missing token.
    """
    try:
        from src.common.infrastructure.adapters.security.tokens import TokenService
        from src.common.infrastructure.core import settings

        token_service = TokenService(
            secret=settings.SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        payload = token_service.decode(token)

        # Must be a WS-specific token
        if payload.get("type") != "ws" or payload.get("purpose") != "websocket":
            await websocket.close(code=4001)
            return

        tenant_id_str = payload.get("tenant_id")
        if tenant_id_str is None:
            await websocket.close(code=4001)
            return
        tenant_id = str(tenant_id_str)
    except Exception:
        await websocket.close(code=4001)
        return

    try:
        await manager.connect(tenant_id, websocket)
    except Exception:
        await websocket.close(code=4001)
        return
    try:
        while True:
            # Keep connection alive by waiting for messages
            # (we don't process client messages in this version)
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(tenant_id, websocket)
