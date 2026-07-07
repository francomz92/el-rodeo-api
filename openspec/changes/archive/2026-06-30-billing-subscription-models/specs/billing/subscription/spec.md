# Billing — Subscription Specification

## Purpose

Defines the Subscription entity, lifecycle management, trial provisioning, and the tenant-plan denormalization for fast reads.

## Requirements

### Requirement: Subscription entity

The system MUST define a Subscription dataclass with: `id: UUID`, `tenant_id: UUID`, `plan_id: UUID`, `status: SubscriptionStatus`, `current_period_start: datetime`, `current_period_end: datetime`, `trial_end: datetime | None`, `canceled_at: datetime | None`.

#### Scenario: Create new subscription

- GIVEN a tenant has registered
- WHEN `TrialManagementService.start_trial(tenant_id)` is called
- THEN a Subscription is created with status=TRIAL and trial_end=14 days from now

#### Scenario: Subscription status transitions

- GIVEN a subscription with status=TRIAL
- WHEN trial_end is past due and no payment method is configured
- THEN the subscription status is set to EXPIRED

### Requirement: SubscriptionStatus enum

The system MUST define `SubscriptionStatus` as a StrEnum with values: `TRIAL`, `ACTIVE`, `CANCELED`, `EXPIRED`, `PAST_DUE`. The status lifecycle MUST be: TRIAL → ACTIVE → {CANCELED, EXPIRED, PAST_DUE}.

#### Scenario: Past-due recovery

- GIVEN a subscription with status=PAST_DUE
- WHEN payment is received
- THEN status returns to ACTIVE

### Requirement: ISubscriptionRepository port

The system MUST define `ISubscriptionRepository` with: `get_by_tenant(tenant_id) -> Subscription | None`, `save(subscription) -> Subscription`, `list_expired_trials() -> list[Subscription]`. All methods are async.

#### Scenario: Find subscription by tenant

- GIVEN a tenant with an active subscription
- WHEN `get_by_tenant(tenant_id)` is called
- THEN the correct Subscription is returned

### Requirement: Registration hook for trial creation

The system MUST create a 14-day PRO trial Subscription when a new tenant registers. `RegisterUserCase` MUST call `TrialManagementService.start_trial(tenant_id)` after tenant creation.

#### Scenario: New registration creates PRO trial

- GIVEN a user completes registration
- WHEN the tenant is created
- THEN `TrialManagementService.start_trial` creates a PRO subscription with 14-day trial
- AND the tenant's `plan_id` is set to PRO

#### Scenario: Existing tenant without subscription defaults to FREE

- GIVEN a tenant existed before this feature
- WHEN the migration runs
- THEN a FREE subscription is created for that tenant
- AND the tenant's `plan_id` is set to FREE

### Requirement: Tenant plan_id denormalization

The tenents table MUST include a `plan_id` FK column. This is the current effective plan, updated on subscription changes for fast read-side access.

#### Scenario: Plan change updates tenant

- GIVEN a tenant's subscription changes from FREE to PRO
- WHEN the subscription is updated
- THEN `tenant.plan_id` reflects the new plan
