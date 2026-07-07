from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from src.billing.domain.entities._payment_status import PaymentStatus


@dataclass(frozen=True)
class ItemData:
    title: str
    quantity: int
    unit_price: Decimal
    currency_id: str = "ARS"


@dataclass(frozen=True)
class PreferenceResult:
    id: str
    init_point: str


@dataclass(frozen=True)
class PaymentResult:
    """Rich result from get_payment, including MP response details."""

    id: str
    status: PaymentStatus
    external_reference: str | None = None
    transaction_amount: Decimal | None = None
    payment_method_id: str | None = None
    payment_type_id: str | None = None
    payer_email: str | None = None


class IPaymentGateway(ABC):
    @abstractmethod
    async def create_preference(
        self,
        items: list[ItemData],
        back_urls: dict,
        notification_url: str,
        external_reference: str,
    ) -> PreferenceResult:
        """Create a MercadoPago Checkout Pro preference.

        Args:
            items: List of items to include in the preference.
            back_urls: Dict with success/failure/pending URLs.
            notification_url: Webhook URL for IPN notifications.
            external_reference: Tenant reference string.

        Returns:
            PreferenceResult with the preference ID and checkout URL.

        Raises:
            MercadoPagoError: If the MP API returns an error.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_payment(self, payment_id: str) -> PaymentResult:
        """Get the status and details of a MercadoPago payment.

        Args:
            payment_id: The MercadoPago payment ID.

        Returns:
            PaymentResult with status, external_reference, amount, etc.

        Raises:
            MercadoPagoError: If the MP API returns an error.
        """
        raise NotImplementedError

    @abstractmethod
    async def refund(self, payment_id: str, amount: Decimal | None = None) -> bool:
        """Refund a MercadoPago payment, fully or partially.

        Args:
            payment_id: The MercadoPago payment ID.
            amount: Amount to refund (None for full refund).

        Returns:
            True if the refund was successful.

        Raises:
            MercadoPagoError: If the MP API returns an error.
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
