from typing import Literal, TypedDict

ErrorCode = Literal[
    "domain_error",
    "conflict_error",
    "duplicated_error",
    "not_found_error",
    "validation_error",
    "invalid_credentials_error",
    "permission_error",
    "unauthorized_error",
    "quota_exceeded_error",
    "mercadopago_error",
    "plan_change_error",
]


class ErrorDetail(TypedDict):
    field: str | None
    message: str
