# RBAC — Main Spec

## user-role-enum

### Requirement: UserRole Enum

The system MUST define `UserRole` as a `StrEnum` with SUPER_ADMIN("super_admin", rank=5), OWNER("owner", rank=4), ADMIN("admin", rank=3), EDITOR("editor", rank=2), VIEWER("viewer", rank=1). Each MUST expose a `rank` property for comparison.
(Previously: 4 members OWNER through VIEWER, max rank=4)

#### Scenario: Rank hierarchy
- GIVEN the UserRole enum
- WHEN comparing ranks
- THEN SUPER_ADMIN.rank > OWNER.rank > ADMIN.rank > EDITOR.rank > VIEWER.rank
(Previously: OWNER was highest)

#### Scenario: String values are lowercase roles
- GIVEN each UserRole member
- WHEN accessed as string
- THEN str(SUPER_ADMIN) == "super_admin", str(OWNER) == "owner", str(ADMIN) == "admin", str(EDITOR) == "editor", str(VIEWER) == "viewer"

#### Scenario: Default role on registration
- GIVEN a UserCreationValueObject without role
- WHEN creating a user
- THEN role defaults to UserRole.VIEWER
(Unchanged)

#### Scenario: Role persists and maps back
- GIVEN a user saved with role "super_admin" in the DB
- WHEN UserRepository._build_user maps the row
- THEN returned UserEntity.role == UserRole.SUPER_ADMIN
(Previously: only tested viewer/editor/admin/owner)

### Requirement: Entity, Model, VO, Repository wiring (is_admin field removal)

The system MUST remove `is_admin: bool` from `UserEntity`, `User` SQLAlchemy model, and `UserRoleResponseSchema`. The `_build_user` mapping MUST NOT reference `is_admin`. The `UserCreationValueObject` and `UserUpdateValueObject` MUST NOT include `is_admin`.
(Previously: is_admin was a required field on entity, model, schema, and VO)

#### Scenario: Entity construction without is_admin
- GIVEN a `UserEntity` constructor call
- WHEN passing all required fields except is_admin
- THEN construction succeeds
- AND `is_admin` raises AttributeError

#### Scenario: API response excludes is_admin
- GIVEN a response from `PUT /users/{id}/role`
- WHEN inspecting the JSON body
- THEN `is_admin` is not present in the response

#### Scenario: _build_user mapping excludes is_admin
- GIVEN a DB row from the `users` table
- WHEN UserRepository._build_user maps it
- THEN the returned UserEntity has no `is_admin` attribute

## role-guard

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

### Requirement: Role guards work with SUPER_ADMIN

SUPER_ADMIN (rank 5) MUST satisfy any `require_role()` guard, including `require_role(UserRole.OWNER)`.

#### Scenario: SUPER_ADMIN passes OWNER guard
- GIVEN a user with role SUPER_ADMIN
- WHEN checked against `require_role(UserRole.OWNER)`
- THEN access is granted (rank 5 >= rank 4)

## role-assignment

### Requirement: Role assignment authority

The system MUST allow only ADMIN and OWNER users to promote or demote roles within their tenant. No user MAY self-escalate — registration always sets VIEWER. SUPER_ADMIN MUST NOT be assignable through this endpoint.
(Previously: no mention of SUPER_ADMIN)

#### Scenario: ADMIN promotes a user to EDITOR
- GIVEN an ADMIN user and a VIEWER user in the same tenant
- WHEN the ADMIN assigns role EDITOR to the VIEWER
- THEN the target user's role becomes EDITOR
(Unchanged)

#### Scenario: VIEWER cannot assign roles
- GIVEN a VIEWER user
- WHEN they attempt to assign any role
- THEN NotPermissionError is raised
(Unchanged)

#### Scenario: Self-escalation blocked
- GIVEN a user with role VIEWER
- WHEN they attempt to change their own role to ADMIN
- THEN the request is rejected with NotPermissionError
(Unchanged)

#### Scenario: SUPER_ADMIN assignment rejected at schema level
- GIVEN an OWNER user
- WHEN they attempt `PUT /users/{id}/role` with `role="super_admin"`
- THEN the request is rejected with HTTP 422 (validation error)
- AND the target user's role remains unchanged
(New: SUPER_ADMIN is not a valid PUT target)

### Requirement: SUPER_ADMIN not assignable via API

The system MUST NOT accept SUPER_ADMIN in `PUT /users/{id}/role`. The `UpdateRoleSchema` MUST exclude `UserRole.SUPER_ADMIN` from valid values. SUPER_ADMIN MUST only be assignable via DB seed or direct migration.

#### Scenario: PUT role rejects SUPER_ADMIN
- GIVEN an OWNER user authenticated against `PUT /users/{id}/role`
- WHEN the request body contains `{"role": "super_admin"}`
- THEN the response is HTTP 422 (validation error)
- AND the target user's role is unchanged

