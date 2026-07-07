# GDPR Compliance Specification

## Purpose

Enable data portability and right-to-erasure as required by GDPR Article 15 (right of access) and Article 17 (right to erasure) for PII stored across all bounded contexts.

## PII Inventory

| Table | PII Fields | Action on Delete |
|-------|-----------|------------------|
| `users` | name, dni, email | Anonymize: name→'Anonymized', email→hash, dni→null |
| `buyers` | name, contact_number, contact_address | Anonymize: all PII→'Anonymized' |
| Business records (sales, purchases, animals, protocols, events) | user_id (FK) | NULLify user_id |

## Requirements

### R1: GDPR Data Export

The system MUST provide `GET /users/me/export` returning a JSON blob of all user data.

#### Scenario: Successful export

- GIVEN an authenticated user with associated records
- WHEN `GET /users/me/export` is called
- THEN a JSON response contains: user profile, buyers linked to this user, sales, animals, animal protocols, schedule events, purchases, financial records
- AND no credentials (password hashes, refresh tokens) are included

#### Scenario: No associated records

- GIVEN a user with no business records
- WHEN the export endpoint is called
- THEN the JSON returns `{"user": {...}, "records": {}}` with empty collections

#### Scenario: Auth required

- GIVEN an unauthenticated request
- WHEN `GET /users/me/export` is called
- THEN 401 Unauthorized is returned

#### Scenario: Role protection

- GIVEN an authenticated user with VIEWER role
- WHEN the export endpoint is called
- THEN access is granted (minimum role: VIEWER)

### R2: GDPR Data Deletion

The system MUST provide `DELETE /users/me/data` that initiates data anonymization.

#### Scenario: Async deletion accepted

- GIVEN an authenticated user
- WHEN `DELETE /users/me/data` is called
- THEN 202 Accepted is returned
- AND the response includes a tracking ID for the async operation

#### Scenario: Account disabled

- GIVEN a user account
- WHEN GDPR delete executes
- THEN the user account is disabled (login blocked, `is_active=False` or equivalent)
- AND the user record is NOT deleted (preserves referential integrity)

#### Scenario: PII anonymized

- GIVEN a user with PII data
- WHEN GDPR delete executes
- THEN `users.name` → `'Anonymized'`
- AND `users.email` → SHA-256 hashed original
- AND `users.dni` → `null`
- AND `password` → `'ANONYMIZED_ACCOUNT'` (invalid hash)

#### Scenario: Business record NULLification

- GIVEN business records referencing the user (sales, purchases, animals)
- WHEN GDPR delete executes
- THEN `user_id` on those records is set to NULL
- AND the records remain intact for tenant analytics

#### Scenario: Token revocation

- GIVEN active refresh tokens for the user
- WHEN GDPR delete executes
- THEN all user tokens are revoked via `revoke_all_user_tokens()`

#### Scenario: Auth required

- GIVEN an unauthenticated request
- WHEN `DELETE /users/me/data` is called
- THEN 401 Unauthorized is returned

### Constraints

- Export is SYNCHRONOUS — returns JSON directly in the HTTP response
- Delete is ASYNCHRONOUS — returns 202, executes in background task
- Deletion NEVER destroys business data — only anonymizes PII and NULLifies FK
- Role minimum: VIEWER for both endpoints
- Anonymization is IRREVERSIBLE — no recovery of original PII
