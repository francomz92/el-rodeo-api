# Proposal: RBAC Phase 4 — Role-Based Access Control

## Intent

Replace binary `is_admin` with a 4-tier role hierarchy (VIEWER < EDITOR < ADMIN < OWNER) for tenant-scoped authorization. Keep `is_admin` as a separate cross-tenant super-admin flag for SaaS-level operations.

## Scope

### In Scope
- `UserRole` StrEnum with `rank` property on auth domain
- `role` VARCHAR(20) column on `users` table, default `"viewer"`
- Role guards on all ~40 routes across cattle, finance, market
- `require_role(min_role)` FastAPI dependency factory
- `bypass_filter` production fix in `_get_current_user` / `get_authenticated_user`
- Migration: seed existing `is_admin=True` → `role=admin`, `is_admin=False` → `role=viewer`
- OWNER-only role assignment endpoints (no self-escalation)
- Integration and unit tests for RBAC

### Out of Scope
- Multi-user-per-tenant / membership table
- Granular per-module or per-action permissions
- External auth providers (OAuth2 social, SAML, LDAP)

## Capabilities

### New Capabilities
- `user-role-enum`: `UserRole` StrEnum with OWNER(4), ADMIN(3), EDITOR(2), VIEWER(1) and `.rank` for comparison
- `role-guard`: `require_role(min_role: UserRole)` FastAPI dependency factory
- `role-assignment`: OWNER/ADMIN-only endpoints to promote/demote tenant user roles
- `role-migration`: Data migration seeding existing `is_admin` values into `role` column

### Modified Capabilities
- `user-auth`: UserEntity gains `role: UserRole` field; `get_authenticated_user` sets `uow.bypass_filter` when `is_admin=True` (fixes production gap)
- `admin-auth`: `is_admin_user` dependency uses `require_role(UserRole.ADMIN)` under the hood for tenant-scoped routes

## Approach

1. **Add `UserRole` enum** to `auth/domain/entities/` — StrEnum with `rank` property
2. **Add role field** to `UserEntity`, SQLAlchemy model, VOs, repo mapping, defaults
3. **Create `require_role(min_role)` factory** in `auth_dependencies.py` — returns `Depends`-compatible callable
4. **Fix `bypass_filter` production bug**: in `get_authenticated_user`, set `uow.bypass_filter = user.is_admin` after loading user
5. **Replace `is_admin_user` on routes** with `Depends(require_role(UserRole.ADMIN))` or equivalent tenant-level role checks
6. **Admin-only route special case** (animal_types, supply_types): `Depends(require_role(UserRole.ADMIN))`
7. **OWNER protection**: prevent demotion/deletion of last OWNER; prevent self-escalation
8. **Migration**: add `role` column to users table, backfill from `is_admin`, add CHECK constraint

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `_user_entity.py` | Modified | Add `role: UserRole` field + define `UserRole` enum |
| `_user_models.py` | Modified | Add `role: Mapped[str]` column + CHECK |
| `user_value_object.py` | Modified | Add `role` to creation/update VOs |
| `user_repository.py` | Modified | Map role in `_build_user` |
| `auth_dependencies.py` | Modified | Add `require_role()`, fix `_get_current_user` bypass |
| `authentication_service.py` | Modified | Set `uow.bypass_filter` in prod; add `validate_role()` |
| `register_user_case.py` | Modified | Set default `role=VIEWER` |
| `_animals.py` (5 routes) | Modified | Add role guards |
| `_animal_protocols.py` (5) | Modified | Add role guards |
| `_schedule_events.py` (4) | Modified | Add role guards |
| `_animal_types.py` (3) | Modified | Replace `is_admin_user` with `require_role(ADMIN)` |
| `_purchases.py` (4) | Modified | Add role guards |
| `_animal_supply_types.py` (5) | Modified | Replace `is_admin_user` with `require_role(ADMIN)` |
| `_animal_supplies.py` (5) | Modified | Add role guards |
| `_sales.py` (4) | Modified | Add role guards |
| `_buyers.py` (5) | Modified | Add role guards |
| Tests (~8 files) | Modified | Factories, conftest, new RBAC integration tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Role escalation via API | Low | Registration sets VIEWER only; role assignment requires OWNER/ADMIN |
| Last-OWNER protection bypass | Low | Validate min 1 OWNER per tenant before demotion/deletion |
| Test fixture churn | Med | Override patterns exist; factories gain `role=` default; existing overrides continue working |
| OpenAPI invisibility | Low | Use `dependencies=[...]` on router/endpoint; document via summary text |
| `is_admin` regression during migration | Med | Keep `is_admin` column in DB, backfill from role; dual-read during transition |
| Non-tenant repos (animal_types, supply_types) | Low | Check uses `require_role(ADMIN)` explicitly — these repos use `SessionMixin`, not `TenantAwareRepository` |

## Rollback Plan

1. Revert `role` column addition (remove column, drop CHECK)
2. Revert `UserRole` enum and all dependency changes
3. Revert `bypass_filter` production fix
4. Rollback route guards — routes return to `is_admin_user` / no-role state
5. Migration rollback: all users return to binary `is_admin` from stored `is_admin` column

## Dependencies

- Alembic migration for `role` column
- Existing `is_admin` column kept during migration for backfill

## Success Criteria

- [ ] All 4 roles enforce correct access: VIEWER read-only, EDITOR create+update, ADMIN full CRUD, OWNER full + role mgmt
- [ ] Existing `is_admin=True` users get `role=admin` after migration
- [ ] `bypass_filter` activates for super-admins in production (verified via integration test)
- [ ] OWNER protection prevents last-owner demotion
- [ ] All existing test suites pass without fixture changes (role defaults match current behavior)
- [ ] New RBAC integration tests cover: role hierarchy inheritance, forbidden actions, bypass_filter flow
