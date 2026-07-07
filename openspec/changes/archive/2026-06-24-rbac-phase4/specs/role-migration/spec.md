# role-migration — Specification

## Purpose
Add the `role` column to the `users` table, backfill from `is_admin`, add a CHECK constraint, and keep `is_admin` for dual-read during transition.

## Requirements

### Requirement: Column addition and CHECK constraint

The migration MUST add `role VARCHAR(20) NOT NULL DEFAULT 'viewer'` to the `users` table, add CHECK (role IN ('viewer','editor','admin','owner')), and keep the existing `is_admin` column.

#### Scenario: Migration applies cleanly
- GIVEN existing users table with is_admin column
- WHEN the migration runs
- THEN role column exists with CHECK constraint, is_admin column remains

### Requirement: Data backfill

The migration MUST backfill: `is_admin = True` → `role = 'admin'`, `is_admin = False` → `role = 'viewer'`.

#### Scenario: Admin users get admin role
- GIVEN an existing user with is_admin=True
- AFTER the backfill migration
- THEN role == "admin"

#### Scenario: Non-admin users get viewer role
- GIVEN an existing user with is_admin=False
- AFTER the backfill migration
- THEN role == "viewer"
