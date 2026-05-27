"""
Webhook Engine.

Production-grade webhook delivery with:
  - HMAC-SHA256 payload signing
  - Exponential backoff retries
  - Idempotency via unique delivery IDs
  - Dead-letter tracking
  - Async delivery via httpx
"""
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx

from app.config.settings import get_settings
from app.domain.models.alert import WebhookDelivery, WebhookEndpoint

logger = logging.getLogger(__name__)
settings = get_settings()


def sign_payload(payload_bytes: bytes, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature.
    The receiver validates: HMAC(secret, body) == X-Signature header.
    This prevents spoofing and ensures payload integrity.
    """
    signature = hmac.new(
        secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"


class WebhookEngine:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=5.0,
                read=settings.WEBHOOK_TIMEOUT_SECONDS,
                write=5.0,
                pool=5.0,
            ),
            limits=httpx.Limits(max_connections=50),
        )

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()

    async def deliver(
        self,
        endpoint: WebhookEndpoint,
        event_type: str,
        payload: dict,
        idempotency_key: str,
    ) -> WebhookDelivery:
        """
        Deliver a single webhook attempt.
        Returns a delivery record regardless of success/failure.
        """
        payload_bytes = json.dumps(payload, default=str).encode()
        signature = sign_payload(payload_bytes, endpoint.secret)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event_type,
            "X-Idempotency-Key": idempotency_key,
            "X-Delivery-Timestamp": datetime.now(timezone.utc).isoformat(),
            **(endpoint.headers or {}),
        }

        delivery = WebhookDelivery(
            endpoint_id=endpoint.id,
            event_type=event_type,
            idempotency_key=idempotency_key,
            payload=payload,
            attempt_number=1,
            max_attempts=endpoint.max_retries,
            created_at=datetime.now(timezone.utc),
        )

        try:
            response = await self._client.post(
                str(endpoint.url),
                content=payload_bytes,
                headers=headers,
            )
            delivery.status_code = response.status_code
            delivery.response_body = response.text[:1000]  # cap storage
            delivery.success = 200 <= response.status_code < 300
            if delivery.success:
                delivery.delivered_at = datetime.now(timezone.utc)
            else:
                logger.warning(
                    f"Webhook delivery failed for {endpoint.url}: HTTP {response.status_code}"
                )
        except httpx.TimeoutException as e:
            delivery.success = False
            delivery.error_message = f"Timeout: {str(e)[:200]}"
            logger.error(f"Webhook timeout to {endpoint.url}: {e}")
        except Exception as e:
            delivery.success = False
            delivery.error_message = str(e)[:200]
            logger.error(f"Webhook error to {endpoint.url}: {e}")

        return delivery

    def compute_next_retry(self, attempt: int) -> datetime:
        """
        Exponential backoff with configured delay list.
        Falls back to 2^attempt seconds if delays list is exhausted.
        """
        delays = settings.webhook_retry_delays_list
        if attempt <= len(delays):
            delay_seconds = delays[attempt - 1]
        else:
            delay_seconds = min(2 ** attempt, 3600)
        return datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)


webhook_engine = WebhookEngine()
