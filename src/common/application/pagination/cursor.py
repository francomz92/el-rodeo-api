"""Opaque cursor token encoding and decoding for application pagination."""

import base64
import json


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
