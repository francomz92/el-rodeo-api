# Billing — Quota Enforcement Specification

## Purpose

Defines quota checking at the application boundary — prevents write operations when a tenant exceeds their plan's resource limits.

## Requirements

### Requirement: QuotaExceededException

The system MUST define `QuotaExceededException` extending `DomainError` with `error_code = "quota_exceeded_error"`. The Literal `ErrorCode` in errors.py MUST include `"quota_exceeded_error"`.

#### Scenario: Quota breach raises exception

- GIVEN a tenant on FREE plan with 50 animals already registered
- WHEN a user tries to register the 51st animal
- THEN `QuotaEnforcementService.check_quota` raises `QuotaExceededException`
- AND the error message includes the resource name and current limit

### Requirement: QuotaEnforcementService

The system MUST define `QuotaEnforcementService` with method: `check_quota(tenant_id, resource_name, delta=1) -> bool`. It MUST accept `ISubscriptionRepository` and `IPlanRepository` as dependencies.

#### Scenario: Quota check passes within limits

- GIVEN a tenant on FREE plan with 30 animals registered
- WHEN `check_quota(tenant_id, "animals", delta=1)` is called
- THEN it returns True

#### Scenario: Quota check with delta exceeding limit

- GIVEN a tenant on FREE plan with 49 animals registered
- WHEN `check_quota(tenant_id, "animals", delta=5)` is called
- THEN it raises `QuotaExceededException`

#### Scenario: Unlimited quota passes for any delta

- GIVEN an ENTERPRISE tenant (limit=-1)
- WHEN `check_quota(tenant_id, "animals", delta=999)` is called
- THEN it returns True

### Requirement: Used counts via subscription metadata

For Phase 7.1, used counts MUST be stored in subscription.metadata as a JSON dict. The service reads current usage from metadata, increments the delta, and compares against plan quotas.

#### Scenario: Used count in metadata

- GIVEN a subscription with `metadata = {"animals": 30}`
- WHEN `check_quota(tenant_id, "animals")` is called
- THEN the service reads 30 from metadata, adds 1, and compares against the FREE plan limit of 50

### Requirement: Configurable enforcement

The system SHOULD allow per-operation opt-out of quota enforcement via a `skip_quota_check` parameter or configuration flag. This is needed for admin/internal operations.

#### Scenario: Admin bypasses quota check

- GIVEN an internal operation with `skip_quota_check=True`
- WHEN the operation proceeds
- THEN `QuotaEnforcementService` is not called

### Error Code Extension

The `ErrorCode` Literal in `src/common/domain/entities/errors.py` MUST be extended to include `"quota_exceeded_error"`.
