# Proposal: Payment Gateway — MercadoPago Integration

## Intent

Phase 7.1 established billing entities (Plan, Subscription, Quota) and trial lifecycle. Phase 7.2 enables actual payment collection via MercadoPago Checkout Pro, subscription plan changes, and payment history. Without this, subscriptions remain in TRIAL or FREE with no paid path.

## Scope

### In Scope
- MercadoPago HTTP client abstraction (httpx.AsyncClient, NOT SDK)
- Checkout Pro preference creation endpoint
- IPN webhook handler — x-signature validation + payment status update
- Subscription plan change (PUT /billing/subscriptions/plan)
- Payment history (GET /billing/payments)
- Celery monthly billing task — create preference, notify user
- Payment entity + repository (domain + persistence)
- Alembic migration: `payments` table, `mp_preference_id`/`mp_subscription_id` on `subscriptions`
- New billing repos registered in UoW registry
- DI factory functions for MP service + new use cases

### Out of Scope
- MP subscription API (recurring auto-debit) — user confirmed manual monthly Checkout Pro
- Refund endpoint — MP refund API exists, deferred
- FREE plan pricing/trial redesign — needs Phase 7.1 decision
- Automated dunning / retry logic

## Capabilities

### New Capabilities
- `billing/payment`: Payment entity, status enum, repository port + impl, alembic migration
- `billing/payment-gateway`: MercadoPago HTTP client, preference creation, IPN webhook handler
- `billing/subscription-change`: Plan change use case + endpoint
- `billing/payment-history`: Payment history query endpoint

### Modified Capabilities
- `billing/subscription`: Add `mp_preference_id`, `mp_subscription_id` fields; add `change_plan()` method to Subscription entity
- `billing/plan`: `Plan.price_monthly` reconsideration — currently `None` for FREE. Needs resolution (see Ambiguities)

## Approach

**Architecture**: Three new layers per Clean Architecture:
1. **Domain**: `Payment` entity, `PaymentStatus` enum, `IPaymentRepository` port, `PaymentService` as domain service
2. **Application**: `MercadoPagoService` (orchestrates MP API calls), `CreatePaymentCase`, `ProcessWebhookCase`, `ChangeSubscriptionPlanCase`
3. **Infrastructure**: `MercadoPagoHttpClient` (httpx.AsyncClient wrapper with Bearer auth), `PaymentRepository` (SQLAlchemy), webhook + billing routers, Celery task

**Why httpx over SDK**: SDK v3.2.0 uses sync `requests`. Our codebase is async throughout — httpx is consistent and already a dependency (used in test ASGITransport).

**Why Checkout Pro**: User confirmed "manual monthly" model — no recurring auto-debit. User pays each month via MP checkout link. Celery task creates a new preference and notifies the user.

**Payment Flow**: User requests plan → API creates MP Checkout preference → returns `init_point` URL → user pays on MP → MP POSTs webhook → handler validates x-signature, maps payment to subscription, updates Payment status → if `approved`, activate subscription.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/billing/domain/entities/` | New | `_payment.py`, `_payment_status.py` |
| `src/billing/domain/repositories/` | New | `_payment_repository_port.py` |
| `src/billing/application/services/` | New | `_mercadopago_service.py`, `_payment_service.py` |
| `src/billing/infrastructure/persistence/models/` | New + Modified | `_payment_model.py`, modify `_subscription_model.py` |
| `src/billing/infrastructure/persistence/repositories/` | New | `_payment_repository.py` |
| `src/billing/infrastructure/presentation/routers/` | New | billing routers (webhooks, subscriptions, payments) |
| `src/billing/infrastructure/presentation/dependencies/` | New | DI factory functions |
| `src/common/infrastructure/persistence/repositories/_registry.py` | Modified | Register IPaymentRepository |
| `src/common/infrastructure/presentation/routers/__init__.py` | Modified | Register billing routers |
| `src/common/infrastructure/core/_config.py` | Modified | Add MP_ACCESS_TOKEN, MP_WEBHOOK_SECRET |
| `src/common/infrastructure/workers/app.py` | Modified | Add billing tasks to autodiscover |
| `src/common/infrastructure/workers/cron_tasks_register.py` | Modified | Add monthly billing cron |
| Alembic migrations | New | Create payments table + subscription columns |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| MP webhook delivery delay/duplicates | Med | Idempotency key on mp_payment_id; reconcile via Celery |
| x-signature validation misconfiguration | Low | Unit-test with known MP test vectors |
| FREE plan price_monthly=None breaks payment logic | High | Must resolve before spec phase — see Ambiguities |
| MP test access token vs production | Low | ENVIRONMENT-based config (dev uses test token) |

## Rollback Plan

1. Revert MP_ACCESS_TOKEN + MP_WEBHOOK_SECRET from .env
2. Revert alembic migration (downgrade drops payments table)
3. Revert router registration in `configure_routers()`
4. Revert repo registry entries
5. Remove billing tasks from Celery autodiscover + cron

## Dependencies

- MercadoPago account + API credentials (test + prod access tokens)
- Phase 7.1 billing entities already deployed
- `.env` additions: `MP_ACCESS_TOKEN`, `MP_WEBHOOK_SECRET`, `MP_WEBHOOK_URL`

## Success Criteria

- [ ] MP Checkout preference created via httpx returns valid `init_point`
- [ ] Webhook receives IPN, validates x-signature, creates Payment record
- [ ] Subscription plan change persists and returns updated subscription
- [ ] Payment history endpoint returns paginated payments for tenant
- [ ] Celery monthly task creates preference and logs without error
- [ ] All test scenarios pass (unit + integration with httpx mocks)

## Ambiguities (Needs Resolution Before Spec)

1. **FREE plan pricing**: `Plan.price_monthly=None` for FREE currently. If "all plans require payment after trial", what price does FREE have? Options: (a) give FREE a `price_monthly=Decimal("0.00")` — payment entity still created with zero amount (free tier keeps a $0 "payment" record for audit); (b) FREE remains free forever, no payment required after trial expire — contradicts "all plans paid" decision; (c) FREE stays as post-trial fallback with no payment, only PRO/ENTERPRISE require payment. **Recommendation**: Clarify — is FREE truly "paid" or is it the fallback after trial expires?
2. **Trial plan type**: Trial currently provisions PRO. If user doesn't pay after 14 days, do they (a) drop to FREE, or (b) lose access entirely? The `expire_trial()` method in Phase 7.1 drops to FREE — but if FREE requires payment too, this must change.
3. **Webhook URL configuration**: Should we use a single `MP_WEBHOOK_URL` that includes the full path (e.g., `https://api.el-rodeo.com/billing/webhooks/mercadopago`), or just the base domain and construct at runtime?
