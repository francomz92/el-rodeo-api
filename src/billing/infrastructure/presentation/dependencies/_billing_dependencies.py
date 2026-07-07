"""Dependency injection wiring for billing application services.

Follows the Annotated + Depends pattern from auth_dependencies.py.
"""

from typing import Annotated

from fastapi import Depends

from src.billing.application.services._change_plan_service import ChangePlanService
from src.billing.application.services._mercadopago_service import MercadoPagoService
from src.billing.application.services._payment_history_service import (
    PaymentHistoryService,
)
from src.billing.application.services._payment_webhook_service import (
    PaymentWebhookService,
)
from src.billing.domain.repositories import (
    IPaymentGateway,
    IPaymentRepository,
    IPlanRepository,
    ISubscriptionRepository,
)
from src.billing.infrastructure.payment_gateway._client import MercadoPagoHttpClient
from src.billing.infrastructure.persistence.repositories._plan_repository import (
    PlanRepository,
)
from src.common.domain.ports.event_bus import IEventBus
from src.common.infrastructure.events.bus import InMemoryEventBus
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork

# ── Repository factories ─────────────────────────────────────────────────


def _get_plan_repository() -> IPlanRepository:
    """Return an in-memory PlanRepository (seed data, no DB needed)."""
    return PlanRepository()


def _get_payment_repository(uow: GetUnitOfWork) -> IPaymentRepository:
    """Resolve IPaymentRepository from the Unit of Work registry."""
    return uow.get_repository(IPaymentRepository)  # type: ignore[return-value]


def _get_subscription_repository(uow: GetUnitOfWork) -> ISubscriptionRepository:
    """Resolve ISubscriptionRepository from the Unit of Work registry."""
    return uow.get_repository(ISubscriptionRepository)  # type: ignore[return-value]


# ── Gateway factory ──────────────────────────────────────────────────────


def _get_mercadopago_http_client() -> MercadoPagoHttpClient:
    """Return a singleton-style MercadoPago HTTP client."""
    return MercadoPagoHttpClient()


# ── Event bus factory ────────────────────────────────────────────────────


def _get_billing_event_bus() -> IEventBus:
    """Return a plain InMemoryEventBus for billing domain events.

    Outbox scheduling is handled by the request-scoped bus in the
    cattle/animals dependency module. For the billing public webhook
    endpoint, we use a throw-away bus — the event is dispatched to
    allow any registered handlers to react.
    """
    return InMemoryEventBus()


# ── Service factories ────────────────────────────────────────────────────


def _get_mercadopago_service(
    gateway: Annotated[MercadoPagoHttpClient, Depends(_get_mercadopago_http_client)],
    payment_repo: Annotated[IPaymentRepository, Depends(_get_payment_repository)],
    sub_repo: Annotated[ISubscriptionRepository, Depends(_get_subscription_repository)],
    plan_repo: Annotated[IPlanRepository, Depends(_get_plan_repository)],
    uow: GetUnitOfWork,
) -> MercadoPagoService:
    return MercadoPagoService(gateway, payment_repo, sub_repo, plan_repo, uow)


def _get_change_plan_service(
    plan_repo: Annotated[IPlanRepository, Depends(_get_plan_repository)],
    sub_repo: Annotated[ISubscriptionRepository, Depends(_get_subscription_repository)],
    mercado_pago_service: Annotated[MercadoPagoService, Depends(_get_mercadopago_service)],
    uow: GetUnitOfWork,
) -> ChangePlanService:
    return ChangePlanService(plan_repo, sub_repo, mercado_pago_service, uow)


def _get_payment_history_service(
    payment_repo: Annotated[IPaymentRepository, Depends(_get_payment_repository)],
) -> PaymentHistoryService:
    return PaymentHistoryService(payment_repo)


def _get_payment_webhook_service(
    gateway: Annotated[
        IPaymentGateway,
        Depends(_get_mercadopago_http_client),
    ],
    payment_repo: Annotated[IPaymentRepository, Depends(_get_payment_repository)],
    sub_repo: Annotated[ISubscriptionRepository, Depends(_get_subscription_repository)],
    event_bus: Annotated[IEventBus, Depends(_get_billing_event_bus)],
) -> PaymentWebhookService:
    return PaymentWebhookService(gateway, payment_repo, sub_repo, event_bus)


# ── Type-aliased dependencies (Annotated + Depends) ──────────────────────

GetMercadoPagoHttpClient = Annotated[MercadoPagoHttpClient, Depends(_get_mercadopago_http_client)]
GetMercadoPagoService = Annotated[MercadoPagoService, Depends(_get_mercadopago_service)]
GetChangePlanService = Annotated[ChangePlanService, Depends(_get_change_plan_service)]
GetPaymentHistoryService = Annotated[PaymentHistoryService, Depends(_get_payment_history_service)]
GetPaymentWebhookService = Annotated[PaymentWebhookService, Depends(_get_payment_webhook_service)]
