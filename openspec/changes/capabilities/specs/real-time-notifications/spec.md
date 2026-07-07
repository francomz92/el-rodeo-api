# Real-Time Notifications Specification

## Purpose

Server-to-client real-time notification capability using WebSocket connections with Redis Pub/Sub for cross-instance fan-out. When a domain event is dispatched, all WebSocket connections for the affected tenant receive a notification. This enables live UI updates without polling.

## Requirements

### Requirement: WebSocket connection manager

The system MUST provide a `ConnectionManager` that maintains per-tenant WebSocket connections in an in-memory dict: `dict[UUID, set[WebSocket]]`. It SHALL support:

- `connect(ws, tenant_id)` — add connection and store tenant mapping.
- `disconnect(ws)` — remove connection and clean up.
- `broadcast(tenant_id, message)` — send JSON to all connections for a tenant; failed sends SHALL disconnect and remove the failed connection.

#### Scenario: Connect adds to tenant set

- GIVEN a WebSocket connection for tenant `"t1"`
- WHEN `connect(ws, "t1")` is called
- THEN `"t1"` maps to a set containing that WebSocket

#### Scenario: Disconnect removes from tenant set

- GIVEN a connected WebSocket for tenant `"t1"`
- WHEN `disconnect(ws)` is called
- THEN the WebSocket is removed from `"t1"`'s set
- AND if the set is empty, the tenant key is deleted

#### Scenario: Broadcast skips stale connections

- GIVEN tenant `"t1"` has 3 connections, one of which is closed
- WHEN `broadcast("t1", {"type": "test"})` is called
- THEN the closed connection is removed
- AND the other 2 connections receive the message

### Requirement: WebSocket endpoint with JWT auth

The system MUST expose a WebSocket endpoint at `/ws/notifications` accepting a JWT token via query parameter `token`. The endpoint SHALL:

- Accept upgrade only.
- Validate the JWT on connect.
- Extract `tenant_id` from the token payload.
- Close with code 4001 if the token is missing, expired, or invalid.
- Close with code 4001 if the tenant cannot be resolved.

#### Scenario: Valid token connects successfully

- GIVEN a valid JWT with `tenant_id` claim
- WHEN a WebSocket connects to `/ws/notifications?token={valid_jwt}`
- THEN the connection is accepted
- AND the connection is registered under the tenant from the token

#### Scenario: Missing token rejected with 4001

- GIVEN no token query parameter
- WHEN a WebSocket connects to `/ws/notifications`
- THEN the connection is closed with code 4001

#### Scenario: Expired token rejected with 4001

- GIVEN an expired JWT
- WHEN a WebSocket connects to `/ws/notifications?token={expired_jwt}`
- THEN the connection is closed with code 4001

### Requirement: Redis Pub/Sub cross-instance fan-out

The system MUST publish each domain event to a Redis Pub/Sub channel `notifications:{tenant_id}`. A background asyncio task SHALL subscribe to Redis Pub/Sub on startup and forward received messages to the local `ConnectionManager` for the matching tenant.

#### Scenario: Event published to Redis channel

- GIVEN a tenant `"t1"` with a connected WebSocket
- WHEN a domain event for tenant `"t1"` is dispatched
- THEN a JSON message is published to Redis channel `notifications:t1`
- AND the WebSocket connection receives the notification

#### Scenario: Background subscriber forwards messages

- GIVEN the background subscriber is running
- WHEN a message is published to `notifications:t1` (from another instance)
- THEN the subscriber receives it from Redis
- AND forwards it to all local connections for tenant `"t1"`

### Requirement: EventBus handler integration

The system MUST register a WebSocket notification handler on the `IEventBus` that, for every dispatched domain event, publishes to the matching Redis Pub/Sub channel. The handler SHALL extract `tenant_id` from event metadata.

#### Scenario: Handler registered for all events

- GIVEN an `IEventBus` instance
- WHEN an `animal.created` event is dispatched with metadata containing `tenant_id`
- THEN the WebSocket handler is invoked
- AND the event is published to `notifications:{tenant_id}`

### Requirement: Reconnect on Redis failure

The background subscriber MUST log a warning on Redis connection loss and retry with exponential backoff (1s, 2s, 4s, max 30s). It SHALL NOT crash the application.

#### Scenario: Redis reconnects after temporary failure

- GIVEN the background subscriber is running
- WHEN the Redis connection drops
- THEN a warning is logged
- AND the subscriber retries with backoff
- AND when Redis is available again, subscriptions are re-established
