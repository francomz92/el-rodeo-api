# Delta for rbac

## MODIFIED Requirements

### Requirement: Route protection matrix — user management (admin-auth)

The system MUST extend the route protection matrix with user management routes:

| Context | Router | GET (list) | GET (by id) | PUT | DELETE |
|---------|--------|-----------|-------------|-----|--------|
| Auth | `_user_routers.py` (profile) | VIEWER | — | VIEWER | — |
| Auth | `_user_routers.py` (admin) | ADMIN | ADMIN | — | ADMIN |

(Previously: auth routes were not listed in the protection matrix)

#### Scenario: VIEWER can access own profile

- GIVEN a VIEWER user
- WHEN calling `GET /users/me` and `PUT /users/me`
- THEN access is granted (200)

#### Scenario: VIEWER cannot access admin routes

- GIVEN a VIEWER user
- WHEN calling `GET /users`, `GET /users/{id}`, or `DELETE /users/{id}`
- THEN response is 403

#### Scenario: ADMIN has full access

- GIVEN an ADMIN user
- WHEN calling any profile or admin user-management route
- THEN access is granted for all operations (200)
