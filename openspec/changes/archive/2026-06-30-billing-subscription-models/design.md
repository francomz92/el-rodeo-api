# Design: Billing — Subscription Models (Phase 7.1)

## Technical Approach

New `src/billing/` bounded context following the project's Clean Architecture layout (domain → application → infrastructure). Seed data for plans lives in-memory in the repository impl. Subscription is the runtime entity linking tenant → plan. Quota enforcement is a domain service that reads usage from subscription metadata and compares against plan limits. Registration hook injects `TrialManagementService` into `RegisterUserCase`.

## Architecture Decisions

### Decision: Plan seed data storage
| Option | Tradeoff | Decision |
|--------|----------|----------|
| JSON/CSV file | Externalizes config, needs loader | **In-code dict** in `_plan_repository.py` |
| In-code dict | Simple, no extra I/O, follows enum-like pattern | ✅ Chosen |

**Rationale**: Plans are immutable seed data. An in-code dict keeps them close to the domain, matches the "enum-like" intent. JSON adds parsing complexity for zero benefit at this scale.

### Decision: Usage tracking storage
| Option | Tradeoff | Decision |
|--------|----------|----------|
| Dedicated usage table | Normalized, queryable, more schema | **JSON metadata column** on subscriptions |
| JSON metadata | Simple phase-1, no extra table, limited query | ✅ Chosen |

**Rationale**: Spec requires Phase 7.1 to use `subscription.metadata` JSON dict. Dedicated table is a future extraction when metering needs queries.

### Decision: Quota enforcement pattern
| Option | Tradeoff | Decision |
|--------|----------|----------|
| Raises exception | Forces handler at call site, clear error path | ✅ Chosen: raises `QuotaExceededException` |
| Returns bool | Caller can ignore, silent failure risk | ❌ Rejected |

**Rationale**: The spec scenarios require exception on breach. The service has a `skip_quota_check` flag for admin bypass.

### Decision: Tenant plan_id mutation
| Option | Tradeoff | Decision |
|--------|----------|----------|
| Update via subscription service | Single responsibility, explicit | ✅ Chosen |
| Auto-sync via DB trigger | Hidden, harder to debug | ❌ Rejected |

**Rationale**: `TrialManagementService.start_trial()` updates `tenant.plan_id` after creating the subscription. Explicit orchestration in the service method.

## Data Flow

```
Registration flow:
  RegisterUserCase.execute()
    → tenant_repo.create()                     # Creates tenant (plan_id = None)
    → trial_service.start_trial(tenant.id)     # Creates subscription, sets plan_id
    → user_repo.create()
    → commit

Quota enforcement flow:
  QuotaEnforcementService.check_quota(tenant_id, resource, delta)
    → subscription_repo.get_by_tenant(tenant_id)    # Get sub + metadata
    → plan_repo.get_by_id(sub.plan_id)              # Get plan quotas
    → read current_usage from sub.metadata[resource]
    → if current + delta > plan.limit → raise QuotaExceededException
    → return True
```

## File Changes

