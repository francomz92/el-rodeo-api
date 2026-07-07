## Exploration: is_admin Column Cleanup Scope

### Current State

RBAC Phase 4 is complete. The `is_admin` boolean column on `users` was kept orthogonal to the new `UserRole` enum (VIEWER < EDITOR < ADMIN < OWNER) during the transition. Now it must be removed.

The `is_admin` field currently serves ONLY ONE production-critical function: **enabling cross-tenant super-admin access** via the `bypass_filter` mechanism in `TenantAwareRepository`. All route-level authorization has already been migrated to `require_role()`.

---

### Complete Inventory

#### Source Files (6 files, 8 references)

| # | File | Line(s) | Usage |
|---|------|---------|-------|
| 1 | `src/auth/domain/entities/_user_entity.py` | 16 | **Field**: `is_admin: bool` — UserEntity dataclass field |
| 2 | `src/auth/infrastructure/persistence/models/_user_models.py` | 19 | **Column**: `is_admin: Mapped[bool] = mapped_column(Boolean, default=False)` — DB column |
| 3 | `src/auth/infrastructure/persistence/repositories/user_repository.py` | 91 | **Mapping**: `is_admin=user_db["is_admin"]` — builds UserEntity from DB row |
| 4 | `src/auth/application/services/authentication_service.py` | 37 | **Logic**: `_uow.bypass_filter = user.is_admin` — activates cross-tenant access |
| 5 | `src/auth/application/services/authentication_service.py` | 41 | **Logic**: `if not user.is_admin:` — `validate_admin_user()` (DEAD CODE — see below) |
| 6 | `src/auth/infrastructure/adapters/http/output/role_schemas.py` | 17 | **Schema**: `is_admin: bool` — `UserRoleResponseSchema` Pydantic model |
| 7 | `src/auth/infrastructure/presentation/routers/_role_routers.py` | 60 | **Response**: `is_admin=updated_user.is_admin` — populates response schema |
| 8 | `src/auth/infrastructure/presentation/dependencies/auth_dependencies.py` | 182 | **Alias**: `is_admin_user = Depends(_get_current_admin_user)` — UNUSED by any route |

#### Test Files (10 files, ~50 references)

| # | File | Ref Count | Natur of Usage |
|---|------|-----------|----------------|
| 1 | `tests/factories.py` | 1 | `is_admin=False` default in `make_user_entity()` |
| 2 | `tests/integration/conftest.py` | 8 | `is_admin=False`/`True` in DB seed rows + `UserEntity(...)` objects for 6 client fixtures |
| 3 | `tests/unit/auth/test_bypass_filter.py` | 8 | Tests that `bypass_filter` activates based on `is_admin` |
| 4 | `tests/unit/auth/test_user_entity.py` | 10 | Tests that `role` and `is_admin` are independent fields |
| 5 | `tests/unit/auth/test_user_entity_tenant.py` | 3 | `is_admin=False` in constructor |
| 6 | `tests/unit/auth/test_user_repository.py` | 3 | `_build_user` test with `is_admin=True/False` in mock row |
| 7 | `tests/integration/cattle/test_role_guards.py` | 3 | `is_admin=False` in DB seed rows |
| 8 | `tests/integration/finance/test_role_guards.py` | 3 | `is_admin=False` in DB seed rows |
| 9 | `tests/integration/market/test_role_guards.py` | 3 | `is_admin=False` in DB seed rows |
| 10 | `tests/integration/auth/test_role_assignment.py` | 3 | `is_admin=False` in seed rows and `_entity()` builder |

#### Migration Files (1 file, 3 references)

| File | Lines | Usage |
|------|-------|-------|
| `alembic/versions/a54adbe62ca3_add_user_role_column.py` | 30-32 | Backfill queries: `UPDATE users SET role = 'admin' WHERE is_admin = TRUE` (and inverse) |

> **Note**: The current migration does NOT drop the `is_admin` column. A NEW migration is needed to remove it.

#### Docs/Specs (openspec/)

