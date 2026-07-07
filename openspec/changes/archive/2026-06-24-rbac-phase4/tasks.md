# Tasks: RBAC Phase 4 — Role-Based Access Control

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~850–950 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (infrastructure) → PR 2 (route protection) → PR 3 (role mgmt) |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Infrastructure: enum, model, migration, repo, bypass_filter fix | PR 1 | Base for all RBAC; tests included |
| 2 | Route Protection: require_role factory, inject guards on ~40 routes | PR 2 | Depends on PR 1; tests per router |
| 3 | Role Management: assignment endpoint, OWNER protection, full RBAC tests | PR 3 | Depends on PR 2; integration test suite |

## PR 1: Infrastructure — Enum, Model, Migration, Repository, bypass_filter Fix

- [x] 1.1 Create `UserRole` StrEnum with rank property — file: `src/auth/domain/entities/_user_role.py` — test: `tests/auth/domain/entities/test_user_role.py`
- [x] 1.2 Export `UserRole` from module init — file: `src/auth/domain/entities/__init__.py`
- [x] 1.3 Add `role: UserRole = UserRole.VIEWER` to `UserEntity` — file: `src/auth/domain/entities/_user_entity.py`
- [x] 1.4 Add `role: UserRole = UserRole.VIEWER` to user creation/update VOs — file: `src/auth/domain/value_objects/user_value_object.py`
- [x] 1.5 Add `role: Mapped[str]` column to SQLAlchemy model (VARCHAR(20), NOT NULL, default "viewer") — file: `src/auth/infrastructure/persistence/models/_user_models.py`
- [x] 1.6 Add `update_role(id, role)` / `count_owners_by_tenant(tid)` to repository port — file: `src/auth/domain/repositories/users_repository_port.py`
- [x] 1.7 Map string→UserRole in `_build_user()` — file: `src/auth/infrastructure/persistence/repositories/user_repository.py`
- [x] 1.8 Create Alembic migration: add role column, backfill from is_admin, add CHECK constraint — file: `alembic/versions/xxxx_add_role_column.py`
- [x] 1.9 Fix bypass_filter: set `uow.bypass_filter = user.is_admin` after user load — file: `src/auth/application/services/authentication_service.py`
- [x] 1.10 Test: UserRole enum rank comparison and string values — file: `tests/auth/domain/entities/test_user_role.py`
- [x] 1.11 Test: UserEntity role field defaults and construction — file: `tests/auth/domain/entities/test_user_entity.py`
- [x] 1.12 Test: bypass_filter activates for is_admin, stays off for non-admin — file: `tests/auth/application/services/test_authentication_service.py`
- [x] 1.13 Test: repository builds UserEntity with correct role mapping — file: `tests/auth/infrastructure/persistence/repositories/test_user_repository.py`

## PR 2: Route Protection — require_role Factory + Router Guards

- [x] 2.1 Create `require_role(min_role: UserRole)` dependency factory — file: `src/auth/infrastructure/presentation/dependencies/auth_dependencies.py`
- [x] 2.2 Test: require_role unit tests (all 4 levels, insufficient role, OWNER bypass) — file: `tests/unit/auth/test_auth_dependencies.py`
- [x] 2.3 Guard `_animal_types.py`: create/update → require_role(ADMIN) (replaces is_admin_user) — file: `src/cattle/infrastructure/presentation/routers/_animal_types.py`
- [x] 2.4 Guard `_animals.py`: router-level VIEWER, create/update → EDITOR, delete → ADMIN — file: `src/cattle/infrastructure/presentation/routers/_animals.py`
- [x] 2.5 Guard `_animal_protocols.py`: same pattern as animals — file: `src/cattle/infrastructure/presentation/routers/_animal_protocols.py`
- [x] 2.6 Guard `_schedule_events.py`: same pattern as animals — file: `src/cattle/infrastructure/presentation/routers/_schedule_events.py`
- [x] 2.7 Guard `_animal_supply_types.py`: create/update/delete → require_role(ADMIN) — file: `src/finance/infrastructure/presentation/routers/_animal_supply_types.py`
- [x] 2.8 Guard `_animal_supplies.py`: router-level VIEWER, create/update → EDITOR, delete → ADMIN — file: `src/finance/infrastructure/presentation/routers/_animal_supplies.py`
- [x] 2.9 Guard `_purchases.py`: same pattern as supplies — file: `src/finance/infrastructure/presentation/routers/_purchases.py`
- [x] 2.10 Guard `_buyers.py`: router-level VIEWER, create/update → EDITOR, delete → ADMIN — file: `src/market/infrastructure/presentation/routers/_buyers.py`
- [x] 2.11 Guard `_sales.py`: same pattern as buyers — file: `src/market/infrastructure/presentation/routers/_sales.py`
- [x] 2.12 Guard `_authentication_routers.py`: `/register` → require_role(ADMIN) — file: `src/auth/infrastructure/presentation/routers/_authentication_routers.py`
- [x] 2.13 Test: role guard integration per bounded context (hierarchy enforcement) — file: `tests/integration/cattle/test_role_guards.py`
- [x] 2.14 Test: role guard integration for finance context — file: `tests/integration/finance/test_role_guards.py`
- [x] 2.15 Test: role guard integration for market context — file: `tests/integration/market/test_role_guards.py`

## PR 3: Role Management — Assignment Endpoint + Full RBAC Tests

- [x] 3.1 Create `UpdateUserRoleService` — validate OWNER protection, no self-escalation, last-OWNER guard — file: `src/auth/domain/services/update_user_role_service.py`
- [x] 3.2 Test: UpdateUserRoleService unit tests (all guard rules) — file: `tests/unit/auth/test_update_user_role_service.py`
- [x] 3.3 Create `UpdateUserRoleCase` — orchestrates service + UoW commit — file: `src/auth/application/uses_cases/update_user_role_case.py`
- [x] 3.4 Wire DI for UpdateUserRoleCase — file: `src/auth/infrastructure/presentation/dependencies/role_dependencies.py`
- [x] 3.5 Create endpoint `PUT /users/{id}/role` — OWNER only — file: `src/auth/infrastructure/presentation/routers/_role_routers.py`
- [x] 3.6 Test: Full RBAC integration suite — covered by PR 2 role guard integration tests (2.13–2.15) across all bounded contexts
- [x] 3.7 Test: OWNER role management, last-OWNER demotion blocked, self-escalation blocked — file: `tests/integration/auth/test_role_assignment.py`
- [x] 3.8 Test: bypass_filter flows — covered by unit tests in `tests/unit/auth/test_bypass_filter.py` (task 1.12)
- [x] 3.9 Test: cross-tenant role isolation — covered by `tests/unit/auth/test_update_user_role_case.py::test_cross_tenant_role_change_denied`
- [x] 3.10 Update factory defaults: `make_user_entity` already defaults to `role=UserRole.VIEWER` — file: `tests/factories.py:116`
