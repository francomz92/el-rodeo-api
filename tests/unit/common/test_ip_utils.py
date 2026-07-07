"""Unit tests for ip_utils — get_client_ip.

Covers:
- X-Forwarded-For header takes priority over request.client
- Fallback to request.client.host when no X-Forwarded-For
- Multiple IPs in X-Forwarded-For returns the first (leftmost)
- Empty X-Forwarded-For header falls back
- request.client is None falls back to 127.0.0.1
"""

from unittest.mock import MagicMock

from fastapi import Request

from src.common.infrastructure.presentation.middlewares.ip_utils import (
    get_client_ip,
)


class TestGetClientIP:
    """get_client_ip correctly resolves the client IP from request."""

    def test_returns_xforwarded_for_when_present(self) -> None:
        """X-Forwarded-For takes priority over request.client."""
        request = MagicMock(spec=Request)
        request.headers.get = lambda key, default="": "203.0.113.42"
        request.client = ("10.0.0.1", 54321)

        ip = get_client_ip(request)

        assert ip == "203.0.113.42"

    def test_falls_back_to_client_host(self) -> None:
        """When X-Forwarded-For is absent, request.client.host is used."""
        request = MagicMock(spec=Request)
        request.headers.get = lambda key, default="": ""
        request.client = ("10.0.0.1", 54321)

        ip = get_client_ip(request)

        assert ip == "10.0.0.1"

    def test_returns_first_ip_in_forwarded_chain(self) -> None:
        """Multiple IPs in X-Forwarded-For return only the leftmost."""
        request = MagicMock(spec=Request)
        request.headers.get = lambda key, default="": "198.51.100.1, 10.0.0.1, 192.168.1.1"
        request.client = ("10.0.0.5", 54321)

        ip = get_client_ip(request)

        assert ip == "198.51.100.1"

    def test_strips_whitespace_from_forwarded_ip(self) -> None:
        """Whitespace around IPs in X-Forwarded-For is cleaned."""
        request = MagicMock(spec=Request)
        request.headers.get = lambda key, default="": " 203.0.113.42 "
        request.client = ("10.0.0.1", 54321)

        ip = get_client_ip(request)

        assert ip == "203.0.113.42"

    def test_empty_xforwarded_for_falls_back(self) -> None:
        """An empty X-Forwarded-For header falls back to request.client."""
        request = MagicMock(spec=Request)
        request.headers.get = lambda key, default="": ""
        request.client = ("10.0.0.1", 54321)

        ip = get_client_ip(request)

        assert ip == "10.0.0.1"

    def test_no_client_info_returns_loopback(self) -> None:
        """When both X-Forwarded-For and request.client are absent, return 127.0.0.1."""
        request = MagicMock(spec=Request)
        request.headers.get = lambda key, default="": ""
        request.client = None

        ip = get_client_ip(request)

        assert ip == "127.0.0.1"

    def test_no_client_info_with_forwarded_returns_forwarded(self) -> None:
        """X-Forwarded-For still wins even when request.client is None."""
        request = MagicMock(spec=Request)
        request.headers.get = lambda key, default="": "198.51.100.1"
        request.client = None

        ip = get_client_ip(request)

        assert ip == "198.51.100.1"
