# PR 1: Foundation — Archive Report

**Archived**: 2026-07-03
**Change**: Event Infrastructure (PR 1 of 3)

## Scope Delivered

PR 1 implemented the Foundation tasks (1.1–1.8) of the Event Infrastructure change:

### Domain Event Base & Ports
- **Task 1.1** — `src/common/domain/events/base.py`: `DomainEvent` frozen dataclass with auto-generated `event_id` (UUID), `aggregate_id`, `event_type`, UTC `timestamp`, and `metadata` dict
- **Task 1.2** — `src/common/domain/ports/event_bus.py`: `IEventBus` ABC with `register(event_type, handler)` and `dispatch(event)` abstract methods

### Event Bus Implementation
- **Task 1.3** — `src/common/infrastructure/events/bus.py`: `InMemoryEventBus` dict-backed with handler isolation (one failing handler never blocks others)

### Typed Domain Events
- **Task 1.4** — `src/cattle/domain/events/animal_events.py`: `AnimalCreated(event_type="animal.created")` 
- **Task 1.5** — `src/billing/domain/events/payment_events.py`: `PaymentReceived(event_type="payment.received")`

### Outbox Model & UoW Integration
- **Task 1.6** — `src/common/infrastructure/persistence/models/event_outbox.py`: `EventOutbox` SQLAlchemy model (event_id, event_type, aggregate_id, payload JSONB, status PENDING/SENT/FAILED, retry_count, timestamps, composite index on status+created_at)
- **Task 1.7** — `src/common/application/ports/uow.py`: Added `outbox_events: list[DomainEvent]` field and `add_outbox_event()` method to `IUoW`
- **Task 1.8** — `src/common/infrastructure/persistence/uow.py`: `UnitOfWork._flush_outbox_events()` called in `commit()` after audit flush, before `db.commit()`; `rollback()` clears `outbox_events`

## Files Delivered

| File | Action |
|------|--------|
| `src/common/domain/events/__init__.py` | Created |
| `src/common/domain/events/base.py` | Created |
| `src/common/domain/ports/event_bus.py` | Created |
| `src/common/infrastructure/events/__init__.py` | Created |
| `src/common/infrastructure/events/bus.py` | Created |
| `src/common/infrastructure/persistence/models/event_outbox.py` | Created |
| `src/cattle/domain/events/__init__.py` | Created |
| `src/cattle/domain/events/animal_events.py` | Created |
| `src/billing/domain/events/__init__.py` | Created |
| `src/billing/domain/events/payment_events.py` | Created |
| `src/common/application/ports/uow.py` | Modified (outbox_events, add_outbox_event) |
| `src/common/infrastructure/persistence/uow.py` | Modified (outbox flush on commit, clear on rollback) |

## Test Results

### Event-Specific Tests

| Test File | Count | Status |
|-----------|-------|--------|
| `tests/unit/common/events/test_domain_event.py` | 10 | ✅ All pass |
| `tests/unit/common/events/test_event_bus.py` | 8 | ✅ All pass |
| `tests/unit/common/events/test_uow_outbox.py` | 5 | ✅ All pass |
| `tests/unit/common/test_event_outbox.py` | 12 | ✅ All pass |
| `tests/unit/common/test_uow_outbox_flush.py` | 9 | ✅ All pass |
| **Total event tests** | **44** | **44/44 pass** |

### Full Suite
- **1009 passed**, 13 failed (all pre-existing logger/correlation/UoW tenant failures), 12 skipped

## Architecture Decisions (Carried Forward)

| Decision | Rationale |
|----------|-----------|
| **Per-request EventBus** via FastAPI `Depends` | Keeps handlers simple with constructor injection |
| **DomainEvent as frozen dataclass** | Light, familiar, matches existing IUoW pattern |
| **Outbox flush as direct call in commit()** | Explicit ordering: audit → outbox → db.commit() |
| **OutboxStatus as StrEnum** | Clear status transitions for Celery forwarder |
| **Composite index (status, created_at)** | Optimizes `get_pending()` query pattern |

## Spec Sync

| Domain | Action | Details |
|--------|--------|---------|
| `domain-events` | Created in main specs | Copied delta spec as full main spec |
| `event-outbox` | Created in main specs | Copied delta spec as full main spec |
| `webhook-subscriptions` | Created in main specs | Copied delta spec as full main spec |
| `billing/payment` | Merged delta | Added "PaymentReceived event on IPN approval" requirement |

## Open Items (Deferred to PR 2 & PR 3)

- OutboxRepository with get_pending/mark_sent
- Cache invalidation handlers
- RegisterAnimalCase event emission wiring
- Celery outbox forwarder task
- Webhook subscription model & dispatch with retry
- PaymentReceived event wiring in MP webhook handler
- Full integration tests for end-to-end event flow
- Outbox index strategy evaluation
- WebhookSubscription secret encryption approach

## Risks & Follow-ups

| Risk | Status | Action |
|------|--------|--------|
| Outbox index strategy | Open | Evaluate query pattern in PR 2 |
| WebhookSecret encryption | Deferred | HMAC per tenant for now; encrypt at DB layer if needed |
| Event schema drift | Low | Shared DomainEvent base class mitigates this |
