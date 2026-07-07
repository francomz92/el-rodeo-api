# Design: Modularización de Estructura

## Technical Approach

Refactor en 5 fases atómicas. Cada fase produce commits verdes. Sin big bang. Priorizar legibilidad sobre pureza. El acoplamiento real que se ataca es el **bidireccional auth↔billing** (impide testing independiente). El resto es reorganización de archivos y unificación de patrones.

---

## Architecture Decisions

### F1: Auth↔billing vía eventos

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Evento cross-context | + testing independiente, − 1 handler import en infra | ✅ Elegida — acoplamiento bidireccional actual bloquea tests |
| Interfaz compartida en `common/` | + simple, − acoplamiento persiste | ❌ Rechazada — no resuelve testing |
| Singleton bus global | + simple, −副作用 globales | ❌ Rechazada — seguir patrón request-scoped existente |

**Data flow**:
```
RegisterUserCase.execute()
  └─ uow.commit()
       └─ event_bus.dispatch(UserRegistered(aggregate_id=tenant.id))
            └─ TrialProvisioningHandler (billing)
                 └─ TrialManagementService.start_trial(tenant_id)
```

Handler registration: Auth DI crea bus, registra handler billing (import unidireccional en infra wiring).

### F2: Unificar repositorios

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Migrar UserRepository a TenantAware | + patrón único, − login bypass | ✅ Elegida — `_filter_tenant` no-op si tenant_id es None |
| Mantener SessionMixin | + 0 cambios, − 2 patrones conviven | ❌ Rechazada |
| Crear AuthBaseRepository | + explícito, − overengineering | ❌ Rechazada |

**Repos a migrar**: solo `UserRepository` (único con `tenant_id`). Los otros quedan en SessionMixin con deprecation warning.

### F3: División archivos grandes

| Archivo (L) | Split | Resultado |
|-------------|-------|-----------|
| `_client.py` (293) | HTTP/retry, signature, mappers | `_client.py` (~120) + `_http.py` (~80) + `_signature.py` (~60) + `_mappers.py` (~30) |
| `_billing_tasks.py` (255) | Una tarea por archivo | `_monthly_billing_task.py` (~120) + `_expire_trials_task.py` (~110) |
| `sales.py` (232) | Builders a mapper | `sales.py` (~160) + `_mappers.py` (~70) |
| `user_repository.py` (230) | _json_safe, _build_user | `user_repository.py` (~180) + `_mappers.py` (~30) |
| `animal_repository.py` (221) | _build_animal a mapper | `animal_repository.py` (~180) + `_mappers.py` (~40) |
| `tests/factories.py` (473) | Por contexto | `tests/factories/{auth,cattle,market,finance}.py` + `__init__.py` re-exports |

### F4: Registry por contexto

Cada contexto expone su `_registry.py`. El central mergea dicts. Se elimina `__getattr__` en los `__init__.py`.

### F5: Pyright

Config actual: `typeCheckingMode: "basic"`. Se mantiene + se habilitan `reportOptionalMemberAccess: "error"` y `reportUnusedImport: "error"`. Strict fuera de scope.

---

## File Changes

| Fase | File | Acción | Descripción |
|------|------|--------|-------------|
| F1 | `src/auth/domain/events/user_registered.py` | Create | UserRegistered event |
| F1 | `src/auth/.../register_user_case.py` | Modify | IEventBus inyectado, TrialManagementService eliminado |
| F1 | `src/auth/.../auth_dependencies.py` | Modify | IEventBus + handler billing |
| F1 | `src/billing/application/events/__init__.py` | Create | TrialProvisioningHandler |
| F1 | `src/billing/.../_trial_management_service.py` | Modify | Sin ITenantRepository |
| F2 | `src/common/.../tenant_aware_repository.py` | Modify | Constructor tolera tenant_id=None |
| F2 | `src/auth/.../user_repository.py` | Modify | SessionMixin → TenantAwareRepository |
| F2 | `src/common/.../mixins.py` | Modify | DeprecationWarning en SessionMixin |
| F3 | `src/billing/.../_http.py` | Create | _request con retry |
| F3 | `src/billing/.../_signature.py` | Create | validate_signature |
| F3 | `src/billing/.../_mappers.py` | Create | MP mappers |
| F3 | `src/billing/.../_monthly_billing_task.py` | Create | Task extraída |
| F3 | `src/billing/.../_expire_trials_task.py` | Create | Task extraída |
| F3 | `src/billing/.../_billing_tasks.py` | Delete | Reemplazado |
| F3 | `src/{market,auth,cattle}/.../repositories/_mappers.py` | Create | Build methods extraídos |
| F3 | `tests/factories/` | Create | auth, cattle, market, finance |
| F4 | `src/*/.../repositories/_registry.py` | Create | Registry por contexto |
| F4 | `src/common/.../repositories/_registry.py` | Modify | Merge contextual |
| F4 | `src/*/.../repositories/__init__.py` | Modify | Eliminar __getattr__ |
| F5 | `pyrightconfig.json` | Modify | reports adicionales |

---

## Interfaces / Contracts

```python
class UserRegistered(DomainEvent):
    def __init__(self, aggregate_id: UUID, **kwargs) -> None:
        super().__init__(event_type="user.registered", aggregate_id=aggregate_id, **kwargs)

class TrialProvisioningHandler:
    def __init__(self, plan_repo: IPlanRepository, sub_repo: ISubscriptionRepository) -> None: ...
    def __call__(self, event: DomainEvent) -> None: ...
```

TenantAwareRepository modificado: sin ValueError si tenant_id es None.

---

## Testing Strategy

| Fase | Scope | Approach |
|------|-------|----------|
| F1 | RegisterUserCase | Mock IEventBus, verificar dispatch |
| F1 | TrialManagementService | Sin ITenantRepository, mock sub/plan |
| F1 | TrialProvisioningHandler | Unit, verificar start_trial |
| F2 | UserRepository TenantAware | Tests existentes sin cambios |
| F3 | Archivos divididos | Mismos tests, imports actualizados |
| F4 | Registry merge | UoW.get_repository con cada tipo |
| F5 | Pyright | `uv run pyright` sin errores |

---

## Migration / Rollout

No migration de datos. Orden commits: F5 → F2 → F1 → F3 → F4. Cada fase es commit independiente y reversible.

---

## Open Questions

- [ ] `TenantRepository.update(plan_id)` tiene otros consumidores además de TrialManagementService? Si no, eliminar — subscription como fuente de verdad.
- [ ] Verificar imports de `RefreshTokenRepository` — hay consumidores que usan `from ...repositories import RefreshTokenRepository`?
