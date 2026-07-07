# CORS & Trusted Hosts Specification — Environment-Aware

## Purpose

Replace permissive `["*"]` defaults with environment-aware CORS origins and TrustedHost validation. Production and staging MUST reject unauthorized origins and hosts.

## Requirements

### Requirement: Environment-aware CORS origins

The system MUST reject origins not in `ALLOWED_ORIGINS` for non-development environments. The `["*"]` wildcard MUST be allowed ONLY when `ENVIRONMENT=development`.

#### Scenario: Production rejects unknown origin

- GIVEN `ENVIRONMENT=production` and `ALLOWED_ORIGINS=["https://app.elrodeo.com"]`
- WHEN a request arrives with `Origin: https://evil.com`
- THEN the response lacks `Access-Control-Allow-Origin`

#### Scenario: Development allows wildcard

- GIVEN `ENVIRONMENT=development` and `ALLOWED_ORIGINS=["*"]`
- WHEN a request arrives from any origin
- THEN CORS headers permit the request

### Requirement: TrustedHost validation per environment

The system MUST validate the `Host` header against `TRUSTED_HOSTS`. Wildcard `["*"]` MUST be replaced with explicit hosts in production.

#### Scenario: Production rejects unknown host

- GIVEN `ENVIRONMENT=production` and `TRUSTED_HOSTS=["api.elrodeo.com"]`
- WHEN a request arrives with `Host: evil.com`
- THEN the response status is 400
