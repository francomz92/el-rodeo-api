# user-auth — Specification (Modified Capability)

## ADDED Requirements

### Requirement: bypass_filter activation (Production Bug Fix)

In `AuthService.get_authenticated_user`, AFTER loading the user from the repository, the system MUST set `uow.bypass_filter = user.is_admin` BEFORE returning. This enables cross-tenant super-admin access for `is_admin=True` users in production.

#### Scenario: Super-admin bypass activates
- GIVEN a user with is_admin=True
- WHEN get_authenticated_user resolves them
- THEN uow.bypass_filter is set to True

#### Scenario: Non-admin bypass stays off
- GIVEN a user with is_admin=False
- WHEN get_authenticated_user resolves them
- THEN uow.bypass_filter is set to False (or remains default)

### Requirement: UserEntity carries role

UserEntity MUST carry `role: UserRole = UserRole.VIEWER` alongside the existing `is_admin: bool`.

#### Scenario: Entity exposes both role and is_admin
- GIVEN a UserEntity with is_admin=True, role=UserRole.VIEWER
- WHEN inspecting both fields
- THEN is_admin and role are independent — is_admin controls cross-tenant, role controls tenant-scoped access