| File | Ref Count | Notes |
|------|-----------|-------|
| `openspec/specs/auth/rbac.md` | ~14 | Describes dual-read contract — needs update |
| `openspec/changes/archive/2026-06-24-rbac-phase4/*.md` | ~40 | Archived artifacts — no changes needed |

---

### bypass_filter Flow

**Production flow** (only active code path):

```
UserEntity.is_admin  (from DB column via repository mapping)
        │
        ▼
AuthService.get_authenticated_user()
  → _uow.bypass_filter = user.is_admin          [auth:37]
        │
        ▼
UnitOfWork.get_repository(repo_type)
  → if issubclass(repo, TenantAwareRepository):
      repo(session, tenant_id, bypass_filter=self.bypass_filter)  [uow.py:24]
        │
        ▼
TenantAwareRepository._filter_tenant(stmt)
  → if self._bypass: return stmt  (skips WHERE tenant_id = X)    [tenant_aware_repo:45]
  → else: return stmt.where(model.tenant_id == self._tenant_id)
```

**Test override flow** (dependency override for integration tests):

```python
admin_client fixture  [conftest.py:441-471]:
  → uow.bypass_filter = True  (set manually in the override function)
  → bypasses tenant filter, allowing cross-tenant reads
```

**Supporting infrastructure**:
- `IUoW.bypass_filter: bool = False` — abstract port (default False)
- `UnitOfWork.bypass_filter = False` — init in `__init__`
- `MockUoW.bypass_filter = False` — init in `__init__` (tests/mocks.py)
- `TenantAwareRepository.__init__` accepts `bypass_filter` kwarg
- 3 unit tests in `test_tenant_aware_repository.py` cover bypass mode
- 3 unit tests in `test_uow_tenant.py` cover bypass propagation
- 3 unit tests in `test_bypass_filter.py` cover is_admin → bypass activation

---

### Dead Code Discovered

Two paths are **DEAD CODE** — they exist but no production route uses them:

1. **`AuthService.validate_admin_user()`** (authentication_service.py:40-42) — only called by `_get_current_admin_user`

2. **`_get_current_admin_user`** (auth_dependencies.py:126-132) / `is_admin_user` alias (line 182) — NOT imported by any router in `src/`. The commented-out `GetCurrentAdminUser` (line 189) confirms the intent to remove.

3. **Test comment** in `test_auth_api.py:5` references `is_admin_user` but the actual `/auth/register` route now uses `require_role(UserRole.ADMIN)`.

These can be removed as part of this cleanup.

---

### Impact Analysis

#### What breaks if is_admin is removed WITHOUT a replacement:

| Area | Breaks? | Severity | Details |
|------|---------|----------|---------|
| bypass_filter mechanism | **YES** | 🔴 Critical | `bypass_filter = user.is_admin` would fail. `UserEntity` no longer has `is_admin`. Super-admins lose cross-tenant access. |
| validate_admin_user() | **YES** | 🟡 Harmless | Dead code — no route uses it. But would crash if ever called. |
| _get_current_admin_user / is_admin_user | **YES** | 🟡 Harmless | Dead code — no route uses these. |
| UserRoleResponseSchema | **YES** | 🟡 Low | Response schema field would be missing. API clients reading `is_admin` would get `None` or error. |
| _role_routers.py response | **YES** | 🟡 Low | Would break when building response if `updated_user.is_admin` no longer exists. |
| All test fixtures | **YES** | 🟡 High | ~50 references across 10 test files would fail at import/construction time. |

#### bypass_filter Dependency Chain (Critical Path)

The ONLY critical production impact is the `bypass_filter` chain. Without a replacement, cross-tenant super-admin access is lost entirely. The dead code paths can be cleanly removed with no production impact.

---

### Proposed Approaches for bypass_filter Replacement

#### Option A: Add `SUPER_ADMIN` role (rank 5) — **RECOMMENDED**

Extend `UserRole` with a new `SUPER_ADMIN = "super_admin"` at rank 5, above OWNER.

