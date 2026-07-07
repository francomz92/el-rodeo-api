"""Security Headers ASGI middleware.

Injects security hardening headers (CSP, HSTS, XFO, nosniff, etc.)
on every HTTP response. Configurable via application settings.
"""

from typing import Any

from src.common.infrastructure.core import settings as app_settings

# Security headers applied to every HTTP response.
_BASE_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


class SecurityHeadersMiddleware:
    """ASGI middleware that injects security headers into every HTTP response.

    HSTS is only added in non-development environments.
    CSP is configured from settings.CSP_DEFAULT_SRC.

    Must be placed AFTER CORS middleware in the chain to avoid
    interference with preflight responses.
    """

    def __init__(self, app: Any, settings: Any = None) -> None:
        self.app = app
        self.settings = settings or app_settings

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                # Add base security headers
                for name, value in _BASE_HEADERS.items():
                    headers.append((name.lower().encode(), value.encode()))

                # CSP (configurable from settings)
                directives = getattr(self.settings, "CSP_DIRECTIVES", None)
                if directives:
                    csp_value = "; ".join(f"{k} {v}" for k, v in directives.items())
                else:
                    csp_value = f"default-src {self.settings.CSP_DEFAULT_SRC}"
                headers.append((b"content-security-policy", csp_value.encode()))

                # HSTS — only for non-development environments
                if not self.settings.DEBUG:
                    hsts_value = f"max-age={self.settings.HSTS_MAX_AGE}; includeSubDomains"
                    headers.append((b"strict-transport-security", hsts_value.encode()))

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_headers)
