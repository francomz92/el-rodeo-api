"""Integration tests for security headers middleware.

Verifies that every HTTP response includes the required security headers
as defined in the SecurityHeadersMiddleware.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from main import app

# Expected security headers and their expected values (substring match for CSP).
EXPECTED_HEADERS: dict[str, str | None] = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": None,  # present but value varies
    "content-security-policy": None,  # present but value varies per env
}

# HSTS is only present in non-development environments.
HSTS_HEADER = "strict-transport-security"


@pytest.mark.asyncio
class TestSecurityHeaders:
    """Security headers present on all HTTP responses."""

    async def _get_headers(self, path: str = "/health") -> dict[str, str]:
        """Make a GET request and return response headers."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(path)
            return dict(resp.headers)

    async def test_all_security_headers_present_on_health(self) -> None:
        """Every required security header is present on the /health endpoint."""
        headers = await self._get_headers("/health")

        for header_name, expected_value in EXPECTED_HEADERS.items():
            assert header_name in headers, f"Missing security header: {header_name}. Present headers: {list(headers.keys())}"
            if expected_value is not None:
                actual_lower = headers[header_name].lower()
                expected_lower = expected_value.lower()
                assert expected_lower in actual_lower, (
                    f"Header {header_name} expected to contain '{expected_value}', got '{headers[header_name]}'"
                )

    async def test_all_security_headers_present_on_error_response(self) -> None:
        """Security headers present on 404 responses too."""
        headers = await self._get_headers("/nonexistent-path-12345")

        for header_name in EXPECTED_HEADERS:
            assert header_name in headers, f"Missing security header: {header_name} on 404 response"

    async def test_hsts_not_present_in_development(self) -> None:
        """HSTS header is absent in development environment.

        In dev mode (settings.DEBUG=True), the middleware skips HSTS.
        """
        headers = await self._get_headers("/health")
        # The test environment is development, so HSTS should not be present
        assert HSTS_HEADER not in headers, f"HSTS header should NOT be present in development, but found: {headers.get(HSTS_HEADER)}"

    async def test_content_security_policy_has_default_src(self) -> None:
        """CSP header has a default-src directive."""
        headers = await self._get_headers("/health")
        csp = headers.get("content-security-policy", "")
        assert "default-src" in csp, f"CSP header missing 'default-src'. Got: {csp}"
