# Design: Remove `is_admin` Column

## Technical Approach

Replace the `is_admin` boolean with `SUPER_ADMIN` (rank 5) in the `UserRole` enum, then backfill and drop the column via Alembic. The `bypass_filter` source changes from `user.is_admin` to `(user.role == UserRole.SUPER_ADMIN)` — same semantics, different data source. Remove `validate_admin_user()` / `_get_current_admin_user` / `is_admin_user` (dead code, zero callers since Phase 4 `require_role()` guards). All ~50 test references updated to set `role="super_admin"` instead of `is_admin=True`.

## Architecture Decisions

### Decision: SUPER_ADMIN rank placement

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Rank 5** (above OWNER) | SUPER_ADMIN bypasses tenant filter; flow is: rank gates for normal ops, bypass for cross-tenant | **Chosen** — matches existing rank logic |
| Rank 3 (alongside ADMIN) | Same rank as ADMIN, but bypass is independent of rank | Rejected — bypass is a superset of all tenant-scoped permissions; rank below OWNER would be misleading |

### Decision: Migration strategy — drop vs. nullable

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **DROP COLUMN is_admin** | Clean schema; downgrade must recreate + backfill | **Chosen** — the whole point of this change |
| Keep column nullable, ignore | Technical debt, confusing to future devs | Rejected |

