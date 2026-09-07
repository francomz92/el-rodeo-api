"""Correlation ID management via contextvars.

Provides async-safe correlation ID propagation using Python's
``contextvars.ContextVar``. Every request gets a unique ID, either
from a client-provided ``X-Request-ID`` header or auto-generated.
"""

import uuid
from contextvars import ContextVar, Token

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Return the current correlation ID, or ``""`` if none is set."""
    return correlation_id_var.get()


def set_correlation_id(value: str | None = None) -> tuple[str, Token]:
    """Set and return a correlation ID for the current context.

    If *value* is ``None`` (default) a new UUID hex string is generated.
    Otherwise *value* is stored as-is.
    """
    cid = value if value is not None else uuid.uuid4().hex
    token = correlation_id_var.set(cid)
    return cid, token


def reset_correlation_id(token: Token) -> None:
    """Reset the correlation ID for the current context to ``""``."""
    correlation_id_var.reset(token)


__all__ = ["correlation_id_var", "get_correlation_id", "set_correlation_id", "reset_correlation_id"]
