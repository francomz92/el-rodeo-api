# rbac-tests — Specification

## ADDED Requirements

### Requirement: Factory default role

The system MUST set `role=UserRole.VIEWER` as default in the `make_user_entity` test factory. Existing fixtures MUST continue working without changes.

#### Scenario: Existing factory still works
- GIVEN a test using make_user_entity without role arg
- WHEN the entity is created
- THEN role == UserRole.VIEWER, same as current implicit behavior

### Requirement: RBAC integration tests

The system SHOULD include integration tests covering:
1. VIEWER cannot create/update/delete (read-only)
2. EDITOR can create and update, but not delete
3. ADMIN can perform all CRUD within tenant
4. OWNER can perform all CRUD plus role management
5. `bypass_filter` activates for is_admin=True in auth dependency chain
6. Last-OWNER demotion is rejected
7. Self-escalation is blocked (registration always sets VIEWER)

#### Scenario: VIEWER read-only
- GIVEN an authenticated user with role VIEWER
- WHEN sending POST/PUT/DELETE to protected routes
- THEN response status is 403

#### Scenario: bypass_filter flow
- GIVEN a user with is_admin=True and role VIEWER
- WHEN get_authenticated_user resolves them
- THEN uow.bypass_filter is True, allowing cross-tenant reads

#### Scenario: Last-OWNER protection
- GIVEN a tenant with one OWNER user
- WHEN attempting to demote that user to EDITOR
- THEN the request fails with validation error
