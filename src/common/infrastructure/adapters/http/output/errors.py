from pydantic import BaseModel


class ErrorDetailSchema(BaseModel):
    field: str | None = None
    message: str


class ErrorPayloadSchema(BaseModel):
    code: str
    message: str
    details: list[ErrorDetailSchema] = []


class StandardErrorResponse(BaseModel):
    success: bool = False
    error: ErrorPayloadSchema
    timestamp: str


def format_error_location(loc: tuple) -> str:
    return ".".join(str(c) for c in loc) if loc else "unknown"
