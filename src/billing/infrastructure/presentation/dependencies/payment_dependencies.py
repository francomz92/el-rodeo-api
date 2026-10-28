"""Dependency injection wiring for billing payment cases."""

from typing import Annotated

from fastapi import Depends

from src.billing.application.uses_cases.payment_cases.list_payments_case import (
    ListPaymentsCase,
)
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_list_payments_case(uow: GetUnitOfWork) -> ListPaymentsCase:
    return ListPaymentsCase(uow=uow)


GetListPaymentsCase = Annotated[ListPaymentsCase, Depends(_get_list_payments_case)]

__all__ = ["GetListPaymentsCase"]
