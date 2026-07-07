# Design: Phase 9a — Polish & Scale Foundation

## Technical Approach

Five independent work items: (1) fix integration test 403s by raising `client` fixture role to ADMIN and adding `viewer_client` for role-guard tests, (2) build a `CacheService` adapter wrapping the existing Redis client, (3) add cursor-paginated `CursorPage[T]` schema alongside existing offset/limit, (4) audit `list_*` repo methods for N+1 via explicit joins, (5) make pool settings environment-configurable.

## Architecture Decisions

### Decision: CacheService is a direct class, not a decorator

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Decorator-based `@cached(ttl=60)` | Clean on use-case layer, harder to test and compose | ⛔ Rejected |
| Service class with `get`/`set`/`invalidate` | Testable, injectable via DI, explicit at call site | ✅ **Chosen** |

**Rationale**: The codebase uses constructor-injected dependencies (`GetXCase` pattern). A class fits the existing DI flow.

### Decision: Cursor encoding uses base64(JSON) for opaque tokens

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Raw ID in cursor | Simple but exposes DB internals | ⛔ Rejected |
| Base64(JSON `{id, sort}`) | Opaque, handles mixed types (UUID, int), allows multi-column sort keys | ✅ **Chosen** |

**Rationale**: Spec requires opaque cursors. Base64-encoded JSON supports both UUID (animals, sales) and integer IDs without introducing a serialization framework.

### Decision: Keep offset/limit as deprecated, add cursor params alongside

The spec mandates backward compatibility. `StandardQueryParams` gains optional `cursor: str | None = None`. When `cursor` is provided, the endpoint uses cursor-based pagination; when `offset` is provided, it falls back to the legacy path with a deprecation warning.

### Decision: Pool settings read from env vars with current values as defaults

`DB_POOL_SIZE=10`, `DB_POOL_OVERFLOW=20`, `DB_POOL_RECYCLE=3600` in `Settings` class, passed to `create_async_engine`. This satisfies the spec's "overridable via environment variables" requirement without adding a config file.

## Data Flow

```
┌──────────────┐     get/set/invalidate     ┌──────────────┐     SELECT/INSERT    ┌──────────┐
│  Use Case    │ ──────────────────────────→ │  CacheService │ ──────────────────→ │ Postgres │
│  (domain)    │ ←────────────────────────── │  (adapter)    │ ←────────────────── │          │
└──────────────┘    cached or fresh data     └──────┬───────┘                    └──────────┘
                                                    │ JSON serialize/deserialize
                                                    ↓
                                             ┌──────────────┐
                                             │  Redis        │
                                             │  (existing)   │
                                             └──────────────┘

┌──────────────┐  cursor/limit params   ┌──────────────────┐  WHERE id > X     ┌──────────┐
│  HTTP Router  │ ──────────────────────→│  Use Case        │ ────────────────→ │ Repo     │
│  list_*()     │ ←──────────────────────│  (domain)        │ ←──────────────── │          │
└──────────────┘  CursorPage[T] response └──────────────────┘  scalar data      └──────────┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/common/infrastructure/adapters/cache_service.py` | Create | `ICacheService` port + `RedisCacheService` adapter with JSON serialization |
| `src/common/infrastructure/adapters/http/input/query_params.py` | Modify | Add `cursor: str | None` to `StandardQueryParams`; add `CursorPage[T]` generic schema |
| `src/common/infrastructure/core/_config.py` | Modify | Add `DB_POOL_SIZE`, `DB_POOL_OVERFLOW`, `DB_POOL_RECYCLE` env vars |
| `src/common/infrastructure/persistence/connections/db.py` | Modify | Read pool settings from `settings` instead of hardcoded values |
| `tests/integration/conftest.py` | Modify | Set `role=UserRole.ADMIN` on `client`; add `viewer_client` fixture with `role=VIEWER` |
| `tests/integration/*/test_role_guards.py` | Modify | Replace `client` → `viewer_client` in tests asserting VIEWER-gets-403 |
| `src/cattle/infrastructure/persistence/repositories/animal_repository.py` | Modify | Accept `cursor` param in `list_for_user`; N+1 fix if needed |
| `src/market/infrastructure/persistence/repositories/sales.py` | Modify | Accept `cursor` param; N+1 fix |
| `src/market/infrastructure/persistence/repositories/buyers.py` | Modify | Accept `cursor` param; N+1 fix |
| `src/finance/infrastructure/persistence/repositories/animal_supplies.py` | Modify | Accept `cursor` param; N+1 fix |
| `src/finance/infrastructure/persistence/repositories/purchases.py` | Modify | Accept `cursor` param; N+1 fix |
| `src/auth/infrastructure/persistence/repositories/user_repository.py` | Modify | Accept `cursor` param in `list()`; N+1 fix |
| `src/cattle/infrastructure/presentation/routers/_animals.py` | Modify | Pass cursor params from query to use case |
| `src/cattle/infrastructure/adapters/http/input/animal_schemas.py` | Modify | Inherit cursor field from `StandardQueryParams` |
| `src/billing/` | Review | N+1 audit on `list_expired_trials`, `list_by_tenant`, `list_all` |

## Interfaces / Contracts

```python
# CacheService port (src/common/domain/ports/)
class ICacheService(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def get_or_set(self, key: str, ttl: int, factory: Callable[[], Awaitable[Any]]) -> Any: ...

# CursorPage schema
class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    total: int
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | CacheService get/set/invalidate/ttl | Mock Redis, test each method with Pydantic models and plain dicts |
| Unit | CursorPage encode/decode | Test opaque roundtrip via base64 for UUID and int IDs |
| Unit | PaginationUtils.build_cursor/parse_cursor | Unit test with known input/output pairs |
| Integration | Fixture role alignment | Run all tests — expect 0 regressions (883 baseline) |
| Integration | Cursor-paginated endpoints | Migration test: cursor + limit returns correct next_cursor, items, total |
| E2E | Role guard fixtures | Each `*_client` correctly scoped (ADMIN write, VIEWER blocked) |

## Migration / Rollout

No data migration required. Cursor pagination keeps offset/limit as deprecated — clients transparently upgrade by switching to cursor params. Cache service is opt-in (no existing code uses it yet).

## Open Questions

- [ ] N+1 audit: confirm whether `buyers.list_for_user` iterates related `user` lazily (it selects `Buyer` columns only — may N+1 on `user_id` access per row)
- [ ] Cursor migration order: which 2 endpoints to migrate first as spec requires "two endpoints" as success criteria?
