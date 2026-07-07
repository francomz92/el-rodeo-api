# Design: Payment Gateway — MercadoPago Integration (Phase 7.2)

## Technical Approach

Four application services layered over a gateway port: `IPaymentGateway` (abstract, domain), `MercadoPagoHttpClient` (httpx.AsyncClient). `Payment` entity + `IPaymentRepository` track lifecycle. `ChangePlanService` delegates upgrades to `MercadoPagoService`. Webhooks validated via HMAC-SHA256. Celery beat: monthly preference creation + trial expiry. All services follow existing DI (Annotated + Depends) and repository patterns (port + impl + UoW registry).

## Architecture Decisions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Gateway port vs direct client | Testability vs simplicity | **Port** — `IPaymentGateway` enables mock-based unit tests without MP credentials |
| Webhook inline vs Celery deferral | Latency vs complexity | **Inline** — MP GET + DB write <500ms; defer if >2s observed |
| FREE guard at which layer | Depth of defense | **Service + Gateway** — `ChangePlanService` rejects FREE in domain; `MercadoPagoService` checks price_monthly ≤ 0 before HTTP call |
| httpx.AsyncClient lifecycle | Pool reuse vs fresh per call | **Singleton per app** — connection pool to `api.mercadopago.com` via `@lru_cache` on factory |

## Data Flow

```
[Checkout]   User → PUT /billing/subscriptions/plan {plan_type}
               → ChangePlanService.change_plan()
                 → upgrade: MercadoPagoService.create_preference() → MP API → init_point
                 → downgrade: update plan_id immediately
               ← {subscription, checkout_url?}

[Webhook]    MP → POST /billing/webhooks/mercadopago?topic=payment&id=pay-123
               → validate x-signature (HMAC-SHA256)
               → PaymentWebhookService.handle_ipn()
                 → get_payment() → MP API
                 → idempotency check (get_by_mp_payment_id)
                 → create/update Payment + transition Subscription
               ← 200 OK

[Celery]     monthly_billing_task (daily)
               → list_active_near_period_end(7) → create_preference() each
             expire_trials_task (daily)
               → list_expired_trials() → EXPIRED + plan_id→FREE
```

## Status Transitions

| PaymentStatus | Subscription → | When |
|---------------|----------------|------|
| APPROVED | ACTIVE | Payment confirmed, set period dates |
| REJECTED | PAST_DUE | Payment failed |
| REFUNDED | PAST_DUE | Money returned |
| CHARGED_BACK | PAST_DUE | Dispute lost |
| PENDING / CANCELLED | No change | Awaiting or abandoned |

## File Changes

| File | Action |
|------|--------|
| `src/billing/domain/entities/_payment_status.py` | Create — PaymentStatus StrEnum |
| `src/billing/domain/entities/_payment.py` | Create — Payment + PaymentMethod dataclasses |
| `src/billing/domain/entities/_subscription.py` | Modify — add mp_preference_id, mp_subscription_id |
| `src/billing/domain/repositories/_payment_repository_port.py` | Create — IPaymentRepository |
| `src/billing/domain/services/_payment_gateway_port.py` | Create — IPaymentGateway abstract port |
| `src/billing/domain/exceptions.py` | Modify — add MercadoPagoError, PlanNotChangeableError |
| `src/billing/application/services/_mercadopago_service.py` | Create — gateway orchestrator |
| `src/billing/application/services/_payment_webhook_service.py` | Create — IPN + idempotency |
| `src/billing/application/services/_change_plan_service.py` | Create — plan change rules |
| `src/billing/application/services/_payment_history_service.py` | Create — paginated payments |
| `src/billing/infrastructure/payment_gateway/_client.py` | Create — httpx.AsyncClient wrapper |
| `src/billing/infrastructure/persistence/models/_payment_model.py` | Create — SA model |
| `src/billing/infrastructure/persistence/repositories/_payment_repository.py` | Create — SA impl |
| `src/billing/infrastructure/presentation/dependencies/_billing_dependencies.py` | Create — DI factories |
| `src/billing/infrastructure/presentation/routers/_webhook_router.py` | Create — POST (public) |
| `src/billing/infrastructure/presentation/routers/_subscription_router.py` | Create — PUT (auth) |
| `src/billing/infrastructure/presentation/routers/_payment_router.py` | Create — GET (auth) |
| `src/billing/infrastructure/presentation/routers/__init__.py` | Create — router aggregator |
| `src/billing/infrastructure/workers/_billing_tasks.py` | Create — monthly_billing, expire_trials |
| `src/common/infrastructure/persistence/repositories/_registry.py` | Modify — register IPaymentRepository |
| `src/common/infrastructure/presentation/routers/__init__.py` | Modify — include billing_routers |
| `src/common/infrastructure/workers/app.py` | Modify — autodiscover billing tasks |
| `src/common/infrastructure/workers/cron_tasks_register.py` | Modify — add billing beats |
| `src/common/infrastructure/core/_config.py` | Modify — add MP_*, TRIAL_DAYS |
| `alembic/versions/xxxx_payment_mercadopago.py` | Create — payments table + subscription columns + seed prices |

