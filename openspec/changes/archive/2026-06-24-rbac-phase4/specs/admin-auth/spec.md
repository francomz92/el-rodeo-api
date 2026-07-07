# admin-auth — Specification (Modified Capability)

## ADDED Requirements

### Requirement: is_admin_user delegates to require_role

The system MUST replace the internal admin check in `_get_current_admin_user` (or equivalent) with `Depends(require_role(UserRole.ADMIN))` for tenant-scoped authorization. The `is_admin` field remains orthogonal for cross-tenant super-admin bypass.

#### Scenario: ADMIN passes the guard
- GIVEN a user with role ADMIN
- WHEN accessing a route with Depends(require_role(UserRole.ADMIN))
- THEN access is granted

#### Scenario: EDITOR rejected from admin route
- GIVEN a user with role EDITOR
- WHEN accessing a route with Depends(require_role(UserRole.ADMIN))
- THEN response is HTTP 403

### Requirement: Route protection matrix

Each bounded context MUST apply role guards per this matrix:

| Context | Router | GET (list) | GET (by id) | POST | PUT | DELETE |
|---------|--------|-----------|-------------|------|-----|--------|
| Cattle | `_animal_types.py` (3 routes) | VIEWER | — | ADMIN | ADMIN | — |
| Cattle | `_animals.py` (5 routes) | VIEWER | VIEWER | EDITOR | EDITOR | ADMIN |
| Cattle | `_animal_protocols.py` (5 routes) | VIEWER | VIEWER | — | EDITOR | ADMIN |
| Cattle | `_schedule_events.py` (4 routes) | VIEWER | — | EDITOR | EDITOR | ADMIN |
| Finance | `_animal_supply_types.py` (5 routes) | VIEWER | VIEWER | ADMIN | ADMIN | ADMIN |
| Finance | `_animal_supplies.py` (5 routes) | VIEWER | VIEWER | EDITOR | EDITOR | ADMIN |
| Finance | `_purchases.py` (4 routes) | VIEWER | VIEWER | EDITOR | EDITOR | ADMIN |
| Market | `_buyers.py` (5 routes) | VIEWER | VIEWER | EDITOR | EDITOR | ADMIN |
| Market | `_sales.py` (4 routes) | VIEWER | VIEWER | EDITOR | EDITOR | ADMIN |

#### Scenario: VIEWER can only read
- GIVEN a VIEWER user
- WHEN calling any POST/PUT/DELETE across cattle, finance, or market
- THEN response is HTTP 403

#### Scenario: EDITOR can create and update, cannot delete
- GIVEN an EDITOR user
- WHEN calling any DELETE endpoint
- THEN response is HTTP 403

#### Scenario: ADMIN has full CRUD within tenant
- GIVEN an ADMIN user
- WHEN calling any endpoint within their tenant
- THEN access is granted for all operations
