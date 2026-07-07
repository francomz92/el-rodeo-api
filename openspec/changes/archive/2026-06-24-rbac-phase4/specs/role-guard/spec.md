# role-guard — Specification

## Purpose
Provide a `require_role(min_role)` FastAPI dependency factory that enforces role-based access via `NotPermissionError` (HTTP 403).

## Requirements

### Requirement: require_role factory

The system MUST expose `require_role(min_role: UserRole)` that returns a FastAPI `Depends`-compatible callable. When current_user.role.rank < min_role.rank, it MUST raise `NotPermissionError`.

#### Scenario: User meets minimum role
- GIVEN a current_user with role ADMIN, min_role=EDITOR
- WHEN the guard executes
- THEN access is granted (no exception)

#### Scenario: User below minimum role
- GIVEN a current_user with role VIEWER, min_role=EDITOR
- WHEN the guard executes
- THEN NotPermissionError is raised → HTTP 403

#### Scenario: Guard used on a single endpoint
- GIVEN `@router.get(..., dependencies=[Depends(require_role(UserRole.EDITOR))])`
- WHEN a VIEWER accesses the endpoint
- THEN request is rejected with 403

#### Scenario: Guard used on router prefix
- GIVEN `router = APIRouter(dependencies=[Depends(require_role(UserRole.ADMIN))])`
- WHEN any endpoint under that router is called by a non-admin
- THEN request is rejected with 403

### Requirement: Existing NotPermissionError reused

The system MUST reuse the existing `NotPermissionError` from `src/common/domain/exceptions.py`. No new exception class is needed.
