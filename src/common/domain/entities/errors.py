from typing import Literal, TypedDict

ErrorCode = Literal[
    "conflict_error",
    "not_found_error",
    "validation_error",
    "invalid_credentials_error",
    "permission_error",
    "unauthorized_error",
]


class ErrorDetail(TypedDict):
    field: str | None
    message: str
