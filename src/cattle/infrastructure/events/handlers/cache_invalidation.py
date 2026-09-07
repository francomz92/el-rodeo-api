"""Cache invalidation handler for cattle domain events.

When an animal-related domain event is dispatched, this handler
invalidates matching cache entries.
"""

from src.common.domain.events.base import DomainEvent
from src.common.domain.ports.cache_service import ICacheService


class AnimalCacheInvalidationHandler:
    """Invalidates cattle cache entries when an animal event occurs."""

    ANIMAL_CACHE_PATTERN = "cattle:animals:*"

    def __init__(self, cache_service: ICacheService) -> None:
        self._cache_service = cache_service

    async def __call__(self, event: DomainEvent) -> None:
        """Invalidate all animal cache keys."""
        await self._cache_service.invalidate_pattern(self.ANIMAL_CACHE_PATTERN)
