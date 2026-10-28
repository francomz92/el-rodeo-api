from src.common.domain.exceptions import DomainError


class BillingError(DomainError):
    """Base exception for all billing domain errors."""

    error_code = "billing_error"


class QuotaExceededException(BillingError):
    error_code = "quota_exceeded_error"

    def __init__(self, resource_name: str, limit: int, current_usage: int) -> None:
        self.resource_name = resource_name
        self.limit = limit
        self.current_usage = current_usage
        message = f"Cuota '{resource_name}' excedida: {current_usage} en uso, límite {limit}"
        super().__init__(message, [])


class PaymentGatewayError(BillingError):
    """Payment-gateway failure carrying two distinct status concepts.

    Attributes:
        status_code: HTTP status this error maps to in OUR API response. It is
            read by the standard domain-error handler (``domain_errors.py``),
            the same response-mapping role ``PlanNotChangeableError.status_code``
            plays at class level. When it is falsy (``None`` or the
            ``NO_RESPONSE_STATUS`` sentinel), the handler falls back to the
            error-code mapping (``payment_gateway_error`` -> 502).
        gateway_error: Raw error message reported by the gateway, when one was
            extracted from a response body.
        upstream_status: HTTP status returned by the payment-gateway upstream,
            when an HTTP exchange happened; ``None`` for transport failures
            (timeout/connection error) and for errors raised outside an
            upstream exchange (e.g. webhook signature rejections).
    """

    error_code = "payment_gateway_error"

    #: Sentinel stored in ``status_code`` for transport failures where no
    #: upstream HTTP response exists. It is falsy, so the domain-error handler
    #: keeps falling back to the error-code mapping (502).
    NO_RESPONSE_STATUS: int = 0

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        gateway_error: str | None = None,
        upstream_status: int | None = None,
    ) -> None:
        self.status_code = status_code
        self.gateway_error = gateway_error
        self.upstream_status = upstream_status
        super().__init__(message, [])


# Backward-compat alias
MercadoPagoError = PaymentGatewayError


class PlanNotChangeableError(BillingError):
    error_code = "plan_change_error"
    # Preserves the pre-refactor router status (422) under the standard
    # domain-errors envelope, which would otherwise map this code to 400.
    status_code = 422

    def __init__(self, message: str) -> None:
        super().__init__(message, [])
