# Proposal: Phase 9a — Polish & Scale Foundation

## Intent

Fix systemic test failures blocking CI confidence, then add the caching and pagination infrastructure that downstream Phase 9 work (9b observability, 9c S3 file storage, 9d performance) depends on.

## Scope

### In Scope
1. Fix 41 integration test 403s — add proper roles to `client`/`tenant_client` fixtures
2. Redis caching service — reusable abstraction for animals, users, catalogs queries
3. Cursor-based pagination schema — shared Pydantic schema + migrate all limit/offset endpoints
4. N+1 query audit — scan repositories for N+1 patterns, fix found instances
5. Connection pool tuning — review `pool_size=10, max_overflow=20` settings

### Out of Scope
- S3 file storage (Phase 9c)
- Observability/metrics (Phase 9b)
- Performance benchmarking (Phase 9d)
- Celery task optimization

## Capabilities

### New Capabilities
- `caching`: Shared Redis caching service with TTL, invalidation, and serialization for frequent domain queries
- `pagination`: Reusable cursor-based pagination schema with `CursorPage[T]` generic model and query helpers

### Modified Capabilities
- None — test fixture fixes align with existing RBAC spec; pool tuning and N+1 fixes are implementation-only

## Approach

| Work Item | Approach |
|-----------|----------|
| Fix 403 tests | Set `role=ADMIN` on `client` fixture for write-capable tests, verify role-guard tests use role-specific fixtures |
| Redis caching | Service class wrapping `redis.asyncio.Redis`, JSON serialization, configurable TTL per domain, decorator-style or dependency-injected |
| Cursor pagination | `CursorPage[T]` generic schema with `cursor`, `next_cursor`, `items`, `total`; migrate each domain's query params, use cases, repos |
| N+1 audit | Check each `list_*` repo method for eager-loading gaps; fix with `selectinload`/`joinedload` |
| Pool tuning | Benchmark connection usage under load, adjust `pool_size`/`max_overflow`/`pool_recycle` |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `tests/integration/conftest.py` | Modified | Add role to `client`/`tenant_client` fixtures |
| `src/common/infrastructure/adapters/http/input/query_params.py` | Modified | Add cursor-based pagination schema |
| `src/common/infrastructure/persistence/connections/redis.py` | Modified | Build caching service on existing Redis client |
| `src/*/infrastructure/persistence/repositories/*.py` | Modified | Migrate limit/offset → cursor; fix N+1 |
| `src/common/infrastructure/persistence/connections/db.py` | Modified | Tune pool settings |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Cursor pagination breaks existing API contracts | Low | Keep old query params as deprecated aliases |
| Redis cache invalidation misses stale data | Med | Add TTL; use cache-aside with write-through on mutation |
| Pool tuning causes OOM under peak load | Low | Test under synthetic load before production deploy |

## Rollback Plan

1. Revert fixture changes → tests go red again (status quo ante)
2. Disable caching via feature flag (no code revert needed)
3. Cursor pagination: keep `offset`/`limit` params as fallback, toggle via config
4. Pool tuning: revert `pool_size`/`max_overflow` to previous values

## Dependencies

- Redis already available (used for Celery, token blacklist, rate limiter)

## Success Criteria

- [ ] 41 failing integration tests pass with proper roles
- [ ] All 883 existing tests still pass (no regressions)
- [ ] Caching service works end-to-end with one domain query
- [ ] Two endpoints migrated to cursor pagination with passing tests
- [ ] N+1 audit report produced with zero critical instances
- [ ] Pool tuning deployed with verified stability under load test
