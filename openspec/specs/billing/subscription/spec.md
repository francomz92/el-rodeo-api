# Billing — Subscription Specification

## Purpose

Defines the Subscription entity, lifecycle management, trial provisioning, and the tenant-plan denormalization for fast reads.

## Requirements

### Requirement: Subscription entity

The system MUST define a Subscription dataclass with: `id: UUID`, `tenant_id: UUID`, `plan_id: UUID`, `status: SubscriptionStatus`, `current_period_start: datetime`, `current_period_end: datetime`, `trial_end: datetime | None`, `canceled_at: datetime | None`, `mp_preference_id: str | None`, `mp_subscription_id: str | None`.

#### Scenario: Create new subscription

- GIVEN a tenant has registered
- WHEN `TrialManagementService.start_trial(tenant_id)` is called
- THEN a Subscription is created with status=TRIAL and trial_end=14 days from now

#### Scenario: Trial expiry transitions to EXPIRED, tenant falls to FREE

- GIVEN a subscription with status=TRIAL
- WHEN trial_end is past due and no payment has been received
- THEN the subscription status is set to EXPIRED
- AND the tenant's `plan_id` is set to FREE (read-only grace state)

#### Scenario: Past-due recovery

- GIVEN a subscription with status=PAST_DUE
- WHEN a new approved payment is received
- THEN status returns to ACTIVE
- AND the subscription is reactivated

### Requirement: MercadoPago identifiers on Subscription

The system MUST extend the Subscription entity with `mp_preference_id: str | None` and `mp_subscription_id: str | None`. These store the most recent MP checkout preference and subscription identifiers for payment lifecycle tracking.

#### Scenario: Preference stored after checkout creation

- GIVEN a new MP checkout preference is created for a subscription
- WHEN `create_checkout_preference` completes successfully
- THEN `subscription.mp_preference_id` is set to the new preference ID

#### Scenario: Payment approved stores mp_subscription_id

- GIVEN an approved payment via IPN
- WHEN the payment includes a `mp_subscription_id`
- THEN the subscription's `mp_subscription_id` is updated

### Requirement: SubscriptionStatus enum

The system MUST define `SubscriptionStatus` as a StrEnum with values: `TRIAL`, `ACTIVE`, `CANCELED`, `EXPIRED`, `PAST_DUE`. The status lifecycle MUST be: TRIAL → ACTIVE → {CANCELED, EXPIRED, PAST_DUE}.

#### Scenario: Past-due recovery

- GIVEN a subscription with status=PAST_DUE
- WHEN payment is received
- THEN status returns to ACTIVE

### Requirement: ISubscriptionRepository port

The system MUST define `ISubscriptionRepository` with: `get_by_tenant(tenant_id) -> Subscription | None`, `save(subscription) -> Subscription`, `list_expired_trials() -> list[Subscription]`, `list_active_near_period_end(days_ahead: int) -> list[Subscription]`. All methods are async.

#### Scenario: Find subscription by tenant

- GIVEN a tenant with an active subscription
- WHEN `get_by_tenant(tenant_id)` is called
- THEN the correct Subscription is returned

#### Scenario: Active subscriptions near period end

- GIVEN 3 ACTIVE subscriptions — one ending in 2 days, two ending in 10 days
- WHEN `list_active_near_period_end(5)` is called
- THEN only the subscription ending in 2 days is returned

### Requirement: Registration hook for trial creation

The system MUST create a 14-day PRO trial Subscription when a new tenant registers. `RegisterUserCase` MUST call `TrialManagementService.start_trial(tenant_id)` after tenant creation.

#### Scenario: New registration creates PRO trial

- GIVEN a user completes registration
- WHEN the tenant is created
- THEN `TrialManagementService.start_trial` creates a PRO subscription with 14-day trial
- AND the tenant's `plan_id` is set to PRO
- AND no MP checkout preference is created (trial is free)

#### Scenario: Trial expires without payment → FREE grace state

- GIVEN a PRO trial subscription whose trial_end has passed
- WHEN `expire_trials_task` Celery task runs
- THEN subscription status becomes EXPIRED
- AND tenant plan_id is set to FREE
- AND the tenant can only READ data (no creates/updates)

#### Scenario: Existing tenant without subscription defaults to FREE

- GIVEN a tenant existed before this feature
- WHEN the migration runs
- THEN a FREE subscription is created for that tenant
- AND the tenant's `plan_id` is set to FREE

### Requirement: Tenant plan_id denormalization

The tenents table MUST include a `plan_id` FK column. This is the current effective plan, updated on subscription changes for fast read-side access. The plan_id SHALL be updated on: trial creation (→ PRO), plan change (→ PRO/ENTERPRISE), and trial expiry (→ FREE).

#### Scenario: Trial expiry updates tenant plan

- GIVEN a tenant with plan_id=PRO whose trial expired
- WHEN the expire_trials_task runs
- THEN `tenant.plan_id` is set to FREE

#### Scenario: Plan change updates tenant

- GIVEN a tenant's subscription changes from PRO to ENTERPRISE
- WHEN the subscription is updated
- THEN `tenant.plan_id` reflects the new plan
