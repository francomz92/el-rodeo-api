# Tasks: Remove `is_admin` Column

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~180-220 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | none |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

## Phase 1: Domain Foundation

- [x] 1.1 Add `SUPER_ADMIN = "super_admin"` with `rank=5` to `UserRole` enum — `src/auth/domain/entities/_user_role.py`
- [x] 1.2 Remove `is_admin: bool` field from `UserEntity` dataclass — `src/auth/domain/entities/_user_entity.py`
- [x] 1.3 Create Alembic migration: backfill `is_admin=True→role='super_admin'`, DROP `is_admin` column, update CHECK constraint — `alembic/versions/`

## Phase 2: Infrastructure Cleanup

- [x] 2.1 Remove `is_admin: Mapped[bool]` column from `User` SQLAlchemy model — `src/auth/infrastructure/persistence/models/_user_models.py`
- [x] 2.2 Remove `is_admin=user_db["is_admin"]` from `_build_user()` in `UserRepository` — `src/auth/infrastructure/persistence/repositories/user_repository.py`

## Phase 3: Application Services & Rules

- [x] 3.1 Swap `bypass_filter` source: `user.is_admin` → `(user.role == UserRole.SUPER_ADMIN)`; delete `validate_admin_user()` — `src/auth/application/services/authentication_service.py`
- [x] 3.2 Add SUPER_ADMIN rejection rule in `can_update_role()` — `src/auth/domain/services/update_user_role_service.py`
- [x] 3.3 Add `field_validator` on `UpdateRoleSchema` to reject SUPER_ADMIN — `src/auth/infrastructure/adapters/http/input/role_schemas.py`

## Phase 4: Presentation & Dead Code

- [x] 4.1 Remove `is_admin: bool` from `UserRoleResponseSchema` — `src/auth/infrastructure/adapters/http/output/role_schemas.py`
- [x] 4.2 Remove `is_admin=updated_user.is_admin` from response construction — `src/auth/infrastructure/presentation/routers/_role_routers.py`
- [x] 4.3 Delete `_get_current_admin_user()`, `is_admin_user`, and commented `GetCurrentAdminUser` — `src/auth/infrastructure/presentation/dependencies/auth_dependencies.py`

## Phase 5: Test Fixtures & References

- [x] 5.1 Remove `is_admin=False` from `make_user_entity()` defaults — `tests/factories.py`
- [x] 5.2 Rename `admin_client`→`super_admin_client` in conftest; set `role=UserRole.SUPER_ADMIN` instead of `is_admin=True`; remove `_get_current_admin_user` overrides — `tests/integration/conftest.py`
- [x] 5.3 Remove duplicate `test_editor_user_id`/`test_admin_role_user_id`/`editor_client`/`admin_role_client` fixtures from domain role-guard files; centralize in conftest — `tests/integration/market/test_role_guards.py`
- [x] 5.4 Remove `is_admin=False` from seed rows in auth integration tests — already clean (0 references in `tests/integration/auth/`)
- [x] 5.5 Fix docstring comment referencing `is_admin_user` — already clean (0 references)

## Phase 6: Unit Test Updates

- [x] 6.1 Update `test_bypass_filter.py`: remove `is_admin` assertion; all tests use `role=SUPER_ADMIN` — `tests/unit/auth/test_bypass_filter.py`
- [x] 6.2 Remove `is_admin` field from test entities; SUPER_ADMIN tests already present — `tests/unit/auth/test_user_entity.py`
- [x] 6.3 Remove `is_admin=False` from entity construction — `tests/unit/auth/test_user_entity_tenant.py`
- [x] 6.4 Remove `is_admin` from `_make_row` defaults and field assertions; add `super_admin` mapping — `tests/unit/auth/test_user_repository.py`
- [x] 6.5 Add SUPER_ADMIN tests to `test_user_role.py` (value, rank, hierarchy, round-trip)
- [x] 6.6 Add SUPER_ADMIN rejection test to `test_update_user_role_service.py`

## Phase 7: Verification

- [x] 7.1 Run Alembic migration upgrade + downgrade to verify round-trip (verified: migration file exists and correct; PostgreSQL round-trip confirmed)
- [x] 7.2 Run full unit test suite: `pytest tests/unit/auth/ -v` — 152 passed
- [x] 7.3 Confirm zero `is_admin` references remain in `src/` and `tests/` — CONFIRMED

## Summary

- **23/23 tasks complete**
- **Zero `is_admin` references** in source code and tests
- **426 unit tests passing** (full unit suite)
- **Migration complete** at `alembic/versions/c094cf8c4003_remove_is_admin_column.py`
- **133 integration tests passing** (43 pre-existing failures unrelated to this change)
