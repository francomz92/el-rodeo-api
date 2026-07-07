# Tasks: Modularización de Estructura

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 800–1500 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | 5 PRs (F5→F2→F1→F3→F4) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | F5: Pyright config + type fixes | PR 1 | main base; codebase fully type-checked |
| 2 | F2: Unify repos (TenantAware) | PR 2 | main base; tests pass unchanged |
| 3 | F1: Decouple auth↔billing via events | PR 3 | main base; event + handler + wiring |
| 4 | F3: Split large files | PR 4 | main base; 6 files + factories |
| 5 | F4: Registry per context | PR 5 | main base; remove __getattr__ |

## Phase 5: Pyright First

- [x] 5.1 Enable `reportOptionalMemberAccess` + `reportUnusedImport` in `pyrightconfig.json`
- [x] 5.2 Fix type errors across codebase until `uv run pyright` exits zero

## Phase 2: Unify Repositories

- [ ] 2.1 Modify `TenantAwareRepository.__init__` — tolerate `tenant_id=None`, remove ValueError
- [ ] 2.2 Migrate `UserRepository`: `SessionMixin` → `TenantAwareRepository`, pass `tenant_id=None`
- [ ] 2.3 Add `DeprecationWarning` to `SessionMixin.__init__`
- [ ] 2.4 Verify all existing auth/repo tests pass (TDD: contract is unchanged)

## Phase 1: Decouple Auth↔Billing via Events

- [ ] 1.1 Create `auth/domain/events/user_registered.py` with `UserRegistered(DomainEvent)` dataclass
- [ ] 1.2 RED: test `RegisterUserCase` dispatches `UserRegistered` on success via mock IEventBus
- [ ] 1.3 Modify `RegisterUserCase`: inject `IEventBus`, remove `TrialManagementService`, dispatch after commit
- [ ] 1.4 GREEN: verify mock-IEventBus test passes
- [ ] 1.5 Remove `ITenantRepository` from `TrialManagementService`; keep only sub/plan repos
- [ ] 1.6 Create `TrialProvisioningHandler` in `billing/application/events/`
- [ ] 1.7 Wire handler + bus in `auth_dependencies.py` (unidirectional infra import to billing)
- [ ] 1.8 RED: test handler creates trial from event → GREEN: implement `__call__`

## Phase 3: Split Large Files

- [ ] 3.1 Split `billing/_client.py` → `_http.py`, `_signature.py`, `_mappers.py`; thin re-export in `_client.py`
- [ ] 3.2 Split `billing/_billing_tasks.py` → `_monthly_billing_task.py`, `_expire_trials_task.py`; delete original
- [ ] 3.3 Extract mappers from `market/sales.py` → `market/repositories/_mappers.py`
- [ ] 3.4 Extract mappers from `auth/user_repository.py` → `auth/repositories/_mappers.py`
- [ ] 3.5 Extract mappers from `cattle/animal_repository.py` → `cattle/repositories/_mappers.py`
- [ ] 3.6 Split `tests/factories.py` → `tests/factories/{auth,cattle,market,finance}.py` + `__init__.py`

## Phase 4: Registry per Context

- [ ] 4.1 Create context `_registry.py` files (auth, cattle, market, finance, billing)
- [ ] 4.2 Modify `common/repositories/_registry.py` to merge contextual registries
- [ ] 4.3 Remove `__getattr__` from all `*/repositories/__init__.py`; use explicit imports
- [ ] 4.4 Verify UoW resolves every repository type with new registry
