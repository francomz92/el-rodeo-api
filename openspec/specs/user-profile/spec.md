# User Profile Specification

## Purpose

Self-service profile management for authenticated users. No admin elevation required — any authenticated user can read and update their own profile.

## Requirements

### Requirement: Get Current User Profile

The system MUST expose `GET /users/me` returning the authenticated user's full profile. The response MUST contain `id`, `name`, `dni`, `email`, `role`, `is_active`, `tenant_id`, and `created_at`.

#### Scenario: Authenticated user reads own profile

- GIVEN an authenticated user with a valid Bearer token
- WHEN sending `GET /users/me`
- THEN the response status is 200
- AND the body includes `id`, `name`, `dni`, `email`, `role`, `is_active`, `tenant_id`, `created_at`

#### Scenario: Unauthenticated request is rejected

- GIVEN no Bearer token
- WHEN sending `GET /users/me`
- THEN the response status is 401

### Requirement: Update Current User Profile

The system MUST expose `PUT /users/me` allowing the authenticated user to update `name` and/or `email`. If the new email is already taken by another active user, the system MUST reject with HTTP 409. The `name` field MUST have a `max_length` constraint of 100 characters. The `email` field MUST use Pydantic's `EmailStr` type for format validation. The response MUST return the full updated `UserSchema`.
(Previously: name and email had no max_length or format constraints)

#### Scenario: User updates name within limit

- GIVEN an authenticated user
- WHEN sending `PUT /users/me` with `{"name": "New Name"}`
- THEN the response status is 200
- AND `body.name` equals "New Name"

#### Scenario: User updates email with valid format

- GIVEN an authenticated user
- WHEN sending `PUT /users/me` with `{"email": "new@example.com"}`
- THEN the response status is 200
- AND `body.email` equals "new@example.com"

#### Scenario: Duplicate email rejected

- GIVEN another user with email "taken@example.com"
- WHEN sending `PUT /users/me` with `{"email": "taken@example.com"}`
- THEN the response status is 409

#### Scenario: Name exceeds max_length rejected

- GIVEN an authenticated user
- WHEN sending `PUT /users/me` with a `name` longer than 100 characters
- THEN the response status is 422
- AND the error indicates `name` exceeds maximum length

#### Scenario: Invalid email format rejected

- GIVEN an authenticated user
- WHEN sending `PUT /users/me` with `{"email": "not-an-email"}`
- THEN the response status is 422
- AND the error indicates invalid email format

#### Scenario: Unauthenticated update rejected

- GIVEN no Bearer token
- WHEN sending `PUT /users/me`
- THEN the response status is 401
