# Data Retention Specification

## Purpose

Automated lifecycle management for audit data with configurable time-to-live and monthly partition housekeeping.

## Requirements

### R1: Configurable Retention Period

The system MUST read `AUDIT_RETENTION_DAYS` from environment configuration with a default of 180 days (6 months).

#### Scenario: Default retention

- GIVEN no `AUDIT_RETENTION_DAYS` env var is set
- WHEN the system starts
- THEN retention period is 180 days

#### Scenario: Custom retention

- GIVEN `AUDIT_RETENTION_DAYS=90`
- WHEN the system starts
- THEN retention period is 90 days

#### Scenario: Invalid value

- GIVEN `AUDIT_RETENTION_DAYS=0` or negative
- WHEN the system starts
- THEN the system MUST use the default of 180 days
- AND a warning is logged

### R2: Partition Drop Task

The system MUST provide a scheduled task (or CLI command) that DROPs partitions whose entire date range is older than `AUDIT_RETENTION_DAYS + 1 month` (the grace month).

#### Scenario: Old partition dropped

- GIVEN partition `audit_log_2026_01` covers Jan 2026
- GIVEN current date is 2026-07-01 and retention is 180 days
- WHEN the retention task runs
- THEN partition `audit_log_2026_01` is DROPped

#### Scenario: Active partition preserved

- GIVEN partition `audit_log_2026_06` covers Jun 2026
- GIVEN current date is 2026-07-01 and retention is 180 days
- WHEN the retention task runs
- THEN the partition is NOT dropped

#### Scenario: No partitions to drop

- GIVEN all partitions are within retention period
- WHEN the retention task runs
- THEN the task completes successfully with no action

### R3: Retention Change Warning

The system SHOULD log a WARNING-level message when `AUDIT_RETENTION_DAYS` changes from its previously stored value.

#### Scenario: Retention value changed

- GIVEN retention was 180 days and is now 90
- WHEN the system starts
- THEN a warning is logged: `AUDIT_RETENTION_DAYS changed from 180 to 90`

### R4: Partition Management Ownership

The system MAY use either an in-app scheduled task or an external tool (e.g., `pg_partman`) for partition management. The decision is deferred to design phase.

### Constraints

- Retention applies ONLY to `audit_log` partitions — no other tables are affected
- Partition drop is IRREVERSIBLE — data is permanently deleted
- Minimum 1 month grace beyond retention period to avoid data loss from timezone/latency
- The retention task MUST be idempotent (safe to run multiple times)
