# Event Outbox Specification

## Purpose

Defines the EventOutbox ORM model, the outbox repository with UoW integration, flush on commit, and a Celery forwarder task to dispatch unprocessed entries to async handlers.

## Requirements

### Requirement: EventOutbox ORM model

The system MUST define an EventOutbox SQLAlchemy model with columns: `id: UUID` (PK), `event_id: UUID`, `event_type: str`, `aggregate_id: UUID`, `payload: JSON`, `status: OutboxStatus` (PENDING, SENT, FAILED), `created_at: datetime`, `processed_at: datetime | None`, `retry_count: int` (default 0).

#### Scenario: Row created on async dispatch

- GIVEN an event with event_id="evt-1" and event_type="payment.received"
- WHEN an async handler schedules an outbox entry
- THEN a new EventOutbox row is created with status=PENDING and retry_count=0

#### Scenario: Status transitions to SENT

- GIVEN a PENDING row
- WHEN the Celery forwarder dispatches successfully
- THEN status becomes SENT and processed_at is set

### Requirement: OutboxRepository

The system MUST provide an OutboxRepository with `add(event)` (queues in UoW memory), `get_pending(limit) -> list`, and `mark_sent(outbox_id)`. All methods are async.

#### Scenario: Pending rows retrieved in batches

- GIVEN 50 PENDING rows
- WHEN get_pending(limit=10) is called
- THEN exactly 10 rows are returned

#### Scenario: Mark sent after dispatch

- GIVEN a PENDING row with id="row-1"
- WHEN mark_sent("row-1") is called
- THEN status becomes SENT and processed_at is set to now

### Requirement: UoW flush on commit

The system MUST add a before-commit hook in UoW.commit() that flushes queued outbox rows as part of the same transaction. On rollback, the in-memory queue SHALL be cleared.

#### Scenario: Rows flushed atomically

- GIVEN a use-case queues 3 events in the outbox
- WHEN UoW.commit() succeeds
- THEN 3 EventOutbox rows are persisted in the same transaction

#### Scenario: Queue cleared on rollback

- GIVEN a use-case queues 2 events but the transaction fails
- WHEN rollback is triggered
- THEN no rows are persisted and the in-memory queue is cleared

### Requirement: Celery outbox forwarder

The system MUST provide a Celery periodic task that queries PENDING rows, dispatches async handlers (email, webhook), and marks rows SENT on success or increments retry_count on failure.

#### Scenario: Forwarder processes pending rows

- GIVEN 3 PENDING rows exist
- WHEN the Celery forwarder runs
- THEN each row is dispatched to its async handlers and marked SENT

#### Scenario: Failed dispatch increments retry

- GIVEN a PENDING row whose dispatch raises an exception
- WHEN the forwarder processes it
- THEN retry_count is incremented and status stays PENDING
