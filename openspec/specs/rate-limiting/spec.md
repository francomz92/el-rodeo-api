# Rate Limiting Specification — Global Defaults + Endpoint Overrides

## Purpose

Prevent abuse with default rate limits on all endpoints while preserving stricter limits on auth-sensitive endpoints. The rate limiter MUST enforce limits directly (no log-only mode).

## Requirements

### Requirement: Global default rate limit

The system MUST apply a default rate limit (e.g., 60/minute) to all endpoints not covered by a specific override. Health and metrics paths MUST remain exempt.

#### Scenario: Anonymous request within limit

- GIVEN an IP that has made 50 requests in the last minute
- WHEN the 51st request arrives at a generic endpoint
- THEN the response status is 200

#### Scenario: Global limit exceeded

- GIVEN an IP that has made 60 requests in the last minute
- WHEN the 61st request arrives
- THEN the response status is 429
- AND the response includes `Retry-After` header

#### Scenario: Health endpoint always exempt

- GIVEN an IP that has exceeded the global limit
- WHEN requesting `GET /health`
- THEN the response status is 200

### Requirement: Proxy-aware client IP detection

The rate limiter key function MUST use the `X-Forwarded-For` header when behind a reverse proxy, falling back to `X-Real-IP`, then `request.client.host`.

#### Scenario: Client behind proxy

- GIVEN a request with `X-Forwarded-For: 203.0.113.50`
- WHEN the rate limiter resolves the client key
- THEN `203.0.113.50` is used as the limiting key, not the proxy IP
