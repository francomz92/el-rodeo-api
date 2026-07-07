# Caching Service Specification

## Purpose

Shared Redis caching service for frequent domain queries (animals, users, catalogs) to reduce database load and improve response latency.

## Requirements

### Requirement: CacheService abstraction

The system MUST expose a `CacheService` class wrapping `redis.asyncio.Redis` with JSON serialization/deserialization, configurable TTL per domain, and cache-aside semantics.

#### Scenario: Cache hit returns deserialized data

- GIVEN a key `"user:42"` stored in Redis with JSON value `{"id": 42, "name": "Alice"}`
- WHEN `CacheService.get("user:42")` is called
- THEN the parsed dict `{"id": 42, "name": "Alice"}` is returned

#### Scenario: Cache miss returns None

- GIVEN no value for key `"user:99"` in Redis
- WHEN `CacheService.get("user:99")` is called
- THEN `None` is returned

### Requirement: TTL configuration per domain

The system MUST accept per-domain or per-operation TTL overrides, with a default fallback of 300 seconds.

#### Scenario: Domain-specific TTL applied

- GIVEN a `CacheService` configured with `{"animals": 60}` TTL mapping
- WHEN setting `"animal:1"` with `domain="animals"`
- THEN the key expires after 60 seconds

#### Scenario: Default TTL used when no domain override

- GIVEN a `CacheService` with default TTL of 300
- WHEN setting `"unknown:1"` with no domain override
- THEN the key expires after 300 seconds

### Requirement: Invalidation by key and pattern

The system MUST support deleting individual keys and key patterns (e.g., `"user:*"`). Mutation use cases MUST invalidate cache entries to prevent stale reads.

#### Scenario: Invalidate by key removes entry

- GIVEN a cached value at key `"animal:1"`
- WHEN `CacheService.invalidate("animal:1")` is called
- THEN `CacheService.get("animal:1")` returns `None`

#### Scenario: Invalidate by pattern clears multiple entries

- GIVEN cached keys `"animal:1"`, `"animal:2"`, `"user:1"`
- WHEN `CacheService.invalidate_pattern("animal:*")` is called
- THEN `CacheService.get("animal:1")` and `CacheService.get("animal:2")` return `None`
- AND `CacheService.get("user:1")` still returns its cached value
