# Design: Audit & Compliance (Phase 6)

## Technical Approach

Instrument every CUD operation across 11 repositories (~33 sites) with immutable audit logging. A new `AuditRepository` queues entries in-memory and flushes them via a UoW `before_commit` hook in the same transaction. Actor identity flows via explicit `current_user` injection into the UoW constructor. GDPR export/delete are application services that collect or anonymize user data across all bounded contexts.

## Architecture Decisions

### Decision: UoW Hook Interface

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `before_commit` callbacks | Simple FIFO, hook receives no args, failure → rollback | ✅ **Adopted** — matches spec R5 |
| `after_commit` callbacks | Added to port for future use, not used in Phase 6 | ✅ **Included in port** |
| Event emitter | Over-engineered for this phase | ❌ Rejected |

**Rationale**: Hooks are registered via `add_before_commit_hook(callable)`. The `commit()` method iterates hooks in FIFO order before `db.commit()`. If any hook raises, the exception propagates and `__aexit__` triggers rollback.

### Decision: Actor Threading (UoW Injection)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `contextvars` | Implicit, no endpoint changes, but testability suffers | ❌ Rejected |
| **UoW constructor** | Explicit, testable, avoids circular deps with adapter | ✅ **Adopted** — user choice |

**Rationale**: `current_user` is passed to `UnitOfWork(session, current_user=user)` via a new `GetAuditableUnitOfWork` dependency. The existing `GetUnitOfWork` (used in auth flows like `_get_current_user`) remains unchanged, avoiding circular resolution. `GetAuditableUnitOfWork = Annotated[IUoW, Depends(_get_auditable_uow)]` combines `GetSession` + `GetCurrentUser`.

### Decision: AuditRepository (Queue + Flush)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Direct INSERT per call | N+1 on multi-CUD use cases | ❌ Rejected |
| **Queue + bulk flush** | Batch INSERT via Core in before_commit hook | ✅ **Adopted** — spec R7 |

**Rationale**: Entries accumulate in-memory (`_queue: list[dict]`). `flush(connection)` executes a single `insert(audit_log_table).values(entries)` with Core DML — consistent with existing pattern (spec R10).

### Decision: Repository Instrumentation (Mixin)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **AuditableRepositoryMixin** | Reusable, 3 helpers (`_audit_create/update/delete`), 1 line per CUD site | ✅ **Adopted** |
| Override `execute()` in base | Too invasive, repos use direct Core, not ORM | ❌ Rejected |
| Manual per repo | 33 sites × 3 lines = code duplication | ❌ Rejected |

**Rationale**: Mixin provides `_audit_create`, `_audit_update`, `_audit_delete` that call `self._audit.record(...)`. The UoW injects `_audit` ref after repo construction. Each CUD method adds 1 line (or 2 for pre-update SELECT). 7 tenant-aware repos (animal, buyer, sale, purchase, supplies, events, protocols) + 2 non-tenant repos (user, tenant) need instrumentation.

### Decision: Pre-update SELECT

For `update()` and `delete()`, a SELECT-before captures old state. In practice, most `update()` calls already follow with `get_by_id()` to return the entity, so we SELECT once and pass the snapshot to both the audit record and the return value. Performance impact is negligible.

### Decision: Partitioning & Retention

Partition by RANGE on `created_at` with monthly partitions (audit_log_YYYY_MM). Retention purge drops partitions older than 180 days + 1-month grace. Partition creation: trigger function or pg_partman. Deferred to alembic migration design.

## Data Flow

```
┌─ Endpoint ──────────────────────────────────────────────────┐
│  POST /animals (current_user, data)                          │
│       │                                                      │
│       ▼                                                      │
│  UseCase.execute(data)                                       │
│       │                                                      │
│       ▼                                                      │
│  async with uow:      ◄── UnitOfWork(current_user)           │
│    repo = uow.get_repo(IAnimalsRepo)                         │
│    repo.create(data)   ── calls _audit_create('animal',...)  │
│    uow.commit()                                              │
│       │                                                      │
│       ▼                                                      │
│  UnitOfWork.commit():                                         │
│    1. Iterate _before_commit_hooks[FIFO]                     │
│    2. AuditRepository.flush(db) → INSERT INTO audit_log      │
│    3. db.commit()                                            │
│    4. Iterate _after_commit_hooks[FIFO]                      │
└──────────────────────────────────────────────────────────────┘
```

## Interfaces / Contracts

### IUoW Port (extended)

```python
@dataclass
class IUoW(ABC):
    bypass_filter: bool = False

    # Existing abstract methods unchanged...
    # Add these concrete defaults:
    
    def add_before_commit_hook(self, hook: Callable[[], Awaitable[None]]) -> None:
        raise NotImplementedError

    def add_after_commit_hook(self, hook: Callable[[], Awaitable[None]]) -> None:
        raise NotImplementedError
```

### AuditRepository Port

```python
class IAuditRepository(IRepository):
    async def record(
        action: str,           # "create" | "update" | "delete"
        entity_type: str,      # Table/entity name
        entity_id: UUID,
        old_values: dict | None,
        new_values: dict | None,
        metadata: dict | None = None,
        ip_address: str | None = None,
    ) -> None: ...

    async def flush(self, connection: AsyncConnection) -> None: ...
```

### AuditableRepositoryMixin

