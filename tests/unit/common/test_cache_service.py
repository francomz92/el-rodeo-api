"""Unit tests for ICacheService port and RedisCacheService adapter.

Covers cache hit/miss, TTL resolution (domain-specific & default),
invalidation by key and pattern, get_or_set cache-aside semantics,
and JSON/Pydantic serialisation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from src.common.domain.ports.cache_service import ICacheService
from src.common.infrastructure.adapters.cache_service import (
    RedisCacheService,
    _deserialize,
    _serialize,
)

# =========================================================================
# Port contract
# =========================================================================


class TestICacheServiceInterface:
    """ICacheService is an abstract class — instantiation must fail."""

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ICacheService()  # type: ignore[abstract]


# =========================================================================
# Serialisation helpers
# =========================================================================


class _DummyModel(BaseModel):
    id: int
    name: str


class TestSerialize:
    """_serialize handles dicts, models, and edge cases."""

    def test_plain_dict(self) -> None:
        result = _serialize({"a": 1, "b": "hello"})
        assert result == '{"a": 1, "b": "hello"}'

    def test_pydantic_model(self) -> None:
        model = _DummyModel(id=42, name="Alice")
        result = _serialize(model)
        assert result == '{"id": 42, "name": "Alice"}'

    def test_list_of_models(self) -> None:
        models = [_DummyModel(id=1, name="A"), _DummyModel(id=2, name="B")]
        result = _serialize(models)
        assert result == '[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]'

    def test_none(self) -> None:
        assert _serialize(None) == "null"


class TestDeserialize:
    """_deserialize restores JSON strings to Python objects."""

    def test_dict(self) -> None:
        assert _deserialize('{"a": 1}') == {"a": 1}

    def test_list(self) -> None:
        assert _deserialize("[1, 2, 3]") == [1, 2, 3]

    def test_none(self) -> None:
        assert _deserialize("null") is None


# =========================================================================
# RedisCacheService — cache hit / miss
# =========================================================================


@pytest.fixture
def mock_redis() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def cache(mock_redis: AsyncMock) -> RedisCacheService:
    return RedisCacheService(redis=mock_redis)


class TestGet:
    """CacheService.get behaviour."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_deserialized_data(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = '{"id": 42, "name": "Alice"}'

        result = await cache.get("user:42")

        assert result == {"id": 42, "name": "Alice"}
        mock_redis.get.assert_awaited_once_with("cache:user:42")

    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = None

        result = await cache.get("user:99")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_applies_key_prefix(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = None

        await cache.get("animal:1")

        mock_redis.get.assert_awaited_once_with("cache:animal:1")


class TestSet:
    """CacheService.set behaviour."""

    @pytest.mark.asyncio
    async def test_sets_with_explicit_ttl(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        await cache.set("k1", {"x": 1}, ttl=60)

        mock_redis.set.assert_awaited_once_with("cache:k1", '{"x": 1}', ex=60)

    @pytest.mark.asyncio
    async def test_sets_with_domain_ttl(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        await cache.set("animal:1", {"name": "Bessie"}, domain="animals")

        mock_redis.set.assert_awaited_once_with("cache:animal:1", '{"name": "Bessie"}', ex=60)

    @pytest.mark.asyncio
    async def test_sets_with_default_ttl_when_no_domain_or_explicit(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        await cache.set("unknown:1", "val")

        mock_redis.set.assert_awaited_once_with("cache:unknown:1", '"val"', ex=300)

    @pytest.mark.asyncio
    async def test_explicit_ttl_overrides_domain(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        await cache.set("animal:1", "val", ttl=999, domain="animals")

        mock_redis.set.assert_awaited_once_with("cache:animal:1", '"val"', ex=999)

    @pytest.mark.asyncio
    async def test_custom_domain_ttls_via_constructor(self, mock_redis: AsyncMock) -> None:
        cache = RedisCacheService(redis=mock_redis, domain_ttls={"rare": 10})

        await cache.set("x", "val", domain="rare")

        mock_redis.set.assert_awaited_once_with("cache:x", '"val"', ex=10)


class TestDelete:
    """CacheService.delete behaviour."""

    @pytest.mark.asyncio
    async def test_delete_removes_key(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        await cache.delete("animal:1")

        mock_redis.delete.assert_awaited_once_with("cache:animal:1")

    @pytest.mark.asyncio
    async def test_delete_is_noop_on_missing_key(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        mock_redis.delete.return_value = 0

        await cache.delete("non_existent")

        mock_redis.delete.assert_awaited_once_with("cache:non_existent")


class TestInvalidatePattern:
    """CacheService.invalidate_pattern behaviour."""

    @pytest.mark.asyncio
    async def test_clears_matching_keys(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        mock_redis.scan.side_effect = [
            (42, [b"cache:animal:1", b"cache:animal:2"]),
            (0, []),
        ]

        await cache.invalidate_pattern("animal:*")

        mock_redis.scan.assert_any_call(cursor=0, match="cache:animal:*", count=100)
        mock_redis.delete.assert_awaited_once_with(b"cache:animal:1", b"cache:animal:2")

    @pytest.mark.asyncio
    async def test_does_not_affect_non_matching_keys(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        mock_redis.scan.side_effect = [
            (99, [b"cache:user:1"]),
            (0, []),
        ]

        await cache.invalidate_pattern("animal:*")

        # Only the scanned keys are passed to delete
        mock_redis.delete.assert_awaited_once_with(b"cache:user:1")

    @pytest.mark.asyncio
    async def test_empty_pattern_no_errors(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        mock_redis.scan.return_value = (0, [])

        await cache.invalidate_pattern("nonexistent:*")

        mock_redis.scan.assert_awaited_once()


class TestGetOrSet:
    """CacheService.get_or_set — cache-aside pattern."""

    @pytest.mark.asyncio
    async def test_returns_cached_value_when_hit(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = '"cached"'
        factory = AsyncMock(return_value="fresh")

        result = await cache.get_or_set("k1", ttl=60, factory=factory)

        assert result == "cached"
        factory.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_calls_factory_and_caches_on_miss(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = None  # miss
        factory = AsyncMock(return_value={"computed": "data"})

        result = await cache.get_or_set("k1", ttl=60, factory=factory)

        assert result == {"computed": "data"}
        factory.assert_awaited_once()
        mock_redis.set.assert_awaited_once_with("cache:k1", '{"computed": "data"}', ex=60)


# =========================================================================
# Pydantic model serialisation
# =========================================================================


class _AnimalModel(BaseModel):
    id: int
    name: str
    breed: str | None = None


class TestPydanticSerialisation:
    """RedisCacheService correctly serialises/deserialises Pydantic models."""

    @pytest.mark.asyncio
    async def test_set_and_get_pydantic_model(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        animal = _AnimalModel(id=1, name="Bessie", breed="Angus")
        mock_redis.set.return_value = True

        await cache.set("animal:1", animal)

        mock_redis.set.assert_awaited_once_with(
            "cache:animal:1",
            '{"id": 1, "name": "Bessie", "breed": "Angus"}',
            ex=300,
        )

    @pytest.mark.asyncio
    async def test_get_returns_dict_not_model(self, cache: RedisCacheService, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = '{"id": 1, "name": "Bessie", "breed": "Angus"}'

        result = await cache.get("animal:1")

        # Cache returns raw dicts — deserialisation is JSON, not model-aware
        assert result == {"id": 1, "name": "Bessie", "breed": "Angus"}


# =========================================================================
# Custom key prefix
# =========================================================================


class TestCustomKeyPrefix:
    """Constructor-level key prefix override."""

    @pytest.mark.asyncio
    async def test_uses_custom_prefix(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = None
        cache = RedisCacheService(redis=mock_redis, key_prefix="myapp:")

        await cache.get("k")

        mock_redis.get.assert_awaited_once_with("myapp:k")


# =========================================================================
# Custom default TTL
# =========================================================================


class TestCustomDefaultTtl:
    """Constructor-level default TTL override."""

    @pytest.mark.asyncio
    async def test_uses_custom_default_ttl(self, mock_redis: AsyncMock) -> None:
        cache = RedisCacheService(redis=mock_redis, default_ttl=600)

        await cache.set("k", "v")

        mock_redis.set.assert_awaited_once_with("cache:k", '"v"', ex=600)
