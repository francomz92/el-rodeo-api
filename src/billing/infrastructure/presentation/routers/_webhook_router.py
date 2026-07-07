"""Webhook router for MercadoPago IPN notifications.

This router is PUBLIC — no authentication dependency. MercadoPago
requires a 200 OK response to every IPN request.
"""

import asyncio
import logging

from fastapi import APIRouter, Header, Query, Request, Response, status

from src.billing.domain.exceptions import MercadoPagoError
from src.billing.infrastructure.presentation.dependencies._billing_dependencies import (
    GetPaymentWebhookService,
)

logger = logging.getLogger(__name__)

webhook_router = APIRouter(prefix="/billing", tags=["Billing / Webhooks"])


@webhook_router.post(
    path="/webhooks/mercadopago",
    status_code=status.HTTP_200_OK,
    summary="Receive MercadoPago IPN webhook",
    description="Public endpoint for MercadoPago IPN notifications. Always returns 200 OK. Processing happens in a background task.",
)
async def mercadopago_webhook(
    request: Request,
    webhook_service: GetPaymentWebhookService,
    topic: str = Query(..., description="Notification topic (payment, merchant_order)"),
    id: str = Query(..., description="Resource ID"),
    x_signature: str = Header(..., alias="x-signature"),
    x_request_id: str = Header(..., alias="x-request-id"),
) -> Response:
    """Handle MercadoPago IPN notifications.

    Validates x-signature synchronously before spawning the background
    task so forged requests are rejected immediately (before any async
    processing). Always returns 200 OK for valid requests; processing
    is deferred to avoid blocking MP's 22-second timeout.
    """
    # Validate signature synchronously before background processing
    if not webhook_service.validate_signature(
        x_signature=x_signature,
        x_request_id=x_request_id,
        data_id=id,
    ):
        raise MercadoPagoError(
            message="Invalid webhook x-signature",
            status_code=401,
        )

    asyncio.create_task(
        webhook_service.handle_ipn(
            topic=topic,
            id=id,
            x_signature=x_signature,
            x_request_id=x_request_id,
        )
    )
    return Response(status_code=200)