| Step | Change |
|------|--------|
| Enum | `UserRole.SUPER_ADMIN = "super_admin"` with `rank = 5` |
| Migration | `is_admin=True` → `role='super_admin'` (with backfill edge case logic) |
| Migration | Drop `is_admin` column |
| Entity | Remove `is_admin` field from `UserEntity` |
| Model | Remove `is_admin` column from `User` model |
| Repo | Remove `is_admin=user_db["is_admin"]` from `_build_user()` |
| AuthService | `bypass_filter = (user.role == UserRole.SUPER_ADMIN)` |
| Response schema | Remove `is_admin` from `UserRoleResponseSchema` |
| Route | Remove `is_admin=updated_user.is_admin` from `_role_routers.py` |
| Dead code | Remove `validate_admin_user()`, `_get_current_admin_user`, `is_admin_user` alias |

**Pros**:
- Clear semantic: OWNER owns a tenant, SUPER_ADMIN owns the platform
- Extends existing role hierarchy cleanly
- No need for separate configuration system
- Self-documenting in the database
- CHECK constraint already extensible

**Cons**:
- Adds a new role concept mid-stream
- Migration edge case: what if a user is both `is_admin=True` AND `role=ADMIN/OWNER`? Need precedence rules.

**Effort**: Medium (7 source files, 10 test files, 1 migration)

#### Option B: Config-based super-admin IDs

Store super-admin user IDs in `settings.py` or env var (e.g., `SUPER_ADMIN_IDS`).

```python
# settings.py
SUPER_ADMIN_IDS: list[str] = []  # env: "uuid1,uuid2"

# authentication_service.py
_uow.bypass_filter = str(user.id) in settings.SUPER_ADMIN_IDS
```

**Pros**:
- No DB changes needed for the bypass logic itself
- Super-admin access controlled outside the data layer (more secure)
- Easy to audit who has super-admin access

**Cons**:
- Adds configuration management overhead
- Doesn't remove the need to remove `is_admin` column from DB anyway
- No SQL-level visibility of super-admin status
- Less discoverable than a DB column

**Effort**: Medium (still need to remove is_admin column + field, 6 source files, 10 test files, 1 migration)

#### Option C: Remove bypass_filter entirely

Remove cross-tenant super-admin capability. `_filter_tenant` always applies.

**Pros**:
- Simplest implementation
- No replacement logic needed
- Maximum tenant isolation

**Cons**:
- **Breaks existing functionality** — lose the ability to provide cross-tenant support
- Not viable if super-admin access is a product requirement
- `admin_client` fixture in conftest.py would need rethinking

**Effort**: Low but breaks functionality

---

### Recommendation

**Option A: Add `SUPER_ADMIN` role (rank 5)** is the cleanest approach.

Rationale:
1. The role hierarchy is already the system's authorization model — extending it is the natural evolution
2. It makes super-admin status visible and queryable in the database
3. The `bypass_filter` change is a one-liner: `user.role == UserRole.SUPER_ADMIN`
4. Removes ALL `is_admin` references cleanly
5. The migration is straightforward with a known edge case to handle

**Edge case to handle in migration**:
- `is_admin=True` + `role=viewer` → `super_admin` (was a platform admin with low tenant role)
- `is_admin=True` + `role=admin` or `role=owner` → `super_admin` (super_admin overrides, but maybe preserve their tenant role too?)

Suggested migration logic:
```sql
UPDATE users SET role = 'super_admin' WHERE is_admin = TRUE;
-- super_admin role becomes the single source of truth
```

If you want to keep the tenant-role distinction for super-admins (they could be VIEWER in their own tenant but still have platform access), you'd need a separate column. But since these are SaaS platform employees, having `role='super_admin'` with the same tenant_id is sufficient.

#### Migration Strategy
1. Add `SUPER_ADMIN` to UserRole enum
2. Backfill: `UPDATE users SET role = 'super_admin' WHERE is_admin = TRUE`
3. Create new migration to DROP `is_admin` column
4. Update CHECK constraint to include 'super_admin'
5. Remove `is_admin` from entity, model, repo mapping
6. Update bypass_filter logic
7. Remove dead code (`validate_admin_user`, `_get_current_admin_user`, `is_admin_user`)
8. Update test fixtures (remove is_admin from all constructors + seed rows)

