"""MercadoPago payment gateway implementation."""

from src.billing.infrastructure.adapters.payment_gateway.client import MercadoPagoHttpClient

__all__ = ["MercadoPagoHttpClient"]
