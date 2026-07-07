## Exploration: Modularización y Separación de Responsabilidades

### Current State

El proyecto tiene **5 bounded contexts** (`auth`, `cattle`, `finance`, `market`, `billing`) más un módulo `common` compartido. Cada contexto implementa la arquitectura hexagonal con 3 capas: `domain/`, `application/`, `infrastructure/`. La estructura es consistente en todos los contextos:

```
src/{context}/
├── domain/
│   ├── entities/         ← Entidades como dataclasses (anémicas con validación mínima)
│   ├── services/         ← Lógica de dominio pura
│   ├── repositories/     ← Puertos (interfaces abstractas, prefijo I*)
│   ├── value_objects/    ← Value objects
│   ├── events/           ← Eventos de dominio
│   └── exceptions.py
├── application/
│   ├── uses_cases/       ← Casos de uso (orquestan servicios + repositorios)
│   └── services/         ← Servicios de aplicación
└── infrastructure/
    ├── persistence/
    │   ├── models/       ← Modelos SQLAlchemy
    │   └── repositories/ ← Implementaciones concretas de repositorios
    ├── presentation/
    │   ├── routers/      ← FastAPI routers
    │   └── dependencies/ ← Inyección de dependencias (FastAPI Depends)
    └── adapters/http/
        ├── input/        ← Schemas de request (Pydantic)
        └── output/       ← Schemas de response (Pydantic)
```

**Entry points**: `main.py` → `common.infrastructure.core.app.configure_app()` → `configure_routers()` que agrega routers de todos los contextos.

**Stack**: Python 3.12, FastAPI, SQLAlchemy async (asyncpg), Redis, Celery, Pydantic v2.

**Testing**: 274 tests, pytest asyncio mode=auto, fixture loop scope=session. Unit tests con `MockUoW`/`MockRepository`, tests de integración con base de datos real.

---

### Affected Areas

#### 1. Acoplamiento crítico entre bounded contexts (DOMAIN LAYER)

Varias entidades de dominio importan directamente entidades de **otros contextos**, violando el principio fundamental de bounded contexts:

- `src/cattle/domain/entities/animal_entity.py:5` — importa `UserEntity` de `src.auth.domain.entities`
- `src/finance/domain/entities/animal_supplies.py:5` — importa `UserEntity` de `src.auth.domain.entities`
- `src/market/domain/entities/buyers.py:5` — importa `UserEntity` de `src.auth.domain.entities`
- `src/market/domain/entities/sales.py:5-6` — importa `UserEntity` DE auth Y `AnimalEntity` DE cattle

**Esto es lo más grave**. Las entidades de dominio son la capa más interna del hexágono. Un cambio en `UserEntity` (auth) puede forzar cambios en `SaleEntity` (market), `AnimalSupplyEntity` (finance), `AnimalEntity` (cattle) y `BuyerEntity` (market). Son 5 dependencias directas entre dominios.

#### 2. Acoplamiento entre capas de aplicación (APPLICATION LAYER)

- `src/auth/application/uses_cases/register_user_case.py:12` — importa `TrialManagementService` de `src.billing.application.services`
- `src/billing/application/services/_trial_management_service.py:16` — importa `ITenantRepository` de `src.auth.domain.repositories`

El `RegisterUserCase` del contexto auth tiene una dependencia directa hacia billing. Esto es bidireccional (auth←→billing), lo que significa que no se puede desplegar ni testear auth sin billing y viceversa.

#### 3. Acoplamiento en repositorios (INFRASTRUCTURE LAYER)

Repositorios de un contexto importan **modelos SQLAlchemy** de otro contexto:

- `src/cattle/infrastructure/persistence/repositories/schedule_event_repository.py:6` — importa `User` de `auth.infrastructure.persistence.models`
- `src/finance/infrastructure/persistence/repositories/purchases.py:6` — importa `User` de `auth.infrastructure.persistence.models`

#### 4. Registry monolitico de repositorios

`src/common/infrastructure/persistence/repositories/_registry.py` importa TODOS los repositorios de TODOS los contextos en un solo diccionario. Incluye un comentario explícito sobre dependencia circular usando lazy imports (`__getattr__`). Esto centraliza el acoplamiento de infraestructura.

#### 5. Inconsistencia en el patrón de repositorios

- `UserRepository` usa `SessionMixin` (solo guarda `self.db`)
- `AnimalRepository` y otros usan `TenantAwareRepository` (guarda `self.db` + `self._tenant_id` + filtrado)
- `UserRepository` NO es tenant-aware, mientras que los demás sí
- La UoW tiene un `if issubclass(repository, TenantAwareRepository)` para manejar la diferencia

