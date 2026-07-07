"""IP utility functions for middleware.

Provides a helper to determine the real client IP behind reverse
proxies by reading the ``X-Forwarded-For`` header first.
"""

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Resolve the originating client IP from a request.

    Reads ``X-Forwarded-For`` first (taking the leftmost address),
    then falls back to ``request.client.host`` and finally to the
    loopback address ``127.0.0.1``.

    Args:
        request: The incoming FastAPI ``Request`` instance.

    Returns:
        A string representation of the client IP address.
    """
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client[0] if client else "127.0.0.1"
