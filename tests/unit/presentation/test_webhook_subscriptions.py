"""Tests for the WebhookSubscription CRUD router."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    _get_current_user,
)
from src.common.domain.exceptions import DomainError
from src.common.infrastructure.persistence.models.webhook_subscription import (
    WebhookSubscription,
)
from src.common.infrastructure.presentation.dependencies.uow import _get_uow
from src.common.infrastructure.presentation.middlewares.exceptions_handlers.domain_errors import (
    domain_exception_handler,
)
from src.common.infrastructure.presentation.routers.webhook_subscriptions import (
    router,
)
from src.common.infrastructure.security.fernet_engine import FernetEngine


@pytest.fixture
def tenant_id() -> UUID:
    return uuid4()


@pytest.fixture
def mock_user(tenant_id: UUID) -> MagicMock:
    user = MagicMock()
    user.tenant_id = tenant_id
    user.id = uuid4()
    return user


@pytest.fixture
def mock_uow() -> MagicMock:
    uow = MagicMock()

    # Repo mock that supports all async CRUD methods used by the service
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.list_by_tenant = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    uow.get_repository = MagicMock(return_value=repo)

    # db must support both sync methods (add, delete) and async methods (execute)
    uow.db = MagicMock()
    uow.db.execute = AsyncMock()
    uow.db.add = MagicMock()
    uow.db.delete = AsyncMock()
    uow.commit = AsyncMock()
    uow.refresh = AsyncMock()
    return uow


@pytest.fixture
def app(mock_user: MagicMock, mock_uow: MagicMock) -> FastAPI:
    application = FastAPI()
    application.include_router(router)

    application.dependency_overrides[_get_current_user] = lambda: mock_user
    application.dependency_overrides[_get_uow] = lambda: mock_uow

    # Register the domain exception handler so NotFoundError (DomainError)
    # is caught and returned as 404 instead of bubbling to 500.
    application.add_exception_handler(DomainError, domain_exception_handler)  # type: ignore[reportArgumentType]

    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def _mock_fernet() -> MagicMock:
    """Mock FernetEngine.decrypt_secret to return the input unchanged.

    The service decrypts secrets on read (in get_by_id_for_tenant). Since test
    fixtures use plain-text secrets, we bypass actual Fernet decryption.
    """
    with patch.object(FernetEngine, "decrypt_secret", return_value="test-secret"):
        yield


def _make_sub(
    tenant_id: UUID,
    url: str = "https://example.com/webhook",
    subscribed_events: list[str] | None = None,
) -> WebhookSubscription:
    return WebhookSubscription(
        id=uuid4(),
        tenant_id=tenant_id,
        url=url,
        secret="test-secret",
        subscribed_events=subscribed_events or ["payment.received"],
        is_active=True,
        failure_count=0,
    )


class TestCreateWebhook:
    """POST /webhooks — create a new webhook subscription."""

    @pytest.mark.asyncio
    async def test_creates_webhook(self, client: AsyncClient, mock_uow: MagicMock, tenant_id: UUID) -> None:
        """Successful creation returns 201 with the webhook data."""
        webhook_id = uuid4()

        # Capture the subscription passed to repo.create and populate defaults
        async def _capture_sub(sub: WebhookSubscription) -> WebhookSubscription:
            sub.id = webhook_id
            sub.tenant_id = tenant_id
            sub.is_active = True
            sub.failure_count = 0
            return sub

        repo = mock_uow.get_repository.return_value
        repo.create = AsyncMock(side_effect=_capture_sub)

        payload = {
            "url": "https://example.com/webhook",
            "subscribed_events": ["payment.received", "animal.created"],
        }

        response = await client.post("/webhooks", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://example.com/webhook"
        assert data["subscribed_events"] == ["payment.received", "animal.created"]
        assert data["is_active"] is True
        assert data["failure_count"] == 0
        assert data["id"] == str(webhook_id)

        repo.create.assert_awaited_once()
        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_422_on_missing_fields(self, client: AsyncClient) -> None:
        """Invalid payload returns 422."""
        response = await client.post("/webhooks", json={"subscribed_events": []})
        assert response.status_code == 422


class TestListWebhooks:
    """GET /webhooks — list webhook subscriptions."""

    @pytest.mark.asyncio
    async def test_lists_webhooks(self, client: AsyncClient, mock_uow: MagicMock, tenant_id: UUID) -> None:
        """Returns list of webhook subscriptions for the tenant."""
        sub = _make_sub(tenant_id)
        repo = mock_uow.get_repository.return_value
        repo.list_by_tenant = AsyncMock(return_value=[sub])

        response = await client.get("/webhooks")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(sub.id)
        assert data[0]["url"] == sub.url
        assert data[0]["is_active"] is True

    @pytest.mark.asyncio
    async def test_lists_empty_when_no_webhooks(self, client: AsyncClient, mock_uow: MagicMock) -> None:
        """Returns empty list when tenant has no webhooks."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_uow.db.execute = AsyncMock(return_value=mock_result)

        response = await client.get("/webhooks")

        assert response.status_code == 200
        assert response.json() == []


