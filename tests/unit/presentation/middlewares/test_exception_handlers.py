"""Unit tests for exception handler logging.

Each exception handler must log at the correct level (ERROR for server
and application errors, WARNING for domain errors, validation errors,
and rate limit exceeded) and include the correlation ID in the log
output.
"""

import asyncio
import json
from io import StringIO

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from slowapi.wrappers import Limit

from src.common.infrastructure.adapters.correlation import set_correlation_id

# Pre-import all handler modules so configure_logger() runs BEFORE
# _capture_logs() adds its handler. This prevents configure_logger()
# calling logger.remove() which would remove our capture sink.
from src.common.infrastructure.presentation.middlewares.exceptions_handlers.application_errors import (  # noqa: F401, E501
    application_exception_handler,
)
from src.common.infrastructure.presentation.middlewares.exceptions_handlers.domain_errors import (  # noqa: F401, E501
    domain_exception_handler,
)
from src.common.infrastructure.presentation.middlewares.exceptions_handlers.request_validation_error import (  # noqa: F401, E501
    _request_validation_exception_handler,
)
from src.common.infrastructure.presentation.middlewares.exceptions_handlers.server_error import (  # noqa: F401, E501
    server_exception_handler,
)

# ── Log capture helper ─────────────────────────────────────────────────────────


def _capture_logs(action):
    """Execute *action* and return list of loguru records captured via serialize.

    Adds a temporary JSON-serialized sink, runs *action*, removes the sink,
    and returns parsed records (each record is the nested Loguru record dict).
    """
    from loguru import logger

    buf = StringIO()
    sink_id = logger.add(
        buf,
        format="{message}",
        level="DEBUG",
        enqueue=False,
        serialize=True,
    )

    try:
        action()
        logger.complete()
    finally:
        try:
            logger.remove(sink_id)
        except ValueError:
            pass

    output = buf.getvalue()
    records = []
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
            records.append(parsed["record"])
        except (json.JSONDecodeError, KeyError):
            continue
    return records


# ── Mock request factory ──────────────────────────────────────────────────────


def _make_request(path: str = "/test") -> Request:
    """Create a Starlette Request with a proper URL as derived from scope."""
    scope = {
        "type": "http",
        "scheme": "http",
        "server": ("testserver", 80),
        "root_path": "",
        "method": "GET",
        "path": path,
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
    }
    return Request(scope)


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestServerErrorHandler:
    """server_error.py — ``server_exception_handler``"""

    @staticmethod
    def _handler():
        request = _make_request()
        exc = ValueError("something broke")
        return asyncio.run(server_exception_handler(request, exc))

    def test_logs_at_error_level(self):
        """Unhandled server errors are logged at ERROR level."""
        records = _capture_logs(self._handler)
        assert any(r["level"]["name"] == "ERROR" for r in records), f"No ERROR log found in: {[r['level']['name'] for r in records]}"

    def test_logs_generic_message_without_leak(self):
        """The log message is generic and does not leak exception details."""
        records = _capture_logs(self._handler)
        error_logs = [r for r in records if r["level"]["name"] == "ERROR"]
        assert len(error_logs) >= 1
        combined = " ".join(r["message"] for r in error_logs)
        assert "Internal server error" in combined
        assert "something broke" not in combined

    def test_includes_correlation_id(self):
        """Correlation ID is included in the ERROR log record."""
        set_correlation_id("srv-err-cid-999")
        try:
            records = _capture_logs(self._handler)
        finally:
            set_correlation_id()

        error_logs = [r for r in records if r["level"]["name"] == "ERROR"]
        assert len(error_logs) >= 1
        cids = {r["extra"].get("correlation_id", "") for r in error_logs}
        assert "srv-err-cid-999" in cids, f"Expected correlation_id in: {cids}"


class TestApplicationErrorHandler:
    """application_errors.py — ``application_exception_handler``"""

    @staticmethod
    def _handler():
        from src.common.application.exceptions import AppValidationError

        request = _make_request()
        # AppValidationError has error_code="validation_error" and status_code=422
        exc = AppValidationError(message="Invalid token", details=[])
        return asyncio.run(application_exception_handler(request, exc))

    def test_logs_at_error_level(self):
        """Application errors are logged at ERROR level."""
        records = _capture_logs(self._handler)
        assert any(r["level"]["name"] == "ERROR" for r in records), f"No ERROR log found in: {[r['level']['name'] for r in records]}"

    def test_logs_error_code_and_message(self):
        """The error code and message appear in the log."""
        records = _capture_logs(self._handler)
        error_logs = [r for r in records if r["level"]["name"] == "ERROR"]
        assert len(error_logs) >= 1
        combined = " ".join(r["message"] for r in error_logs)
        assert "validation_error" in combined or "Invalid token" in combined

    def test_includes_correlation_id(self):
        """Correlation ID is included in the ERROR log record."""
        set_correlation_id("app-err-cid-888")
        try:
            records = _capture_logs(self._handler)
        finally:
            set_correlation_id()

        error_logs = [r for r in records if r["level"]["name"] == "ERROR"]
        assert len(error_logs) >= 1
        cids = {r["extra"].get("correlation_id", "") for r in error_logs}
        assert "app-err-cid-888" in cids, f"Expected correlation_id in: {cids}"


