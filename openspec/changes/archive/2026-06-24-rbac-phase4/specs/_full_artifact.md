# RBAC Phase 4 — Complete Spec Artifact

## user-role-enum

Define `UserRole` StrEnum with OWNER(4) > ADMIN(3) > EDITOR(2) > VIEWER(1), each with `.rank`. Add `role: UserRole` (default VIEWER) to UserEntity, `role VARCHAR(20) NOT NULL DEFAULT 'viewer'` with CHECK to SQLAlchemy model, `role` to creation/update VOs, and string→enum mapping in `_build_user`.

- **Scenarios**: Rank hierarchy, string values, default VIEWER on registration, round-trip persistence

## role-guard

`require_role(min_role: UserRole)` factory returns a `Depends`-compatible callable. Raises `NotPermissionError` (→ 403) if `current_user.role.rank < min_role.rank`. Reuses existing `NotPermissionError`. Works on endpoint and router-prefix level.

- **Scenarios**: User meets role, user below role, endpoint guard, router-level guard

## role-assignment

Only ADMIN/OWNER can assign roles. No self-escalation (registration sets VIEWER). Last-OWNER protection prevents demotion when only 1 OWNER remains per tenant.

- **Scenarios**: ADMIN promotes, VIEWER cannot assign, self-escalation blocked, last-OWNER demotion blocked, non-last OWNER demotion succeeds

## role-migration

Add `role VARCHAR(20) NOT NULL DEFAULT 'viewer'` with CHECK (`'viewer','editor','admin','owner'`). Backfill: `is_admin=True`→`role='admin'`, `is_admin=False`→`role='viewer'`. Keep `is_admin` column for dual-read.

- **Scenarios**: Migration applies, admin backfill, non-admin backfill

## user-auth (Modified)

**Added**: In `get_authenticated_user`, set `uow.bypass_filter = user.is_admin` after loading user (fixes production bug). UserEntity carries both `role` and `is_admin` as independent fields.

- **Scenarios**: Super-admin bypass activates, non-admin stays off, role + is_admin independence

## admin-auth (Modified)

**Added**: Replace `is_admin_user` internal check with `Depends(require_role(UserRole.ADMIN))`. Route protection matrix across 9 routers (~40 routes): VIEWER=read-only, EDITOR=create+update, ADMIN=full CRUD, animal/supply types require ADMIN.

- **Scenarios**: ADMIN passes guard, EDITOR rejected, VIEWER read-only across all routes, EDITOR cannot delete, ADMIN full CRUD

## rbac-tests

Factory default `role=UserRole.VIEWER` in `make_user_entity`. Integration tests: VIEWER read-only, EDITOR create+update (no delete), ADMIN full CRUD, OWNER role management, bypass_filter flow, last-OWNER protection, self-escalation blocked.

- **Scenarios**: Factory backwards-compat, read-only VIEWER, bypass_filter flow, last-OWNER protection
