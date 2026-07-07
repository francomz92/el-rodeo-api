# Request Body Size Limit Specification

## Purpose

Enforce maximum request body size to prevent resource exhaustion attacks on all endpoints.

## Requirements

### Requirement: Reject oversized request bodies with 413

The system MUST enforce a configurable maximum request body size (default: 10 MB). Requests exceeding the limit MUST be rejected with HTTP 413 before reaching any route handler.

#### Scenario: Oversized POST rejected

- GIVEN a POST request with a body of 2 MB
- WHEN the body size limit middleware processes the request
- THEN the response status is 413
- AND the response body explains the size limit was exceeded

#### Scenario: Normal-sized request passes through

- GIVEN a POST request with a body of 100 KB
- WHEN the middleware processes the request
- THEN the request reaches the route handler normally

#### Scenario: Configurable via settings

- GIVEN `MAX_REQUEST_BODY_SIZE` set to `5 * 1024 * 1024` (5 MB)
- WHEN a 3 MB request arrives
- THEN the request is accepted
