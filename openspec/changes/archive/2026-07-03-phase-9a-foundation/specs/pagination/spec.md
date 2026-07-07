# Cursor-Based Pagination Specification

## Purpose

Reusable cursor-based pagination schema with `CursorPage[T]` generic model and query helpers, replacing limit/offset in list endpoints for stable ordering under concurrent writes.

## Requirements

### Requirement: CursorPage[T] generic schema

The system MUST define a generic Pydantic model `CursorPage[T]` with fields: `items: list[T]`, `cursor: str | None` (cursor of first item), `next_cursor: str | None` (cursor for next page), `has_next: bool` (derived from next_cursor), `total: int`. Cursors MUST be opaque, Base64-encoded strings.

#### Scenario: First page returns cursor for next page

- GIVEN 25 items in the database
- WHEN querying with `limit=10`
- THEN `items` contains 10 items, `next_cursor` is a non-null string, `total` is 25

#### Scenario: Last page returns null next_cursor

- GIVEN 5 items in the database
- WHEN querying with `limit=10`
- THEN `items` contains 5 items, `next_cursor` is null, `total` is 5

#### Scenario: Cursor is opaque and stable

- GIVEN a cursor string from a previous page response
- WHEN decoding the cursor
- THEN it does not expose database internals (e.g., raw IDs)

### Requirement: Backward-compatible query params

Existing list endpoints MUST keep `offset`/`limit` as deprecated parameters alongside new `cursor`/`limit`. Deprecated params MUST emit a warning but continue to work.

#### Scenario: New cursor params work on endpoint

- GIVEN an endpoint `/api/animals` originally using `offset`/`limit`
- WHEN sending `GET /api/animals?cursor=abc&limit=10`
- THEN the response uses cursor pagination and returns `CursorPage` format

#### Scenario: Old offset/limit still function

- GIVEN the same endpoint
- WHEN sending `GET /api/animals?offset=0&limit=10`
- THEN the response uses limit/offset pagination (deprecated) and succeeds

### Requirement: Cursor query helper for repositories

The system SHOULD provide a repository-level cursor helper that translates cursor tokens to SQL WHERE clauses (e.g., `WHERE id > :cursor_value ORDER BY id ASC LIMIT :limit`).

#### Scenario: Cursor-based query returns next page

- GIVEN items with IDs 1 through 20
- WHEN querying with cursor pointing to ID 10, limit=5
- THEN items with IDs 11, 12, 13, 14, 15 are returned
