## Exploration: Domain Event / Event Bus / Webhook Dispatch (Phase 9b)

### Current State

**No event system exists.** The codebase has zero event-related patterns — no `EventBus`, `DomainEvent`, `dispatch`, `publish`, `subscribe`, or transactional outbox patterns. Here's what *does* exist:

**Async infrastructure:**
- **Celery** configured via `src/common/infrastructure/workers/app.py`: Redis broker/backend, JSON serializer, autodiscovers 3 task modules. Uses `@shared_task` (no custom base task class, no centralized error handling/retry config).
- **Redis** shared client in `src/common/infrastructure/persistence/connections/redis.py` — currently used for Celery broker/backend, token blacklist, rate limiter backend, and `RedisCacheService` (Phase 9a).
- **Periodic tasks**: monthly billing, trial expiry, upcoming events notification — registered via `cron_tasks_register.py`.

**Only existing async dispatch (Email):**
```
WellcomeEmailService → EmailNotifier (adapter) → send_email.apply_async()
```
This is a fire-and-forget Celery task — no domain events, no event bus, no handlers.

**MercadoPago Webhook** (`src/billing/infrastructure/presentation/routers/_webhook_router.py`):
- Public `POST /billing/webhooks/mercadopago?topic=payment&id=...`
- Uses `asyncio.create_task()` for fire-and-forget background processing
- `PaymentWebhookService.handle_ipn()` validates signature, fetches payment from MP, persists to DB, updates subscription
- **Does NOT emit any events** after processing — it's a direct handler with no event abstraction

**Existing patterns to leverage:**
- **Audit system** (`AuditableRepositoryMixin` + `AuditRepository`): in-memory queue → flushed in `UnitOfWork.commit()`. This is the EXACT pattern to replicate for a transactional event outbox.
- **UoW `add_before_commit_hook()`**: already supports registering hooks before DB commit.
- **FastAPI DI**: `Annotated[Type, Depends()]` pattern well established across all domains.

**Domain entities** are plain `@dataclass` objects — no base entity class, no lifecycle hooks, no event emission from entities themselves. Events would need to be emitted from **use cases** (application layer) after successful domain operations.

### Affected Areas

- `src/common/domain/events/` — **NEW**: Domain event base class, event bus port
- `src/common/infrastructure/events/` — **NEW**: In-memory EventBus, outbox repository, Redis pub/sub adapter
- `src/common/infrastructure/persistence/models/` — **NEW**: outbox SQLAlchemy model (+ Alembic migration)
- `src/common/infrastructure/workers/` — **NEW**: outbox forwarder Celery task
- `src/common/application/ports/uow.py` — Add event outbox flushing to IUoW
- `src/common/infrastructure/persistence/uow.py` — Wire outbox flush into commit()
- `src/common/domain/ports/cache_service.py` — Already exists (Phase 9a), no change needed
- `src/cattle/application/uses_cases/animals_use_cases/register_animal_case.py` — First event emission point
- `src/billing/application/services/_payment_webhook_service.py` — Should emit PaymentReceived event
- `src/cattle/application/uses_cases/animals_use_cases/` (all) — Cache invalidation handlers
- `src/auth/application/uses_cases/register_user_case.py` — UserRegistered event
- `src/market/application/uses_cases/sale_cases/create_sale_case.py` — SaleCreated event
- `tests/unit/common/` — New test files for EventBus, outbox, handlers

### Approaches

1. **In-memory EventBus + Sync Handlers Only** — Simplest approach
   - Pros: Zero infrastructure, trivial to test, follows existing patterns
   - Cons: No durability (events lost on crash), no retries, no webhook dispatch, handlers run in request scope
   - Effort: Low (2-3 days)

2. **Transactional Outbox (DB-backed) + Celery Consumer** — Reliable, durable
   - Pros: Events survive crashes, ACID with business transaction (same UoW), retries via Celery, follows audit pattern exactly
   - Cons: Adds DB table, polling latency, more moving parts
   - Effort: Medium (5-7 days)

3. **Redis Pub/Sub Broadcasting** — Real-time, existing Redis
   - Pros: Near-zero latency, no DB overhead, existing Redis connection
   - Cons: No durability (events lost if no subscriber connected), no delivery guarantees, no retries, not suitable for critical events (billing, payments)
   - Effort: Low (2-3 days)

4. **Full Layered System: Domain Events + Outbox + Webhook Dispatch** — Complete solution
   - Pros: Reliable, durable, extensible, each concern separated
   - Cons: Highest upfront cost, overkill if only 1-2 consumers exist initially
   - Effort: High (10-14 days)

5. **Combined: In-memory Bus (sync) + Outbox (async durability)** — **RECOMMENDED**
   - Sync bus for fast handlers (cache invalidation, audit enrichment)
   - Outbox for durable async dispatch (webhooks, emails, notifications)
   - Can start with sync-only and add outbox in same PR
   - Pros: Best of both worlds, follows audit pattern, cache invalidation stays synchronous, webhooks go through outbox
   - Cons: More code than pure sync, but still manageable
   - Effort: Medium-High (7-10 days for full scope, 4-5 days for MVP)

