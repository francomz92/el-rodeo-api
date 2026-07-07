# Tasks: Phase 9a — Polish & Scale Foundation

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~560 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: Fixtures → PR 2: Cache → PR 3: Cursor → PR 4: N+1 → PR 5: Pool |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Fix fixture roles + `viewer_client` | PR 1 | base=main; fixes 41 failing tests |
| 2 | ICacheService + RedisCacheService | PR 2 | base=main; independent abstraction |
| 3 | CursorPage[T] + migrate 2 endpoints | PR 3 | base=main; query_params, repos, routers |
| 4 | N+1 audit + fixes | PR 4 | base=main; review all `list_*` methods |
| 5 | Pool env vars + docs | PR 5 | base=main; tiny (~20 lines) |

## Phase 1: Fixtures Fix

- [x] 1.1 Add `role=UserRole.ADMIN` to `client` fixture in `tests/integration/conftest.py`
- [x] 1.2 Add `viewer_client` fixture with `role=UserRole.VIEWER` in `tests/integration/conftest.py`
- [x] 1.3 Replace `client` → `viewer_client` in role-guard 403 assertions (cattle, market, finance `test_role_guards.py`)
- [x] 1.4 Verify: run all 936 tests, expect 0 failures — 936 collected, 0 failed (188 integration + 736 unit + 12 skipped)

## Phase 2: Cache Service

- [x] 2.1 Create `ports/` dir and `ICacheService` protocol in `src/common/domain/ports/cache_service.py`
- [x] 2.2 Create `RedisCacheService` in `src/common/infrastructure/adapters/cache_service.py`
- [x] 2.3 Unit: cache hit/miss, TTL, invalidation by key + pattern, JSON serialization

## Phase 3: Cursor Pagination

- [x] 3.1 Add `cursor: str | None` to `StandardQueryParams` in `query_params.py`; deprecation warning on offset
- [x] 3.2 Create `CursorPage[T]` schema + base64(JSON) encode/decode helpers
- [x] 3.3 Add cursor WHERE helpers in `cattle/animal_repository.py` and `auth/user_repository.py`
- [x] 3.4 Migrate `GET /cattle/animals` and `GET /auth/users` schemas/routers to accept cursor params
- [x] 3.5 Integration: cursor page returns correct items/next_cursor/total; old offset/limit still works

## Phase 4: N+1 Audit

- [x] 4.1 Audit `list_*` methods: animal, animal_supplies, purchases, sales, buyers, user, billing repositories
- [x] 4.2 Add `selectinload`/`joinedload` where lazy loads detected; run all tests (0 regressions)
- [x] 4.3 Produce audit report listing each method's status (clean / fixed)

### N+1 Audit Report

**Audit Date**: 2026-07-03 (PR 4 of 5 — `phase-9a-foundation`)

**Methodology**: For each repository, reviewed:
- Query construction: does it use Core-style column projection (`*__table__.columns` or explicit columns) with `.mappings()` (returning `RowMapping` dicts, not ORM model instances)?
- ORM relationship access: does the returned entity access lazy `relationship()` attributes after the query?
- Join coverage: does the query explicitly join and project related table columns that the domain entity consumes?

**Key Finding**: ALL repositories use SQLAlchemy **Core-style** patterns — they select specific columns (never ORM model instances), use `.mappings().all()` to get `RowMapping` dicts, and build domain entities from those dicts. This pattern **never triggers lazy loading** regardless of `relationship()` definitions on models.

| Repository | File | Methods | Status | Notes |
|------------|------|---------|--------|-------|
| **Animal** | `animal_repository.py` | `list_for_user()` | **CLEAN** | Already uses `outerjoin(AnimalType)` + column projection. No fix needed. |
| **Animal Supplies** | `animal_supplies.py` | `list_for_user()` | **CLEAN** | Already uses `outerjoin(AnimalSupplyType)` + column projection. No fix needed. |
| **Purchases** | `purchases.py` | `list_for_user()` | **CLEAN** | Already uses `outerjoin(User)` + `outerjoin(AnimalSupply)` with column projections. No fix needed. |
| **Sales** | `sales.py` | `list_for_user()` | **CLEAN** | Already uses `outerjoin(Buyer)` + `outerjoin(Animal)` + `outerjoin(AnimalType)` with full column projections. No fix needed. |
| **Buyers** | `buyers.py` | `list_for_user()` | **CLEAN** | Uses Core-style column selection (`*Buyer.__table__.columns`). Model has `user` relationship but domain entity `BuyerEntity` has only scalar fields — no lazy access occurs. No fix needed. |
| **User** | `user_repository.py` | `list()` | **CLEAN** | Uses Core-style column selection. No relationships to cause N+1 in list context. No fix needed. |
| **Billing — Subscription** | `_subscription_repository.py` | `list_expired_trials()`, `list_active_near_period_end()` | **CLEAN** | Selects explicit scalar columns. No relationships. No fix needed. |
| **Billing — Payment** | `_payment_repository.py` | `list_by_tenant()` | **CLEAN** | Selects explicit scalar columns. No relationships. No fix needed. |
| **Billing — Plan** | `_plan_repository.py` | `list_all()` | **CLEAN** | In-memory seed data (no DB query). No fix needed. |
| **Tenant** | `tenant_repository.py` | `list_all()` | **CLEAN** | Selects scalar columns. `TenantEntity` has only scalar fields. No fix needed. |
| **Schedule Event** | `schedule_event_repository.py` | `list_for_user()` | **CLEAN** | Core-style selection. Model has `user` relationship but entity `ScheduleEventEntity` has scalar fields only. No fix needed. |
| **Animal Protocol** | `animal_protocol_repository.py` | `list_for_user()` | **CLEAN** | Already uses `outerjoin(Animal)` + `outerjoin(AnimalType)` with full column projections. No fix needed. |
| **Animal Type** | `animal_type_repository.py` | `list()` | **CLEAN** | Selects scalar columns. No relationships to cause N+1. No fix needed. |
| **Refresh Token** | `refresh_token_repository.py` | _(no list method)_ | **N/A** | No `list_*` method exists. No fix needed. |
| **Audit** | `audit_repository.py` | _(no list method)_ | **N/A** | In-memory queue, not a DB query repository. No fix needed. |

**Summary**: **0 repositories fixed, 13 repositories clean, 2 N/A. No `selectinload`/`joinedload` additions required.** The project's existing Core-style query pattern with explicit joins for related data effectively prevents N+1 queries by design.

**Test Suite**: 964 passed, 12 skipped — 0 regressions confirmed.

## Phase 5: Pool Tuning & Docs

- [x] 5.1 Add `DB_POOL_SIZE`, `DB_POOL_OVERFLOW`, `DB_POOL_RECYCLE` to `Settings` in `_config.py`
- [x] 5.2 Wire env vars into `create_async_engine` call in `db.py`
- [x] 5.3 Document rationale for defaults with inline comment in `db.py`
