"""Unit tests for AnimalCacheInvalidationHandler.

Verifies that when the handler is called, it fires async cache
invalidation via asyncio.create_task.
"""

import asyncio
from unittest.mock import AsyncMock
from uuid import UUID

from src.cattle.infrastructure.events.handlers.cache_invalidation import (
    AnimalCacheInvalidationHandler,
)
from src.common.domain.events.base import DomainEvent
from src.common.domain.ports.cache_service import ICacheService


class TestAnimalCacheInvalidationHandler:
    """AnimalCacheInvalidationHandler invalidates cattle cache on animal events."""

    def setup_method(self) -> None:
        self.cache_service = AsyncMock(spec=ICacheService)
        self.handler = AnimalCacheInvalidationHandler(
            cache_service=self.cache_service,
        )

    async def test_handler_invalidates_animal_cache_pattern(self) -> None:
        """Calling the handler triggers cache invalidation for the animal pattern."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="animal.created",
        )

        self.handler(event)
        # Yield control to the event loop so the create_task fires
        await asyncio.sleep(0)

        self.cache_service.invalidate_pattern.assert_called_once_with(
            "cattle:animals:*",
        )

    def test_uses_correct_cache_pattern(self) -> None:
        """ANIMAL_CACHE_PATTERN constant is exposed and matches expected."""
        assert AnimalCacheInvalidationHandler.ANIMAL_CACHE_PATTERN == "cattle:animals:*"

    def test_handler_is_callable(self) -> None:
        """Handler is callable with a DomainEvent."""
        assert callable(self.handler)
