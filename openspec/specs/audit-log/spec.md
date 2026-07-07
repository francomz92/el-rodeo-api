# Audit Log Specification

## Purpose

Immutable mutation trail recording actor, entity, old/new values across all bounded contexts. Provides operational traceability and compliance evidence for who changed what and when.

## Requirements

### R1: Audit Log Table

The system MUST maintain an `audit_log` table with schema: `id UUID PK`, `tenant_id UUID FK`, `user_id UUID` (nullable — system operations), `action VARCHAR(20)` (create/update/delete), `entity_type VARCHAR(50)`, `entity_id UUID`, `old_values JSONB`, `new_values JSONB`, `ip_address VARCHAR(45)`, `metadata JSONB`, `created_at TIMESTAMPTZ DEFAULT now()`.

#### Scenario: Record creation logged

- GIVEN a user creates an entity
- WHEN the repository create method executes
- THEN an `audit_log` row is inserted with `action='create'`, `old_values=null`, `new_values=<full entity snapshot>`

#### Scenario: Record update with diff

- GIVEN a user updates an entity
- WHEN the repository update method executes
- THEN old_values captures the entity BEFORE the mutation (SELECT-before-UPDATE)
- AND new_values captures the entity AFTER

#### Scenario: Record deletion with snapshot

- GIVEN a user deletes an entity
- WHEN the repository delete method executes
- THEN old_values captures the full entity BEFORE deletion
- AND new_values=null

#### Scenario: Anonymous system operation

- GIVEN a system-internal mutation (no authenticated user)
- WHEN the operation is recorded
- THEN `user_id` IS NULL

### R2: Partitioning by Month

The `audit_log` table MUST be range-partitioned by month on `created_at` using PostgreSQL declarative partitioning.

#### Scenario: Insert routes to correct partition

- GIVEN an audit entry with `created_at='2026-06-15'`
- WHEN the INSERT executes
- THEN the row is stored in partition `audit_log_2026_06`

#### Scenario: Partition pruning on queries

- GIVEN a date-filtered query
- WHEN the planner executes
- THEN only relevant partitions are scanned

### R3: Indexes

The system MUST create indexes on `(tenant_id, entity_type, entity_id)`, `(tenant_id, created_at DESC)`, and `(user_id)`.

### R4: RLS Tenant Isolation

The system MUST enforce tenant-scoped reads on `audit_log` via RLS policy.

#### Scenario: Cross-tenant read isolation

- GIVEN tenant A queries audit logs
- WHEN the query executes
- THEN only rows with tenant A's tenant_id are returned

### R5: UoW Before-Commit Hook System

The IUoW interface MUST support `add_before_commit_hook(callable)` that registers hooks executed in FIFO order before `commit()`.

#### Scenario: FIFO execution

- GIVEN two hooks registered sequentially
- WHEN `commit()` is called
- THEN hook 1 executes before hook 2

#### Scenario: Hook failure aborts transaction

- GIVEN a hook that raises an exception
- WHEN `commit()` executes it
- THEN the transaction is rolled back and the exception propagates

#### Scenario: After-commit hook registration

- GIVEN `add_after_commit_hook(callable)` on IUoW
- WHEN `commit()` succeeds
- THEN after-commit hooks execute after commit (for future use)

### R6: UoW Actor Injection

The UoW MUST accept `current_user: UserEntity | None` at construction as an explicit parameter.

#### Scenario: Actor recorded in audit

- GIVEN a UoW constructed with `current_user=<UserEntity>`
- WHEN an audit entry is flushed
- THEN `user_id` in `audit_log` matches `current_user.id`

#### Scenario: No actor for system ops

- GIVEN a UoW constructed with `current_user=None`
- WHEN an audit entry is flushed
- THEN `user_id` IS NULL

### R7: AuditRepository

The system MUST provide an `AuditRepository` with `record(action, entity_type, entity_id, old_values, new_values, metadata=None)`.

#### Scenario: In-memory accumulation

- GIVEN multiple `record()` calls
- WHEN no flush has occurred
- THEN entries are held in memory (not persisted)

#### Scenario: Batch flush on commit

- GIVEN accumulated audit entries
- WHEN the before-commit hook calls `flush()`
- THEN all entries are INSERTed via raw SQLAlchemy Core in a single batch

### R8: Updated-at on Base Model

The `Model` base class MUST include `updated_at: Mapped[datetime]` with `onupdate=func.now()` and a server default of `created_at` for existing rows.

#### Scenario: Auto-set on update

- GIVEN an existing row
- WHEN an UPDATE executes
- THEN `updated_at` is set to current timestamp

#### Scenario: Migration for existing tables

- GIVEN all models inherit from `Model`
- WHEN the migration adds `updated_at` to base
- THEN ALTER TABLE ADD COLUMN with DEFAULT `created_at` is applied to every table

### R9: Repository Instrumentation

Every repository CUD method MUST record audit entries via the UoW's AuditRepository. All ~33 mutation sites across 11 repositories must be instrumented.

#### Scenario: Create instrumentation

- GIVEN a repository `create(data)` call
- WHEN it succeeds
- THEN `audit.record('create', entity_type, entity_id, None, new_values)` is called

#### Scenario: Update with before/after capture

- GIVEN a repository `update(id, data)` call
- THEN a SELECT-before captures the entity
- AND `audit.record('update', entity_type, entity_id, old_values, new_values)` is called
- AND `updated_at` is explicitly set in the UPDATE

#### Scenario: Delete with snapshot

- GIVEN a repository `delete(id)` call
- THEN a SELECT-before captures the entity
- AND `audit.record('delete', entity_type, entity_id, entity_snapshot, None)` is called

#### Scenario: Specialized mutations

- GIVEN an `update_status(id, status)` or `increase_stock(id, amount)` call
- THEN old_values capture the full entity before mutation
- AND new_values capture the entity after mutation (with changed fields)

### R10: Raw SQLAlchemy Core

All audit inserts MUST use raw SQLAlchemy Core DML (not ORM), consistent with the existing repository pattern.

### Constraints

- Audit table is APPEND-ONLY — no UPDATE or DELETE on audit rows
- All 33 mutation sites MUST be instrumented before this spec is complete
- Each audit entry shares the same DB transaction as the CUD operation
- UoW hook execution and audit flush happen in the SAME transaction boundary
