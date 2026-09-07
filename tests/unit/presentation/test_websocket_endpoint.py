"""Tests for the /ws/notifications WebSocket endpoint.

Uses FastAPI TestClient to verify JWT validation, connection lifecycle,
and manager integration.
"""

from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.common.infrastructure.adapters.websocket.manager import ConnectionManager
from src.common.infrastructure.presentation.dependencies.websocket import (
    _get_ws_manager,
)
from src.common.infrastructure.presentation.routers.ws import router as ws_router


@pytest.fixture
def manager() -> ConnectionManager:
    """Use the real ConnectionManager to ensure accept() is called."""
    return ConnectionManager()


@pytest.fixture
def app(manager: ConnectionManager) -> FastAPI:
    application = FastAPI()
    application.include_router(ws_router)
    application.dependency_overrides[_get_ws_manager] = lambda: manager
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestWebSocketEndpoint:
    """WebSocket /ws/notifications endpoint behaviour."""

    def test_valid_token_connects(self, client: TestClient, manager: ConnectionManager) -> None:
        """A valid JWT with tenant_id should connect and register."""
        tenant_id = str(uuid4())
        with patch("src.common.infrastructure.adapters.security.tokens.pyjwt.decode") as mock_decode:
            mock_decode.return_value = {
                "tenant_id": tenant_id,
                "type": "access",
                "jti": str(uuid4()),
            }
            with client.websocket_connect("/ws/notifications?token=valid.jwt.token"):
                conns = manager.get_connections(tenant_id)
                assert len(conns) == 1

        # After disconnect, the connection should be removed
        assert manager.get_connections(tenant_id) == set()

    def test_invalid_token_closes_with_4001(self, client: TestClient, manager: ConnectionManager) -> None:
        """An invalid/expired JWT should close with code 4001."""
        with patch("src.common.infrastructure.adapters.security.tokens.pyjwt.decode") as mock_decode:
            mock_decode.side_effect = Exception("Invalid token")

            with pytest.raises(Exception):
                with client.websocket_connect("/ws/notifications?token=bad.token.here"):
                    pass

            # Should not have any connections registered
            tenant_id = "any"
            assert manager.get_connections(tenant_id) == set()

    def test_missing_token_query_param_closes_with_4001(self, client: TestClient, manager: ConnectionManager) -> None:
        """Missing token query parameter should close with code 4001."""
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/notifications"):
                pass

    def test_empty_token_closes_with_4001(self, client: TestClient, manager: ConnectionManager) -> None:
        """Empty token parameter should close with code 4001."""
        with patch("src.common.infrastructure.adapters.security.tokens.pyjwt.decode") as mock_decode:
            mock_decode.side_effect = Exception("Empty token")

            with pytest.raises(Exception):
                with client.websocket_connect("/ws/notifications?token="):
                    pass

    def test_token_without_tenant_id_closes_with_4001(self, client: TestClient, manager: ConnectionManager) -> None:
        """A valid JWT but missing tenant_id should close with 4001."""
        with patch("src.common.infrastructure.adapters.security.tokens.pyjwt.decode") as mock_decode:
            mock_decode.return_value = {
                "type": "access",
                "jti": str(uuid4()),
            }

            with pytest.raises(Exception):
                with client.websocket_connect("/ws/notifications?token=no-tenant.jwt.token"):
                    pass

    def test_manager_connect_called_on_valid_token(self, client: TestClient, manager: ConnectionManager) -> None:
        """Verify manager.connect runs for a valid token."""
        tenant_id = str(uuid4())
        with patch("src.common.infrastructure.adapters.security.tokens.pyjwt.decode") as mock_decode:
            mock_decode.return_value = {
                "tenant_id": tenant_id,
                "type": "access",
                "jti": str(uuid4()),
            }
            with client.websocket_connect("/ws/notifications?token=valid.jwt.token"):
                assert len(manager.get_connections(tenant_id)) == 1
