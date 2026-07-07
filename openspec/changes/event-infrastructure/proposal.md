# Proposal: Event Infrastructure

## Intent

Add a domain event system for decoupled side-effects (cache invalidation, webhooks, audit) without direct use-case coupling. Follows the existing audit pattern — in-memory queue + UoW flush — to keep consistency guarantees.

## Scope

### In Scope
- DomainEvent base class, IEventBus port, InMemoryEventBus (sync dispatch)
- EventOutbox model + repository + flush in UoW commit
- `AnimalCreated` event emitted from `RegisterAnimalCase`
- `AnimalCacheInvalidationHandler` (sync, uses ICacheService)
- Celery outbox forwarder task
- Webhook subscriptions (tenant-scoped model) + dispatch with retry + dead-letter
- `PaymentReceived` event from existing MP webhook handler

### Out of Scope
- Event sourcing or event store
- Async EventBus (sync-only for now)
- Domain events beyond AnimalCreated and PaymentReceived
- Dead-letter admin UI or dashboard

## Capabilities

### New Capabilities
- `domain-events`: DomainEvent base class, IEventBus port, InMemoryEventBus, typed event definitions
- `event-outbox`: EventOutbox SQLAlchemy model, outbox repository, UoW flush integration, Celery forwarder task
- `webhook-subscriptions`: Tenant-scoped webhook model (url, secret, subscribed_events, is_active), dispatch with retry/backoff, dead-letter after N failures

### Modified Capabilities
- `billing/payment`: MP webhook handler now emits `PaymentReceived` event on successful payment notification

## Approach

Replicate the existing audit pattern: queue events in memory during the use-case, flush outbox rows in UoW `commit()` (before-commit hook), clear on rollback. FastAPI DI injects EventBus. Sync handlers (cache invalidation) run inline during dispatch. Async handlers (webhooks) persist via outbox and are consumed by a Celery periodic task.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/common/domain/events/` | New | EventBus port, DomainEvent base |
| `src/common/infrastructure/events/` | New | InMemoryEventBus, OutboxRepository, serializer |
| `src/common/infrastructure/persistence/models/` | New | EventOutbox ORM model |
| `src/common/infrastructure/persistence/uow.py` | Modified | Add before-commit hook for outbox flush |
| `src/common/infrastructure/workers/` | New | Outbox forwarder Celery task |
| `src/common/infrastructure/tasks/` | New | Webhook dispatcher task |
| `src/cattle/application/events/` | New | AnimalCreated event + CacheInvalidationHandler |
| `src/cattle/application/uses_cases/register_animal_case.py` | Modified | Emit AnimalCreated on success |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Outbox stale if Celery worker down | Medium | Health check + alert on outbox age |
| Webhook secret leak in DB | Low | Encrypt at rest, restrict DB access |
| Event schema drift producer/consumer | Low | Shared base class, typed events |

## Rollback Plan

- Remove outbox flush hook from UoW
- Remove Celery forwarder + webhook dispatcher deployments
- Revert EventOutbox model migration
- Keep event classes (no-op without dispatch)

## Dependencies

- Existing Redis + Celery infrastructure
- Existing ICacheService for invalidation handler
- Existing UoW before-commit hook system

## Success Criteria

- [ ] `AnimalCreated` event emitted on animal registration, handled by cache invalidation
- [ ] Outbox rows flushed in same transaction as use-case commit
- [ ] Celery forwarder picks up unflushed outbox rows and dispatches handlers
- [ ] Webhook POST succeeds with retry on 5xx, dead-letter after N failures
- [ ] `PaymentReceived` event emitted from MP webhook handler