## Interfaces / Contracts

```python
# IPaymentGateway (domain port)
class IPaymentGateway(ABC):
    async def create_preference(self, plan, tenant_id, plan_type) -> PreferenceResult
    async def get_payment(self, mp_payment_id: str) -> dict
    async def refund(self, mp_payment_id: str, amount: Decimal | None) -> bool
    def validate_signature(self, x_signature: str, x_request_id: str, data_id: str) -> bool

# MercadoPagoHttpClient (implements IPaymentGateway)
class MercadoPagoHttpClient:
    def __init__(self, access_token, webhook_secret):
        self._client = httpx.AsyncClient(base_url="https://api.mercadopago.com",
            headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    # Retry: 5xx exponential backoff (3 attempts), 4xx raise immediately
    # Error mapping: httpx.HTTPStatusError → MercadoPagoError
    # Idempotency: x-idempotency-key header on POST requests (UUID per call)

# MercadoPagoService (application)
class MercadoPagoService:
    def __init__(self, uow, gateway: IPaymentGateway)
    # create_checkout_preference: validate price>0 → gateway.create_preference → save mp_preference_id
    # get_payment: gateway.get_payment → map to domain
    # refund: gateway.refund

# PaymentWebhookService (application)
class PaymentWebhookService:
    def __init__(self, uow, gateway: IPaymentGateway)
    # handle_ipn: validate → get_payment → idempotency → create Payment → transition Subscription
```

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Unit | PaymentStatus enum | Pure Python — no mocks |
| Unit | validate_signature | Known HMAC test vectors |
| Unit | ChangePlanService guards | Mock repos, assert FREE rejection |
| Unit | ChangePlanService upgrade/downgrade | Mock MercadoPagoService + repos |
| Unit | MercadoPagoService.create_preference | Mock IPaymentGateway + repos |
| Int | PaymentWebhookService.handle_ipn | Mock httpx responses, spy on repos |
| Int | Webhook router | TestClient + mocked services |
| Int | Plan change + payment routers | TestClient + JWT auth header |

## Migration / Rollout

1. Deploy Alembic migration (create payments, alter subscriptions, seed prices)
2. Add `MP_ACCESS_TOKEN`, `MP_WEBHOOK_SECRET`, `MP_WEBHOOK_URL` to .env
3. Deploy code — Celery beat picks up tasks on next cycle
4. Register `MP_WEBHOOK_URL` in MP dashboard per environment
5. Rollback: revert .env vars, run `alembic downgrade -1`, revert router registration

## Open Questions

- [ ] `plan_change_at` on subscription vs. infer from audit log? Spec says add to subscription — follow spec unless audit already covers it.
