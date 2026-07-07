"""Webhook dispatcher with HMAC-SHA256 signing and exponential backoff."""

import asyncio
import hashlib
import hmac
import json
import logging
from typing import Any

from httpx import AsyncClient, HTTPError

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    """Dispatches domain events to tenant webhook subscribers.

    Signs the payload with HMAC-SHA256 using the subscriber's secret,
    POSTs to the subscriber URL, and implements exponential backoff
    (1s, 2s, 4s, 8s, 16s — 5 attempts).
    """

    MAX_RETRIES = 5

    def __init__(self, client: AsyncClient | None = None) -> None:
        self._client = client or AsyncClient(timeout=10.0)

    async def dispatch(
        self,
        url: str,
        secret: str,
        payload: dict[str, Any],
    ) -> bool:
        """POST *payload* to *url* signed with HMAC-SHA256 using *secret*.

        Retries up to MAX_RETRIES with exponential backoff.
        Returns True on success, False after all retries fail.
        """
        body = json.dumps(payload, default=str)
        signature = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
        }

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = await self._client.post(url, content=body, headers=headers)
                if resp.is_success:
                    return True
                logger.warning("Webhook %s attempt %d: HTTP %d", url, attempt, resp.status_code)
            except HTTPError as e:
                logger.warning("Webhook %s attempt %d failed: %s", url, attempt, e)

            if attempt < self.MAX_RETRIES:
                await asyncio.sleep(2 ** (attempt - 1))  # 1, 2, 4, 8, 16s

        logger.error("Webhook %s failed after %d attempts", url, self.MAX_RETRIES)
        return False
