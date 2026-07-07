# Tasks: Audit & Compliance (Phase 6)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~750–1,100 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Audit table + UoW hooks + AuditRepository | PR 1 | Base: `feature/audit-and-compliance`. ~250 lines, 7 files |
| 2 | Mixin + instrument all 11 repositories | PR 2 | Base: PR 1 branch. ~200–350 lines, 13 files |
| 3 | GDPR export/delete services + endpoints | PR 3 | Base: feature branch. ~200 lines, 4 files |
| 4 | Retention purge task | PR 4 | Base: feature branch. ~100 lines, 2 files |

## Phase 1: Foundation — Audit Infrastructure

- [x] 1.1 Create `AuditLogEntry` domain entity — `src/common/domain/entities/_audit_log_entry.py`
- [x] 1.2 Create `AuditLog` SQLAlchemy model (partitioned) — `src/common/infrastructure/persistence/models/_audit_log_model.py`
- [x] 1.3 Create Alembic migration — `audit_log` table + monthly partitions + indexes
- [x] 1.4 Extend `IUoW` port — add `add_before_commit_hook()`, `current_user` field, `audit_repository` field
- [x] 1.5 Extend `UnitOfWork` — implement hook queue, execute FIFO before commit, rollback on failure
- [x] 1.6 Create `IAuditRepository` port — `src/common/domain/repositories/audit_repository_port.py`
- [x] 1.7 Create `AuditRepository` impl — queue + bulk flush via Core — `src/common/infrastructure/persistence/repositories/audit_repository.py`
- [x] 1.8 Wire `AuditRepository` into UoW — register repo, flush in commit sequence
- [x] 1.9 Add `GetAuditableUnitOfWork` dependency — `src/common/infrastructure/presentation/dependencies/auditable_uow.py` (deferred to PR 2)
- [x] 1.10 Tests: UoW hook ordering, rollback on failure, AuditRepository queue+flush

## Phase 2: Instrumentation — Mixin + All Repositories

- [x] 2.1 Add `updated_at` to `Model` base — `src/common/infrastructure/persistence/models/_base.py`
- [x] 2.2 Create `AuditableRepositoryMixin` — `src/common/infrastructure/persistence/repositories/_auditable_mixin.py`
- [x] 2.3 Instrument `AnimalRepository` (3 CUD sites)
- [x] 2.4 Instrument `AnimalProtocolsRepository` (3 CUD sites)
- [x] 2.5 Instrument `AnimalTypeRepository` (2 CUD sites)
- [x] 2.6 Instrument `ScheduleEventRepository` (3 CUD sites)
- [x] 2.7 Instrument `AnimalSuppliesRepository` (3 CUD sites)
- [x] 2.8 Instrument `PurchasesRepository` (3 CUD sites)
- [x] 2.9 Instrument `BuyersRepository` (3 CUD sites)
- [x] 2.10 Instrument `SalesRepository` (3 CUD sites)
- [x] 2.11 Instrument `UserRepository` (4 CUD sites)
- [x] 2.12 Instrument `TenantRepository` (1 CUD site)
- [x] 2.13 Instrument `RefreshTokenRepository` (3 CUD sites)
- [x] 2.14 Migration: add `updated_at` to all tables + backfill
- [x] 2.15 Tests: audit entries created for each mutation type across contexts

## Phase 3: GDPR Services & Endpoints

- [x] 3.1 Create `GDPRExportService` — `src/common/application/services/gdpr_export_service.py`
- [x] 3.2 Create `GDPRDeleteService` — `src/common/application/services/gdpr_delete_service.py`
- [x] 3.3 Add GDPR router — `GET /users/me/export`, `DELETE /users/me/data`
- [x] 3.4 Create request/response schemas for GDPR endpoints
- [x] 3.5 Register GDPR router in auth router
- [x] 3.6 Tests: GDPR export returns correct data shape, delete anonymizes correctly

## Phase 4: Data Retention

- [x] 4.0 Migration: add `is_active` to users table — `alembic/versions/4d5e6f7a8b9c_add_is_active_to_users.py`
- [x] 4.1 Create retention purge task — `src/common/infrastructure/tasks/retention_purge.py`
- [x] 4.2 Add `AUDIT_RETENTION_DAYS=180` env var — `src/common/infrastructure/core/_config.py`
- [x] 4.3 CLI command or scheduler to DROP old partitions — `python -m src.common.infrastructure.tasks.retention_purge --days 180`
- [x] 4.4 Tests: purge drops correct partitions, respects env var override — `tests/unit/common/test_retention_purge.py` (7 tests)
