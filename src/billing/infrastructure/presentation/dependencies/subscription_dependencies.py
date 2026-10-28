"""Dependency injection wiring for billing subscription cases."""

from typing import Annotated

from fastapi import Depends

from src.billing.application.uses_cases.plan_cases.create_checkout_case import (
    CreateCheckoutCase,
)
from src.billing.application.uses_cases.subscription_cases.cancel_subscription_case import (
    CancelSubscriptionCase,
)
from src.billing.application.uses_cases.subscription_cases.change_plan_case import (
    ChangePlanCase,
)
from src.billing.application.uses_cases.subscription_cases.create_subscription_case import (
    CreateSubscriptionCase,
)
from src.billing.application.uses_cases.subscription_cases.get_subscription_case import (
    GetSubscriptionCase,
)
from src.billing.application.uses_cases.subscription_cases.list_subscriptions_case import (
    ListSubscriptionsCase,
)
from src.billing.application.uses_cases.subscription_cases.update_payment_method_case import (
    UpdatePaymentMethodCase,
)
from src.billing.domain.services.subscription_services.change_plan_service import (
    ChangePlanService,
)
from src.billing.infrastructure.adapters.payment_gateway.client import MercadoPagoHttpClient
from src.billing.infrastructure.adapters.payment_gateway.shared import (
    get_shared_mercadopago_client,
)
from src.common.infrastructure.core import settings
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_mercadopago_http_client() -> MercadoPagoHttpClient:
    """Return the process-shared MercadoPago HTTP client (closed on shutdown)."""
    return get_shared_mercadopago_client()


def _get_create_checkout_case(
    uow: GetUnitOfWork,
    gateway: Annotated[MercadoPagoHttpClient, Depends(_get_mercadopago_http_client)],
) -> CreateCheckoutCase:
    return CreateCheckoutCase(uow=uow, gateway=gateway, webhook_url=settings.MP_WEBHOOK_URL)


def _get_change_plan_case(
    uow: GetUnitOfWork,
    create_checkout_case: Annotated[CreateCheckoutCase, Depends(_get_create_checkout_case)],
) -> ChangePlanCase:
    """Build ChangePlanCase with its checkout case resolved by FastAPI.

    The checkout case comes through ``Depends(_get_create_checkout_case)``
    instead of a direct call so the shared gateway-client factory override
    (used by the integration tests) keeps applying to both flows.
    """
    return ChangePlanCase(
        uow=uow,
        service=ChangePlanService(),
        create_checkout_case=create_checkout_case,
    )


def _get_create_subscription_case(
    uow: GetUnitOfWork,
    gateway: Annotated[MercadoPagoHttpClient, Depends(_get_mercadopago_http_client)],
) -> CreateSubscriptionCase:
    return CreateSubscriptionCase(uow=uow, gateway=gateway, webhook_url=settings.MP_WEBHOOK_URL)


def _get_cancel_subscription_case(
    uow: GetUnitOfWork,
    gateway: Annotated[MercadoPagoHttpClient, Depends(_get_mercadopago_http_client)],
) -> CancelSubscriptionCase:
    return CancelSubscriptionCase(uow=uow, gateway=gateway)


def _get_update_payment_method_case(
    uow: GetUnitOfWork,
    gateway: Annotated[MercadoPagoHttpClient, Depends(_get_mercadopago_http_client)],
) -> UpdatePaymentMethodCase:
    return UpdatePaymentMethodCase(uow=uow, gateway=gateway)


def _get_list_subscriptions_case(uow: GetUnitOfWork) -> ListSubscriptionsCase:
    return ListSubscriptionsCase(uow=uow)


def _get_subscription_detail_case(uow: GetUnitOfWork) -> GetSubscriptionCase:
    return GetSubscriptionCase(uow=uow)


GetMercadoPagoHttpClient = Annotated[MercadoPagoHttpClient, Depends(_get_mercadopago_http_client)]
GetChangePlanCase = Annotated[ChangePlanCase, Depends(_get_change_plan_case)]
GetCreateSubscriptionCase = Annotated[CreateSubscriptionCase, Depends(_get_create_subscription_case)]
GetCancelSubscriptionCase = Annotated[CancelSubscriptionCase, Depends(_get_cancel_subscription_case)]
GetUpdatePaymentMethodCase = Annotated[UpdatePaymentMethodCase, Depends(_get_update_payment_method_case)]
GetListSubscriptionsCase = Annotated[ListSubscriptionsCase, Depends(_get_list_subscriptions_case)]
GetSubscriptionDetailCase = Annotated[GetSubscriptionCase, Depends(_get_subscription_detail_case)]

__all__ = [
    "GetCancelSubscriptionCase",
    "GetChangePlanCase",
    "GetCreateSubscriptionCase",
    "GetListSubscriptionsCase",
    "GetMercadoPagoHttpClient",
    "GetSubscriptionDetailCase",
    "GetUpdatePaymentMethodCase",
]
