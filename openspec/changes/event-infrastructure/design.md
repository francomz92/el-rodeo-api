# Design: Event Infrastructure

## Technical Approach

Replicate the existing audit pattern — queue events in memory during use-case execution, flush outbox rows in `UoW.commit()` via a before-commit hook, and consume them via a Celery periodic task. `IEventBus` follows the `ICacheService` port/adapter pattern. The EventBus is request-scoped via FastAPI DI so sync handlers (like the outbox scheduler) can access the current `IUoW`.

## Architecture Decisions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| EventBus scoped per-request vs singleton | Singleton needs out-of-band UoW lookup; per-request keeps handlers simple with constructor injection | **Per-request** via FastAPI `Depends` factory |
| `DomainEvent` as dataclass vs Pydantic | Dataclass matches IUoW pattern; Pydantic adds serialization but pulls in heavy deps for a base | **Dataclass** — light, familiar, serialized to JSON in outbox |
| Outbox flush: before-commit hook vs direct call in commit() | Hook is generic but ordering matters; direct call gives explicit sequence | **Direct call** in `commit()` after audit, before `db.commit()` — explicit and testable |
| Webhook secret: encrypt at DB vs HMAC-only | Encrypt adds key management overhead; HMAC with per-tenant secret already mitigates replay | **HMAC key only** — encrypt at DB layer if needed later, not in app code |

## Data Flow

```
Use Case ──→ EventBus.dispatch(event)
                 │
                 ├── Sync: CacheInvalidationHandler (inline, fails isolated)
                 │       └── ICacheService.invalidate_pattern("cattle:animals:*")
                 │
                 └── Sync: OutboxSchedulingHandler (inline, queues in UoW memory)
                         └── uow.add_outbox_event(event)

UoW.commit()
  ├── before_commit_hooks
  ├── audit flush
  ├── flush outbox  ←  bulk INSERT EventOutbox rows
  └── db.commit()

Celery Beat ──→ outbox_forwarder_task()
                  └── get_pending(50) → for each:
                        ├── WebhookDispatchHandler (POST + HMAC + retry/backoff)
                        ├── mark_sent() or retry_count++
                        └── if retry_count >= 5: dead-letter (is_active=False)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/common/domain/events/base.py` | Create | `DomainEvent` dataclass base |
| `src/common/domain/ports/event_bus.py` | Create | `IEventBus` ABC port with `register()` and `dispatch()` |
| `src/common/infrastructure/events/bus.py` | Create | `InMemoryEventBus` — dict-backed, handler-isolated dispatch |
| `src/common/infrastructure/persistence/models/event_outbox.py` | Create | `EventOutbox` SQLAlchemy model |
| `src/common/infrastructure/events/outbox_repository.py` | Create | `OutboxRepository` — `add()`, `get_pending()`, `mark_sent()` |
| `src/common/application/ports/uow.py` | Modify | Add `outbox_events`, `add_outbox_event()` to `IUoW` |
| `src/common/infrastructure/persistence/uow.py` | Modify | Add outbox flush in `commit()`; clear in `rollback()` |
| `src/cattle/domain/events/animal_events.py` | Create | `AnimalCreated` typed event |
| `src/cattle/application/uses_cases/.../register_animal_case.py` | Modify | Emit `AnimalCreated` via EventBus after successful creation |
| `src/cattle/infrastructure/events/handlers/cache_invalidation.py` | Create | `AnimalCacheInvalidationHandler` — calls `cache.invalidate_pattern()` |
| `src/common/infrastructure/events/handlers/outbox_scheduler.py` | Create | `OutboxSchedulingHandler` — calls `uow.add_outbox_event()` |
| `src/billing/domain/events/payment_events.py` | Create | `PaymentReceived` typed event |
| `src/billing/application/services/_payment_webhook_service.py` | Modify | Emit `PaymentReceived` via EventBus on APPROVED |
| `src/common/infrastructure/persistence/models/webhook_subscription.py` | Create | `WebhookSubscription` SQLAlchemy model |
| `src/common/infrastructure/events/webhook_dispatcher.py` | Create | HTTP POST + HMAC + retry with backoff |
| `src/common/infrastructure/workers/event_tasks.py` | Create | Celery outbox forwarder + webhook dispatch task |
| `src/common/infrastructure/workers/cron_tasks_register.py` | Modify | Register outbox forwarder periodic task |
| `src/cattle/infrastructure/presentation/dependencies/animals.py` | Modify | Inject `IEventBus` into `RegisterAnimalCase` |

## Interfaces / Contracts

```python
# Port (src/common/domain/ports/event_bus.py)
class IEventBus(ABC):
    @abstractmethod
    def register(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None: ...
    @abstractmethod
    def dispatch(self, event: DomainEvent) -> None: ...

# Additions to IUoW (src/common/application/ports/uow.py)
outbox_events: list[DomainEvent] = field(default_factory=list)

def add_outbox_event(self, event: DomainEvent) -> None:
    self.outbox_events.append(event)
```

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | `DomainEvent` base + typed events | Dataclass instantiation, field defaults |
| Unit | `InMemoryEventBus` | Register + dispatch, handler isolation |
| Unit | `OutboxRepository` | In-memory impl for add/get/mark/sent |
| Unit | `AnimalCacheInvalidationHandler` | Mock ICacheService, verify invalidation call |
| Unit | Webhook HMAC signing + retry | Mock HTTP client, verify backoff schedule |
| Integration | UoW commit → outbox flush | DB test: verify rows after commit, none after rollback |
| Integration | Celery forwarder | DB test: process PENDING rows, verify SENT status |
| Integration | MP webhook → PaymentReceived | Wire EventBus into handler, verify dispatch |

## Migration / Rollout

No migration required. EventOutbox and WebhookSubscription tables created fresh via Alembic. Existing data unaffected. Feature-flagged: outbox forwarder can be deployed before any event is emitted.

## Open Questions

- [x] **EventBus scoping**: resolved — per-request via FastAPI DI, handlers registered in factory
- [ ] **Outbox index strategy**: one composite index on (status, created_at) for efficient `get_pending` queries? Evaluate query pattern during implementation
- [ ] **WebhookSubscription secret**: should it be encrypted at the application layer or rely on DB-at-rest encryption? Deferred — HMAC key per tenant for now
