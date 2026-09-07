"""MercadoPago HTTP client implementing IPaymentGateway.

Uses httpx.AsyncClient with Bearer auth, 5xx retry with exponential
backoff, and error mapping to MercadoPagoError.

Split into _http.py (request/retry), _signature.py (webhook validation),
and _mappers.py (status mapping) for maintainability.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx

from src.billing.domain.exceptions import PaymentGatewayError
from src.billing.domain.repositories._payment_gateway_port import (
    AuthorizedPaymentResult,
    AutoRecurringData,
    BackUrlsData,
    IPaymentGateway,
    ItemData,
    PaymentResult,
    PreferenceResult,
    SubscriptionResult,
)
from src.common.infrastructure.core._config import settings

from ._http import request as _request
from ._mappers import map_mp_status as _map_mp_status
from ._signature import validate_signature as _validate_signature

__all__ = ["MercadoPagoHttpClient"]


class MercadoPagoHttpClient(IPaymentGateway):
    """HTTP client for the MercadoPago API.

    Provides preference creation, payment retrieval, refunds, and
    webhook signature validation.
    """

    BASE_URL = "https://api.mercadopago.com"

    def __init__(self) -> None:
        access_token = settings.MP_ACCESS_TOKEN
        if not access_token:
            raise PaymentGatewayError(
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
        back_urls: BackUrlsData,
        notification_url: str,
        external_reference: str,
    ) -> PreferenceResult:
        """Create a MercadoPago Checkout Pro preference."""
        body: dict[str, Any] = {
            "items": [
                {
                    "title": item.title,
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "currency_id": item.currency_id,
                }
                for item in items
            ],
            "back_urls": {
                "success": back_urls.success,
                "failure": back_urls.failure,
                "pending": back_urls.pending,
            },
            "notification_url": notification_url,
            "external_reference": external_reference,
        }
        data = await _request(
            self._client,
            method="POST",
            path="/checkout/preferences",
            json_body=body,
            idempotent=True,
        )
        return PreferenceResult(id=data["id"], init_point=data["init_point"])

    async def get_payment(self, payment_id: str) -> PaymentResult:
        """Get the status and details of a MercadoPago payment."""
        data = await _request(
            self._client,
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
        """Refund a MercadoPago payment, fully or partially."""
        body: dict[str, Any] = {}
        if amount is not None:
            body["amount"] = float(amount)

        data = await _request(
            self._client,
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
        """Validate an IPN webhook x-signature using HMAC-SHA256."""
        return _validate_signature(x_signature, x_request_id, data_id, secret)

    # ── Subscription methods (Phase 0b) ────────────────────────────────────

    async def create_subscription(
        self,
        reason: str,
        auto_recurring: AutoRecurringData,
        payer_email: str,
        card_token_id: str,
        external_reference: str,
        back_url: str,
    ) -> SubscriptionResult:
        """Create a MercadoPago subscription with immediate first charge."""
        body: dict[str, Any] = {
            "reason": reason,
            "auto_recurring": {
                "frequency": auto_recurring.frequency,
                "frequency_type": auto_recurring.frequency_type,
                "transaction_amount": auto_recurring.transaction_amount,
                "currency_id": auto_recurring.currency_id,
            },
            "payer_email": payer_email,
            "card_token_id": card_token_id,
            "external_reference": external_reference,
            "back_url": back_url,
            "status": "authorized",
        }
        data = await _request(
            self._client,
            method="POST",
            path="/preapproval",
            json_body=body,
            idempotent=True,
        )
        return self._parse_subscription_result(data)

    async def get_subscription(self, gateway_subscription_id: str) -> SubscriptionResult:
        """Get the status and details of a MercadoPago subscription."""
        data = await _request(
            self._client,
            method="GET",
            path=f"/preapproval/{gateway_subscription_id}",
        )
        return self._parse_subscription_result(data)

    async def cancel_subscription(self, gateway_subscription_id: str) -> None:
        """Cancel a MercadoPago subscription."""
        await _request(
            self._client,
            method="PUT",
            path=f"/preapproval/{gateway_subscription_id}",
            json_body={"status": "cancelled"},
        )

    async def update_subscription(self, gateway_subscription_id: str, data: dict) -> SubscriptionResult:
        """Update a MercadoPago subscription (e.g. change payment method)."""
        result = await _request(
            self._client,
            method="PUT",
            path=f"/preapproval/{gateway_subscription_id}",
            json_body=data,
        )
        return self._parse_subscription_result(result)

    async def get_authorized_payment(self, authorized_payment_id: str) -> AuthorizedPaymentResult:
        """Get details of an authorized payment invoice for a subscription."""
        data = await _request(
            self._client,
            method="GET",
            path=f"/authorized_payments/{authorized_payment_id}",
        )
        txn_amount = data.get("transaction_amount")
        return AuthorizedPaymentResult(
            id=str(data["id"]),
            status=data.get("status", ""),
            preapproval_id=str(data.get("preapproval_id", "")),
            transaction_amount=Decimal(str(txn_amount)) if txn_amount is not None else None,
            payment_id=data.get("payment_id") or data.get("payment", {}).get("id"),
            next_billing_date=self._parse_mp_datetime(data.get("next_billing_date")),
        )

    @staticmethod
    def _parse_subscription_result(data: dict) -> SubscriptionResult:
        """Parse MP /preapproval response into SubscriptionResult."""
        return SubscriptionResult(
            id=str(data["id"]),
            status=data.get("status", ""),
            next_billing_date=MercadoPagoHttpClient._parse_mp_datetime(data.get("next_billing_date")),
            billing_date=MercadoPagoHttpClient._parse_mp_datetime(data.get("billing_date")),
            card_id=data.get("card_id"),
            payer_email=data.get("payer_email"),
        )

    @staticmethod
    def _parse_mp_datetime(value: str | None) -> datetime | None:
        """Parse an ISO 8601 datetime string from MP, or return None."""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                if value.endswith("Z"):
                    value = value[:-1] + "+00:00"
                return datetime.fromisoformat(value)
            return None
        except (ValueError, TypeError):
            return None

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
