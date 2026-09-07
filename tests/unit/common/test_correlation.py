"""Unit tests for the correlation ID module.

Tests the contextvar-based correlation ID set/get functions
that don't exist yet (RED phase — proving they must be built).
"""

import re
import uuid

from src.common.infrastructure.adapters.correlation import (
    get_correlation_id,
    set_correlation_id,
)


class TestCorrelationId:
    """Correlation ID context management."""

    def test_default_is_empty_string(self) -> None:
        """get_correlation_id() returns '' when nothing has been set.

        The contextvar default is "" — no value means empty string.
        """
        assert get_correlation_id() == ""

    def test_set_with_explicit_value(self) -> None:
        """set_correlation_id('abc-123') stores and returns 'abc-123'."""
        result = set_correlation_id("abc-123")[0]
        assert result == "abc-123"
        assert get_correlation_id() == "abc-123"

    def test_set_with_none_generates_uuid_hex(self) -> None:
        """set_correlation_id() with no argument generates a UUID hex string."""
        result = set_correlation_id()[0]
        assert isinstance(result, str)
        assert len(result) == 32
        # UUID hex is 32 hex chars (no dashes)
        assert re.fullmatch(r"[0-9a-f]{32}", result)

    def test_set_with_none_uses_uuid4_hex(self) -> None:
        """set_correlation_id() generates a valid UUID v4 hex.

        The hex string must represent a valid UUID (version nibble = 4).
        """
        cid = set_correlation_id()[0]
        # Insert dashes to validate it as a UUID
        uuid_with_dashes = f"{cid[0:8]}-{cid[8:12]}-{cid[12:16]}-{cid[16:20]}-{cid[20:]}"
        parsed = uuid.UUID(uuid_with_dashes)
        assert parsed.version == 4

    def test_context_isolation(self) -> None:
        """Correlation IDs in different contexts do not leak.

        This tests that ContextVar correctly isolates values across
        logical scopes.
        """
        import asyncio

        async def worker_1() -> str:
            set_correlation_id("worker-1-id")
            await asyncio.sleep(0.01)
            return get_correlation_id()

        async def worker_2() -> str:
            set_correlation_id("worker-2-id")
            await asyncio.sleep(0.01)
            return get_correlation_id()

        async def main() -> tuple[str, str]:
            r1, r2 = await asyncio.gather(worker_1(), worker_2())
            return r1, r2

        r1, r2 = asyncio.run(main())
        assert r1 == "worker-1-id"
        assert r2 == "worker-2-id"

    def test_multiple_sets_update_value(self) -> None:
        """Calling set_correlation_id multiple times overwrites the value."""
        set_correlation_id("first")
        assert get_correlation_id() == "first"

        set_correlation_id("second")
        assert get_correlation_id() == "second"

    def test_generated_ids_are_unique(self) -> None:
        """Multiple calls to set_correlation_id(None) produce different values."""
        ids = {set_correlation_id()[0] for _ in range(100)}
        assert len(ids) == 100
