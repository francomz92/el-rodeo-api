from typing import Annotated

from fastapi import Depends

from src.common.application.services.webhook_subscription_service import (
    WebhookSubscriptionService,
)
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_webhook_subscription_service(
    uow: GetUnitOfWork,
) -> WebhookSubscriptionService:
    return WebhookSubscriptionService(uow=uow)


GetWebhookSubscriptionService = Annotated[
    WebhookSubscriptionService,
    Depends(_get_webhook_subscription_service),
]
