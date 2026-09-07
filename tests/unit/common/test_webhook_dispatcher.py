"""Unit tests for WebhookDispatcher.

Tests HMAC-SHA256 signing, successful delivery, retry on failure,
and max retries exceeded behavior.
"""

import hashlib
import hmac
import json
from unittest import mock as unittest_mock
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient, HTTPError, Response

from src.common.infrastructure.events.webhook_dispatcher import WebhookDispatcher


class TestWebhookDispatcher:
    """WebhookDispatcher signs payloads and retries on failure."""

    def setup_method(self) -> None:
        self.client = AsyncMock(spec=AsyncClient)
        self.dispatcher = WebhookDispatcher(client=self.client)

    def _make_mock_response(self, status_code: int) -> MagicMock:
        resp = MagicMock(spec=Response)
        resp.is_success = 200 <= status_code < 300
        resp.status_code = status_code
        return resp

    def _compute_expected_signature(self, secret: str, payload: dict) -> str:
        body = json.dumps(payload, default=str)
        sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        return f"sha256={sig}"

    @pytest.mark.asyncio
    async def test_dispatch_returns_true_on_success(self) -> None:
        """Successful HTTP POST returns True."""
        self.client.post = AsyncMock(return_value=self._make_mock_response(200))

        result = await self.dispatcher.dispatch(
            url="https://example.com/webhook",
            secret="my-secret",
            payload={"event": "test"},
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_dispatch_sends_hmac_signature(self) -> None:
        """Payload is signed with HMAC-SHA256 and sent in X-Webhook-Signature."""
        self.client.post = AsyncMock(return_value=self._make_mock_response(200))

        payload = {"event": "test", "id": "123"}
        secret = "my-secret"

        await self.dispatcher.dispatch(
            url="https://example.com/webhook",
            secret=secret,
            payload=payload,
        )

        self.client.post.assert_awaited_once()
        (args, kwargs) = self.client.post.call_args
        assert args[0] == "https://example.com/webhook"
        headers = kwargs["headers"]
        assert "X-Webhook-Signature" in headers

        # Verify the signature is correct
        kwargs["content"]
        expected_sig = self._compute_expected_signature(secret, payload)
        assert headers["X-Webhook-Signature"] == expected_sig

    @pytest.mark.asyncio
    async def test_dispatch_sends_content_type_json(self) -> None:
        """Content-Type header is application/json."""
        self.client.post = AsyncMock(return_value=self._make_mock_response(200))

        await self.dispatcher.dispatch(
            url="https://example.com/webhook",
            secret="s",
            payload={"key": "value"},
        )

        (_, kwargs) = self.client.post.call_args
        assert kwargs["headers"]["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_dispatch_retries_on_http_500(self) -> None:
        """HTTP 500 triggers retry; returns True if retry succeeds."""
        # First call fails (500), second succeeds (200)
        self.client.post = AsyncMock(
            side_effect=[
                self._make_mock_response(500),
                self._make_mock_response(200),
            ]
        )

        result = await self.dispatcher.dispatch(
            url="https://example.com/webhook",
            secret="s",
            payload={"event": "test"},
        )

        assert result is True
        assert self.client.post.await_count == 2

    @pytest.mark.asyncio
    async def test_dispatch_retries_on_http_429(self) -> None:
        """HTTP 429 triggers retry."""
        self.client.post = AsyncMock(
            side_effect=[
                self._make_mock_response(429),
                self._make_mock_response(200),
            ]
        )

        result = await self.dispatcher.dispatch(
            url="https://example.com/webhook",
            secret="s",
            payload={"event": "test"},
        )

        assert result is True
        assert self.client.post.await_count == 2

    @pytest.mark.asyncio
    async def test_dispatch_retries_on_network_error(self) -> None:
        """HTTPError (network failure) triggers retry."""
        self.client.post = AsyncMock(
            side_effect=[
                HTTPError("Connection refused"),
                self._make_mock_response(200),
            ]
        )

        result = await self.dispatcher.dispatch(
            url="https://example.com/webhook",
            secret="s",
            payload={"event": "test"},
        )

        assert result is True
        assert self.client.post.await_count == 2

    @pytest.mark.asyncio
    async def test_dispatch_returns_false_after_max_retries(self) -> None:
        """After MAX_RETRIES failures, dispatch returns False."""
        self.client.post = AsyncMock(return_value=self._make_mock_response(500))

        result = await self.dispatcher.dispatch(
            url="https://example.com/webhook",
            secret="s",
            payload={"event": "test"},
        )

        assert result is False
        assert self.client.post.await_count == WebhookDispatcher.MAX_RETRIES

    @pytest.mark.asyncio
    async def test_dispatch_default_client_is_created(self) -> None:
        """When no client is provided, a default AsyncClient is used."""
        dispatcher = WebhookDispatcher()
        assert dispatcher._client is not None
        assert isinstance(dispatcher._client, AsyncClient)

    @pytest.mark.asyncio
    async def test_dispatch_uses_exponential_backoff(self) -> None:
        """Sleep durations follow 1s, 2s, 4s, 8s, 16s pattern."""
        import asyncio

        self.client.post = AsyncMock(return_value=self._make_mock_response(500))

        original_sleep = asyncio.sleep
        sleep_durations: list[float] = []

        async def tracking_sleep(duration: float) -> None:
            sleep_durations.append(duration)
            await original_sleep(0)  # Don't actually wait

        with (
            unittest_mock.patch("asyncio.sleep", tracking_sleep),
        ):
            result = await self.dispatcher.dispatch(
                url="https://example.com/webhook",
                secret="s",
                payload={"event": "test"},
            )

        assert result is False
        # We expect 4 sleeps (between 5 attempts)
        assert len(sleep_durations) == WebhookDispatcher.MAX_RETRIES - 1
        assert sleep_durations == [1.0, 2.0, 4.0, 8.0]

    @pytest.mark.asyncio
    async def test_signature_changes_with_different_secret(self) -> None:
        """Different secrets produce different signatures."""
        self.client.post = AsyncMock(return_value=self._make_mock_response(200))

        payload = {"event": "test"}

        await self.dispatcher.dispatch(
            url="https://example.com/webhook",
            secret="secret-a",
            payload=payload,
        )

        (_, kwargs_a) = self.client.post.call_args
        sig_a = kwargs_a["headers"]["X-Webhook-Signature"]

        await self.dispatcher.dispatch(
            url="https://example.com/webhook",
            secret="secret-b",
            payload=payload,
        )

        (_, kwargs_b) = self.client.post.call_args
        sig_b = kwargs_b["headers"]["X-Webhook-Signature"]

        assert sig_a != sig_b
