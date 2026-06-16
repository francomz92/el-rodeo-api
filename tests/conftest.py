"""Shared fixtures and configuration for all tests."""

from typing import Any
from uuid import uuid4

import pytest

from src.common.domain.types import Sentinel


@pytest.fixture
def any_uuid() -> Any:
    """Return a random UUID for use in tests where the exact value doesn't matter."""
    return uuid4()


@pytest.fixture
def unset() -> Sentinel:
    """Provide the Sentinel.UNSET sentinel value."""
    return Sentinel.UNSET
