"""Cursor-based pagination schema and helpers.

Provides `CursorPage[T]` generic Pydantic model and Base64-encoded
cursor encode/decode utilities as defined in the page design decision:
Base64(JSON {id, sort_value}) for opaque tokens.
"""

import base64
import json
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field

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


def encode_cursor(id: str, sort_value: str | None = None) -> str:
    """Encode an opaque cursor token.

    The token is a URL-safe Base64-encoded JSON dict with ``id`` and
    ``sort_value`` keys. When ``sort_value`` is omitted the id is used
    for both (single-column sort by id).
    """
    payload = json.dumps(
        {"id": str(id), "sort_value": str(sort_value) if sort_value is not None else str(id)},
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> dict[str, str]:
    """Decode a cursor token back to ``{id, sort_value}``.

    Returns a dict with keys ``id`` and ``sort_value`` (both strings).
    Raises ``ValueError`` if the token is malformed.
    """
    try:
        payload = base64.urlsafe_b64decode(cursor.encode()).decode()
        return json.loads(payload)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        msg = f"Invalid cursor token: {exc}"
        raise ValueError(msg) from exc
