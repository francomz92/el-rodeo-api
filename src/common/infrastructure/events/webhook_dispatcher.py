"""Webhook dispatcher with HMAC-SHA256 signing and exponential backoff."""

import asyncio
import hashlib
import hmac
import json
from typing import Any

from httpx import AsyncClient, HTTPError

from src.common.utils import log


class WebhookDispatcher:
    """Dispatches domain events to tenant webhook subscribers.

    Signs the payload with HMAC-SHA256 using the subscriber's secret,
    POSTs to the subscriber URL, and implements exponential backoff
    (1s, 2s, 4s, 8s — 4 sleeps between 5 attempts, total up to 15s).
    """

    MAX_RETRIES = 5

    def __init__(self, client: AsyncClient | None = None) -> None:
        self._client = client or AsyncClient(timeout=10.0)

    async def dispatch(
        self,
        url: str,
        secret: str,
        payload: dict[str, Any],
        event_id: str = "",
    ) -> bool:
        """POST *payload* to *url* signed with HMAC-SHA256 using *secret*.

        Retries up to MAX_RETRIES with exponential backoff (1, 2, 4, 8s).
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
        if event_id:
            headers["X-Event-Id"] = event_id

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = await self._client.post(url, content=body, headers=headers)
                if resp.is_success:
                    return True
                log.warning("Webhook {} attempt {}: HTTP {}", url, attempt, resp.status_code)
            except HTTPError as e:
                log.warning("Webhook {} attempt {} failed: {}", url, attempt, e)

            if attempt < self.MAX_RETRIES:
                await asyncio.sleep(2 ** (attempt - 1))  # 1, 2, 4, 8s

        log.error("Webhook {} failed after {} attempts", url, self.MAX_RETRIES)
        return False
