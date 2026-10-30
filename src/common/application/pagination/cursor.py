"""Opaque cursor token encoding and decoding for application pagination."""

import base64
import json
from uuid import UUID

from src.common.domain.exceptions import BusinessValidationError


class InvalidCursorError(BusinessValidationError):
    """Raised when a cursor token is malformed (maps to HTTP 422)."""


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
    Raises ``InvalidCursorError`` (HTTP 422) if the token is malformed.
    """
    try:
        payload = base64.urlsafe_b64decode(cursor.encode()).decode()
        data = json.loads(payload)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidCursorError("Token de cursor no válido") from exc

    if not isinstance(data, dict):
        raise InvalidCursorError("Token de cursor no válido")

    id_value = data.get("id")
    sort_value = data.get("sort_value")
    if not isinstance(id_value, str) or not isinstance(sort_value, str):
        raise InvalidCursorError("Token de cursor no válido")

    return {"id": id_value, "sort_value": sort_value}


def cursor_uuid(cursor_data: dict[str, str]) -> UUID:
    """Return the ``id`` field of a decoded cursor as a ``UUID``.

    Single helper for call sites: keeps malformed ids from turning into
    unhandled ``ValueError`` 500s. Raises ``InvalidCursorError`` (HTTP 422).
    """
    try:
        return UUID(cursor_data["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidCursorError("Token de cursor no válido") from exc
