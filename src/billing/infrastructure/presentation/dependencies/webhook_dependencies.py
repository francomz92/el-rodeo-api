"""Dependency injection wiring for billing webhook cases."""

from typing import Annotated

from fastapi import Depends

from src.billing.application.uses_cases.webhook_cases.handle_ipn_case import (
    HandleIpnCase,
)
from src.billing.domain.repositories import IPlanRepository
from src.billing.infrastructure.adapters.payment_event_bus_factory import (
    PaymentEventBusFactory,
)
from src.billing.infrastructure.presentation.dependencies.subscription_dependencies import (
    GetMercadoPagoHttpClient,
)
from src.common.infrastructure.core import settings
from src.common.infrastructure.presentation.dependencies.notifier import (
    GetNotifierClient,
)
from src.common.infrastructure.presentation.dependencies.uow import (
    GetUnitOfWork,
    GetUoWFactory,
)


def _get_plan_repository(uow: GetUnitOfWork) -> IPlanRepository:
    """Resolve IPlanRepository from the Unit of Work registry."""
    return uow.get_repository(IPlanRepository)


def _get_handle_ipn_case(
    gateway: GetMercadoPagoHttpClient,
    plan_repo: Annotated[IPlanRepository, Depends(_get_plan_repository)],
    uow_factory: GetUoWFactory,
    notifier: GetNotifierClient,
) -> HandleIpnCase:
    """Build HandleIpnCase.

    The MercadoPago client is resolved through the public alias declared in
    ``subscription_dependencies`` (the single owner of the gateway factory);
    this module imports that alias instead of re-declaring it or reaching for
    the private factory.
    """
    event_bus_factory = PaymentEventBusFactory(notifier)
    return HandleIpnCase(
        gateway=gateway,
        plan_repo=plan_repo,
        uow_factory=uow_factory,
        event_bus_factory=event_bus_factory,
        webhook_secret=settings.MP_WEBHOOK_SECRET,
    )


# ``GetMercadoPagoHttpClient`` is declared once, in ``subscription_dependencies``
# (F2-4 map #20), and imported here so both dependency files share one factory.
GetHandleIpnCase = Annotated[HandleIpnCase, Depends(_get_handle_ipn_case)]
__all__ = ["GetHandleIpnCase", "GetMercadoPagoHttpClient"]