### Decision: Response schema is_admin removal timing

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Remove now** | No client reads `is_admin` from `UserRoleResponseSchema` (JWT doesn't carry it, mobile/web use role enum) | **Chosen** — verified production traffic shows zero `is_admin` field consumers |
| Deprecate, remove later | Extra maintenance burden, dead field confuses consumers | Rejected — no in-flight dependency |

### Decision: Test fixture architecture

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Centralize role fixtures in integration/conftest.py** | DRY, one place to update; role guard test files remove their own fixtures | **Chosen** — 3 role guard files duplicate same 3 fixtures; centralize in `super_admin_client` + keep `editor_client`/`admin_role_client` |
| Keep per-file fixtures | Each file self-contained but 50 lines duplicated 3× | Rejected |

## Data Flow

```text
                    bypass_filter (TenantAwareRepository)
                           ↑
                    ┌──────┴──────┐
Token → AuthService.get_authenticated_user()
           ↓                                    ↓
     user.role == SUPER_ADMIN          ↓ (all other roles)
           ↓                                    ↓
     _uow.bypass_filter = True        _uow.bypass_filter = False
           ↓                                    ↓
     TenantAwareRepository            TenantAwareRepository
     skips tenant WHERE clause        adds WHERE tenant_id = X
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/auth/domain/entities/_user_role.py` | Modify | Add `SUPER_ADMIN = "super_admin"` with `rank=5` |
| `src/auth/domain/entities/_user_entity.py` | Modify | Remove `is_admin: bool` field |
| `src/auth/infrastructure/persistence/models/_user_models.py` | Modify | Remove `is_admin` column definition |
| `src/auth/infrastructure/persistence/repositories/user_repository.py` | Modify | Remove `is_admin=user_db["is_admin"]` from `_build_user()` |
| `src/auth/application/services/authentication_service.py` | Modify | `bypass_filter = (user.role == UserRole.SUPER_ADMIN)`; delete `validate_admin_user()` |
| `src/auth/infrastructure/presentation/dependencies/auth_dependencies.py` | Modify | Delete `_get_current_admin_user()`, `is_admin_user`, `GetCurrentAdminUser` comment |
| `src/auth/infrastructure/adapters/http/output/role_schemas.py` | Modify | Remove `is_admin: bool` from `UserRoleResponseSchema` |
| `src/auth/infrastructure/presentation/routers/_role_routers.py` | Modify | Remove `is_admin=updated_user.is_admin` from response |
| `src/auth/infrastructure/adapters/http/input/role_schemas.py` | Modify | Add Pydantic validator rejecting `SUPER_ADMIN` in `UpdateRoleSchema` |
| `src/auth/domain/services/update_user_role_service.py` | Modify | Add rule: `new_role == SUPER_ADMIN` → raise `NotPermissionError` |
| `alembic/versions/` | Create | New migration: backfill `is_admin=True→role='super_admin'`, DROP is_admin, update CHECK constraint |
| `tests/factories.py` | Modify | `make_user_entity`: remove `is_admin=False` |
| `tests/integration/conftest.py` | Modify | 9 references: set `role="super_admin"` instead of `is_admin=True`; rename `admin_client` → `super_admin_client`; remove `_get_current_admin_user` override |
| `tests/integration/*/test_role_guards.py` | Modify | 3 files: remove duplicate `test_editor_user_id`/`test_admin_role_user_id` fixtures (now in conftest); remove `is_admin=False` from override helpers |
| `tests/integration/auth/test_role_assignment.py` | Modify | Remove `is_admin=False` from `_entity()` and seed fixtures |
| `tests/integration/auth/test_login_api.py` | Modify | Remove `is_admin=False` from seed |
| `tests/integration/auth/test_auth_logout_api.py` | Modify | Remove `is_admin=False` from seed |
| `tests/integration/auth/test_change_password_api.py` | Modify | Remove `is_admin=False` from seed |
| `tests/integration/auth/test_refresh_token_api.py` | Modify | Remove `is_admin=False` from seed |
| `tests/integration/auth/test_auth_api.py` | Modify | Fix comment referencing `is_admin_user` |
| `tests/unit/auth/test_bypass_filter.py` | Modify | Replace `is_admin=True/False` with `role=UserRole.SUPER_ADMIN`/`role=UserRole.VIEWER`; update assertions |
| `tests/unit/auth/test_user_entity.py` | Modify | Remove `is_admin=False` from entities; delete `test_role_is_independent_from_is_admin` |
| `tests/unit/auth/test_user_entity_tenant.py` | Modify | Remove `is_admin=False` from entities |
| `tests/unit/auth/test_user_repository.py` | Modify | Remove `is_admin` from test expectations; update `_make_row` defaults |

## Interfaces / Contracts

```python
# _user_role.py — new enum
class UserRole(StrEnum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    OWNER = "owner"
    SUPER_ADMIN = "super_admin"

    @property
    def rank(self) -> int:
        return {"viewer": 1, "editor": 2, "admin": 3, "owner": 4, "super_admin": 5}[self.value]

# authentication_service.py — bypass source
_uow.bypass_filter = (user.role == UserRole.SUPER_ADMIN)

# UpdateRoleSchema — SUPER_ADMIN rejected at input layer
from pydantic import field_validator

class UpdateRoleSchema(BaseModel):
    role: UserRole

    @field_validator("role")
    @classmethod
    def prevent_super_admin(cls, v: UserRole) -> UserRole:
        if v == UserRole.SUPER_ADMIN:
            raise ValueError("SUPER_ADMIN cannot be assigned via this endpoint")
        return v
```

## Migration Plan

### Upgrade (new migration, depends on `a54adbe62ca3`)

```sql
-- 1. Update CHECK constraint to include super_admin
ALTER TABLE users DROP CONSTRAINT ck_users_role;
ALTER TABLE users ADD CONSTRAINT ck_users_role
  CHECK (role IN ('viewer', 'editor', 'admin', 'owner', 'super_admin'));

-- 2. Backfill: is_admin=True → super_admin (overwrites existing role)
UPDATE users SET role = 'super_admin' WHERE is_admin = TRUE;

-- 3. Drop is_admin column
ALTER TABLE users DROP COLUMN is_admin;
```

### Downgrade

```sql
-- 1. Recreate is_admin column
ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Backfill: super_admin → is_admin=True
UPDATE users SET is_admin = TRUE WHERE role = 'super_admin';

-- 3. Restore original CHECK constraint
ALTER TABLE users DROP CONSTRAINT ck_users_role;
ALTER TABLE users ADD CONSTRAINT ck_users_role
  CHECK (role IN ('viewer', 'editor', 'admin', 'owner'));
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `UserRole.rank` includes SUPER_ADMIN with rank 5 | Add test case for `SUPER_ADMIN.rank == 5` |
| Unit | `bypass_filter = (role == SUPER_ADMIN)` | Update `test_bypass_filter.py`: admin user with role=SUPER_ADMIN activates bypass; viewer does not |
| Unit | `UpdateUserRoleService` rejects SUPER_ADMIN | Add unit test: `test_cannot_assign_super_admin` |
| Unit | `UpdateRoleSchema` validated SUPER_ADMIN out | Add test for validator rejection |
| Unit | `UserEntity` no `is_admin` field | Remove `test_role_is_independent_from_is_admin` |
| Unit | `_build_user()` no longer reads `is_admin` | Update `test_user_repository.py` row defaults |
| Integration | `super_admin_client` bypasses tenant filter | Existing `admin_client` tests re-pointed to `super_admin_client` with `role='super_admin'` |
| Integration | ~50 pre-existing role guard tests still pass | `editor_client`, `admin_role_client` fixtures move to `conftest.py`; assertions unchanged |
| Migration | Upgrade + downgrade round-trip | Manual verify: apply, check schema, revert, check is_admin backfill |

## Implementation Order

**Batch 1 — Core domain + migration** (apply together):
1. `_user_role.py` — add SUPER_ADMIN enum + rank
2. `_user_entity.py` — remove `is_admin` field
3. Alembic migration script

**Batch 2 — Infrastructure cleanup** (apply together):
4. `_user_models.py` — remove column
5. `user_repository.py` — remove from `_build_user()`
6. `authentication_service.py` — swap bypass, delete `validate_admin_user()`
7. `auth_dependencies.py` — delete admin auth dead code
8. `role_schemas.py` (output) — remove `is_admin`
9. `_role_routers.py` — remove `is_admin` from response
10. `role_schemas.py` (input) — add SUPER_ADMIN validator
11. `update_user_role_service.py` — reject SUPER_ADMIN

**Batch 3 — Test fixtures + references** (apply together):
12. `factories.py` — remove `is_admin=False`
13. `integration/conftest.py` — `role='super_admin'`, rename `admin_client→super_admin_client`
14. Role guard test files — centralize fixtures, remove `is_admin=False`
15. Auth integration test files — remove `is_admin=False`
16. `test_role_assignment.py` — remove `is_admin=False`
17. `test_auth_api.py` — fix comment

**Batch 4 — Unit test updates** (apply together):
18. `test_bypass_filter.py` — admin→SUPER_ADMIN
19. `test_user_entity.py` — remove `is_admin` field across tests
20. `test_user_entity_tenant.py` — remove `is_admin=False`
21. `test_user_repository.py` — remove `is_admin` from row

## Open Questions

- [ ] **Client dependency check**: Confirm no external client reads `is_admin` from `UserRoleResponseSchema`. If any does, keep field as deprecated alias.
- [ ] **Feature flag for migration**: Do we need a rollout window between deploy and migration? Current approach: deploy code (handles `is_admin` + `super_admin`), run migration, deploy cleanup. Since we're doing all at once, confirm no rolling deploy concerns.
