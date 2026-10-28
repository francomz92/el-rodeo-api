"""Webhook router for MercadoPago IPN notifications.

This router is PUBLIC — no authentication dependency. MercadoPago
requires a 200 OK response to accepted IPN requests; requests with an
invalid ``x-signature`` are rejected with 401.

Signature validation FAILS OPEN when ``MP_WEBHOOK_SECRET`` is empty: the
shared ``HandleIpnCase.validate_signature`` accepts any signature when no
secret is configured, so an unconfigured deployment accepts unverified
webhooks. Documented per F2-5 map #19 (odd/tasks/billing-refactor.md);
the runtime behaviour is unchanged in this phase.
"""

import asyncio

from fastapi import APIRouter, Header, Query, Request, Response, status

from src.billing.domain.exceptions import PaymentGatewayError
from src.billing.infrastructure.presentation.dependencies.webhook_dependencies import (
    GetHandleIpnCase,
)
from src.common.infrastructure.presentation.middlewares.rate_limiter import rate_limit
from src.common.utils import log

webhook_router = APIRouter(
    prefix="/billing/webhooks",
    tags=["Billing / Webhooks"],
    responses={401: {}},
)


@webhook_router.post(
    path="/mercadopago",
    status_code=status.HTTP_200_OK,
    summary="Receive MercadoPago IPN webhook",
    description="Public endpoint for MercadoPago IPN notifications. Returns 200 OK for accepted events (valid signature); 401 when the x-signature is invalid. Processing happens in a background task.",
)
@rate_limit("20/minute")
async def mercadopago_webhook(
    request: Request,
    handle_ipn_case: GetHandleIpnCase,
    topic: str = Query(..., description="Notification topic (payment, merchant_order)"),
    id: str = Query(..., description="Resource ID"),
    x_signature: str = Header(..., alias="x-signature"),
    x_request_id: str = Header(..., alias="x-request-id"),
) -> Response:
    """Handle MercadoPago IPN notifications.

    Validates x-signature synchronously before spawning the background
    task so forged requests are rejected immediately (before any async
    processing). Returns 200 OK for accepted requests (401 on an
    invalid signature); processing is deferred to avoid blocking MP's
    22-second timeout.

    Fail-open (F2-5 map #19): when ``MP_WEBHOOK_SECRET`` is empty the
    signature check is skipped entirely and every request is accepted
    with 200 — configure the secret to enforce validation.
    """
    # Validate signature synchronously before background processing
    if not handle_ipn_case.validate_signature(
        x_signature=x_signature,
        x_request_id=x_request_id,
        data_id=id,
    ):
        raise PaymentGatewayError(
            message="Firma x-signature del webhook no válida",
            status_code=401,
        )

    task = asyncio.create_task(
        handle_ipn_case.execute(
            topic=topic,
            id=id,
            x_signature=x_signature,
            x_request_id=x_request_id,
        )
    )

    def _log_task_error(t: asyncio.Task) -> None:
        if t.cancelled():
            return
        exc = t.exception()
        if exc:
            log.error("Webhook IPN task failed", exc_info=exc)

    task.add_done_callback(_log_task_error)
    return Response(status_code=200)