#### 6. Models SQLAlchemy acoplados entre contextos

Los modelos SQLAlchemy usan `ForeignKey` y `relationship()` directos a tablas de otros contextos (e.g., `Animal.tenant_id → ForeignKey("tenants.id")`, `Animal.user → relationship("User")`). Esto acopla el esquema de base de datos entre contextos.

#### 7. Factories de test monolíticos

`tests/factories.py` tiene **473 líneas** y centraliza todas las factories de todos los contextos en un solo archivo. Debería estar dividido por contexto.

#### 8. Archivos grandes

| Archivo | Líneas | Problema |
|---------|--------|----------|
| `src/billing/infrastructure/payment_gateway/_client.py` | 293 | Cliente de pasarela de pago grande |
| `src/billing/infrastructure/workers/_billing_tasks.py` | 255 | Workers de billing |
| `src/market/infrastructure/persistence/repositories/sales.py` | 232 | Repositorio grande |
| `src/auth/infrastructure/persistence/repositories/user_repository.py` | 230 | Mucha lógica en el repo |
| `src/cattle/infrastructure/persistence/repositories/animal_repository.py` | 221 | Idem |
| `tests/factories.py` | 473 | Monolítico, mezcla todos los contextos |

---

### Approaches

#### Approach 1: Refactor por capas (Capa Interna → Capa Externa)

**Descripción**: Abordar la refactorización desde adentro hacia afuera: primero arreglar el dominio, luego aplicación, luego infraestructura. Cada capa se resuelve completamente antes de pasar a la siguiente.

**Pros**:
- Enfoque sistemático, cada fase produce un estado compilable y testeable
- La capa de dominio se estabiliza primero, y todo lo demás depende de ella
- Fácil de verificar progreso

**Cons**:
- Puede requerir cambios grandes en infraestructura que no se ven hasta el final
- Puede generar conflictos de merge si hay desarrollo paralelo
- Las capas externas (routers, repositorios) necesitan cambios grandes después

**Effort**: High

#### Approach 2: Refactor por contexto (Un contexto a la vez)

**Descripción**: Tomar cada bounded context de forma independiente y refactorizarlo completo (dominio + aplicación + infraestructura) antes de pasar al siguiente. Orden propuesto: `billing` (el más limpio) → `auth` (el más referenciado) → `cattle` → `market` → `finance`.

**Pros**:
- Cada iteración produce un contexto completamente independiente
- `billing` es el más limpio y da el ejemplo
- `auth` se estabiliza primero porque otros dependen de él
- Se puede hacer deploy por contexto

**Cons**:
- El orden de dependencias requiere planificación cuidadosa
- `market` depende de `cattle` y `auth` — requiere cambios secuenciales
- Puede ser más lento porque hay que cambiar infraestructura antes de que el dominio esté limpio

**Effort**: High

#### Approach 3: Separación de identidades + Eventos

**Descripción**: No eliminar las entidades referenciadas, sino reemplazar las referencias directas a entidades de otros contextos por **identidades** (UUID) y comunicación vía **eventos de dominio**. Las entities que hoy tienen `user: UserEntity | None` pasarían a tener `user_id: UUID | None`. La composición de datos de múltiples contextos ocurre en los casos de uso o en los schemas de salida.

**Pros**:
- Elimina el acoplamiento de dominio sin cambiar la funcionalidad
- Prepara la arquitectura para comunicación asíncrona real entre contextos
- Los eventos ya existen (`DomainEvent`, `IEventBus`, outbox) — solo hay que usarlos
- Mínimo cambio en infraestructura por entidad

**Cons**:
- No resuelve completamente el acoplamiento de infraestructura (modelos, repositorios)
- Requiere cambiar la lógica de presentación que hoy confía en objetos completos
- Las queries que hoy usan `relationship()` de SQLAlchemy dejarían de funcionar

**Effort**: Medium

#### Approach 4: Estrategia Híbrida (Recomendada)

**Descripción**: Combinar los enfoques 1 y 3 trabajando en paralelo:

1. **FASE 1 — Desacoplar dominios (Approach 3)**: Reemplazar referencias a entidades externas por UUIDs en todas las entidades de dominio. Esto es quirúrgico y de bajo riesgo.
2. **FASE 2 — Limpiar aplicación**: Reemplazar imports directos entre casos de uso de distintos contextos por integración vía eventos o interfaces compartidas en `common`.
3. **FASE 3 — Separar infraestructura**: Dividir el registry de repositorios, desacoplar modelos SQLAlchemy, mover referencias entre modelos a joins explícitos en repositorios.
4. **FASE 4 — Dividir tests/factories**: Separar factories por contexto y eliminar imports cruzados en tests.
5. **FASE 5 — Dividir archivos grandes**: Refactorizar archivos que superan las 200 líneas.

