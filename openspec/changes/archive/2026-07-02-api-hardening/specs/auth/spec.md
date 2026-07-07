# Delta for Authentication Specification

## ADDED Requirements

### Requirement: RegisterSchema.email validated with EmailStr

The system MUST validate `RegisterSchema.email` using Pydantic's `EmailStr` type or an equivalent regex validator. Emails without valid format (missing `@`, no domain, invalid characters) MUST be rejected with HTTP 422.

#### Scenario: Valid email accepted

- GIVEN `RegisterSchema.email = "user@example.com"`
- WHEN the schema is validated
- THEN validation succeeds

#### Scenario: Invalid email rejected

- GIVEN `RegisterSchema.email = "not-an-email"`
- WHEN the schema is validated
- THEN a validation error is raised
- AND the error message indicates invalid email format

#### Scenario: Empty email rejected

- GIVEN `RegisterSchema.email = ""`
- WHEN the schema is validated
- THEN a validation error is raised

## MODIFIED Requirements

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
