# Delta for auth

## ADDED Requirements

### Requirement: UserRegistered domain event

The system MUST define a `UserRegistered` domain event class extending `DomainEvent` with `event_type = "user.registered"` and `aggregate_id` set to the tenant's UUID. The event SHALL follow the same pattern as `AnimalCreated` in `cattle/domain/events/` — frozen dataclass, `aggregate_id` as constructor parameter, no additional payload fields in Fase 1.

#### Scenario: Event created after registration

- GIVEN a user registration completes with tenant_id="tenant-42"
- WHEN `UserRegistered(aggregate_id="tenant-42")` is instantiated
- THEN `event.event_type` is `"user.registered"`
- AND `event.aggregate_id` is `"tenant-42"`

#### Scenario: Inherits DomainEvent contract

- GIVEN a `UserRegistered` event
- WHEN inspecting its fields
- THEN `event_id`, `timestamp`, `metadata` are present as defined in the `DomainEvent` base class

### Requirement: RegisterUserCase emits UserRegistered via IEventBus

`RegisterUserCase` MUST accept `IEventBus` and MUST NOT accept `TrialManagementService`. After `uow.commit()` completes and outside the UoW context block, `RegisterUserCase` MUST call `self.event_bus.dispatch(UserRegistered(aggregate_id=tenant.id))`. The system MUST remove the import of `TrialManagementService` and `ITenantRepository` from `register_user_case.py` — `ITenantRepository` SHALL remain in auth (used by the router layer for tenant resolution), but SHALL NOT be imported by the use case.

#### Scenario: Event dispatched after successful registration

- GIVEN a user registration succeeds with `uow.commit()` returning
- WHEN `RegisterUserCase.execute` finishes
- THEN `IEventBus.dispatch` is called exactly once with a `UserRegistered` event carrying the tenant ID

#### Scenario: No event on registration failure

- GIVEN a registration fails before `uow.commit()` (duplicate email, slug collision)
- WHEN the exception propagates
- THEN `IEventBus.dispatch` is NOT called

#### Scenario: No direct billing code in auth

- GIVEN `RegisterUserCase` is constructed
- WHEN inspecting its constructor or imports
- THEN `TrialManagementService` is absent from both auth imports and constructor params
- AND `IEventBus` is the injected mechanism for cross-context notifications


