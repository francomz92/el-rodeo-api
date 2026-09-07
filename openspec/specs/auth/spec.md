# Authentication Specification — User Management Extensions

## Requirement: UserSchema exposes email, role, is_active, tenant_id

The system MUST expose `email: str`, `role: UserRole`, `is_active: bool`, and `tenant_id: UUID | None` in `UserSchema`. Existing fields `id`, `name`, `dni`, `created_at` remain unchanged.
(Previously: UserSchema only exposed id, name, dni, created_at)

### Scenario: Full schema on register response

- GIVEN a new user registered `POST /register`
- WHEN inspecting the response body
- THEN `email`, `role`, `is_active`, `tenant_id` are present alongside `id`, `name`, `dni`, `created_at`

### Scenario: Full schema on profile endpoint

- GIVEN a user calling `GET /users/me`
- WHEN inspecting the response body
- THEN all enriched fields are populated correctly

## Requirement: Login blocks inactive users

The system MUST reject authentication for users with `is_active=False`. `LoginUserService.validate_credentials` SHALL check `user.is_active` before password verification and raise `UnauthorizedError` with a generic message.
(Previously: Login validated password only; no is_active check existed)

### Scenario: Active user logs in

- GIVEN a user with `is_active=True`
- WHEN calling `POST /login` with valid credentials
- THEN the response is 200 with `access_token` and `refresh_token`

### Scenario: Inactive user rejected

- GIVEN a user with `is_active=False` and valid credentials
- WHEN calling `POST /login`
- THEN the response status is 401
- AND the error message is "Las credenciales proporcionadas no son válidas"

## Requirement: IUserRepository.list_users abstract method

The system MUST add `list_users(tenant_id, page, per_page, search, role)` to `IUserRepository`. The method SHALL return `tuple[list[UserEntity], int]` (items + total count). Search SHALL filter by `name` or `email` (ILIKE). Role filter SHALL match `UserRole` exactly.
(Previously: IUserRepository had no paginated list method)

### Scenario: Repository returns paginated results

- GIVEN 30 users in tenant T1
- WHEN calling `list_users(tenant_id=T1, page=1, per_page=10)`
- THEN 10 users are returned and total is 30

### Scenario: Repository filters by search

- GIVEN users "Alice" and "Bob" in tenant T1
- WHEN calling `list_users(tenant_id=T1, search="ali")`
- THEN only "Alice" is returned

### Scenario: Repository filters by role

- GIVEN EDITOR and VIEWER users in tenant T1
- WHEN calling `list_users(tenant_id=T1, role=EDITOR)`
- THEN all returned users have role EDITOR

## Requirement: RegisterSchema.email validated with EmailStr

The system MUST validate `RegisterSchema.email` using Pydantic's `EmailStr` type or an equivalent regex validator. Emails without valid format (missing `@`, no domain, invalid characters) MUST be rejected with HTTP 422.

### Scenario: Valid email accepted

- GIVEN `RegisterSchema.email = "user@example.com"`
- WHEN the schema is validated
- THEN validation succeeds

### Scenario: Invalid email rejected

- GIVEN `RegisterSchema.email = "not-an-email"`
- WHEN the schema is validated
- THEN a validation error is raised
- AND the error message indicates invalid email format

### Scenario: Empty email rejected

- GIVEN `RegisterSchema.email = ""`
- WHEN the schema is validated
- THEN a validation error is raised

## Requirement: UserRegistered domain event

The system MUST define a `UserRegistered` domain event class extending `DomainEvent` with `event_type = "user.registered"` and `aggregate_id` set to the tenant's UUID. The event SHALL follow the same pattern as `AnimalCreated` in `cattle/domain/events/` — frozen dataclass, `aggregate_id` as constructor parameter, no additional payload fields in Fase 1.

### Scenario: Event created after registration

- GIVEN a user registration completes with tenant_id="tenant-42"
- WHEN `UserRegistered(aggregate_id="tenant-42")` is instantiated
- THEN `event.event_type` is `"user.registered"`
- AND `event.aggregate_id` is `"tenant-42"`

### Scenario: Inherits DomainEvent contract

- GIVEN a `UserRegistered` event
- WHEN inspecting its fields
- THEN `event_id`, `timestamp`, `metadata` are present as defined in the `DomainEvent` base class

## Requirement: RegisterUserCase emits UserRegistered via IEventBus

`RegisterUserCase` MUST accept `IEventBus` and MUST NOT accept `TrialManagementService`. After `uow.commit()` completes and outside the UoW context block, `RegisterUserCase` MUST call `self.event_bus.dispatch(UserRegistered(aggregate_id=tenant.id))`. The system MUST remove the import of `TrialManagementService` and `ITenantRepository` from `register_user_case.py` — `ITenantRepository` SHALL remain in auth (used by the router layer for tenant resolution), but SHALL NOT be imported by the use case.

### Scenario: Event dispatched after successful registration

- GIVEN a user registration succeeds with `uow.commit()` returning
- WHEN `RegisterUserCase.execute` finishes
- THEN `IEventBus.dispatch` is called exactly once with a `UserRegistered` event carrying the tenant ID

### Scenario: No event on registration failure

- GIVEN a registration fails before `uow.commit()` (duplicate email, slug collision)
- WHEN the exception propagates
- THEN `IEventBus.dispatch` is NOT called

### Scenario: No direct billing code in auth

- GIVEN `RegisterUserCase` is constructed
- WHEN inspecting its constructor or imports
- THEN `TrialManagementService` is absent from both auth imports and constructor params
- AND `IEventBus` is the injected mechanism for cross-context notifications
