"""Correlation ID management via contextvars.

Provides async-safe correlation ID propagation using Python's
``contextvars.ContextVar``. Every request gets a unique ID, either
from a client-provided ``X-Request-ID`` header or auto-generated.
"""

import uuid
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Return the current correlation ID, or ``""`` if none is set."""
    return correlation_id_var.get()


def set_correlation_id(value: str | None = None) -> str:
    """Set and return a correlation ID for the current context.

    If *value* is ``None`` (default) a new UUID hex string is generated.
    Otherwise *value* is stored as-is.
    """
    cid = value if value is not None else uuid.uuid4().hex
    correlation_id_var.set(cid)
    return cid


__all__ = ["correlation_id_var", "get_correlation_id", "set_correlation_id"]