### New files (23)
| File | Description |
|------|-------------|
| `src/billing/__init__.py` | Package init |
| `src/billing/domain/__init__.py` | Domain package init |
| `src/billing/domain/entities/__init__.py` | Entity exports |
| `src/billing/domain/entities/_plan.py` | Plan dataclass, PlanType(StrEnum) |
| `src/billing/domain/entities/_subscription.py` | Subscription dataclass, SubscriptionStatus(StrEnum) |
| `src/billing/domain/entities/_feature.py` | Feature VO dataclass |
| `src/billing/domain/entities/_quota.py` | Quota VO dataclass |
| `src/billing/domain/value_objects/__init__.py` | VOs init |
| `src/billing/domain/value_objects/_money.py` | Money value object (amount: Decimal, currency: str) |
| `src/billing/domain/repositories/__init__.py` | Ports init |
| `src/billing/domain/repositories/_plan_repository_port.py` | IPlanRepository (get_default, get_by_name, list_all) |
| `src/billing/domain/repositories/_subscription_repository_port.py` | ISubscriptionRepository (get_by_tenant, save, list_expired_trials) |
| `src/billing/application/__init__.py` | App init |
| `src/billing/application/services/__init__.py` | Services init |
| `src/billing/application/services/_trial_management_service.py` | start_trial, start_trial_for_existing (for migration) |
| `src/billing/application/services/_quota_enforcement_service.py` | check_quota with skip_quota_check flag |
| `src/billing/application/ports/__init__.py` | Ports init |
| `src/billing/infrastructure/__init__.py` | Infra init |
| `src/billing/infrastructure/persistence/__init__.py` | Persistence init |
| `src/billing/infrastructure/persistence/models/__init__.py` | Models init + imports |
| `src/billing/infrastructure/persistence/models/_plan_model.py` | Plan SQLAlchemy model (id, name, features JSON, quotas JSON, prices) |
| `src/billing/infrastructure/persistence/models/_subscription_model.py` | Subscription model (tenant_id FK, plan_id FK, status, dates, metadata JSON) |
| `src/billing/infrastructure/persistence/repositories/__init__.py` | Repos init |
| `src/billing/infrastructure/persistence/repositories/_plan_repository.py` | SQLPlanRepository (seed data dict, reads from DB) |
| `src/billing/infrastructure/persistence/repositories/_subscription_repository.py` | SQLSubscriptionRepository |
| `src/billing/infrastructure/presentation/dependencies/__init__.py` | DI init |
| `src/billing/infrastructure/presentation/dependencies/_billing_dependencies.py` | FastAPI dependency wiring |

### Modified files (4)
| File | Change |
|------|--------|
| `src/auth/domain/entities/_tenant_entity.py` | Add `plan_id: UUID \| None = None` field |
| `src/auth/infrastructure/persistence/models/_tenant_model.py` | Add `plan_id: Mapped[UUID] = mapped_column(ForeignKey("plans.id"), nullable=True)` |
| `src/auth/application/uses_cases/register_user_case.py` | Inject `TrialManagementService`, call `start_trial(tenant.id)` after tenant creation |
| `src/common/domain/entities/errors.py` | Add `"quota_exceeded_error"` to `ErrorCode` Literal |

### Migration
| File | Description |
|------|-------------|
| `alembic/versions/xxxx_add_billing_models.py` | Create plans + subscriptions tables, add plan_id to tenants, seed plans, backfill FREE subscriptions for existing tenants |

## Interfaces / Contracts

```python
# Plan repository port
class IPlanRepository(IRepository):
    async def get_default(self) -> Plan: ...
    async def get_by_name(self, name: str) -> Plan | None: ...
    async def list_all(self) -> list[Plan]: ...

# Subscription repository port
class ISubscriptionRepository(IRepository):
    async def get_by_tenant(self, tenant_id: UUID) -> Subscription | None: ...
    async def save(self, subscription: Subscription) -> Subscription: ...
    async def list_expired_trials(self) -> list[Subscription]: ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Plan/Subscription/Feature/Quota dataclasses | Instantiate and assert field types |
| Unit | QuotaEnforcementService.check_quota boundary conditions | Mock repos, test edge cases |
| Unit | TrialManagementService.start_trial lifecycle | Mock repos, test status/side effects |
| Unit | Subscription status transitions | Pure dataclass tests |
| Integration | Repository CRUD (save, get_by_tenant, list_all) | Test DB with fixtures |
| Integration | Migration up/down | Alembic test with postgres |
| E2E | Registration creates PRO trial | Full registration flow via test client |
| E2E | Quota enforcement via use case | Create tenant on FREE, exceed limit |

## Migration / Rollout

**Migration file**:
1. Create `plans` table — seed FREE, PRO, ENTERPRISE with features/quotas
2. Create `subscriptions` table — tenant_id FK, plan_id FK, status, dates, metadata JSON
3. `ALTER TABLE tenants ADD COLUMN plan_id UUID REFERENCES plans(id)`
4. Backfill: for each existing tenant, create FREE subscription, set `tenant.plan_id` to FREE plan ID

**No feature flags** required — Phase 7.1 is purely additive (new entities, new services). New registrations get PRO trial; existing tenants remain on FREE.

## Open Questions

- [ ] None — spec, proposal, and codebase patterns align without ambiguity
