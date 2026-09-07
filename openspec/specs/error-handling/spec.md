# Error Handling Specification — Safe 500 Responses

## Purpose

Prevent information disclosure via unhandled exceptions. The internal exception details MUST NOT reach the HTTP response body; the real error MUST be logged server-side only.

## Requirements

### Requirement: Generic 500 response with server-side logging

The system MUST return a generic `"Internal server error"` for all unhandled exceptions, EXCEPT for `StarletteHTTPException` which MUST return its original status code. The `StarletteHTTPException` handler MUST be registered BEFORE the generic `Exception` handler to take MRO precedence. Both handlers MUST use the `StandardErrorResponse` format. The original exception detail MUST be written to the application log and MUST NOT appear in the response body.
(Previously: all unhandled exceptions returned 500 regardless of status code)

#### Scenario: Unhandled exception returns generic message

- GIVEN a request that raises an unhandled `ValueError("connection timeout")`
- WHEN the `server_exception_handler` processes the exception
- THEN the response status is 500
- AND the response body contains `"Internal server error"`, NOT `"connection timeout"`
- AND the log contains `"connection timeout"` associated with the correlation ID

#### Scenario: Log contains correlation ID for debugging

- GIVEN a failing request with `X-Request-ID: abc-123`
- WHEN the exception is logged
- THEN the log entry includes `correlation_id=abc-123` and the original exception string

#### Scenario: HTTPException returns original status code

- GIVEN a request that raises `HTTPException(status_code=404, detail="not found")`
- WHEN the `starlette_http_exception_handler` processes the exception
- THEN the response status is 404, NOT 500
- AND the response body uses the `StandardErrorResponse` format
