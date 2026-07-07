"""Cache invalidation handler for cattle domain events.

When an animal-related domain event is dispatched, this handler fires
a fire-and-forget async task that invalidates matching cache entries.
"""

import asyncio

from src.common.domain.events.base import DomainEvent
from src.common.domain.ports.cache_service import ICacheService


class AnimalCacheInvalidationHandler:
    """Invalidates cattle cache entries when an animal event occurs.

    Uses ``asyncio.create_task()`` to fire async cache invalidation
    without blocking the dispatch caller.  This is safe because
    dispatch always happens from an async context.
    """

    ANIMAL_CACHE_PATTERN = "cattle:animals:*"

    def __init__(self, cache_service: ICacheService) -> None:
        self._cache_service = cache_service

    def __call__(self, event: DomainEvent) -> None:
        """Schedule async invalidation of all animal cache keys."""
        asyncio.create_task(
            self._cache_service.invalidate_pattern(self.ANIMAL_CACHE_PATTERN),
        )