#### Scenario: SUPER_ADMIN cannot be self-assigned
- GIVEN a SUPER_ADMIN user
- WHEN they attempt `PUT /users/{id}/role` with any role value
- THEN the request is processed normally (owned by OWNERS only, SUPER_ADMIN is irrelevant here)

### Requirement: Last-OWNER protection

The system MUST prevent demoting or deleting the last OWNER of a tenant. At least one OWNER MUST remain per tenant at all times.

#### Scenario: Demoting last OWNER blocked
- GIVEN a tenant with exactly one OWNER user
- WHEN an ADMIN attempts to demote that OWNER to EDITOR
- THEN the request is rejected with BusinessValidationError

#### Scenario: Demoting non-last OWNER succeeds
- GIVEN a tenant with two OWNER users
- WHEN an ADMIN demotes one OWNER to EDITOR
- THEN the demotion succeeds and the tenant still has one OWNER

## role-migration

### Requirement: New migration DROP is_admin

The system MUST provide an Alembic migration (revision depends on `a54adbe62ca3`) that backfills `is_admin=True → role='super_admin'` UNCONDITIONALLY (overwrites any existing role), then `DROP COLUMN is_admin`. The migration MUST also update the CHECK constraint to include `'super_admin'`.

#### Scenario: Migration backfill overwrites existing role
- GIVEN a user with `is_admin=True, role='admin'` in the DB
- WHEN the migration upgrade runs
- THEN `role = 'super_admin'` (is_admin wins over existing role)

#### Scenario: Migration backfill ignores non-admin
- GIVEN a user with `is_admin=False, role='editor'`
- WHEN the migration upgrade runs
- THEN `role = 'editor'` (unchanged)

#### Scenario: is_admin column is removed
- GIVEN the migration has completed
- WHEN inspecting the `users` table schema
- THEN the `is_admin` column does not exist

#### Scenario: CHECK constraint includes super_admin
- GIVEN the migration has completed
- WHEN inspecting the CHECK constraint on `users.role`
- THEN `'super_admin'` is a valid value in the constraint

#### Scenario: Downgrade restores is_admin column
- GIVEN the migration has been applied
- WHEN running `alembic downgrade -1`
- THEN the `is_admin` column is re-added with existing super_admin users having `is_admin=True`
- AND non super_admin users have `is_admin=False`

## user-auth

### Requirement: bypass_filter activation (Production Bug Fix)

In `AuthService.get_authenticated_user`, AFTER loading the user from the repository, the system MUST set `uow.bypass_filter = (user.role == UserRole.SUPER_ADMIN)` BEFORE returning. This enables cross-tenant super-admin access for SUPER_ADMIN users in production.
(Previously: bypass_filter = user.is_admin)

#### Scenario: Super-admin bypass activates
- GIVEN a user with role==UserRole.SUPER_ADMIN
- WHEN get_authenticated_user resolves them
- THEN uow.bypass_filter is set to True

#### Scenario: Non-admin bypass stays off
- GIVEN a user with role!=UserRole.SUPER_ADMIN (e.g. ADMIN, OWNER)
- WHEN get_authenticated_user resolves them
- THEN uow.bypass_filter is set to False (or remains default)

#### Scenario: is_admin field absent from entity
- GIVEN a UserEntity loaded from the repository
- WHEN accessing fields
- THEN `is_admin` is not a valid attribute — `role` is the sole authority for both tenant-scoped access and cross-tenant bypass
(Previously: is_admin field existed alongside role)

## admin-auth

### Requirement: Route protection matrix

Each bounded context MUST apply role guards per this matrix:

| Context | Router | GET (list) | GET (by id) | POST | PUT | DELETE |
|---------|--------|-----------|-------------|------|-----|--------|
| Cattle | `_animal_types.py` (3 routes) | ADMIN | — | ADMIN | ADMIN | — |
| Cattle | `_animals.py` (5 routes) | VIEWER | VIEWER | EDITOR | EDITOR | ADMIN |
| Cattle | `_animal_protocols.py` (5 routes) | VIEWER | VIEWER | — | EDITOR | ADMIN |
| Cattle | `_schedule_events.py` (4 routes) | VIEWER | — | EDITOR | EDITOR | ADMIN |
| Finance | `_animal_supply_types.py` (5 routes) | VIEWER | VIEWER | ADMIN | ADMIN | ADMIN |
| Finance | `_animal_supplies.py` (5 routes) | VIEWER | VIEWER | EDITOR | EDITOR | ADMIN |
| Finance | `_purchases.py` (4 routes) | VIEWER | VIEWER | EDITOR | EDITOR | ADMIN |
| Market | `_buyers.py` (5 routes) | VIEWER | VIEWER | EDITOR | EDITOR | ADMIN |
| Market | `_sales.py` (4 routes) | VIEWER | VIEWER | EDITOR | EDITOR | ADMIN |
| Auth | `_authentication_routers.py` (profile: /users/me) | VIEWER | — | VIEWER | — | — |
| Auth | `_role_routers.py` (admin: /users) | ADMIN | ADMIN | — | ADMIN | ADMIN |

