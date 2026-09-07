"""Approval + behavioral tests for the Loguru logger configuration.

Phase 1 — Approval tests document CURRENT behavior before refactoring.
Phase 2 — Tests are updated to reflect NEW expected behavior (RED).
Phase 3 — Implementation makes them pass (GREEN).
"""

import datetime
import json
import sys
from unittest.mock import patch

import pytest
from loguru import logger

from src.common.infrastructure.core._config import Settings

# NOTE: ``correlation_id_var``, ``set_correlation_id`` and ``configure_logger``
# are NOT imported at module level because ``test_db.py:_fresh_db_module``
# clears ALL ``src.*`` modules from ``sys.modules`` during collection,
# which causes stale module references.  See ``_ensure_fresh_modules`` for
# the complete explanation and the fixture that resolves imports dynamically.

# ── Helpers ───────────────────────────────────────────────────────────────────


def _ensure_fresh_modules():
    """Ensure ``logger`` and ``correlation`` modules are in ``sys.modules``.

    ``test_db.py:_fresh_db_module`` clears ALL ``src.*`` modules from
    ``sys.modules`` to force fresh imports under patched environment
    variables.  This creates a problem: when a downstream test file has
    module-level imports like::

        from src.common.infrastructure.adapters.logger import configure_logger

    and later does ``unittest.mock.patch("…logger.settings", …)``, the
    ``patch`` call internally re-imports the module (creating a **second**
    copy with its own ``@lru_cache`` and ``ContextVar``), while the
    function call still uses the first copy from the module-level import.

    By deferring ALL imports to fixture time and explicitly re-importing
    stale modules before every test, we guarantee every code path
    (``set_correlation_id``, ``correlation_filter``, ``configure_logger``)
    resolves to the **same** module object.

    Call this at the start of every test's ``_reset_loguru`` fixture.
    """
    for name in (
        "src.common.infrastructure.adapters.logger",
        "src.common.infrastructure.adapters.correlation",
    ):
        if name not in sys.modules:
            # Prune stale entries so re-import is clean
            for k in list(sys.modules):
                if k.startswith("src.common.infrastructure.adapters"):
                    if k in ("src.common.infrastructure.adapters",):
                        continue
                    sys.modules.pop(k, None)
            # Re-import in dependency order
            import src.common.infrastructure.adapters.correlation  # noqa: F401
            import src.common.infrastructure.adapters.logger  # noqa: F401

            break


def _correlation() -> type(sys):
    """Return the canonical ``correlation`` module from ``sys.modules``."""
    _ensure_fresh_modules()
    return sys.modules["src.common.infrastructure.adapters.correlation"]


def _logger_mod():
    """Return the canonical ``logger`` module from ``sys.modules``."""
    _ensure_fresh_modules()
    return sys.modules["src.common.infrastructure.adapters.logger"]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_loguru():
    """Ensure each test starts with a clean logger state.

    Clears Loguru handlers, the ``@lru_cache`` on ``configure_logger``,
    and the correlation_id contextvar so every test gets a fresh slate.
    """
    _ensure_fresh_modules()
    logger_mod = _logger_mod()
    corr = _correlation()
    logger.remove()
    logger_mod.configure_logger.cache_clear()
    corr.correlation_id_var.set("")
    yield
    logger.remove()
    logger_mod.configure_logger.cache_clear()
    corr.correlation_id_var.set("")


@pytest.fixture
def dev_settings() -> Settings:
    """Create Settings with development defaults."""
    env = {
        "DB_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
        "SECRET": "test-secret",
        "JWT_ALGORITHM": "HS256",
        "SMTP_SERVER": "smtp.test.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@test.com",
        "SMTP_PASSWORD": "testpass",
        "DOMAIN": "http://test.com",
        "BROKER_URL": "redis://localhost:6380/0",
        "RESULT_BACKEND_URL": "redis://localhost:6380/0",
        "ENVIRONMENT": "development",
        "LOG_LEVEL": "DEBUG",
        "LOG_FORMAT": "text",
    }
    with patch.dict("os.environ", env, clear=True):
        return Settings(_env_file=None)


# ── Correlation Filter Tests ─────────────────────────────────────────────────


class TestCorrelationFilter:
    """Loguru filter function that injects correlation_id into records."""

    def test_filter_injects_id_when_set(self) -> None:
        """When correlation_id is set in context, the filter injects it into extra."""
        corr = _correlation()
        from src.common.infrastructure.adapters.logger import correlation_filter

        corr.set_correlation_id("abc-123")
        record = {"extra": {}}
        result = correlation_filter(record)
        assert result is True
        assert record["extra"].get("correlation_id") == "abc-123"

    def test_filter_noop_when_not_set(self) -> None:
        """When no correlation_id is set, extra is not modified."""
        from src.common.infrastructure.adapters.logger import correlation_filter

        record = {"extra": {}}
        result = correlation_filter(record)
        assert result is True
        assert "correlation_id" not in record["extra"]


# ── JSON Serialization ───────────────────────────────────────────────────────


