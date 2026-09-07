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
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.wrappers import Limit
from starlette.exceptions import HTTPException as StarletteHTTPException

# NOTE: Handler modules (server_error, domain_errors, etc.) are NOT imported
# at module level.  ``test_db.py:_fresh_db_module`` clears ALL ``src.*``
# modules from ``sys.modules`` during test runs, which causes stale module
# references and mismatched ``ContextVar`` copies.  Instead, each test class
# imports its handler **inline** so that all imports resolve from the same
# ``sys.modules`` state.
# The :mod:`tests.unit.presentation.conftest` :func:`_fresh_modules` fixture
# pre-imports these modules so their ``configure_logger()`` call runs
# BEFORE ``_capture_logs()`` creates its temporary sink.

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
        from src.common.infrastructure.presentation.middlewares.exceptions_handlers.server_error import (  # noqa: E501
            server_exception_handler,
        )

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
        from src.common.infrastructure.adapters.correlation import set_correlation_id

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
        from src.common.infrastructure.presentation.middlewares.exceptions_handlers.application_errors import (  # noqa: E501
            application_exception_handler,
        )

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
        from src.common.infrastructure.adapters.correlation import set_correlation_id

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
        from src.common.infrastructure.presentation.middlewares.exceptions_handlers.domain_errors import (  # noqa: E501
            domain_exception_handler,
        )

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
        from src.common.infrastructure.adapters.correlation import set_correlation_id

        set_correlation_id("domain-err-cid-777")
        try:
            records = _capture_logs(self._handler)
        finally:
            set_correlation_id()

        warning_logs = [r for r in records if r["level"]["name"] == "WARNING"]
        assert len(warning_logs) >= 1
        cids = {r["extra"].get("correlation_id", "") for r in warning_logs}
        assert "domain-err-cid-777" in cids, f"Expected correlation_id in: {cids}"


class TestRateLimitErrorResponseFormat:
    """rate_limit_errors.py — Response format: error.code at top level."""

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

    @staticmethod
    def _handler():
        from src.common.infrastructure.presentation.middlewares.exceptions_handlers.rate_limit_errors import (  # noqa: E501
            _rate_limit_handler,
        )

        request = _make_request()
        from slowapi.errors import RateLimitExceeded

        exc = RateLimitExceeded(limit=TestRateLimitErrorResponseFormat._make_limit("5/minute"))
        return asyncio.run(_rate_limit_handler(request, exc))

    def test_error_code_at_top_level_not_nested(self):
        """``$.error.code`` exists and ``$.detail.error.code`` does not."""
        result = self._handler()
        body = json.loads(result.body)
        # error.code must be at top level
        assert "error" in body
        assert "code" in body["error"]
        assert body["error"]["code"] == "rate_limit_exceeded_error"
        # Must NOT be nested under detail
        assert "detail" not in body or "error" not in body.get("detail", {})

    def test_response_is_429(self):
        """Response status is 429."""
        result = self._handler()
        assert result.status_code == 429


class TestRequestValidationErrorResponseFormat:
    """request_validation_error.py — Response format: error.code at top level."""

    @staticmethod
    def _handler():
        from src.common.infrastructure.presentation.middlewares.exceptions_handlers.request_validation_error import (  # noqa: E501
            _request_validation_exception_handler,
        )

        request = _make_request()
        exc = RequestValidationError(
            errors=[
                {"loc": ("body", "email"), "msg": "field required", "type": "value_error.missing"},
            ]
        )
        return asyncio.run(_request_validation_exception_handler(request, exc))

    def test_error_code_at_top_level_not_nested(self):
        """``$.error.code`` exists and ``$.detail.error.code`` does not."""
        result = self._handler()
        body = json.loads(result.body)
        assert "error" in body
        assert "code" in body["error"]
        assert body["error"]["code"] == "validation_error"
        assert "detail" not in body or "error" not in body.get("detail", {})

    def test_response_is_422(self):
        """Response status is 422."""
        result = self._handler()
        assert result.status_code == 422


class TestRequestValidationErrorHandlerLogging:
    """request_validation_error.py — ``_request_validation_exception_handler`` logging"""

    @staticmethod
    def _handler():

        request = _make_request()
        exc = RequestValidationError(
            errors=[
                {"loc": ("body", "email"), "msg": "field required", "type": "value_error.missing"},
            ]
        )
        from src.common.infrastructure.presentation.middlewares.exceptions_handlers.request_validation_error import (  # noqa: E501
            _request_validation_exception_handler,
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
        from src.common.infrastructure.adapters.correlation import set_correlation_id

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
    """rate_limit_errors.py — ``_rate_limit_handler`` (429 handler)"""

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

    @staticmethod
    def _handler(path="/api/login"):
        from src.common.infrastructure.presentation.middlewares.exceptions_handlers.rate_limit_errors import (  # noqa: E501
            _rate_limit_handler,
        )

        request = _make_request(path)
        exc = RateLimitExceeded(limit=TestRateLimitExceededHandler._make_limit("5/minute"))
        return asyncio.run(_rate_limit_handler(request, exc))

    def test_logs_at_warning_level(self):
        """Rate limit exceeded is logged at WARNING level."""
        records = _capture_logs(lambda: self._handler())
        assert any(r["level"]["name"] == "WARNING" for r in records), f"No WARNING log found in: {[r['level']['name'] for r in records]}"

    def test_logs_path(self):
        """The rate limited path appears in the log."""
        records = _capture_logs(lambda: self._handler("/api/login"))
        warning_logs = [r for r in records if r["level"]["name"] == "WARNING"]
        assert len(warning_logs) >= 1
        combined = " ".join(r["message"] for r in warning_logs)
        assert "/api/login" in combined

    def test_includes_correlation_id(self):
        """Correlation ID is included in the WARNING log record."""
        from src.common.infrastructure.adapters.correlation import set_correlation_id

        set_correlation_id("rate-cid-555")
        try:
            records = _capture_logs(lambda: self._handler())
        finally:
            set_correlation_id()

        warning_logs = [r for r in records if r["level"]["name"] == "WARNING"]
        assert len(warning_logs) >= 1
        cids = {r["extra"].get("correlation_id", "") for r in warning_logs}
        assert "rate-cid-555" in cids, f"Expected correlation_id in: {cids}"


class TestStarletteHttpExceptionHandler:
    """server_error.py — ``starlette_http_exception_handler``"""

    @staticmethod
    def _handler():
        from src.common.infrastructure.presentation.middlewares.exceptions_handlers.server_error import (  # noqa: E501
            starlette_http_exception_handler,
        )

        request = _make_request()
        exc = StarletteHTTPException(status_code=404, detail="not found")
        return asyncio.run(starlette_http_exception_handler(request, exc))

    def test_returns_404_status_code(self):
        """HTTPException(404) returns 404, not 500."""
        result = self._handler()
        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    def test_uses_standard_error_response_body(self):
        """Response body uses StandardErrorResponse format."""
        result = self._handler()
        body = json.loads(result.body)
        assert "error" in body
        assert body["error"]["code"] == "client_error"
        assert "not found" in body["error"]["message"] or "not found" in str(body)
        assert "timestamp" in body

    def test_generic_exception_still_returns_500(self):
        """ValueError (non-HTTPException) still returns 500 via server_exception_handler."""
        from src.common.infrastructure.presentation.middlewares.exceptions_handlers.server_error import (  # noqa: E501
            server_exception_handler,
        )

        request = _make_request()
        exc = ValueError("generic error")
        result = asyncio.run(server_exception_handler(request, exc))

        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        body = json.loads(result.body)
        assert body["error"]["code"] == "server_error"
