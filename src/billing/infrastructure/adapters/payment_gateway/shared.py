"""Shared MercadoPago HTTP client lifecycle.

One ``httpx.AsyncClient`` per process instead of one leak per request or
worker run (Fase 4 #3, odd/tasks/billing-refactor.md L14). The FastAPI
lifespan closes it on shutdown; workers keep reusing it across runs.
"""

from __future__ import annotations

from src.billing.infrastructure.adapters.payment_gateway.client import (
    MercadoPagoHttpClient,
)

_shared: MercadoPagoHttpClient | None = None


def get_shared_mercadopago_client() -> MercadoPagoHttpClient:
    """Return the process-wide client, creating it on first use."""
    global _shared
    if _shared is None:
        _shared = MercadoPagoHttpClient()
    return _shared


async def close_shared_mercadopago_client() -> None:
    """Close the shared client and reset the singleton (app shutdown)."""
    global _shared
    if _shared is not None:
        await _shared.close()
        _shared = None
