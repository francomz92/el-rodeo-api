# Billing — Payment History Specification

## Purpose

Defines the payment history query endpoint for tenants to view their past payments.

## Requirements

### Requirement: GET /billing/payments endpoint

The system MUST expose `GET /billing/payments` returning paginated payments for the current tenant, ordered by `created_at DESC`. Query params: `limit` (default 20, max 100), `offset` (default 0). Each payment SHALL include: id, amount, currency, status, description, payment_method, paid_at, created_at.

#### Scenario: List payments with pagination

- GIVEN an authenticated tenant with 3 payments on record
- WHEN a GET request to `/billing/payments?limit=2&offset=0` is sent
- THEN the response returns 2 payments ordered by created_at DESC
- AND the response includes `remaining` count indicating 1 more page

#### Scenario: No payments returns empty list

- GIVEN an authenticated tenant with no payments
- WHEN a GET request to `/billing/payments` is sent
- THEN the response returns an empty list with `remaining=0`

### Requirement: Tenant isolation

The system MUST only return payments belonging to the authenticated tenant. Cross-tenant access MUST be prevented.

#### Scenario: Cross-tenant isolation

- GIVEN tenant A has 3 payments and tenant B has 2 payments
- WHEN tenant A requests `/billing/payments`
- THEN only tenant A's payments are returned
