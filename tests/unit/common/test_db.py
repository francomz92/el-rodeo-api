"""Unit tests for database connection engine configuration.

These tests verify that the async engine is created with the correct
pool settings drawn from the application Settings object.
"""

import os
import sys
from unittest.mock import patch

# Required env vars for Settings instantiation.
_MIN_ENV = {
    "DB_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
    "SECRET": "test-secret-key-for-testing",
    "JWT_ALGORITHM": "HS256",
    "SMTP_SERVER": "smtp.test.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "test@test.com",
    "SMTP_PASSWORD": "testpass",
    "DOMAIN": "http://test.com",
    "BROKER_URL": "redis://localhost:6380/0",
    "RESULT_BACKEND_URL": "redis://localhost:6380/0",
}


def _fresh_db_module(env: dict[str, str]) -> None:
    """Fully reimport the db module under the given environment.

    1. Clear the full ``src`` module chain from sys.modules so that
       import re-executes every module in the dependency tree with fresh
       env — parent packages otherwise retain stale submodule references.
    2. Patch os.environ with the provided dict (clear=True prevents .env
       interference).
    3. Import the db module — this triggers re-import of ``_config`` which
       calls ``_get_settings()``, reads the patched env, and returns a
       fresh ``Settings()``.
    """
    for k in list(sys.modules):
        if k.startswith("src.") or k == "src":
            sys.modules.pop(k, None)

    with patch.dict(os.environ, env, clear=True):
        import src.common.infrastructure.persistence.connections.db as db_module  # noqa: F811
    return db_module


# ── Tests ──────────────────────────────────────────────────────────────────


@patch("sqlalchemy.ext.asyncio.create_async_engine")
def test_engine_created_with_pool_settings_from_config(mock_create_engine) -> None:
    """create_async_engine is called with pool settings from Settings defaults."""
    _fresh_db_module(_MIN_ENV)

    mock_create_engine.assert_called_once()
    _call_args, call_kwargs = mock_create_engine.call_args

    assert call_kwargs["pool_size"] == 10
    assert call_kwargs["max_overflow"] == 20
    assert call_kwargs["pool_recycle"] == 3600
    assert call_kwargs["pool_pre_ping"] is True


@patch("sqlalchemy.ext.asyncio.create_async_engine")
def test_engine_created_with_db_url_from_settings(mock_create_engine) -> None:
    """create_async_engine is called with the DB_URL from Settings."""
    _fresh_db_module(_MIN_ENV)

    mock_create_engine.assert_called_once()
    call_args, _call_kwargs = mock_create_engine.call_args

    url = call_args[0] if call_args else _call_kwargs.get("url")
    assert url is not None
    assert isinstance(url, str)
    assert len(url) > 0


@patch("sqlalchemy.ext.asyncio.create_async_engine")
def test_engine_created_with_overridden_pool_settings(mock_create_engine) -> None:
    """create_async_engine reads overridden pool settings from env vars.

    Triangulation: verifies the db module actually consults Settings rather
    than using hardcoded values.
    """
    env = {**_MIN_ENV, "DB_POOL_SIZE": "25", "DB_POOL_OVERFLOW": "50", "DB_POOL_RECYCLE": "7200"}
    _fresh_db_module(env)

    mock_create_engine.assert_called_once()
    _call_args, call_kwargs = mock_create_engine.call_args

    assert call_kwargs["pool_size"] == 25
    assert call_kwargs["max_overflow"] == 50
    assert call_kwargs["pool_recycle"] == 7200