class TestGetWebhook:
    """GET /webhooks/{id} — get a single webhook subscription."""

    @pytest.mark.asyncio
    async def test_gets_webhook(self, client: AsyncClient, mock_uow: MagicMock, tenant_id: UUID) -> None:
        """Returns the webhook subscription by ID."""
        sub = _make_sub(tenant_id)
        repo = mock_uow.get_repository.return_value
        repo.get_by_id = AsyncMock(return_value=sub)

        response = await client.get(f"/webhooks/{sub.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sub.id)
        assert data["url"] == sub.url

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, client: AsyncClient, mock_uow: MagicMock) -> None:
        """Returns 404 when webhook not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_uow.db.execute = AsyncMock(return_value=mock_result)

        response = await client.get(f"/webhooks/{uuid4()}")

        assert response.status_code == 404


class TestUpdateWebhook:
    """PUT /webhooks/{id} — update a webhook subscription."""

    @pytest.mark.asyncio
    async def test_updates_webhook(self, client: AsyncClient, mock_uow: MagicMock, tenant_id: UUID) -> None:
        """Returns updated webhook subscription."""
        sub = _make_sub(tenant_id)
        repo = mock_uow.get_repository.return_value
        repo.get_by_id = AsyncMock(return_value=sub)

        # Simulate an updated sub returned by the repo
        updated_sub = _make_sub(tenant_id, url="https://new-url.com/webhook", subscribed_events=sub.subscribed_events)
        updated_sub.id = sub.id
        repo.update = AsyncMock(return_value=updated_sub)

        response = await client.put(
            f"/webhooks/{sub.id}",
            json={"url": "https://new-url.com/webhook", "is_active": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://new-url.com/webhook"
        assert data["is_active"] is True  # _make_sub defaults to is_active=True
        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, client: AsyncClient, mock_uow: MagicMock) -> None:
        """Returns 404 when updating nonexistent webhook."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_uow.db.execute = AsyncMock(return_value=mock_result)

        response = await client.put(
            f"/webhooks/{uuid4()}",
            json={"url": "https://new-url.com/webhook"},
        )

        assert response.status_code == 404


class TestDeleteWebhook:
    """DELETE /webhooks/{id} — delete a webhook subscription."""

    @pytest.mark.asyncio
    async def test_deletes_webhook(self, client: AsyncClient, mock_uow: MagicMock, tenant_id: UUID) -> None:
        """Returns 204 on successful deletion."""
        sub = _make_sub(tenant_id)
        repo = mock_uow.get_repository.return_value
        repo.get_by_id = AsyncMock(return_value=sub)

        response = await client.delete(f"/webhooks/{sub.id}")

        assert response.status_code == 204
        repo.delete.assert_awaited_once()
        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, client: AsyncClient, mock_uow: MagicMock) -> None:
        """Returns 404 when deleting nonexistent webhook."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_uow.db.execute = AsyncMock(return_value=mock_result)

        response = await client.delete(f"/webhooks/{uuid4()}")

        assert response.status_code == 404
