# Logging Sanitization Specification — Redact Sensitive Data

## Purpose

Prevent sensitive data (query strings, tokens, credentials) from appearing in application logs, reducing log injection and information disclosure risk.

## Requirements

### Requirement: Query strings excluded from request logs

The system MUST NOT log the raw query string in request log entries. Query parameters that may contain sensitive data (tokens, codes) MUST be omitted or redacted.

#### Scenario: Query string absent from log

- GIVEN a request `GET /search?token=secret123&q=test`
- WHEN the `RequestLoggingMiddleware` logs the request
- THEN the log entry does NOT contain `token=secret123` or the raw query string
- AND the log entry still contains `method`, `path`, `correlation_id`, and `client_ip`

#### Scenario: Non-sensitive query parameters logged safely

- GIVEN a request `GET /api/items?page=1&per_page=20`
- WHEN the request is logged
- THEN the log entry MAY include sanitized query params but MUST NOT contain raw `?page=1&per_page=20`
