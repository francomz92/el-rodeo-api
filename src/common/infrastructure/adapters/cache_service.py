"""Redis-backed cache service adapter.

Implements :class:`ICacheService` using a shared ``redis.asyncio.Redis``
connection.  Values are JSON-serialised with Pydantic model support.

All Redis operations are wrapped in try/except so a Redis outage
degrades gracefully (cache miss / no-op) instead of raising 500.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel
from redis.asyncio import Redis

from src.common.domain.ports.cache_service import ICacheService
from src.common.utils import log


def _safe_key(key: str) -> str:
    """Sanitise a cache key for logging — truncate and hash sensitive segments.

    Replaces anything after the first colon with a SHA-256 prefix so PII
    (e.g. emails, user IDs in key values) never appears raw in logs.
    """
    import hashlib

    if ":" in key:
        prefix, suffix = key.split(":", 1)
        suffix_hash = hashlib.sha256(suffix.encode()).hexdigest()[:8]
        return f"{prefix}:{suffix_hash}"
    return key


# All cache keys are prefixed to avoid collisions with other Redis consumers
# (e.g. the token blacklist).
_KEY_PREFIX = "cache:"

# Default per-domain TTLs in seconds.
_DEFAULT_TTLS: dict[str, int] = {
    "animals": 60,
    "users": 120,
    "catalogs": 300,
}

_DEFAULT_TTL = 300


def _serialize(value: Any) -> str:
    """JSON-serialise *value*, handling Pydantic models transparently."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    elif isinstance(value, dict):
        value = _serialize_dict(value)
    elif isinstance(value, list):
        value = [_serialize_value(item) for item in value]
    return json.dumps(value, default=str)


def _serialize_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively serialise a dict, converting non-serialisable values."""
    return {k: _serialize_value(v) for k, v in d.items()}


def _serialize_value(value: Any) -> Any:
    """Convert a single value to a JSON-safe type."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return _serialize_dict(value)
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def _deserialize(data: str) -> Any:
    """Return the Python object decoded from a JSON *data* string."""
    return json.loads(data)


class RedisCacheService(ICacheService):
    """Cache-aside adapter backed by a shared ``redis.asyncio.Redis`` pool.

    Parameters
    ----------
    redis:
        The shared Redis client (usually from ``connections/redis.py``).
    domain_ttls:
        Optional mapping of domain name → TTL in seconds.  Merged on top of
        the built-in defaults so callers can override or extend per-domain
        TTLs without replacing the whole dictionary.
    key_prefix:
        Optional key prefix (default ``"cache:"``).
    default_ttl:
        Fallback TTL when no domain-specific TTL is configured and no
        explicit *ttl* is passed to ``set()``.
    """

    def __init__(
        self,
        redis: Redis,
        domain_ttls: dict[str, int] | None = None,
        key_prefix: str | None = None,
        default_ttl: int | None = None,
    ) -> None:
        self._redis = redis
        self._key_prefix = key_prefix or _KEY_PREFIX

        # Merge caller domain TTLs over built-in defaults.
        merged = dict(_DEFAULT_TTLS)
        if domain_ttls:
            merged.update(domain_ttls)
        self._domain_ttls = merged

        self._default_ttl = default_ttl or _DEFAULT_TTL

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prefixed(self, key: str) -> str:
        """Return *key* with the application key prefix."""
        return f"{self._key_prefix}{key}"

    def _resolve_ttl(self, ttl: int | None, domain: str | None) -> int:
        """Determine the effective TTL for a ``set()`` call.

        Precedence: explicit *ttl* > domain default > application default.
        """
        if ttl is not None:
            return ttl
        if domain is not None and domain in self._domain_ttls:
            return self._domain_ttls[domain]
        return self._default_ttl

    # ------------------------------------------------------------------
    # ICacheService
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Any | None:
        """Return deserialised value for *key*, or ``None``.

        Returns ``None`` on any Redis error (cache miss degradation).
        """
        try:
            raw = await self._redis.get(self._prefixed(key))
            if raw is None:
                return None
            return _deserialize(raw)
        except Exception:
            log.exception("Redis GET failed for key={} — degrading as cache miss", _safe_key(key))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        domain: str | None = None,
    ) -> None:
        """JSON-serialise *value* and store under *key* with resolved TTL.

        Silently no-ops on Redis error (write-through degradation).
        """
        try:
            effective_ttl = self._resolve_ttl(ttl, domain)
            serialised = _serialize(value)
            await self._redis.set(self._prefixed(key), serialised, ex=effective_ttl)
        except Exception:
            log.exception("Redis SET failed for key={} — degrading silently", key)

    async def delete(self, key: str) -> None:
        """Remove the entry at *key* (no-op if missing).

        Silently no-ops on Redis error.
        """
        try:
            await self._redis.delete(self._prefixed(key))
        except Exception:
            log.exception("Redis DELETE failed for key={} — degrading silently", key)

    async def get_or_set(
        self,
        key: str,
        ttl: int,
        factory: Callable[[], Awaitable[Any]],
        domain: str | None = None,
    ) -> Any:
        """Cache-aside: return cached value or call *factory*, cache, return.

        Falls through to *factory* on any Redis error.
        """
        try:
            cached = await self.get(key)
            if cached is not None:
                return cached
        except Exception:
            log.exception(
                "Redis GET (get_or_set) failed for key={} — falling through to factory",
                key,
            )

        value = await factory()
        await self.set(key, value, ttl=ttl, domain=domain)
        return value

    async def invalidate_pattern(self, pattern: str) -> None:
        """Remove all keys matching *pattern* via non-blocking SCAN.

        Silently no-ops on Redis error.
        """
        try:
            prefixed_pattern = self._prefixed(pattern)
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(cursor=cursor, match=prefixed_pattern, count=100)
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            log.exception(
                "Redis SCAN/DELETE failed for pattern={} — degrading silently",
                pattern,
            )
