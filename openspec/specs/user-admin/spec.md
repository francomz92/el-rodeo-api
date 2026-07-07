# User Admin Specification

## Purpose

Admin user management — list, detail, and soft-delete users within the authenticated user's tenant. Restricted to ADMIN and OWNER roles.

## Requirements

### Requirement: List Users

The system MUST expose `GET /users` returning a paginated, tenant-scoped user list. Only ADMIN and OWNER users MAY access this endpoint. The response MUST contain `items`, `total`, `page`, and `per_page`. Search SHALL filter by name or email. Role filter SHALL restrict by `UserRole` value.

#### Scenario: ADMIN lists users

- GIVEN an authenticated ADMIN in tenant T1 with 30 users
- WHEN sending `GET /users?page=1&per_page=20`
- THEN the response status is 200
- AND `body.items` has 20 users, all from T1
- AND `body.total` is 30
- AND `body.page` is 1, `body.per_page` is 20

#### Scenario: Search by name fragment

- GIVEN users "Alice", "Bob", "Alison" in tenant T1
- WHEN sending `GET /users?search=Ali`
- THEN `body.items` contains "Alice" and "Alison" but not "Bob"

#### Scenario: Filter by role

- GIVEN EDITORS and VIEWERS in tenant T1
- WHEN sending `GET /users?role=editor`
- THEN every item in `body.items` has `role` "editor"

#### Scenario: VIEWER gets 403

- GIVEN an authenticated VIEWER
- WHEN sending `GET /users`
- THEN the response status is 403

### Requirement: Get User Detail

The system MUST expose `GET /users/{id}` returning a single user's profile. The target user MUST belong to the same tenant as the requester. Only ADMIN and OWNER MAY access.

#### Scenario: ADMIN views user detail

- GIVEN an ADMIN in T1 and a target user in T1
- WHEN sending `GET /users/{target_id}`
- THEN the response status is 200
- AND `body.id` equals `target_id`

#### Scenario: Cross-tenant isolation

- GIVEN an ADMIN in T1 and a target user in T2
- WHEN sending `GET /users/{target_id}`
- THEN the response status is 404

### Requirement: Soft-Delete User

The system MUST expose `DELETE /users/{id}` setting `is_active=false` for the target user. Self-deletion MUST be rejected. Deleting the last OWNER of a tenant MUST be rejected. Only ADMIN and OWNER MAY access.

#### Scenario: ADMIN soft-deletes a VIEWER

- GIVEN an ADMIN and a target VIEWER in the same tenant
- WHEN sending `DELETE /users/{target_id}`
- THEN the response status is 200
- AND `target.is_active` is `false` in the database

#### Scenario: Self-deletion rejected

- GIVEN an authenticated ADMIN
- WHEN sending `DELETE /users/{own_id}`
- THEN the response status is 400

#### Scenario: Last owner deletion rejected

- GIVEN a tenant with exactly one OWNER
- WHEN sending `DELETE /users/{owner_id}`
- THEN the response status is 400
- AND the owner remains active

#### Scenario: Soft-deleted user cannot log in

- GIVEN a user with `is_active=false`
- WHEN calling `POST /login` with valid credentials
- THEN the response status is 401