### Risks
- **Migration rollback**: Dropping a column is destructive. Script must include a downgrade that recreates `is_admin` and backfills from `role='super_admin'`.
- **Test suite disruption**: ~50 references across 10 files — high change surface. Every fixture, seed row, and helper that creates User/UserEntity must update.
- **API client breakage**: `UserRoleResponseSchema.is_admin` removal could break API consumers reading that field. Verify if any client depends on it.
- **Edge case users**: If any production user has `is_admin=True` AND a custom role set after Phase 4 migration, the backfill could overwrite their role. Need to check current data.

### File Change Estimate

| Category | Files | Est. Changes |
|----------|-------|--------------|
| Domain (entity + enum) | 2 | Add SUPER_ADMIN to enum, remove `is_admin` from entity |
| Infrastructure (model + repo + schema) | 4 | Remove column, mapping, response field |
| Application (auth service) | 1 | Replace `user.is_admin` → `user.role == SUPER_ADMIN`, remove `validate_admin_user` |
| Dependencies (auth_dependencies) | 1 | Remove `_get_current_admin_user`, `is_admin_user` alias |
| Routes (_role_routers) | 1 | Remove `is_admin=...` from response building |
| Migration | 1 | New Alembic version: add SUPER_ADMIN to CHECK, backfill, drop column |
| Test fixtures & factories | 1 | Remove `is_admin` from `make_user_entity` defaults |
| Integration conftest | 1 | Remove `is_admin` from all UserEntity constructors and User seed rows |
| Test: bypass_filter | 1 | Rewrite to test SUPER_ADMIN role → bypass activation |
| Test: user_entity | 1 | Remove `test_role_is_independent_from_is_admin` test |
| Test: user_entity_tenant | 1 | Remove `is_admin` from constructors |
| Test: user_repository | 1 | Remove `is_admin` from mock rows |
| Test: role guard fixtures (x3) | 3 | Remove `is_admin=False` from seed rows |
| Test: role_assignment | 1 | Remove `is_admin=False` from seeds |
| **Total** | **~20** | |

**Test fixture count**: ~50 individual `is_admin=` references across these files.

### Ready for Proposal

**Yes** — full picture is clear. The exploration is done.

Orchestrator should tell the user:
- Complete inventory of 6 source files, 10 test files, 1 migration
- bypass_filter is the ONLY critical dependency
- Recommend Option A (add SUPER_ADMIN role) as replacement
- ~20 files need changes, ~50 test fixture updates
- Dead code removal is a bonus cleanup opportunity
- Need clarification on: is the `is_admin_user` alias used by ANY external integration or CI script?

---

### Appendix: bypass_filter Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION FLOW                              │
│                                                                     │
│  Request → _get_current_user → AuthService.get_authenticated_user() │
│                                     │                               │
│                          ┌──────────▼──────────┐                    │
│                          │  user_repo          │                    │
│                          │  .get_by_id(token)  │                    │
│                          └──────────┬──────────┘                    │
│                                     │ UserEntity(is_admin=...)     │
│                                     ▼                               │
│                          ┌──────────────────────┐                   │
│                          │ _uow.bypass_filter = │                   │
│                          │   user.is_admin      │                   │
│                          └──────────┬───────────┘                   │
│                                     │                               │
│  Response ← UseCase ── Repository ←─┘                               │
│                           │                                         │
│                           ▼                                         │
│              ┌──────────────────────────────┐                       │
│              │ TenantAwareRepository        │                       │
│              │  ._filter_tenant(stmt)       │                       │
│              │                              │                       │
│              │  if self._bypass:            │                       │
│              │    return stmt  ◄── SKIP     │                       │
│              │  else:                       │                       │
│              │    return stmt.where(        │                       │
│              │      tenant_id==X)           │                       │
│              └──────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────┘
```
