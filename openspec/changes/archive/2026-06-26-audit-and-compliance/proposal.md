# Proposal: Audit & Compliance (Phase 6)

## Intent

Multi-tenant SaaS (Phase 3) and RBAC (Phase 4) are in production with zero auditability. When a user creates, updates, or deletes a record, no one can answer who did what. For a system handling livestock, finance, and PII, this is a compliance and operational liability. We need immutable audit trails, data retention, and GDPR readiness before (a) regulatory scrutiny, (b) customer data requests, or (c) incident investigation demands them.

## Business Value

- **SaaS trust**: tenants expect traceability in a multi-tenant system
- **GDPR readiness**: export/delete rights require PII inventory and data operations
- **Operational debugging**: answer "who changed this animal's status and when"
- **Security audit**: detect unauthorized or abnormal mutation patterns

## Current State

- No `audit_log` table exists
- No `updated_at` timestamp on any model (only `created_at` on `Model` base)
- Only `TenantEntity` has `updated_at` at the domain level
- Repositories use raw `insert()`, `update()`, `delete()` DML — no SQLAlchemy ORM tracking
- UoW has no before-commit hooks
- No PII inventory, no data retention policy, no export/delete capabilities
- ~11 repository classes × 3 CUD operations ≈ 33 mutation sites across 4 bounded contexts

## Scope

### In Scope
- **Audit log table**: `audit_log` with JSONB `old_values`, `new_values`, actor context, table name, operation type, timestamp
- **UoW audit hook**: before-commit hook that flushes accumulated audit entries in the same transaction
- **Audit-aware repositories**: each CUD method records audit entries via the UoW (with old-value capture for updates/deletes)
- **`updated_at` on all models**: add column to SQLAlchemy `Model` base, auto-set on commit
- **Data retention**: configurable TTL (default 12 months), monthly table partitioning on `created_at`
- **GDPR Export service**: collects all data for a user (auth, cattle, finance, market records) as a JSON blob
- **GDPR Delete service**: anonymizes user's PII in business records (name → "Anonymized", dni → null, email → hashed), cascade-deletes non-business records
- **PII Inventory**: users (name, dni, email), buyers (name, contact_number, contact_address)

### Out of Scope
- Domain events or event sourcing (deferred)
- Soft-delete (archive tables instead)
- Audit log viewer UI (API endpoints only for Phase 6)
- Real-time alerts / anomaly detection
- Data encryption at rest (infra concern)

## Capabilities

### New Capabilities
- `audit-log`: immutable mutation trail with actor, entity, old/new values
- `gdpr-compliance`: data export and anonymization endpoints for user rights
- `data-retention`: configurable TTL with automated partition management

### Modified Capabilities
- None — no existing spec changes at this level (rbac/auth specs are unaffected)

## Approach

**SQL audit table + UoW commit hook**:
1. Add `audit_log` table with columns: `id`, `tenant_id`, `actor_id`, `table_name`, `operation` (CREATE/UPDATE/DELETE), `entity_id`, `old_values` (JSONB), `new_values` (JSONB), `created_at`
2. Extend `UnitOfWork` with an `audit` property — a list/queue of pending entries — and a `_flush_audit()` method called before `commit()`
3. Pass UoW reference to all repositories so CUD methods can call `self.uow.audit.record(...)` after executing DML, capturing old values before updates/deletes
4. Add `updated_at` to `Model` base as `DateTime(timezone=True)`, auto-set in a `before_flush` listener
5. Use Alembic for migration: create `audit_log` table, add `updated_at` to all existing tables, set up partitioning template
6. GDPR: application service `GdprService` with `export_user_data(user_id)` → collects across all bounded contexts, and `anonymize_user(user_id)` → replaces PII fields in `users` + `buyers` tables

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `common/infrastructure/persistence/models/_base.py` | Modified | Add `updated_at` column |
| `common/infrastructure/persistence/uow.py` | Modified | Add audit queue + before-commit flush |
| `common/domain/ports/` | New | Add audit record port interface |
| `common/infrastructure/persistence/audit_log.py` | New | Audit SQLAlchemy model |
| `common/application/services/gdpr_service.py` | New | GDPR export/delete service |
| All repository files (11 repos) | Modified | Add audit recording to CUD methods |
| `alembic/versions/` | New | Migration for audit_log + updated_at + partitioning |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Audit I/O impacts write throughput | Medium | Async writes in same transaction; partition pruning for queries |
| old_values capture for updates requires SELECT-before-UPDATE (double query) | Medium | Cache in repo method; acceptable for ~33 mutation sites |
| GDPR anonymization leaves orphaned references | Low | Cascade FK rules; business records keep anonymized user reference |
| Partition management adds ops complexity | Low | Use pg_partman or cron job + monitoring alert before partition boundaries |

## Rollback Plan

1. **Down-migration**: Alembic downgrade drops `audit_log` table and `updated_at` columns
2. **Code revert**: Revert UoW changes; repos fall back to current CUD-only behavior
3. **Partitions**: Drop partition tables, revert to unpartitioned `audit_log` (or drop entirely)
4. No production data is lost — audit entries are non-essential for core business operations

## Dependencies

- PostgreSQL 14+ (JSONB support, native partitioning)
- Alembic for migration management
- `pg_partman` or custom cron for partition management (deferred decision)

## Success Criteria

- [ ] Every CUD operation across all 4 bounded contexts produces an immutable `audit_log` row
- [ ] `updated_at` auto-populates on every model insert and update
- [ ] GDPR export endpoint returns complete JSON dump for a given user
- [ ] GDPR anonymization replaces PII in `users` + `buyers` tables without breaking FK references
- [ ] Retention policy purges partitions older than configured TTL (tested)
- [ ] All existing tests pass without modification

## Proposal Question Round

Before finalizing, these product assumptions need your review:

1. **Audit granularity**: Capture all columns in old/new JSONB, or only changed columns? Full-snapshot is simpler but bloats storage.
2. **Actor threading**: Use `contextvars` (implicit, no code changes per endpoint) or UoW injection (explicit, but guaranteed correct)?
3. **Retention default**: 12 months seems right for a livestock SaaS — or do you need longer for tax/fiscal compliance?
4. **GDPR export format**: JSON blob returned via API endpoint, or do you want async email delivery (e.g., background job)?
5. **Partition ownership**: App-level partition management (cron/scheduler inside the app) or infra-level (`pg_partman` extension)?

Want to adjust any of these, skip them, or run a second round?

