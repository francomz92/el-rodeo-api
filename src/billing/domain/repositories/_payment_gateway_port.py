from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.billing.domain.entities._payment_status import PaymentStatus


@dataclass(frozen=True)
class ItemData:
    title: str
    quantity: int
    unit_price: Decimal
    currency_id: str = "ARS"


@dataclass(frozen=True)
class BackUrlsData:
    """URLs for redirect after payment."""

    success: str
    failure: str
    pending: str


@dataclass(frozen=True)
class AutoRecurringData:
    """Configuration for auto-recurring billing."""

    frequency: int
    frequency_type: str
    transaction_amount: float
    currency_id: str = "ARS"


@dataclass(frozen=True)
class PreferenceResult:
    id: str
    init_point: str


@dataclass(frozen=True)
class PaymentResult:
    """Rich result from get_payment, including gateway response details."""

    id: str
    status: PaymentStatus
    external_reference: str | None = None
    transaction_amount: Decimal | None = None
    payment_method_id: str | None = None
    payment_type_id: str | None = None
    payer_email: str | None = None


@dataclass(frozen=True)
class SubscriptionResult:
    """Result from gateway subscriptions API (/preapproval)."""

    id: str
    status: str
    next_billing_date: datetime | None = None
    billing_date: datetime | None = None
    card_id: str | None = None
    payer_email: str | None = None


@dataclass(frozen=True)
class AuthorizedPaymentResult:
    """Result from gateway authorized payments API."""

    id: str
    status: str
    preapproval_id: str
    transaction_amount: Decimal | None = None
    payment_id: str | None = None
    next_billing_date: datetime | None = None


class IPaymentGateway(ABC):
    @abstractmethod
    async def create_preference(
        self,
        items: list[ItemData],
        back_urls: BackUrlsData,
        notification_url: str,
        external_reference: str,
    ) -> PreferenceResult:
        """Create a Checkout Pro preference.

        Args:
            items: List of items to include in the preference.
            back_urls: URLs for success/failure/pending redirects.
            notification_url: Webhook URL for IPN notifications.
            external_reference: Tenant reference string.

        Returns:
            PreferenceResult with the preference ID and checkout URL.

        Raises:
            PaymentGatewayError: If the gateway API returns an error.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_payment(self, payment_id: str) -> PaymentResult:
        """Get the status and details of a gateway payment.

        Args:
            payment_id: The gateway payment ID.

        Returns:
            PaymentResult with status, external_reference, amount, etc.

        Raises:
            PaymentGatewayError: If the gateway API returns an error.
        """
        raise NotImplementedError

    @abstractmethod
    async def refund(self, payment_id: str, amount: Decimal | None = None) -> bool:
        """Refund a gateway payment, fully or partially.

        Args:
            payment_id: The gateway payment ID.
            amount: Amount to refund (None for full refund).

        Returns:
            True if the refund was successful.

        Raises:
            PaymentGatewayError: If the gateway API returns an error.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_signature(
        self,
        x_signature: str,
        x_request_id: str,
        data_id: str,
        secret: str,
    ) -> bool:
        """Validate an IPN webhook x-signature using HMAC-SHA256.

        Args:
            x_signature: The x-signature header value (ts=...|v1=...).
            x_request_id: The x-request-id header value.
            data_id: The data.id query parameter value.
            secret: The webhook secret key.

        Returns:
            True if the signature is valid.
        """
        raise NotImplementedError

    # ── Subscription methods (Phase 0b) ────────────────────────────────────

    @abstractmethod
    async def create_subscription(
        self,
        reason: str,
        auto_recurring: AutoRecurringData,
        payer_email: str,
        card_token_id: str,
        external_reference: str,
        back_url: str,
    ) -> SubscriptionResult:
        """Create a gateway subscription with auto-recurring.

        Args:
            reason: Description/label for the subscription.
            auto_recurring: AutoRecurringData with frequency, frequency_type, transaction_amount, currency_id.
            payer_email: Email of the payer.
            card_token_id: Card token from gateway.js CardForm.
            external_reference: Tenant reference string.
            back_url: Redirect URL after subscription creation.

        Returns:
            SubscriptionResult with gateway subscription details.

        Raises:
            PaymentGatewayError: If the gateway API returns an error.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_subscription(self, gateway_subscription_id: str) -> SubscriptionResult:
        """Get the status and details of a gateway subscription.

        Args:
            gateway_subscription_id: The gateway subscription ID.

        Returns:
            SubscriptionResult with current subscription state.

        Raises:
            PaymentGatewayError: If the gateway API returns an error.
        """
        raise NotImplementedError

    @abstractmethod
    async def cancel_subscription(self, gateway_subscription_id: str) -> None:
        """Cancel a gateway subscription.

        Args:
            gateway_subscription_id: The gateway subscription ID to cancel.

        Raises:
            PaymentGatewayError: If the gateway API returns an error.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_subscription(self, gateway_subscription_id: str, data: dict) -> SubscriptionResult:
        """Update a gateway subscription (e.g. change payment method).

        Args:
            gateway_subscription_id: The gateway subscription ID.
            data: Dict of fields to update (e.g. card_token_id, status).

        Returns:
            SubscriptionResult with updated subscription state.

        Raises:
            PaymentGatewayError: If the gateway API returns an error.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_authorized_payment(self, authorized_payment_id: str) -> AuthorizedPaymentResult:
        """Get details of an authorized payment invoice for a subscription.

        Args:
            authorized_payment_id: The gateway authorized payment ID.

        Returns:
            AuthorizedPaymentResult with payment details.

        Raises:
            PaymentGatewayError: If the gateway API returns an error.
        """
        raise NotImplementedError
