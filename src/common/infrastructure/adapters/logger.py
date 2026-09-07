"""Loguru logger configuration with structured JSON/text output.

Provides ``configure_logger()`` (cached) that sets up:

- Stdout sink at ``LOG_LEVEL`` level, format determined by ``LOG_FORMAT``
- ``{project_root}/logs/error.log`` — ERROR+, 10 MB rotation, 30-day retention
- ``{project_root}/logs/app_{date}.log`` — INFO+, 10 MB rotation, 30-day retention (only non-DEBUG)

A ``correlation_filter`` function injects the active correlation ID
into every log record's ``extra`` dict before formatting.
"""

import json
import sys
from datetime import datetime
from functools import lru_cache

from loguru import logger
from loguru._logger import Logger

from src.common.infrastructure.adapters.correlation import get_correlation_id
from src.common.infrastructure.core import settings

# ── Text format template ──────────────────────────────────────────────────────

_TEXT_FORMAT = "{time:%d-%m-%Y %H:%M:%S} | {level:8} | {name}:{function}:{line} - {message}"


# ── Correlation filter ────────────────────────────────────────────────────────


def correlation_filter(record: dict) -> bool:
    """Loguru filter: inject current correlation_id into *record* ``extra``.

    Always returns ``True`` (never drops records).
    """
    cid = get_correlation_id()
    if cid:
        record["extra"]["correlation_id"] = cid
    return True


# ── Format helpers ─────────────────────────────────────────────────────────────


def _make_json_record(record: dict) -> dict:
    """Convert a Loguru record dict into a JSON-safe dictionary."""
    timestamp = record["time"]
    if isinstance(timestamp, datetime):
        timestamp = timestamp.isoformat()
    else:
        timestamp = str(timestamp)

    return {
        "timestamp": timestamp,
        "level": record["level"].name,
        "name": record["name"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
        "correlation_id": record["extra"].get("correlation_id", ""),
    }


def _json_format(record: dict) -> str:
    """Callable format for JSON log output.

    Returns a format template that Loguru can process via ``format_map``.
    JSON braces are escaped so they pass through literally, while the
    ``{exception}`` placeholder is preserved for Loguru to resolve.
    Angle brackets in the JSON are escaped to avoid Loguru's color-tag
    parser raising ``ValueError``.
    """
    d = _make_json_record(record)
    raw = json.dumps(d, default=str)
    # Escape JSON structural braces so format_map treats them literally
    escaped = raw.replace("{", "{{").replace("}", "}}")
    # Escape angle brackets for Loguru's Colorizer.
    # Use the JSON unicode escape \u003C (U+003C = '<') so the final
    # output is still valid JSON after format_map resolves.
    escaped = escaped.replace("<", "\\u003C")
    # Append exception placeholder (Loguru resolves this via format_map)
    return f"{escaped}\n{{exception}}"


# ── Public API ─────────────────────────────────────────────────────────────────


@lru_cache
def configure_logger() -> Logger:
    """Configure Loguru sinks.

    Call once at application startup. Subsequent calls are no-ops
    thanks to ``@lru_cache``.
    """
    logger.remove()

    is_json = settings.LOG_FORMAT == "json"

    # --- Stdout sink -------------------------------------------------------
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=_json_format if is_json else _TEXT_FORMAT,  # type: ignore[arg-type]
        filter=correlation_filter,  # type: ignore[arg-type]
        colorize=not is_json,
        enqueue=True,
        diagnose=settings.DEBUG,
    )  # ty:ignore[no-matching-overload]

    # --- Error file sink ---------------------------------------------------
    logger.add(  # type: ignore[call-overload]
        settings.LOG_DIR / "error.log",
        level="ERROR",
        format=_json_format if is_json else _TEXT_FORMAT,  # ty:ignore[invalid-argument-type]
        filter=correlation_filter,  # ty:ignore[invalid-argument-type]
        rotation="10 MB",
        retention="30 days",
        enqueue=True,
        backtrace=settings.DEBUG,
        diagnose=settings.DEBUG,
    )

    # --- Application file sink (non-DEBUG only) ----------------------------
    if not settings.DEBUG:
        logger.add(  # type: ignore[call-overload]
            settings.LOG_DIR / "app_{time:YYYY-MM-DD}.log",
            level="INFO",
            format=_json_format if is_json else _TEXT_FORMAT,  # ty:ignore[invalid-argument-type]
            filter=correlation_filter,  # ty:ignore[invalid-argument-type]
            rotation="10 MB",
            retention="30 days",
            enqueue=True,
            backtrace=settings.DEBUG,
            diagnose=settings.DEBUG,
        )

    return logger  # type: ignore
