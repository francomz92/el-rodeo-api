# Tasks: Event Infrastructure

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~650–750 |
| 800-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: Foundation → PR 2: Sync handlers → PR 3: Webhooks |
| Delivery strategy | ask-always |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
800-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR |
|------|------|-----------|
| 1 | DomainEvent + IEventBus + InMemoryEventBus + typed events + Outbox model + UoW hooks | PR 1 (base = main) |
| 2 | OutboxRepository + CacheInvalidation + OutboxScheduler + wire RegisterAnimalCase | PR 2 (depends on PR 1) |
| 3 | WebhookSubscription model + WebhookDispatcher + Celery forwarder + PaymentReceived + CRUD routes | PR 3 (depends on PR 1) |

## Phase 1: Foundation

- [x] 1.1 Create `src/common/domain/events/base.py` — DomainEvent dataclass (event_id, aggregate_id, event_type, timestamp, metadata)
- [x] 1.2 Create `src/common/domain/ports/event_bus.py` — IEventBus ABC (register, dispatch)
- [x] 1.3 Create `src/common/infrastructure/events/bus.py` — InMemoryEventBus dict-backed with isolated handlers
- [x] 1.4 Create `src/cattle/domain/events/animal_events.py` — AnimalCreated(event_type="animal.created")
- [x] 1.5 Create `src/billing/domain/events/payment_events.py` — PaymentReceived(event_type="payment.received")
- [x] 1.6 Create `src/common/infrastructure/persistence/models/event_outbox.py` — EventOutbox SQLA model (id, event_id, event_type, aggregate_id, payload, status, retry_count, timestamps)
- [x] 1.7 Modify `IUoW` port — add `outbox_events` field + `add_outbox_event()` method
- [x] 1.8 Modify UoW `commit()` — flush outbox rows before db.commit(); clear on rollback

## Phase 2: Sync Handlers + Wiring

- [x] 2.1 Create `src/common/infrastructure/events/outbox_repository.py` — add/get_pending(limit)/mark_sent
- [x] 2.2 Create `src/common/infrastructure/events/handlers/outbox_scheduler.py` — queues event to uow.outbox_events
- [x] 2.3 Create `src/cattle/infrastructure/events/handlers/cache_invalidation.py` — calls ICacheService.invalidate_pattern("cattle:animals:*")
- [x] 2.4 Modify `register_animal_case.py` — accept IEventBus, emit AnimalCreated after creation
- [x] 2.5 Modify `dependencies/animals.py` — wire IEventBus injection into RegisterAnimalCase factory

## Phase 3: Webhooks + Celery + Payment

- [x] 3.1 Create `src/common/infrastructure/persistence/models/webhook_subscription.py` — tenant-scoped SQLA model (url, secret, subscribed_events, is_active, failure_count)
- [x] 3.2 Create `src/common/infrastructure/events/webhook_dispatcher.py` — HMAC-SHA256 + POST with exponential backoff (5 attempts) + dead-letter on 5 failures
- [x] 3.3 Create `src/common/infrastructure/workers/event_tasks.py` — Celery outbox forwarder (get_pending → dispatch → mark_sent/retry)
- [x] 3.4 Modify `cron_tasks_register.py` — register outbox_forwarder_task as periodic Celery beat task
- [x] 3.5 Modify `_payment_webhook_service.py` — emit PaymentReceived via IEventBus on APPROVED
- [x] 3.6 Add webhook CRUD routes — LIST/CREATE/UPDATE/DELETE WebhookSubscription per tenant

## Phase 4: Testing

- [x] 4.1 Unit: DomainEvent defaults, UUID generation, metadata passthrough
- [x] 4.2 Unit: InMemoryEventBus register+dispatch, handler isolation on exception, registration order
- [x] 4.3 Unit: OutboxRepository add/get_pending/mark_sent with in-memory impl
- [x] 4.4 Unit: CacheInvalidationHandler — mock ICacheService, verify invalidation call
- [x] 4.5 Unit: WebhookDispatcher — HMAC signing, retry schedule, dead-letter after 5 failures
- [x] 4.6 Integration: UoW commit flushes outbox rows; rollback empties queue
- [x] 4.7 Integration: Celery forwarder processes PENDING → SENT status transition
- [x] 4.8 Integration: PaymentReceived emitted on APPROVED; not emitted on REJECTED
