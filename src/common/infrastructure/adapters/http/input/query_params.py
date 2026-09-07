import warnings

from pydantic import BaseModel, Field, field_validator, model_validator

from src.common.domain.constants import pagination

ALLOWED_ORDER_BY: frozenset[str] = frozenset({"id", "created_at", "updated_at", "name"})


class StandardQueryParams(BaseModel):
    limit: int = Field(
        default=pagination.ROW_PER_PAGE,
        ge=1,
        le=100,
        description="Records per page",
    )
    offset: int = Field(default=0, ge=0, description="Page number (deprecated, use cursor)")
    order_by: str = Field(default="id", max_length=50, description="List ordering")

    @field_validator("order_by")
    @classmethod
    def _validate_order_by(cls, v: str) -> str:
        if v not in ALLOWED_ORDER_BY:
            raise ValueError(f"Invalid order_by '{v}'. Allowed: {', '.join(sorted(ALLOWED_ORDER_BY))}")
        return v

    cursor: str | None = Field(
        default=None,
        description="Cursor for cursor-based pagination (opaque base64 token)",
    )

    @model_validator(mode="after")
    def _deprecate_offset(self) -> "StandardQueryParams":
        if self.offset != 0 and self.cursor is None:
            warnings.warn(
                "offset pagination is deprecated — use cursor-based pagination instead",
                DeprecationWarning,
                stacklevel=2,
            )
        return self
