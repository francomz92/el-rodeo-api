# Domain Events Specification

## Purpose

Defines the DomainEvent base class, the IEventBus port for synchronous dispatch, the InMemoryEventBus implementation, and typed event definitions (AnimalCreated, PaymentReceived).

## Requirements

### Requirement: DomainEvent base class

The system MUST define a DomainEvent base dataclass with: `event_id: UUID` (generated on creation), `aggregate_id: UUID`, `event_type: str`, `timestamp: datetime` (auto-set to UTC now), `metadata: dict[str, Any]` (default empty dict).

#### Scenario: Event created with defaults

- GIVEN aggregate_id="agg-123" and event_type="animal.created"
- WHEN a new DomainEvent is created
- THEN event_id is a non-null UUID and timestamp is set to current UTC time

#### Scenario: Event with custom metadata

- GIVEN caller provides metadata={"trace_id": "abc"}
- WHEN a DomainEvent is created with that metadata
- THEN event.metadata contains the provided entries

### Requirement: IEventBus port

The system MUST define `IEventBus` with `register(event_type, handler)` and `dispatch(event)`. Dispatch MUST call all registered handlers for event.event_type synchronously. A handler exception MUST NOT prevent other handlers from executing.

#### Scenario: Single handler dispatched

- GIVEN a handler registered for "animal.created"
- WHEN dispatch executes with an event of that type
- THEN the handler is called exactly once with the event

#### Scenario: Handler exception does not block others

- GIVEN two handlers for "animal.created" where the first raises
- WHEN dispatch is called
- THEN the second handler still receives the event

### Requirement: InMemoryEventBus

The system MUST provide an `InMemoryEventBus` implementing IEventBus. It SHALL store handlers per event_type in dict of lists and dispatch them in registration order.

#### Scenario: Multiple handlers per event type

- GIVEN three handlers registered for "payment.received"
- WHEN dispatch is called
- THEN all three handlers are invoked in registration order

### Requirement: Typed domain events

The system MUST define concrete `AnimalCreated(event_type="animal.created", aggregate_id=animal_id)` and `PaymentReceived(event_type="payment.received", aggregate_id=payment_id)` classes inheriting from DomainEvent.

#### Scenario: AnimalCreated carries animal_id

- GIVEN an animal_registered use-case completes with animal_id="cow-42"
- WHEN AnimalCreated(aggregate_id="cow-42") is instantiated
- THEN event.event_type is "animal.created" and event.aggregate_id is "cow-42"