```python
class AuditableRepositoryMixin:
    _audit: IAuditRepository | None = None

    async def _audit_create(self, type_: str, id_: UUID, new: dict, meta: dict | None = None) -> None:
        if self._audit:
            await self._audit.record("create", type_, id_, None, new, meta)

    async def _audit_update(self, type_: str, id_: UUID, old: dict, new: dict, meta: dict | None = None) -> None:
        if self._audit:
            await self._audit.record("update", type_, id_, old, new, meta)

    async def _audit_delete(self, type_: str, id_: UUID, old: dict, meta: dict | None = None) -> None:
        if self._audit:
            await self._audit.record("delete", type_, id_, old, None, meta)
```

> **NOTE on `self._audit` injection**: The UoW's `get_repository()` sets `repo._audit = self._audit_queue` on repos that include `AuditableRepositoryMixin`. This is done by checking `isinstance(repo, AuditableRepositoryMixin)` after construction.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/common/infrastructure/persistence/models/_base.py` | Modify | Add `updated_at` column with `onupdate` |
| `src/common/application/ports/uow.py` | Modify | Add `add_before_commit_hook()`, `add_after_commit_hook()` to port |
| `src/common/infrastructure/persistence/uow.py` | Modify | Implement hooks, add `_audit_queue`, `current_user` param, hook iteration in `commit()` |
| `src/common/infrastructure/presentation/dependencies/uow.py` | Modify | Add `GetAuditableUnitOfWork` dependency |
| `src/common/infrastructure/persistence/repositories/mixins.py` | Modify | Add `AuditableRepositoryMixin` |
| `src/common/infrastructure/persistence/repositories/tenant_aware_repository.py` | Modify | Accept optional `uow` param in `__init__` |
| `src/common/domain/entities/_audit_log.py` | Create | `AuditLogEntry` domain entity |
| `src/common/infrastructure/persistence/models/_audit_log_model.py` | Create | `AuditLog` SQLAlchemy model (partitioned) |
| `src/common/domain/repositories/audit_repository_port.py` | Create | `IAuditRepository` port interface |
| `src/common/infrastructure/persistence/repositories/audit_repository.py` | Create | `AuditRepository` (queue + flush via Core) |
| `src/common/application/services/gdpr_export_service.py` | Create | GDPR export (collect user data across contexts) |
| `src/common/application/services/gdpr_delete_service.py` | Create | GDPR delete (anonymize + disable + revoke) |
| `src/common/infrastructure/tasks/retention_purge.py` | Create | Partition drop task (CLI/scheduler) |
| `src/common/infrastructure/presentation/routers/__init__.py` | Modify | Register gdpr routers |
| `src/common/infrastructure/presentation/routers/_gdpr.py` | Create | `GET /users/me/export`, `DELETE /users/me/data` |
| `alembic/versions/xxxx_add_audit_log.py` | Create | Migration: audit_log table + partitioning + updated_at |
| `src/cattle/infrastructure/persistence/repositories/animal_repository.py` | Modify | Instrument CUD with mixin (3 sites) |
| `src/cattle/infrastructure/persistence/repositories/animal_protocol_repository.py` | Modify | Instrument CUD (3 sites) |
| `src/cattle/infrastructure/persistence/repositories/schedule_event_repository.py` | Modify | Instrument CUD (3 sites) |
| `src/finance/infrastructure/persistence/repositories/purchases.py` | Modify | Instrument CUD (3 sites) |
| `src/finance/infrastructure/persistence/repositories/animal_supplies.py` | Modify | Instrument CUD (3 sites) |
| `src/market/infrastructure/persistence/repositories/sales.py` | Modify | Instrument CUD (3 sites) |
| `src/market/infrastructure/persistence/repositories/buyers.py` | Modify | Instrument CUD (3 sites) |
| `src/auth/infrastructure/persistence/repositories/user_repository.py` | Modify | Instrument CUD (4 sites: create, update_data, update_password, update_role) |
| `src/auth/infrastructure/persistence/repositories/refresh_token_repository.py` | Modify | Instrument CUD (3 sites: save, revoke_token, revoke_all_user_tokens) |
| `src/auth/infrastructure/persistence/repositories/tenant_repository.py` | Modify | Instrument CUD (1 site: create) |

## Migration / Rollout

**Migration order** (single Alembic revision):
1. Create `audit_log` table with RANGE partitioning template
2. Create partitions for current month + next 12 months
3. Add `updated_at` column to all model tables with `DEFAULT NULL` initially
4. Backfill `updated_at = created_at` for existing rows
5. Make `updated_at` NOT NULL after backfill
6. Create indexes + FK constraints

**Rollback**: Alembic downgrade drops `audit_log` table + `updated_at` columns.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | AuditRepository queue logic, before_commit hook ordering, GDPR service edge cases | Mock UoW, assert queue state before/after flush |
| Unit | Mixin helper methods (`_audit_create/update/delete`) | Unit test with mock `_audit` |
| Integration | Full audit flow: create → verify audit_log row exists with correct values | Test DB, run CUD, SELECT audit_log |
| Integration | Partition routing: insert across months, verify partition affinity | Test DB with date manipulation |
| Integration | GDPR export: create user with data, call export, assert complete JSON | Test DB, compare returned fields |
| Integration | GDPR delete: anonymize, verify PII is replaced, verify user disabled | Test DB, verify all affected tables |
| E2E | API: POST /animals → verify audit entry created with correct actor | Full API test with auth token |
| E2E | API: GET /users/me/export → verify 200 + JSON body | Full API test |
| E2E | Retention: create partitions, call purge, verify old partition dropped | Full DB + task integration |

## Open Questions

- [ ] Partition creation strategy: `pg_partman` extension or app-level cron/scheduler? (Deferred to task)
- [ ] Do `animal_protocol_repository` and `schedule_event_repository` need the `AuditableRepositoryMixin` or are they read-only? (Check domain)
