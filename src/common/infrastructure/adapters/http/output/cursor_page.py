"""Cursor-based pagination schema with compatibility exports for cursor helpers."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field

from src.common.application.pagination.cursor import decode_cursor, encode_cursor

__all__ = ["CursorPage", "decode_cursor", "encode_cursor"]

T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):
    """Generic cursor-paginated response.

    Usage::

        return CursorPage[AnimalSchema](
            items=[...],
            next_cursor="base64encoded",
            total=42,
        )
    """

    items: list[T]
    cursor: str | None = Field(
        default=None,
        description="Opaque cursor for the first item on this page",
    )
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor for the next page (null if last page)",
    )
    total: int = Field(description="Total number of items matching the query")
    model_config = ConfigDict(ser_json_timedelta="iso8601")

    @computed_field
    @property
    def has_next(self) -> bool:
        """Whether there are more pages after this one."""
        return self.next_cursor is not None
