"""WebSocket-related dependency injection.

Provides the singleton ``ConnectionManager`` instance (app-scoped, not
request-scoped) and related dependencies.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from src.common.infrastructure.adapters.websocket.manager import ConnectionManager

_manager: ConnectionManager | None = None


def _get_ws_manager() -> ConnectionManager:
    """Return the singleton ConnectionManager instance."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


GetWsManager = Annotated[ConnectionManager, Depends(_get_ws_manager)]
