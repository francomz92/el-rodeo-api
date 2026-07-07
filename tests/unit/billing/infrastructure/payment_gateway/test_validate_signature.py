"""Tests for MercadoPagoHttpClient.validate_signature."""

from __future__ import annotations

import hashlib
import hmac
from unittest.mock import patch

import pytest

from src.billing.infrastructure.payment_gateway._client import (
    MercadoPagoHttpClient,
)


def _compute_expected_hmac(data_id: str, x_request_id: str, ts: str, secret: str) -> str:
    """Compute the expected HMAC-SHA256 hex digest for a test vector."""
    data_to_sign = f"{data_id}\n{data_id}|{x_request_id}\n{ts}"
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=data_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


class TestValidateSignature:
    """MercadoPagoHttpClient.validate_signature tests with known vectors."""

    _patcher: patch | None = None

    @pytest.fixture(autouse=True)
    def _patch_settings(self) -> None:
        """Ensure settings has the required MP config values."""
        patcher = patch(
            "src.common.infrastructure.core._config.settings.MP_ACCESS_TOKEN",
            "test-token",
        )
        patcher.start()
        TestValidateSignature._patcher = patcher
        yield
        if TestValidateSignature._patcher is not None:
            TestValidateSignature._patcher.stop()
            TestValidateSignature._patcher = None

    def _make_client(self) -> MercadoPagoHttpClient:
        """Create a client suitable for testing validate_signature.

        Uses __new__ + manual attribute assignment to avoid creating
        an actual httpx.AsyncClient (which is not needed for the
        synchronous validate_signature method).
        """
        client = MercadoPagoHttpClient.__new__(MercadoPagoHttpClient)
        client._access_token = "test-token"
        client._webhook_secret = "test-secret"
        return client

    def test_valid_signature(self) -> None:
        """A correctly computed signature validates successfully."""
        data_id = "pay-123"
        x_request_id = "req-abc"
        ts = "1234567890"
        secret = "s3cret"

        expected_hmac = _compute_expected_hmac(data_id, x_request_id, ts, secret)
        x_signature = f"ts={ts}|v1={expected_hmac}"

        client = self._make_client()
        result = client.validate_signature(
            x_signature=x_signature,
            x_request_id=x_request_id,
            data_id=data_id,
            secret=secret,
        )

        assert result is True

    def test_invalid_signature(self) -> None:
        """A mangled signature fails validation."""
        data_id = "pay-123"
        x_request_id = "req-abc"
        ts = "1234567890"
        secret = "s3cret"

        x_signature = f"ts={ts}|v1=invalidhmacvalue"

        client = self._make_client()
        result = client.validate_signature(
            x_signature=x_signature,
            x_request_id=x_request_id,
            data_id=data_id,
            secret=secret,
        )

        assert result is False

    def test_empty_header_returns_false(self) -> None:
        """Empty x-signature returns False."""
        client = self._make_client()
        result = client.validate_signature(
            x_signature="",
            x_request_id="req-abc",
            data_id="pay-123",
            secret="s3cret",
        )
        assert result is False

    def test_missing_ts_or_v1_returns_false(self) -> None:
        """Header without ts or v1 format returns False."""
        client = self._make_client()
        result = client.validate_signature(
            x_signature="invalid-format",
            x_request_id="req-abc",
            data_id="pay-123",
            secret="s3cret",
        )
        assert result is False

    def test_empty_secret_returns_false(self) -> None:
        """An empty secret returns False."""
        data_id = "pay-123"
        x_request_id = "req-abc"
        ts = "1234567890"
        expected_hmac = _compute_expected_hmac(data_id, x_request_id, ts, "s3cret")
        x_signature = f"ts={ts}|v1={expected_hmac}"

        client = self._make_client()
        result = client.validate_signature(
            x_signature=x_signature,
            x_request_id=x_request_id,
            data_id=data_id,
            secret="",
        )
        assert result is False

    def test_wrong_secret_fails(self) -> None:
        """A different secret produces a different HMAC."""
        data_id = "pay-123"
        x_request_id = "req-abc"
        ts = "1234567890"

        # Compute with one secret
        expected = _compute_expected_hmac(data_id, x_request_id, ts, "correct-secret")
        x_signature = f"ts={ts}|v1={expected}"

        client = self._make_client()
        # Validate with a DIFFERENT secret
        result = client.validate_signature(
            x_signature=x_signature,
            x_request_id=x_request_id,
            data_id=data_id,
            secret="wrong-secret",
        )
        assert result is False

    def test_different_data_id_fails(self) -> None:
        """A signature computed for data_id=A fails for data_id=B."""
        data_id_a = "pay-123"
        data_id_b = "pay-456"
        x_request_id = "req-abc"
        ts = "1234567890"
        secret = "s3cret"

        expected = _compute_expected_hmac(data_id_a, x_request_id, ts, secret)
        x_signature = f"ts={ts}|v1={expected}"

        client = self._make_client()
        result = client.validate_signature(
            x_signature=x_signature,
            x_request_id=x_request_id,
            data_id=data_id_b,
            secret=secret,
        )
        assert result is False
