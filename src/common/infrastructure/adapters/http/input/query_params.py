from pydantic import BaseModel, Field

from src.common.domain.constants import pagination



class StandardQueryParams(BaseModel):
    limit: int = Field(
        default=pagination.ROW_PER_PAGE,
        max_digits=2,
        ge=1,
        le=100,
        description="Records per page",
    )
    offset: int = Field(default=0, ge=0, description="Page number")
    order_by: str = Field(default="id", max_length=50, description="Animal list ordering")