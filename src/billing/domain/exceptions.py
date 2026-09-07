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
        message = f"Quota '{resource_name}' exceeded: {current_usage} used, limit is {limit}"
        super().__init__(message, [])


class PaymentGatewayError(BillingError):
    error_code = "payment_gateway_error"

    def __init__(self, message: str, status_code: int | None = None, gateway_error: str | None = None) -> None:
        self.status_code = status_code
        self.gateway_error = gateway_error
        super().__init__(message, [])


# Backward-compat alias
MercadoPagoError = PaymentGatewayError


class PlanNotChangeableError(BillingError):
    error_code = "plan_change_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])
