# Delta for billing/quota-enforcement

## ADDED Requirements

### Requirement: Trial provisioning on UserRegistered event

The billing/quota-enforcement capability MUST register a handler for the `"user.registered"` event type that provisions a 14-day PRO trial subscription. The handler SHALL depend only on billing-layer ports (`ISubscriptionRepository`, `IPlanRepository`) and SHALL NOT import `ITenantRepository` from auth.

(Previously: trial creation was triggered by `RegisterUserCase` calling `TrialManagementService.start_trial()` directly — a synchronous cross-context call from auth into billing.)

#### Scenario: Handler creates trial from event

- GIVEN a `UserRegistered` event is dispatched with `aggregate_id="tenant-42"`
- WHEN the `"user.registered"` handler executes
- THEN `TrialManagementService.start_trial(tenant_id="tenant-42")` is called
- AND a PRO trial subscription (14 days) is created for tenant "tenant-42"

#### Scenario: Multiple registrations handled independently

- GIVEN two `UserRegistered` events for tenants "t1" and "t2"
- WHEN both handlers execute
- THEN each tenant gets its own PRO trial subscription
- AND the two operations do not interfere

#### Scenario: No auth imports in billing handler

- GIVEN the event handler module
- WHEN inspecting its imports
- THEN `ITenantRepository` or any `src.auth.*` import is NOT present
- AND the handler receives `tenant_id` exclusively from the event payload

### Requirement: TrialManagementService decoupled from ITenantRepository

`TrialManagementService` MUST accept only `ISubscriptionRepository` and `IPlanRepository` as dependencies. The `ITenantRepository` parameter SHALL be removed. The tenant `plan_id` denormalization (previously done inside `start_trial`) SHALL be handled by a subscription event or removed — the subscription entity becomes the authority for the tenant's plan during trial provisioning.

#### Scenario: start_trial creates subscription without tenant update

- GIVEN `start_trial(tenant_id="tenant-42")` is called
- WHEN the method executes
- THEN a `Subscription` with status=TRIAL and plan=PRO is persisted
- AND no call to `ITenantRepository.update()` is made

#### Scenario: Existing handlers unaffected

- GIVEN `QuotaEnforcementService.check_quota` is called
- WHEN the quota check evaluates limits
- THEN existing quota enforcement behavior is unchanged
- AND `ISubscriptionRepository` usage remains the same


