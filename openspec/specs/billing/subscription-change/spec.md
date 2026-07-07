# Billing — Subscription Change Specification

## Purpose

Defines the plan change use case: upgrading/downgrading between PRO and ENTERPRISE, with payment validation for upgrades.

## Requirements

### Requirement: ChangeSubscriptionPlanCase

The system MUST define `ChangeSubscriptionPlanCase` that accepts `tenant_id` and `new_plan_type` (PlanType.PRO | PlanType.ENTERPRISE). For UPGRADES (PRO → ENTERPRISE), it MUST require an active payment for the new plan. For DOWNGRADES (ENTERPRISE → PRO), it SHALL apply at the next billing period. FREE is NOT selectable as a target plan — it is a grace state only reachable via expiration.

#### Scenario: Upgrade requires active payment

- GIVEN an ACTIVE PRO subscription for tenant
- WHEN `ChangeSubscriptionPlanCase` is called with PlanType.ENTERPRISE
- THEN a new MP Checkout preference is created for the ENTERPRISE price
- AND the response includes the `init_point` URL for payment
- AND the plan change is NOT applied until payment is approved

#### Scenario: Downgrade applies next cycle

- GIVEN an ACTIVE ENTERPRISE subscription for tenant
- WHEN `ChangeSubscriptionPlanCase` is called with PlanType.PRO
- THEN the subscription `plan_id` is updated to PRO immediately
- AND the current_period_end stays unchanged
- AND the new PRO rate applies from the next billing period

#### Scenario: FREE plan is not selectable

- GIVEN any subscription
- WHEN `ChangeSubscriptionPlanCase` is called with PlanType.FREE
- THEN a `DomainError` is raised with error code `free_plan_not_selectable`

#### Scenario: Trial cannot change plan

- GIVEN a TRIAL subscription
- WHEN `ChangeSubscriptionPlanCase` is called with any PlanType
- THEN a `DomainError` is raised — plan changes are only available after activation

### Requirement: PUT /billing/subscriptions/plan endpoint

The system MUST expose `PUT /billing/subscriptions/plan` accepting `{ "plan_type": "ENTERPRISE" | "PRO" }` in the request body. The endpoint MUST return the updated subscription and, for upgrades, the MP `init_point` URL.

#### Scenario: Upgrade endpoint returns init_point

- GIVEN an authenticated tenant with ACTIVE PRO subscription
- WHEN a PUT request with `{"plan_type": "ENTERPRISE"}` is sent
- THEN the response contains `subscription` and `checkout_url` fields
- AND the `checkout_url` is the MP init_point for the preference

#### Scenario: Invalid plan_type returns 422

- GIVEN an authenticated tenant
- WHEN a PUT request with `{"plan_type": "FREE"}` is sent
- THEN HTTP 422 is returned with validation error
