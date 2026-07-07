# Proposal: Billing — Subscription Models (Phase 7.1)

## Intent

Foundation for SaaS monetization. Tenants currently have zero billing data — no plan, subscription, or quotas. This phase introduces domain models, repository ports, and enforcement primitives to differentiate FREE vs PRO vs ENTERPRISE tenants without wiring payments yet.

## Scope

### In Scope
- New `billing/` bounded context (domain → application → infrastructure)
- `Plan` entity with seed data: FREE, PRO, ENTERPRISE
- `Subscription` entity: tenant_id, plan_id, status (trial/active/canceled/expired), start/end dates, trial_end
- `Feature` / `Quota` value objects
- Repository ports: `IPlanRepository`, `ISubscriptionRepository`
- Domain services: `TrialManagementService`, `QuotaEnforcementService`
- `QuotaExceededException` (extends `DomainError`)
- Migration: plans + subscriptions tables, plan_id on tenants
- Hook `RegisterUserCase` to auto-create 14-day PRO trial on signup

### Out of Scope
- Payment gateway integration (MercadoPago/Stripe — Phase 7.2)
- Webhooks, invoicing, usage metering
- Plan CRUD UI or admin endpoints
- Stripe/MercadoPago SDK installation

## Capabilities

### New Capabilities
- `billing/plan`: Plan entity, Feature/Quota VOs, `IPlanRepository`, seed data
- `billing/subscription`: Subscription entity, `ISubscriptionRepository`, status lifecycle, `TrialManagementService`
- `billing/quota-enforcement`: `QuotaEnforcementService`, `QuotaExceededException`, enforcement decorator/middleware

### Modified Capabilities
None — no existing specs change. Tenant migration is implementation detail.

## Approach

Clean Architecture in `src/billing/`:
- **Domain**: `entities/` (Plan, Subscription), `value_objects/` (Feature, Quota), `services/` (TrialManagement, QuotaEnforcement), `repositories/` (IPlanRepository, ISubscriptionRepository), `exceptions.py`
- **Application**: use cases for subscription lifecycle, quota checks
- **Infrastructure**: SQLAlchemy models, Alembic migration, repository impls
- Plans as seed data (enum-like, in-code + migration loader)
- `RegisterUserCase` injects `TrialManagementService` to auto-create trial subscription
- Quota enforcement at application boundary (service decorator or middleware)

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/billing/` | New | Full bounded context |
| `src/auth/domain/entities/_tenant_entity.py` | Modified | Add plan_id |
| `src/auth/application/uses_cases/register_user_case.py` | Modified | Inject TrialManagementService |
| `alembic/versions/` | New | Plans + subscriptions + plan_id migration |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Migration conflicts with existing tenants | Low | Default FREE plan for all existing tenants |
| Plan seed drift between envs | Low | Seed in migration + startup assertion |
| Quota enforcement latency | Low | Enforce at write-boundary only |

## Rollback Plan

1. `alembic downgrade -1`
2. Delete `src/billing/`
3. Revert `RegisterUserCase` and `TenantEntity` changes

## Dependencies

- Existing UoW / repository / Alembic patterns (all established)

## Success Criteria

- [ ] Plans table seeded with FREE, PRO, ENTERPRISE
- [ ] Subscriptions table created with tenant FK
- [ ] New registration auto-creates 14-day PRO trial subscription
- [ ] `QuotaEnforcementService` raises `QuotaExceededException` on limit breach
- [ ] Existing tests pass — zero regression