class TestDomainErrorHandler:
    """domain_errors.py — ``domain_exception_handler``

    NOTE: domain_exception_handler is NOT async (unlike the others).
    """

    @staticmethod
    def _handler():
        from src.common.domain.exceptions import NotFoundError

        request = _make_request()
        exc = NotFoundError(message="Resource not found")
        return domain_exception_handler(request, exc)

    def test_logs_at_warning_level(self):
        """Domain errors are logged at WARNING level."""
        records = _capture_logs(self._handler)
        assert any(r["level"]["name"] == "WARNING" for r in records), f"No WARNING log found in: {[r['level']['name'] for r in records]}"

    def test_logs_error_message(self):
        """The error message appears in the log."""
        records = _capture_logs(self._handler)
        warning_logs = [r for r in records if r["level"]["name"] == "WARNING"]
        assert len(warning_logs) >= 1
        combined = " ".join(r["message"] for r in warning_logs)
        assert "Resource not found" in combined

    def test_includes_correlation_id(self):
        """Correlation ID is included in the WARNING log record."""
        set_correlation_id("domain-err-cid-777")
        try:
            records = _capture_logs(self._handler)
        finally:
            set_correlation_id()

        warning_logs = [r for r in records if r["level"]["name"] == "WARNING"]
        assert len(warning_logs) >= 1
        cids = {r["extra"].get("correlation_id", "") for r in warning_logs}
        assert "domain-err-cid-777" in cids, f"Expected correlation_id in: {cids}"


class TestRequestValidationErrorHandler:
    """request_validation_error.py — ``_request_validation_exception_handler``"""

    @staticmethod
    def _handler():

        request = _make_request()
        exc = RequestValidationError(
            errors=[
                {"loc": ("body", "email"), "msg": "field required", "type": "value_error.missing"},
            ]
        )
        return asyncio.run(_request_validation_exception_handler(request, exc))

    def test_logs_at_warning_level(self):
        """Validation errors are logged at WARNING level."""
        records = _capture_logs(self._handler)
        assert any(r["level"]["name"] == "WARNING" for r in records), f"No WARNING log found in: {[r['level']['name'] for r in records]}"

    def test_logs_validation_details(self):
        """Validation error details appear in the log."""
        records = _capture_logs(self._handler)
        warning_logs = [r for r in records if r["level"]["name"] == "WARNING"]
        assert len(warning_logs) >= 1
        combined = " ".join(r["message"] for r in warning_logs)
        assert "field required" in combined or "email" in combined

    def test_includes_correlation_id(self):
        """Correlation ID is included in the WARNING log record."""
        set_correlation_id("val-err-cid-666")
        try:
            records = _capture_logs(self._handler)
        finally:
            set_correlation_id()

        warning_logs = [r for r in records if r["level"]["name"] == "WARNING"]
        assert len(warning_logs) >= 1
        cids = {r["extra"].get("correlation_id", "") for r in warning_logs}
        assert "val-err-cid-666" in cids, f"Expected correlation_id in: {cids}"


class TestRateLimitExceededHandler:
    """rate_limiter.py — ``_rate_limit_handler`` (429 handler)"""

    def _get_handler_and_request(self, path="/api/login"):
        """Get the rate limit handler registered via configure_rate_limiter
        and a properly scoped Request."""
        from unittest.mock import MagicMock

        from fastapi import FastAPI

        app = FastAPI()
        app.state = MagicMock()
        from src.common.infrastructure.presentation.middlewares.rate_limiter import (
            configure_rate_limiter,
        )

        mock_settings = MagicMock()
        configure_rate_limiter(app, mock_settings)

        # The handler is registered with status code 429
        handler = app.exception_handlers.get(429)
        assert handler is not None, "Rate limit handler (429) not registered"

        request = _make_request(path)
        return handler, request

    @staticmethod
    def _make_limit(limit_str: str) -> Limit:
        """Create a slowapi Limit object from a limit string like '5/minute'."""
        from limits import parse as limit_parse

        from src.common.infrastructure.presentation.middlewares.ip_utils import (
            get_client_ip,
        )

        item = limit_parse(limit_str)
        return Limit(
            limit=item,
            key_func=get_client_ip,
            scope=None,
            per_method=False,
            methods=None,
            error_message=None,
            exempt_when=None,
            cost=1,
            override_defaults=False,
        )

    def test_logs_at_warning_level(self):
        """Rate limit exceeded is logged at WARNING level."""
        handler, request = self._get_handler_and_request()

        exc = RateLimitExceeded(limit=self._make_limit("5/minute"))

        def _run():
            asyncio.run(handler(request, exc))

        records = _capture_logs(_run)
        assert any(r["level"]["name"] == "WARNING" for r in records), f"No WARNING log found in: {[r['level']['name'] for r in records]}"

    def test_logs_path(self):
        """The rate limited path appears in the log."""
        handler, request = self._get_handler_and_request("/api/login")

        exc = RateLimitExceeded(limit=self._make_limit("5/minute"))

        def _run():
            asyncio.run(handler(request, exc))

        records = _capture_logs(_run)
        warning_logs = [r for r in records if r["level"]["name"] == "WARNING"]
        assert len(warning_logs) >= 1
        combined = " ".join(r["message"] for r in warning_logs)
        assert "/api/login" in combined

    def test_includes_correlation_id(self):
        """Correlation ID is included in the WARNING log record."""
        handler, request = self._get_handler_and_request()

        exc = RateLimitExceeded(limit=self._make_limit("5/minute"))

        set_correlation_id("rate-cid-555")
        try:

            def _run():
                asyncio.run(handler(request, exc))

            records = _capture_logs(_run)
        finally:
            set_correlation_id()

        warning_logs = [r for r in records if r["level"]["name"] == "WARNING"]
        assert len(warning_logs) >= 1
        cids = {r["extra"].get("correlation_id", "") for r in warning_logs}
        assert "rate-cid-555" in cids, f"Expected correlation_id in: {cids}"