**Note**: The cattle `_animal_types.py` GET list was originally spec'd as VIEWER-access. After verification, it was upgraded to ADMIN (matching the design document) to prevent information disclosure of shared reference data. This is a spec deviation — see archive report for details.

#### Scenario: VIEWER can only read
- GIVEN a VIEWER user
- WHEN calling any POST/PUT/DELETE across cattle, finance, or market
- THEN response is HTTP 403

#### Scenario: EDITOR can create and update, cannot delete
- GIVEN an EDITOR user
- WHEN calling any DELETE endpoint
- THEN response is HTTP 403
#### Scenario: ADMIN has full CRUD within tenant

- GIVEN an ADMIN user
- WHEN calling any endpoint within their tenant
- THEN access is granted for all operations

#### Scenario: VIEWER can access own profile

- GIVEN a VIEWER user
- WHEN calling `GET /users/me` and `PUT /users/me`
- THEN access is granted (200)

#### Scenario: VIEWER cannot access admin user management routes

- GIVEN a VIEWER user
- WHEN calling `GET /users`, `GET /users/{id}`, or `DELETE /users/{id}`
- THEN response is 403

#### Scenario: ADMIN has full user management access

- GIVEN an ADMIN user
- WHEN calling any profile or admin user-management route
- THEN access is granted for all operations (200)

## rbac-tests

### Requirement: Factory default role (is_admin removal)

The system MUST remove `is_admin` from the `make_user_entity` test factory defaults. The factory MUST NOT accept `is_admin` as an override. Existing fixtures MUST continue working without changes by removing `is_admin` from their override calls.
(Previously: is_admin=False was in make_user_entity defaults)

#### Scenario: make_user_entity no longer has is_admin
- GIVEN `make_user_entity()` without overrides
- WHEN accessing the returned entity
- THEN `hasattr(entity, 'is_admin')` is False

#### Scenario: Existing factory calls updated
- GIVEN any test file that called `make_user_entity(is_admin=...)`
- WHEN the test runs after cleanup
- THEN the call uses `role=UserRole.SUPER_ADMIN` instead where `is_admin=True` was used
- AND `is_admin` is simply removed where `is_admin=False` was used

### Requirement: Role-specific test clients

The system MUST provide three new fixtures in `tests/integration/conftest.py`:

1. **editor_client** — authenticated client with `role=EDITOR, is_admin=False`
2. **admin_role_client** — authenticated client with `role=ADMIN, is_admin=False`
3. **super_admin_client** — authenticated client with `role=SUPER_ADMIN`, sets `uow.bypass_filter = True`

The existing `admin_client` fixture MUST be renamed or replaced by `super_admin_client` that uses `role=SUPER_ADMIN` instead of `is_admin=True`.

The `client` and `tenant_client` fixtures MUST no longer reference `is_admin`.

#### Scenario: editor_client has role EDITOR and no bypass
- GIVEN the editor_client fixture
- WHEN making an authenticated request
- THEN `current_user.role == UserRole.EDITOR`
- AND `uow.bypass_filter` is NOT set

#### Scenario: admin_role_client has role ADMIN and no bypass
- GIVEN the admin_role_client fixture
- WHEN making an authenticated request
- THEN `current_user.role == UserRole.ADMIN`
- AND `uow.bypass_filter` is NOT set

#### Scenario: super_admin_client has role SUPER_ADMIN and bypass
- GIVEN the super_admin_client fixture
- WHEN making an authenticated request
- THEN `current_user.role == UserRole.SUPER_ADMIN`
- AND `uow.bypass_filter` is True

#### Scenario: All existing auth fixtures drop is_admin
- GIVEN every fixture in conftest.py that creates a User or UserEntity
- WHEN inspecting the object
- THEN `is_admin` is not present in constructor or field access

### Requirement: RBAC integration tests

The system SHOULD include integration tests covering:
1. VIEWER cannot create/update/delete (read-only)
2. EDITOR can create and update, but not delete
3. ADMIN can perform all CRUD within tenant
4. OWNER can perform all CRUD plus role management
5. `bypass_filter` activates for role=SUPER_ADMIN in auth dependency chain (previously: is_admin=True)
6. Last-OWNER demotion is rejected
7. Self-escalation is blocked (registration always sets VIEWER)
(Previously: item 5 referenced is_admin=True)

#### Scenario: VIEWER read-only
- GIVEN an authenticated user with role VIEWER
- WHEN sending POST/PUT/DELETE to protected routes
- THEN response status is 403
(Unchanged)

#### Scenario: bypass_filter flow uses SUPER_ADMIN
- GIVEN a user with role=SUPER_ADMIN and role VIEWER (impossible state after migration, but for completeness)
- WHEN get_authenticated_user resolves them
- THEN uow.bypass_filter is True, allowing cross-tenant reads
(Previously: used is_admin=True)

#### Scenario: Last-OWNER protection
- GIVEN a tenant with one OWNER user
- WHEN attempting to demote that user to EDITOR
- THEN the request fails with validation error
(Unchanged)
