# Delta for billing/plan

## ADDED Requirements

### Requirement: Seed data pricing

The system SHALL seed the following prices. FREE plan SHALL have `price_monthly=Decimal("0.00")` and `price_yearly=None` — it is a read-only grace state, not a purchasable tier.

#### Scenario: FREE plan price is zero

- GIVEN seed data is loaded
- WHEN the FREE plan is retrieved
- THEN `plan.price_monthly` equals `Decimal("0.00")`
- AND the payment gateway MUST NOT create a checkout preference for FREE

#### Scenario: Paid plans have non-zero prices

- GIVEN seed data is loaded
- WHEN the PRO and ENTERPRISE plans are retrieved
- THEN `plan.price_monthly` is greater than `Decimal("0.00")`

## MODIFIED Requirements

### Requirement: Seed Data Table

The seed data table MUST include monthly and yearly prices for reference. Unit: ARS.
(Previously: seed data lacked price information)

| Plan | price_monthly | price_yearly | Tenants | Animals | Sales/month | Users | Features |
|------|--------------|--------------|---------|---------|-------------|-------|----------|
| FREE | $0 | — | 1 | 50 | 100 | 5 | None |
| PRO | $15 | $150 | 3 | 500 | 1000 | 25 | CSV export |
| ENTERPRISE | $50 | $500 | -1 | -1 | -1 | -1 | All features |

- `-1` means unlimited. FREE is a grace state (not purchasable, read-only).
