# Connection Pool Tuning Specification

## Purpose

Review and adjust database connection pool settings (`pool_size`, `max_overflow`, `pool_recycle`) to prevent connection starvation under peak load while avoiding memory exhaustion from idle connections.

## Requirements

### Requirement: Pool setting review under synthetic load

The system MUST benchmark connection usage under a synthetic load test that simulates peak concurrent requests. Based on results, `pool_size`, `max_overflow`, and `pool_recycle` MAY be adjusted from their current values (`pool_size=10`, `max_overflow=20`).

#### Scenario: Pool does not exhaust under peak load

- GIVEN synthetic load matching expected peak concurrency
- WHEN all workers handle requests simultaneously
- THEN no `TimeoutError` from SQLAlchemy connection pool occurs
- AND active connection count stays below `pool_size + max_overflow`

#### Scenario: Stale connections are recycled

- GIVEN a connection idle beyond `pool_recycle` seconds
- WHEN that connection is checked out for a new request
- THEN SQLAlchemy reconnects transparently (no `OperationalError: server closed the connection`)

### Requirement: Tuned settings documented in config

Final `pool_size`, `max_overflow`, and `pool_recycle` values MUST be documented with the rationale in the DB connection module (`src/common/infrastructure/persistence/connections/db.py`). The values MUST be overridable via environment variables.

#### Scenario: Pool settings overridable via env

- GIVEN env vars `DB_POOL_SIZE=20`, `DB_POOL_OVERFLOW=10`
- WHEN the application starts
- THEN the SQLAlchemy engine uses `pool_size=20`, `max_overflow=10`

#### Scenario: Default pool values documented

- GIVEN the production config file
- WHEN inspecting the pool settings
- THEN a comment or docstring explains the chosen values and load test results that justified them
