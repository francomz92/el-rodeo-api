"""Cache service port (interface).

Defines the contract for cache-aside caching used by domain use cases.
Implementations handle serialization, TTL, and backend-specific concerns.
"""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any


class ICacheService(ABC):
    """Port for a cache-aside cache service.

    Provides typed get/set/delete operations with configurable TTL per key
    and a get_or_set convenience that caches on cache miss via a factory.
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Return deserialized value for *key*, or None if missing / expired."""
        ...

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        domain: str | None = None,
    ) -> None:
        """Store *value* under *key* with optional *ttl* (seconds).

        When *domain* is provided, the domain-specific default TTL is used
        unless *ttl* is explicitly given.  The effective TTL is:

            ttl  if *ttl* is not None
            domain_ttl  if *domain* is configured and *ttl* is None
            default_ttl  otherwise
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove the entry at *key*, if it exists (no-op otherwise)."""
        ...

    @abstractmethod
    async def get_or_set(
        self,
        key: str,
        ttl: int,
        factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        """Return cached value for *key*, or call *factory*, cache, and return.

        This is the classic cache-aside / read-through pattern:
        1. Try ``get(key)``.
        2. If cache hit → return value.
        3. If cache miss → call ``factory()``, ``set(key, result, ttl)``, return result.
        """
        ...

    @abstractmethod
    async def invalidate_pattern(self, pattern: str) -> None:
        """Remove all keys matching Redis-style glob *pattern* (e.g. ``"user:*"``).

        Uses SCAN internally so it does not block the Redis event loop.
        Implementations SHOULD prefix the pattern with the application key
        namespace.
        """
        ...
