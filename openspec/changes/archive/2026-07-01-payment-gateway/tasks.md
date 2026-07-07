# Tasks: Payment Gateway — MercadoPago Integration (Phase 7.2)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1000–1200 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Domain) → PR 2 (Infra+Webhook) → PR 3 (Services) → PR 4 (Routes+DI+Tests) → PR 5 (Celery+Final) |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Domain + Config + Migration | PR 1 | base=main. Types, entities, ports, exceptions, config, alembic. |
| 2 | MP Client + Repo + Webhook | PR 2 | base=PR 1. Gateway impl, webhook handler + router. |
| 3 | Application Services | PR 3 | base=main (depends on PR 1 but not PR 2). MercadoPagoService, ChangePlan, PaymentHistory. |
| 4 | Routes + DI + Integration Tests | PR 4 | base=PR 3. DI wiring, subscription/payment routers, integration tests. |
| 5 | Celery Tasks + Final Wire | PR 5 | base=PR 4. billing_tasks, cron register, remaining tests. |

## PR 1: Domain + Config + Migration

- [x] 1.1 Create `_payment_status.py` — PaymentStatus StrEnum (PENDING/APPROVED/REJECTED/REFUNDED/CANCELLED/CHARGED_BACK)
- [x] 1.2 Create `_payment.py` — Payment dataclass + PaymentMethod VO with all spec fields
- [x] 1.3 Create `_payment_repository_port.py` — IPaymentRepository (create/get_by_id/get_by_tenant/get_by_mp_payment_id/save)
- [x] 1.4 Create `_payment_gateway_port.py` — IPaymentGateway (create_preference/get_payment/refund/validate_signature)
- [x] 1.5 Modify `_subscription.py` — add mp_preference_id, mp_subscription_id fields
- [x] 1.6 Modify `exceptions.py` — add MercadoPagoError, PlanNotChangeableError
- [x] 1.7 Modify `_config.py` — add MP_ACCESS_TOKEN, MP_WEBHOOK_SECRET, MP_WEBHOOK_URL
- [x] 1.8 Create alembic migration — payments table + mp_preference_id/mp_subscription_id on subscriptions + seed prices on plans
- [x] 1.9 Modify Plan seed data — set FREE price_monthly=0.00, PRO=15.00, ENTERPRISE=50.00

## PR 2: MP Infrastructure + Webhook

- [x] 2.1 Create `_client.py` — MercadoPagoHttpClient(IPaymentGateway) with httpx.AsyncClient, Bearer auth, 5xx retry (3), error mapping
- [x] 2.2 Create `_payment_model.py` — SQLAlchemy model for payments table
- [x] 2.3 Create `_payment_repository.py` — SA impl of IPaymentRepository
- [x] 2.4 Create `_payment_webhook_service.py` — handle_ipn with x-signature validation, get_payment, idempotency, sub transition
- [x] 2.5 Create `_webhook_router.py` — POST /billing/webhooks/mercadopago (public, no auth)
- [x] 2.6 Test: validate_signature with known HMAC-SHA256 test vectors
- [x] 2.7 Test: Webhook router with TestClient + mocked IPaymentGateway

## PR 3: Application Services

- [x] 3.1 Create `_mercadopago_service.py` — create_checkout_preference (price>0 guard), get_payment, refund
- [x] 3.2 Create `_change_plan_service.py` — change_plan: FREE rejection, trial rejection, upgrade→preference, downgrade→immediate
- [x] 3.3 Create `_payment_history_service.py` — list_payments with pagination, tenant isolation
- [x] 3.4 Modify `_subscription_repository_port.py` — add list_active_near_period_end(days_ahead)
- [x] 3.5 Modify `_subscription_repository.py` — implement list_active_near_period_end
- [x] 3.6 Test: ChangePlanService guards (FREE reject, trial reject, upgrade flow, downgrade flow)
- [x] 3.7 Test: MercadoPagoService.create_preference (mock IPaymentGateway)
- [x] 3.8 Test: PaymentHistoryService pagination + tenant isolation

## PR 4: Routes + DI + Integration Tests

- [x] 4.1 Create `_billing_dependencies.py` — DI factories: MercadoPagoService, ChangePlanService, PaymentHistoryService, MercadoPagoHttpClient singleton
- [x] 4.2 Create `_subscription_router.py` — PUT /billing/subscriptions/plan (auth, body validation, returns subscription+checkout_url)
- [x] 4.3 Create `_payment_router.py` — GET /billing/payments (auth, pagination, tenant-scoped)
- [x] 4.4 Create routers `__init__.py` — aggregate webhook + subscription + payment routers
- [x] 4.5 Modify `_registry.py` — register IPaymentRepository→PaymentRepository and ISubscriptionRepository→SubscriptionRepository
- [x] 4.6 Modify routers `__init__.py` — include billing_routers
- [x] 4.7 Modify `app.py` — add billing tasks to autodiscover (deferred to PR 5 — Celery+Final)
- [x] 4.8 Test: PUT /billing/subscriptions/plan with TestClient + JWT header (integration)
- [x] 4.9 Test: GET /billing/payments with TestClient + JWT header (integration)
- [x] 4.10 Test: Webhook + plan change + payment history integration (integration)

## PR 5: Celery Tasks + Final Wiring

- [x] 5.1 Create `_billing_tasks.py` — monthly_billing_task (ACTIVE near period_end→create_preference), expire_trials_task (TRIAL past due→EXPIRED+FREE)
- [x] 5.2 Modify `cron_tasks_register.py` — add monthly_billing_task (daily) + expire_trials_task (daily) to Celery Beat
- [x] 5.3 Test: expire_trials_task with MockUoW + MockSubscriptionRepository
- [x] 5.4 Test: monthly_billing_task with MockUoW + mocked MercadoPagoService
- [x] 5.5 Final integration: end-to-end subscription lifecycle (trial→pay→active→plan change→expire)
