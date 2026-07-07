# Billing — Plan Specification

## Purpose

Defines the Plan entity, Feature/Quota value objects, and seed data for SaaS tier management. Plans are immutable seed data — not user-creatable — loaded on migration.

## Requirements

### Requirement: Plan entity

The system MUST define a Plan dataclass with: `id: UUID`, `name: str`, `features: list[Feature]`, `quotas: list[Quota]`, `price_monthly: Decimal`, `price_yearly: Decimal | None`.

#### Scenario: Plan creation from seed data

- GIVEN the system starts with no plans
- WHEN Alembic migration runs seed step
- THEN plans FREE, PRO, and ENTERPRISE exist in the plans table
- AND each plan has associated features and quotas

### Requirement: Feature value object

The system MUST define a Feature dataclass with: `name: str`, `enabled: bool`.

#### Scenario: Feature toggling determines availability

- GIVEN a plan with `Feature("csv_export", enabled=False)`
- WHEN `QuotaEnforcementService` checks csv_export access
- THEN the check returns False for FREE plan
- AND the check returns True for PRO plan

### Requirement: Quota value object

The system MUST define a Quota dataclass with: `name: str`, `limit: int`, `description: str`. The limit MUST be a non-negative integer.

#### Scenario: Quota with zero limit

- GIVEN a Quota for `animals` with `limit=0`
- WHEN the system checks quota availability
- THEN it is treated as "feature disabled" (unlimited is `-1`)

### Requirement: IPlanRepository port

The system MUST define `IPlanRepository` with: `get_default() -> Plan`, `get_by_name(name: str) -> Plan | None`, `list_all() -> list[Plan]`. All methods are async.

#### Scenario: Default plan retrieval

- GIVEN seed data loaded
- WHEN `get_default()` is called
- THEN the FREE plan is returned

#### Scenario: Plan lookup by name

- GIVEN PRO plan exists in seed data
- WHEN `get_by_name("PRO")` is called
- THEN the PRO plan is returned with its features and quotas

### Requirement: Plans are seed-only (not user-creatable)

The system MUST NOT expose any create/update/delete operations for plans. Plan changes are migration-based only.

#### Scenario: Attempt to modify plan

- GIVEN a plan repository instance
- WHEN any code tries to persist a new plan
- THEN the operation is rejected (no create method exists on the port)

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

### Seed Data Table

| Plan | price_monthly | price_yearly | Tenants | Animals | Sales/month | Users | Features |
|------|--------------|--------------|---------|---------|-------------|-------|----------|
| FREE | $0 | — | 1 | 50 | 100 | 5 | None |
| PRO | $15 | $150 | 3 | 500 | 1000 | 25 | CSV export |
| ENTERPRISE | $50 | $500 | -1 | -1 | -1 | -1 | All features |

- `-1` means unlimited. FREE is a grace state (not purchasable, read-only). ENTERPRISE has no numerical limits.