class TestJsonSerialization:
    """When LOG_FORMAT=json, log records are serialized as JSON."""

    @staticmethod
    def _patch_json(monkeypatch: pytest.MonkeyPatch) -> None:
        """Override settings for JSON mode."""
        monkeypatch.setenv("LOG_FORMAT", "json")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("ENVIRONMENT", "development")

    def test_json_format_emits_valid_json(self, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
        """A log entry produces valid JSON when LOG_FORMAT=json."""
        self._patch_json(monkeypatch)
        logger_mod = _logger_mod()
        from src.common.infrastructure.core._config import Settings as S

        with patch.object(S, "_env_file", None, create=True):
            with patch("src.common.infrastructure.adapters.logger.settings", S()):
                logger_mod.configure_logger()

                logger.info("hello json")
                logger.complete()
                captured = capsys.readouterr()
                out = captured.out.strip()

                parsed = json.loads(out)
                assert parsed["level"] == "INFO"
                assert parsed["message"] == "hello json"
                assert "timestamp" in parsed
                assert "name" in parsed
                assert "function" in parsed
                assert "line" in parsed

    def test_json_includes_correlation_id(self, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
        """JSON output includes correlation_id when set in context."""
        self._patch_json(monkeypatch)
        logger_mod = _logger_mod()
        corr = _correlation()
        from src.common.infrastructure.core._config import Settings as S

        with patch.object(S, "_env_file", None, create=True):
            with patch("src.common.infrastructure.adapters.logger.settings", S()):
                logger_mod.configure_logger()

                corr.set_correlation_id("corr-456")
                logger.info("with correlation")
                logger.complete()
                captured = capsys.readouterr()
                out = captured.out.strip()

                parsed = json.loads(out)
                assert parsed["correlation_id"] == "corr-456"

    def test_json_empty_correlation_id(self, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
        """JSON output shows empty string for correlation_id when not set."""
        self._patch_json(monkeypatch)
        logger_mod = _logger_mod()
        from src.common.infrastructure.core._config import Settings as S

        with patch.object(S, "_env_file", None, create=True):
            with patch("src.common.infrastructure.adapters.logger.settings", S()):
                logger_mod.configure_logger()

                logger.info("no correlation")
                logger.complete()
                captured = capsys.readouterr()
                out = captured.out.strip()

                parsed = json.loads(out)
                assert parsed["correlation_id"] == ""


# ── Text Format ──────────────────────────────────────────────────────────────


class TestTextFormat:
    """When LOG_FORMAT=text, logs are human-readable text."""

    def test_text_format_outputs_message(self, dev_settings: Settings, capsys) -> None:
        """Text format produces visible log output with the message."""
        logger_mod = _logger_mod()
        with patch("src.common.infrastructure.adapters.logger.settings", dev_settings):
            logger_mod.configure_logger()

            logger.info("text msg")
            logger.complete()
            captured = capsys.readouterr()
            out = captured.out.strip()

            assert "text msg" in out

    def test_text_format_level_routing(self, dev_settings: Settings, capsys) -> None:
        """Text format produces visible log output with the message."""
        logger_mod = _logger_mod()
        with patch("src.common.infrastructure.adapters.logger.settings", dev_settings):
            logger_mod.configure_logger()

            logger.warning("warning msg")
            logger.complete()
            captured = capsys.readouterr()
            out = captured.out.strip()

            assert "WARNING" in out or "warning msg" in out


# ── Logger Configuration ─────────────────────────────────────────────────────


class TestJsonFormatFunction:
    """Unit tests for the _json_format function as a pure function."""

    def test_json_format_special_chars_in_message(self) -> None:
        """Messages with angle brackets or braces are properly escaped."""
        from src.common.infrastructure.adapters.logger import _json_format

        record = {
            "time": datetime.datetime(2026, 6, 22, 3, 0, 0),
            "level": type("Level", (), {"name": "ERROR"})(),
            "name": "test",
            "function": "test_func",
            "line": 42,
            "message": "<script>alert('xss')</script>",
            "extra": {},
        }
        result = _json_format(record)
        # The result is a format template, but after format_map it becomes JSON
        # Let's test by actually doing format_map on it
        formatted = result.format_map({**record, "exception": ""})
        parsed = json.loads(formatted.strip())
        assert parsed["message"] == "<script>alert('xss')</script>"
        assert parsed["level"] == "ERROR"
        assert parsed["line"] == 42

    def test_json_format_empty_message(self) -> None:
        """Empty message is serialized correctly."""
        from src.common.infrastructure.adapters.logger import _json_format

        record = {
            "time": datetime.datetime(2026, 6, 22, 3, 0, 0),
            "level": type("Level", (), {"name": "DEBUG"})(),
            "name": "test",
            "function": "test_func",
            "line": 1,
            "message": "",
            "extra": {},
        }
        result = _json_format(record)
        formatted = result.format_map({**record, "exception": ""})
        parsed = json.loads(formatted.strip())
        assert parsed["message"] == ""
        assert parsed["level"] == "DEBUG"


class TestLoggerConfiguration:
    """Logger add() calls and sink registration."""

    def test_configure_logger_adds_sinks(self, dev_settings: Settings) -> None:
        """configure_logger adds at least one sink to the logger."""
        logger_mod = _logger_mod()
        with patch("src.common.infrastructure.adapters.logger.settings", dev_settings):
            logger_mod.configure_logger()
            # After configure_logger, logger should have handlers registered
            assert len(logger._core.handlers) > 0

    def test_configure_logger_returns_logger(self, dev_settings: Settings) -> None:
        """configure_logger() returns the loguru logger instance."""
        logger_mod = _logger_mod()
        with patch("src.common.infrastructure.adapters.logger.settings", dev_settings):
            result = logger_mod.configure_logger()
            assert result is logger

    def test_configure_logger_is_cached(self, dev_settings: Settings) -> None:
        """configure_logger is decorated with @lru_cache — second call is no-op."""
        logger_mod = _logger_mod()
        with patch("src.common.infrastructure.adapters.logger.settings", dev_settings):
            result1 = logger_mod.configure_logger()
            result2 = logger_mod.configure_logger()
            assert result1 is result2
