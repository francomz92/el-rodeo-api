# Webhook Subscriptions Specification

## Purpose

Defines the tenant-scoped webhook subscription entity, HTTP dispatch with HMAC signing and retry/backoff, and dead-letter policy after N consecutive failures.

## Requirements

### Requirement: WebhookSubscription entity

The system MUST define a WebhookSubscription entity with: `id: UUID`, `tenant_id: UUID`, `url: str` (valid HTTPS), `secret: str` (HMAC key), `subscribed_events: list[str]`, `is_active: bool` (default True), `failure_count: int` (default 0), `last_error: str | None`, `last_attempt_at: datetime | None`, `created_at: datetime`, `updated_at: datetime`. The secret SHOULD be stored encrypted at rest.

#### Scenario: Active subscription matches event type

- GIVEN a subscription with subscribed_events=["payment.received"] and is_active=True
- WHEN a "payment.received" event is dispatched
- THEN the subscription URL is enqueued for delivery

#### Scenario: Inactive subscription is skipped

- GIVEN a subscription with is_active=False
- WHEN any event is dispatched
- THEN the subscription is NOT enqueued

### Requirement: Webhook dispatch with retry

The system MUST POST the event payload as JSON with HMAC-SHA256 signature in the X-Signature header. On 5xx or network error, it MUST retry with exponential backoff (1s, 2s, 4s, 8s, 16s) up to 5 attempts total.

#### Scenario: Successful delivery

- GIVEN a subscription with url="https://example.com/hook" and secret="s3cr3t"
- WHEN the dispatcher POSTs the event
- THEN the remote receives a valid HMAC-signed JSON payload and responds 200

#### Scenario: Retry on 5xx

- GIVEN the remote returns 500 on first attempt
- WHEN the dispatcher retries with backoff
- THEN up to 5 attempts are made before failure is declared

### Requirement: Dead-letter policy

After 5 consecutive failed delivery attempts, the system SHALL mark the subscription as dead-lettered (is_active=False) and record failure metadata. Dead-lettered subscriptions SHOULD be retried via a separate manual or scheduled process.

#### Scenario: Subscription dead-lettered after 5 failures

- GIVEN a subscription where all 5 delivery attempts failed
- WHEN the last attempt fails
- THEN is_active is set to False, failure_count=5, and last_error is recorded
