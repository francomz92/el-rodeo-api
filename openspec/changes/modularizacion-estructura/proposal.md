# Proposal: Modularización de Estructura

## Intent

Reducir acoplamiento entre bounded contexts y mejorar mantenibilidad dividiendo archivos grandes. Sin dogmatismo: priorizar legibilidad sobre pureza hexagonal.

## Scope

### In Scope
- Dividir 6 archivos >200 líneas + `tests/factories.py` (473 → por contexto)
- Desacoplar auth↔billing (acoplamiento bidireccional)
- Unificar patrón de repositorios (`TenantAwareRepository` como estándar, `SessionMixin` deprecado)
- Simplificar registry de repositorios (eliminar `__getattr__` para dependencias circulares)
- Activar pyright (ya en dev-deps) y corregir type errors
- Corregir bugs encontrados durante el refactor
- Mejorar schemas de API donde simplifique el código

### Out of Scope
- Reemplazar entidades externas por UUIDs donde el import directo sea más legible
- Eventos de dominio forzados donde un import simple basta
- Desacoplar contextos naturalmente relacionados (cattle↔auth via `user_id` se mantiene)
- Migración a microservicios o comunicación asíncrona
- Cambios en schema de base de datos

## Capabilities

### New Capabilities
- None — refactor estructural, sin nuevas capacidades de producto

### Modified Capabilities
- `auth` — `RegisterUserCase` emite evento en lugar de llamar a `TrialManagementService` (billing)
- `billing/quota-enforcement` — consume evento en lugar de depender de `ITenantRepository` (auth)

## Approach

Estrategia híbrida por fases (Approach 4 de exploration):

1. **Desacoplar auth↔billing**: `RegisterUserCase` emite evento → billing consume por event bus
2. **Unificar repositorios**: `TenantAwareRepository` como estándar, migrar `SessionMixin` existentes
3. **Dividir archivos grandes**: 6 archivos + `factories.py` por contexto
4. **Limpiar registry**: registry por contexto, eliminar `__getattr__`
5. **Activar pyright** + corregir type errors detectados
6. **Bug fixes + schema improvements**: durante todo el proceso, commit por fase

## Affected Areas

| Area | Impact | Descripción |
|------|--------|-------------|
| `src/auth/application/uses_cases/register_user_case.py` | Modified | Sin dependencia a billing |
| `src/billing/application/services/_trial_management_service.py` | Modified | Sin depender de auth repositories |
| `src/common/infrastructure/repositories/_registry.py` | Modified | Registry por contexto |
| `src/*/infrastructure/repositories/*.py` | Modified | Unificar patrón |
| 6 archivos >200 líneas en `src/` | Modified | Split por responsabilidad |
| `tests/factories.py` | Modified | Split por contexto |

## Risks

| Risk | Likelihood | Mitigación |
|------|------------|------------|
| Tests rojos durante refactor | Med | Fases atómicas, cada una mantiene tests verdes |
| Registry circular al separar | Bajo | Mantener `__getattr__` como fallback temporal |
| Perder lazy loading SQLAlchemy | Bajo | Joins explícitos donde se necesiten |

## Rollback Plan

Por cada fase: commit atómico. Rollback = revertir el commit de la fase. No hay big bang — el repo siempre está en estado funcional.

## Dependencies

- pyright (ya en dev-deps)
- Sistema de eventos de dominio (ya existe: `IEventBus`, `DomainEvent`, outbox)

## Success Criteria

- [ ] `auth` y `billing` pueden testearse sin importarse mutuamente
- [ ] Archivos >200 líneas en white-list han sido divididos
- [ ] `factories.py` separado por contexto
- [ ] Registry de repositorios sin `__getattr__`
- [ ] pyright pasa sin errores
- [ ] 274 tests verdes
- [ ] Todos los repositorios siguen mismo patrón base
