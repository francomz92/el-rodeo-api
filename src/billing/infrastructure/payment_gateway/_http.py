"""HTTP request execution with retry logic for the MercadoPago API.

Extracted from _client.py to reduce file size. Provides the low-level
HTTP call with exponential backoff, 4xx/5xx handling, and timeout
retry.
"""

import asyncio
import uuid

import httpx

from src.billing.domain.exceptions import PaymentGatewayError


def _extract_mp_error(response: httpx.Response) -> str | None:
    """Extract the error message from a MercadoPago error response."""
    try:
        data = response.json()
        return data.get("message") or data.get("error") or str(data)
    except Exception:
        return response.text[:500] if response.text else None


async def request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    json_body: dict | None = None,
    idempotent: bool = False,
    max_retries: int = 3,
) -> dict:
    """Execute an HTTP request with retry logic.

    Args:
        client: The httpx AsyncClient instance.
        method: HTTP method.
        path: API path (relative to base URL).
        json_body: Optional JSON body.
        idempotent: Whether to add x-idempotency-key header.
        max_retries: Maximum number of retries for 5xx errors.

    Returns:
        Parsed JSON response as dict.

    Raises:
        PaymentGatewayError: On API error (4xx) or after exhausting retries.
    """
    headers: dict[str, str] = {}
    if idempotent:
        headers["x-idempotency-key"] = str(uuid.uuid4())

    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            response = await client.request(
                method=method,
                url=path,
                headers=headers or None,
                json=json_body,
            )

            if response.is_success:
                return response.json()

            # 4xx — map error and raise immediately (no retry)
            if 400 <= response.status_code < 500:
                mp_error = _extract_mp_error(response)
                raise PaymentGatewayError(
                    message=mp_error or "MercadoPago API error",
                    status_code=response.status_code,
                    gateway_error=mp_error,
                )

            # 5xx — retry with exponential backoff
            if response.status_code >= 500:
                last_error = PaymentGatewayError(
                    message=f"MP server error (HTTP {response.status_code})",
                    status_code=response.status_code,
                )
                if attempt < max_retries - 1:
                    wait = 2**attempt  # exponential: 1s, 2s, 4s
                    await asyncio.sleep(wait)
                continue

        except httpx.TimeoutException as exc:
            if attempt == max_retries - 1:
                raise PaymentGatewayError(
                    message="MercadoPago API timeout",
                    status_code=0,
                ) from exc
            await asyncio.sleep(2**attempt)
        except httpx.RequestError as exc:
            if attempt == max_retries - 1:
                raise PaymentGatewayError(
                    message=str(exc),
                    status_code=0,
                ) from exc
            await asyncio.sleep(2**attempt)

    # If we exhausted retries on 5xx
    if last_error:
        raise last_error

    return {}  # unreachable, satisfies return type
