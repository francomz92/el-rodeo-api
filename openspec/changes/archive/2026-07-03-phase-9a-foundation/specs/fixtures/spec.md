# Delta: Test Fixtures — Role Alignment

## MODIFIED Requirements

### Requirement: Role-specific test clients

The system MUST provide six fixtures in `tests/integration/conftest.py`:

1. **client** — authenticated with `role=ADMIN` for write-capable tests
2. **tenant_client** — authenticated with `role=ADMIN` scoped to the default tenant
3. **editor_client** — authenticated with `role=EDITOR`
4. **admin_role_client** — authenticated with `role=ADMIN`, no bypass
5. **super_admin_client** — authenticated with `role=SUPER_ADMIN`, sets `uow.bypass_filter = True`
6. **viewer_client** — authenticated with `role=VIEWER` (for role-guard verification tests)

The `client` fixture MUST default to `role=ADMIN` to satisfy write-capable integration tests. Tests verifying role guards MUST use role-specific fixtures (`viewer_client`, `admin_role_client`, etc.). No fixture MUST reference `is_admin`.
(Previously: client/tenant_client fixture roles were unspecified — `is_admin` was the only access control mechanism)

#### Scenario: client fixture has ADMIN role

- GIVEN the `client` fixture in conftest.py
- WHEN making an authenticated write request via `client`
- THEN `current_user.role == UserRole.ADMIN`
- AND the write request succeeds (no 403)

#### Scenario: Role-guard tests use role-specific fixtures

- GIVEN a test verifying VIEWER cannot create
- WHEN the test uses `viewer_client` instead of `client`
- THEN the test correctly receives 403
- AND the same request via `client` (ADMIN) succeeds

#### Scenario: No fixture references is_admin

- GIVEN every fixture in conftest.py that creates a User or UserEntity
- WHEN inspecting the construction call
- THEN `is_admin` is not passed as a parameter
