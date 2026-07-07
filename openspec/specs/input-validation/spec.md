# Input Validation Specification — Pydantic Constraint Hardening

## Purpose

Add missing numeric constraints (`gt`, `ge`), string length limits (`max_length`), and format validation to all domain input schemas to reject invalid data at the API boundary.

## Requirements

### Requirement: Non-negative numeric constraints for domain schemas

Monetary amounts, weights, and quantities in domain schemas MUST use `gt=0` or `ge=0` as appropriate to reject zero/negative values.

#### Scenario: Animal creation rejects non-positive weight

- GIVEN a request with `initial_weight: -5`
- WHEN `POST /cattle/animals` is called
- THEN the response status is 422
- AND the error indicates `initial_weight` must be greater than 0

#### Scenario: Sale creation rejects zero price

- GIVEN `price: 0` in `POST /market/sales`
- WHEN the request is validated
- THEN the response status is 422

#### Scenario: Purchase amount must be positive

- GIVEN `amount: -10` in `POST /finance/purchases`
- WHEN the request is validated
- THEN the response status is 422

### Requirement: String length constraints on all text fields

All text fields in create/update schemas (name, description, contact info) MUST have explicit `max_length`. Buyer names MUST have `min_length=1`.

#### Scenario: Buyer name exceeds max length

- GIVEN a buyer `name` of 256 characters
- WHEN `POST /market/buyers` is called
- THEN the response status is 422

#### Scenario: Supply name has max_length

- GIVEN a supply `name` of 200 characters
- WHEN `POST /finance/supplies` is called
- THEN the response status is 422
