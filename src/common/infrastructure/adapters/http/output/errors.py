from pydantic import BaseModel



class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = []


class StandardErrorResponse(BaseModel):
    success: bool = False
    error: ErrorPayload
    timestamp: str


def format_error_location(loc: tuple) -> str:
    return ".".join(str(c) for c in loc) if loc else "unknown"
