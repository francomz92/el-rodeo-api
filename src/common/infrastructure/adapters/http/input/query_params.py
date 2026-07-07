import warnings

from pydantic import BaseModel, Field, model_validator

from src.common.domain.constants import pagination


class StandardQueryParams(BaseModel):
    limit: int = Field(
        default=pagination.ROW_PER_PAGE,
        ge=1,
        le=100,
        description="Records per page",
    )
    offset: int = Field(default=0, ge=0, description="Page number (deprecated, use cursor)")
    order_by: str = Field(default="id", max_length=50, description="List ordering")
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
