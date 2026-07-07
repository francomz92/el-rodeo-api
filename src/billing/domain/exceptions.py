from src.common.domain.exceptions import DomainError


class QuotaExceededException(DomainError):
    error_code = "quota_exceeded_error"

    def __init__(self, resource_name: str, limit: int, current_usage: int) -> None:
        self.resource_name = resource_name
        self.limit = limit
        self.current_usage = current_usage
        message = f"Quota '{resource_name}' exceeded: {current_usage} used, limit is {limit}"
        super().__init__(message, [])


class MercadoPagoError(DomainError):
    error_code = "mercadopago_error"

    def __init__(self, message: str, status_code: int | None = None, mp_error: str | None = None) -> None:
        self.status_code = status_code
        self.mp_error = mp_error
        super().__init__(message, [])


class PlanNotChangeableError(DomainError):
    error_code = "plan_change_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])
