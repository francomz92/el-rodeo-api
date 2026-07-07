# Delta for auth

## MODIFIED Requirements

### Requirement: UserSchema exposes email, role, is_active, tenant_id

The system MUST expose `email: str`, `role: UserRole`, `is_active: bool`, and `tenant_id: UUID | None` in `UserSchema`. Existing fields `id`, `name`, `dni`, `created_at` remain unchanged.
(Previously: UserSchema only exposed id, name, dni, created_at)

#### Scenario: Full schema on register response

- GIVEN a new user registered `POST /register`
- WHEN inspecting the response body
- THEN `email`, `role`, `is_active`, `tenant_id` are present alongside `id`, `name`, `dni`, `created_at`

#### Scenario: Full schema on profile endpoint

- GIVEN a user calling `GET /users/me`
- WHEN inspecting the response body
- THEN all enriched fields are populated correctly

### Requirement: Login blocks inactive users

The system MUST reject authentication for users with `is_active=False`. `LoginUserService.validate_credentials` SHALL check `user.is_active` before password verification and raise `UnauthorizedError` with a generic message.
(Previously: Login validated password only; no is_active check existed)

#### Scenario: Active user logs in

- GIVEN a user with `is_active=True`
- WHEN calling `POST /login` with valid credentials
- THEN the response is 200 with `access_token` and `refresh_token`

#### Scenario: Inactive user rejected

- GIVEN a user with `is_active=False` and valid credentials
- WHEN calling `POST /login`
- THEN the response status is 401
- AND the error message is "Las credenciales proporcionadas no son válidas"

### Requirement: IUserRepository.list_users abstract method

The system MUST add `list_users(tenant_id, page, per_page, search, role)` to `IUserRepository`. The method SHALL return `tuple[list[UserEntity], int]` (items + total count). Search SHALL filter by `name` or `email` (ILIKE). Role filter SHALL match `UserRole` exactly.
(Previously: IUserRepository had no paginated list method)

#### Scenario: Repository returns paginated results

- GIVEN 30 users in tenant T1
- WHEN calling `list_users(tenant_id=T1, page=1, per_page=10)`
- THEN 10 users are returned and total is 30

#### Scenario: Repository filters by search

- GIVEN users "Alice" and "Bob" in tenant T1
- WHEN calling `list_users(tenant_id=T1, search="ali")`
- THEN only "Alice" is returned

#### Scenario: Repository filters by role

- GIVEN EDITOR and VIEWER users in tenant T1
- WHEN calling `list_users(tenant_id=T1, role=EDITOR)`
- THEN all returned users have role EDITOR
