# Tasks: Billing — Subscription Models (Phase 7.1)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~750–850 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Domain) → PR 2 (Persistence) → PR 3 (Services + Wiring) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Base | Notes |
|------|------|-----------|------|-------|
| 1 | Domain entities, VOs, ports, exceptions | PR 1 | main | Tests included |
| 2 | Models, repos, migration, registry | PR 2 | PR 1 branch | Tests included |
| 3 | App services, tenant wiring, registration hook | PR 3 | PR 2 branch | Tests included |

## Phase 1: Domain Foundation

- [x] 1.1 Create `src/billing/domain/entities/` — PlanType, Feature, Quota, Plan, SubscriptionStatus, Subscription dataclasses
- [x] 1.2 Create `src/billing/domain/value_objects/_money.py` — Money(amount: Decimal, currency: str)
- [x] 1.3 Create `src/billing/domain/repositories/` — IPlanRepository, ISubscriptionRepository ports
- [x] 1.4 Create `src/billing/domain/exceptions.py` — QuotaExceededException
- [x] 1.5 Add `"quota_exceeded_error"` to ErrorCode Literal in `src/common/domain/entities/errors.py`

## Phase 2: Persistence (PR 2 complete)

- [x] 2.1 Create `src/billing/infrastructure/persistence/models/` — PlanModel + SubscriptionModel (SQLAlchemy)
- [x] 2.2 Create `src/billing/infrastructure/persistence/repositories/` — PlanRepository + SubscriptionRepository
- [x] 2.3 Create Alembic migration — plans (seed FREE/PRO/ENTERPRISE), subscriptions, plan_id on tenants, backfill
- [x] 2.4 Register models in `alembic/env.py`; update Tenant model with plan_id

## Phase 3: Application Services + Wiring

- [x] 3.1 Create `TrialManagementService` — start_trial(tenant_id, plan_type=PRO), start_trial_for_existing
- [x] 3.2 Create `QuotaEnforcementService` — check_quota(tenant_id, resource, delta), skip_quota_check flag
- [x] 3.3 Extend `TenantEntity` + `TenantModel` — add plan_id: UUID | None FK, update repository builder (TenantModel only — TenantEntity deferred to PR 3)
- [x] 3.4 Wire trial creation into `RegisterUserCase` — inject TrialManagementService, call after tenant_create

## Phase 4: Tests

- [x] 4.1 Unit tests for domain entities — Plan, Subscription, Feature, Quota, Money, enums
- [x] 4.2 Unit tests for TrialManagementService — start_trial creates TRIAL sub with 14-day period
- [x] 4.3 Unit tests for QuotaEnforcementService — passes within limit, raises on breach, unlimited(-1) passes, admin bypass
- [x] 4.4 Unit tests for registration hook — tenant gets PRO trial after register
- [x] 4.5 Integration tests for repositories — save/get_by_tenant/list_expired_trials/list_all
