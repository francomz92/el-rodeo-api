"""MercadoPago HTTP client implementing IPaymentGateway.

Uses httpx.AsyncClient with Bearer auth, 5xx retry with exponential
backoff, and error mapping to MercadoPagoError.
"""

import hashlib
import hmac
import re
from decimal import Decimal
from typing import Any

import httpx

from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.exceptions import MercadoPagoError
from src.billing.domain.repositories._payment_gateway_port import (
    IPaymentGateway,
    ItemData,
    PaymentResult,
    PreferenceResult,
)
from src.common.infrastructure.core._config import settings


class MercadoPagoHttpClient(IPaymentGateway):
    """HTTP client for the MercadoPago API.

    Provides preference creation, payment retrieval, refunds, and
    webhook signature validation.
    """

    BASE_URL = "https://api.mercadopago.com"

    def __init__(self) -> None:
        access_token = settings.MP_ACCESS_TOKEN
        if not access_token:
            raise MercadoPagoError(
                message="MP_ACCESS_TOKEN is not configured",
                status_code=0,
            )
        self._access_token = access_token
        self._webhook_secret = settings.MP_WEBHOOK_SECRET
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def create_preference(
        self,
        items: list[ItemData],
        back_urls: dict,
        notification_url: str,
        external_reference: str,
    ) -> PreferenceResult:
        """Create a MercadoPago Checkout Pro preference."""
        body: dict[str, Any] = {
            "items": [
                {
                    "title": item.title,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "currency_id": item.currency_id,
                }
                for item in items
            ],
            "back_urls": back_urls,
            "notification_url": notification_url,
            "external_reference": external_reference,
        }
        data = await self._request(
            method="POST",
            path="/checkout/preferences",
            json_body=body,
            idempotent=True,
        )
        return PreferenceResult(id=data["id"], init_point=data["init_point"])

    async def get_payment(self, payment_id: str) -> PaymentResult:
        """Get the status and details of a MercadoPago payment.

        Returns a PaymentResult with status, external_reference, amount, etc.
        """
        data = await self._request(
            method="GET",
            path=f"/v1/payments/{payment_id}",
        )
        raw_status = data.get("status", "")
        txn_amount = data.get("transaction_amount")
        return PaymentResult(
            id=str(payment_id),
            status=_map_mp_status(raw_status),
            external_reference=data.get("external_reference"),
            transaction_amount=Decimal(str(txn_amount)) if txn_amount is not None else None,
            payment_method_id=data.get("payment_method", {}).get("id") if isinstance(data.get("payment_method"), dict) else None,
            payment_type_id=data.get("payment_type_id"),
            payer_email=data.get("payer", {}).get("email") if isinstance(data.get("payer"), dict) else None,
        )

    async def refund(self, payment_id: str, amount: Decimal | None = None) -> bool:
        """Refund a MercadoPago payment, fully or partially.

        Args:
            payment_id: The MercadoPago payment ID.
            amount: Amount to refund (None for full refund).

        Returns:
            True if the refund was successful.
        """
        body: dict[str, Any] = {}
        if amount is not None:
            body["amount"] = float(amount)

        data = await self._request(
            method="POST",
            path=f"/v1/payments/{payment_id}/refunds",
            json_body=body or None,
        )
        return data.get("status") == "approved"

    def validate_signature(
        self,
        x_signature: str,
        x_request_id: str,
        data_id: str,
        secret: str,
    ) -> bool:
        """Validate an IPN webhook x-signature using HMAC-SHA256.

        The MP x-signature header format is: ts=<timestamp>|v1=<hmac_value>

        The data to sign is:
            data_id + "\\n" + data_id + "|" + x_request_id + "\\n" + ts

        Args:
            x_signature: The x-signature header value (ts=...|v1=...).
            x_request_id: The x-request-id header value.
            data_id: The data.id query parameter value.
            secret: The webhook secret key.

        Returns:
            True if the signature is valid.
        """
        if not x_signature or not secret:
            return False

        # Parse ts and v1 from the x-signature header
        ts_match = re.search(r"ts=(\d+)", x_signature)
        v1_match = re.search(r"v1=([a-f0-9]+)", x_signature)

        if not ts_match or not v1_match:
            return False

        ts = ts_match.group(1)
        expected_hmac = v1_match.group(1)

        # Build the data string to sign
        data_to_sign = f"{data_id}\n{data_id}|{x_request_id}\n{ts}"

        # Compute HMAC-SHA256
        computed = hmac.new(
            key=secret.encode("utf-8"),
            msg=data_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(computed, expected_hmac)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
        idempotent: bool = False,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Execute an HTTP request with retry logic.

        Args:
            method: HTTP method.
            path: API path (relative to base URL).
            json_body: Optional JSON body.
            idempotent: Whether to add x-idempotency-key header.
            max_retries: Maximum number of retries for 5xx errors.

        Returns:
            Parsed JSON response as dict.

        Raises:
            MercadoPagoError: On API error (4xx) or after exhausting retries.
        """
        headers: dict[str, str] = {}
        if idempotent:
            import uuid

            headers["x-idempotency-key"] = str(uuid.uuid4())

        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                response = await self._client.request(
                    method=method,
                    url=path,
                    headers=headers or None,
                    json=json_body,
                )

                if response.is_success:
                    return response.json()

                # 4xx — map error and raise immediately (no retry)
                if 400 <= response.status_code < 500:
                    mp_error = _extract_mp_error(response)
                    raise MercadoPagoError(
                        message=mp_error or "MercadoPago API error",
                        status_code=response.status_code,
                        mp_error=mp_error,
                    )

                # 5xx — retry with exponential backoff
                if response.status_code >= 500:
                    last_error = MercadoPagoError(
                        message=f"MP server error (HTTP {response.status_code})",
                        status_code=response.status_code,
                    )
                    if attempt < max_retries - 1:
                        import asyncio

                        wait = 2**attempt  # exponential: 1s, 2s, 4s
                        await asyncio.sleep(wait)
                    continue

            except httpx.TimeoutException as exc:
                last_error = MercadoPagoError(
                    message="MP API request timed out",
                    status_code=0,
                )
                if attempt < max_retries - 1:
                    import asyncio

                    await asyncio.sleep(2**attempt)
                else:
                    raise MercadoPagoError(
                        message="MP API request timed out after retries",
                        status_code=0,
                    ) from exc
            except httpx.RequestError as exc:
                raise MercadoPagoError(
                    message=f"MP API request failed: {exc}",
                    status_code=0,
                ) from exc

        # If we exhausted retries on 5xx
        if last_error:
            raise last_error

        return {}  # unreachable, satisfies return type


def _extract_mp_error(response: httpx.Response) -> str | None:
    """Extract the error message from a MercadoPago error response."""
    try:
        data = response.json()
        return data.get("message") or data.get("error") or str(data)
    except Exception:
        return response.text[:500] if response.text else None


def _map_mp_status(mp_status: str) -> PaymentStatus:
    """Map MercadoPago payment status to PaymentStatus enum."""
    mapping = {
        "pending": PaymentStatus.PENDING,
        "approved": PaymentStatus.APPROVED,
        "rejected": PaymentStatus.REJECTED,
        "refunded": PaymentStatus.REFUNDED,
        "cancelled": PaymentStatus.CANCELLED,
        "in_process": PaymentStatus.PENDING,
        "in_mediation": PaymentStatus.PENDING,
        "charged_back": PaymentStatus.CHARGED_BACK,
    }
    return mapping.get(mp_status, PaymentStatus.PENDING)
