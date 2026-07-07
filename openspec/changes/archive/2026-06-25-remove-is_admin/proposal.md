# Proposal: Remove `is_admin` Column

## Intent

Eliminate the redundant `is_admin` boolean column. RBAC Phase 4 made it obsolete — route authorization uses `require_role()` on `UserRole`. The only remaining dependency is cross-tenant bypass in `TenantAwareRepository`.

## Scope

**In**: SUPER_ADMIN role (rank 5), migration to backfill + DROP column, bypass_filter source swap, dead code removal, schema cleanup, test factory + 50 reference updates, role-specific test fixtures.

**Out**: No require_role threshold changes, no new exceptions, no tenant isolation logic changes.

## Capabilities

**New**: None — SUPER_ADMIN is an enum value.

**Modified**: `user-role-enum` (+SUPER_ADMIN), `user-auth` (bypass_filter source change), `role-migration` (new migration), `admin-auth` (dead code removal), `rbac-tests` (fixtures + conftest).

## Approach

1. Add `SUPER_ADMIN` (rank 5) to UserRole enum
2. `bypass_filter = user.is_admin` → `bypass_filter = (user.role == UserRole.SUPER_ADMIN)`
3. Migration: backfill `is_admin=True → role='super_admin'`, then `DROP COLUMN is_admin`
4. Remove `is_admin` from entity, model, schema, `_build_user()`, response
5. Delete `validate_admin_user()`, `_get_current_admin_user`, `is_admin_user`
6. Create `super_admin_client`, `editor_client`, `admin_role_client` fixtures
7. Update 50 test references across 17 files

## Affected Areas

| Area | Impact |
|------|--------|
| `_user_role.py`, `_user_entity.py`, `_user_models.py` | Modified |
| `user_repository.py`, `authentication_service.py` | Modified |
| `auth_dependencies.py`, `role_schemas.py`, `_role_routers.py` | Modified |
| `alembic/versions/` | New migration |
| `tests/factories.py`, `tests/integration/conftest.py` | Modified |
| 15 test files (50 references) | Modified |

## Risks

| Risk | Mitigation |
|------|------------|
| `is_admin=True` + `role=ADMIN`: SUPER_ADMIN wins | Migration sets role unconditionally |
| Dead code removal breaks prod | Zero routes use it (verified) |
| Tokens in flight reference `is_admin` | JWT doesn't carry `is_admin` |

## Rollback

`alembic downgrade -1`, revert source changes, deploy previous image. SUPER_ADMIN in enum is harmless if unused.

## Dependencies

RBAC Phase 4 migration (a54adbe62ca3) must be applied first.

## Success Criteria

- [ ] No `is_admin` in Python source or DB schema
- [ ] `bypass_filter` activates for SUPER_ADMIN only
- [ ] All ~50 test references updated; pre-existing 403-failing tests pass
- [ ] Migration applies and downgrades cleanly
- [ ] Dead functions/dependencies removed with no compilation errors