**Pros**:
- FASE 1 produce valor inmediato con bajo riesgo
- Cada fase es autónoma y reversible
- Orden óptimo: dominio (estable) → aplicación → infraestructura → tests
- Compatible con desarrollo paralelo

**Cons**:
- Requiere coordinación entre fases
- La FASE 3 puede requerir cambios en la UoW y el registry
- Esfuerzo total alto pero distribuido en entregables seguros

**Effort**: Medium-High (pero bajo riesgo por fase)

---

### Recommendation

**Approach 4 — Estrategia Híbrida** es la recomendada. Razones:

1. **Riesgo controlado**: Cada fase produce un estado funcional. No necesitas un "big bang" para ver progreso.
2. **Valor temprano**: La FASE 1 (eliminar imports de dominio entre contextos) es bajo riesgo, produce ~20 cambios localizados y elimina el problema estructural más grave de inmediato.
3. **Aprovecha lo que ya existe**: El proyecto ya tiene `IEventBus`, `DomainEvent`, outbox pattern. Solo hay que usarlos para lo que fueron diseñados.
4. **Orden natural**: Dominio → Aplicación → Infraestructura sigue las reglas de la arquitectura hexagonal. Las capas internas cambian primero.

### Detalle de la FASE 1 (la más crítica)

**Qué cambiar en entidades de dominio**:

```
# ANTES (animal_entity.py)
@dataclass
class AnimalEntity:
    ...
    user: UserEntity | None = None  # ← importa de auth

# DESPUÉS
@dataclass
class AnimalEntity:
    ...
    user_id: UUID | None = None  # ← solo UUID, sin import
```

Lo mismo para `AnimalSupplyEntity`, `BuyerEntity`, `SaleEntity`, `SaleEntity.animal`.

**Qué cambia en los repositorios**: Los repositorios que hoy hacen `relationship()` a `User` o hacen join a la tabla `users` deben cambiar a:
- Usar `user_id` como UUID escalar
- Si necesitan datos del usuario, hacer el join en el repositorio (sigue siendo infraestructura) pero mapear solo el `user_id` en la entidad

**Qué cambia en los routers/schemas**: Si los schemas de respuesta incluyen datos anidados del usuario, esos datos se arman en el schema o en el caso de uso, no en la entidad de dominio.

---

### Risks

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| **Rotura de tests**: Los tests existentes crean entidades con `user=UserEntity(...)`. Al cambiar a `user_id`, 50+ tests pueden fallar | Media | Hacer FASE 1 primero, corregir tests de factories en FASE 4 |
| **Acoplamiento bidireccional auth↔billing**: RegisterUserCase usa TrialManagementService. Separarlos requiere evento o interfaz compartida | Alta | Crear un evento `UserRegistered` en auth y que billing lo consuma. Ya existe el bus de eventos |
| **Perder lazy loading de SQLAlchemy**: Si quitamos `relationship()`, perdemos carga automática de datos relacionados | Media | Reemplazar con joins explícitos en los métodos de repositorio que los necesiten |
| **Schema de respuesta cambia**: Si los output schemas hoy serializan `user.name`, al cambiar a `user_id` hay que resolverlo en otra capa | Media | Mover la composición al caso de uso o al schema output |
| **Dependencia circular aplazada**: El `__getattr__` en `repositories/__init__.py` es un workaround que puede romperse | Baja | Dividir el registry en registros por contexto |
| **No hay type checker**: Sin mypy/pyright strict, algunos cambios pueden pasar desapercibidos | Media | Considerar activar pyright antes de la refactorización. Ya está en dev-deps |
| **274 tests para mantener verde**: Refactorización grande puede dejar tests rojos por días | Alta | Por fases, con cada fase manteniendo tests verdes |

---

### Ready for Proposal

**Yes**. La exploración ha identificado problemas claros y soluciones viables. El siguiente paso es `sdd-propose` para formalizar el alcance del cambio, definir la estrategia de entrega (chained PRs recomendado) y obtener aprobación antes de comenzar la implementación.

La estrategia híbrida (Approach 4) minimiza el riesgo y permite iterar con confianza. La FASE 1 (desacoplar dominios) puede iniciarse inmediatamente y produce mejoras visibles en ~1-2 días de trabajo enfocado.