### Recommended Architecture

```
Use Case (emits DomainEvent)
  │
  ├─→ In-Memory EventBus (sync, in-process)
  │     ├─→ CacheInvalidationHandler  (uses ICacheService)
  │     └─→ AuditEnrichmentHandler    (logs to audit, already exists)
  │
  └─→ EventOutbox (queued in UoW, flushed on commit)
        │
        └─→ Celery Task: outbox_forwarder (polls outbox)
              │
              ├─→ EmailNotificationHandler
              ├─→ WebhookDispatchHandler
              │     └─→ POST to registered webhook URLs
              └─→ Other async handlers...
```

**MVP Scope (first iteration):**
1. `DomainEvent` base class (event_id, aggregate_id, event_type, timestamp, metadata)
2. `IEventBus` port + `InMemoryEventBus` implementation (sync handlers)
3. `EventOutbox` model + `OutboxRepository` (DB-backed, queued in UoW)
4. Wire outbox flush into `UnitOfWork.commit()` (same pattern as audit)
5. One event: `AnimalCreated` emitted from `RegisterAnimalCase`
6. One consumer: `AnimalCacheInvalidationHandler` (invalidates animal list cache)
7. One async consumer: `AnimalCreatedWebhookHandler` (via outbox → Celery)

### Risks

- **Transactional integrity**: Outbox flush must happen BEFORE DB commit (like audit). If flush succeeds but commit fails, rollback must clear the outbox queue. The audit pattern already handles this correctly.
- **Duplicate events**: Outbox forwarder must be idempotent (track processed event IDs or use `for update skip locked` when polling).
- **Webhook delivery failures**: External webhooks can fail or timeout — need retry with backoff and dead-letter after N attempts.
- **Sync handler performance**: In-memory handlers run in the request path. Cache invalidation is fast, but any handler that blocks could increase latency. Keep sync handlers for fast operations only.
- **Circular dependencies**: EventBus → Handler → Service dependencies must be carefully wired at the composition root to avoid cycles.
- **Event schema evolution**: Once webhooks go external, changing event payloads breaks consumers. Use versioned event types (e.g., `animal.created.v1`).

### File/Folder Structure Proposal

```
src/common/domain/events/
├── __init__.py
├── _base_event.py              # DomainEvent base dataclass
└── _event_bus_port.py          # IEventBus interface (publish, subscribe)

src/common/infrastructure/events/
├── __init__.py
├── _in_memory_event_bus.py     # Sync EventBus (handler registry, in-process dispatch)
├── _outbox_repository.py       # OutboxRepository (queue + bulk flush, matches audit pattern)
└── _event_serializer.py        # JSON serialization for outbox entries

src/common/infrastructure/persistence/models/
├── _event_outbox_model.py      # event_outbox SQLAlchemy model

src/common/infrastructure/workers/
├── _outbox_forwarder_task.py   # Celery task: polls outbox, dispatches to async handlers
├── _webhook_dispatcher.py      # HTTP POST to registered webhook URLs
└── _webhook_retry_service.py   # Retry/backoff/dead-letter logic

src/cattle/application/events/  (one folder per domain)
├── __init__.py
├── _animal_created.py          # AnimalCreated domain event
├── _animal_updated.py          # AnimalUpdated domain event
├── _animal_deleted.py          # AnimalDeleted domain event
└── handlers/
    ├── __init__.py
    └── _animal_cache_handler.py   # Sync handler: invalidates cache

alembic/versions/
└── xxxxxx_add_event_outbox.py  # CREATE TABLE event_outbox
```

### Proposed Domain Events (Initial)

| Event | Domain | Emitted By | Consumers |
|-------|--------|-----------|-----------|
| `AnimalCreated` | cattle | RegisterAnimalCase | Cache invalidation, webhook |
| `AnimalUpdated` | cattle | UpdateAnimalCase | Cache invalidation, webhook |
| `AnimalDeleted` | cattle | DeleteAnimalCase | Cache invalidation |
| `SaleCreated` | market | CreateSaleCase | Webhook, audit |
| `PaymentReceived` | billing | PaymentWebhookService | Email notif, webhook |
| `UserRegistered` | auth | RegisterUserCase | Email notif (migrate from direct call) |
| `SubscriptionChanged` | billing | ChangePlanService | Webhook |

### Ready for Proposal

Yes. The codebase is well-prepared for this — the audit pattern is a direct template for the outbox, Redis and Celery are already in place, and no structural blockers exist. Recommend starting with **Mini-MVP** (in-memory EventBus + cache invalidation only) as a 1st commit, then adding the outbox + Celery consumer as a 2nd commit, then webhook dispatch as a 3rd phase.
