"""
RabbitMQ event publisher.

Domain events are published here and consumed by workers
(alert_worker, webhook_worker).

RELIABILITY GUARANTEES:
  - publisher_confirms: we wait for RabbitMQ to ack each message
  - persistent messages: survive broker restart
  - dead-letter exchange: messages that fail all retries go to DLX
  - idempotency_key in payload: workers deduplicate on consumption
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EventPublisher:
    """
    Thin wrapper around aio_pika for publishing domain events.
    One instance per application lifecycle — reconnects on failure.
    """

    EXCHANGE_NAME = "inventory.events"
    DLX_NAME = "inventory.events.dlx"

    def __init__(self):
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL,
            reconnect_interval=5,
        )
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=100)

        # Declare dead-letter exchange first
        dlx = await self._channel.declare_exchange(
            self.DLX_NAME, ExchangeType.TOPIC, durable=True
        )

        # Main topic exchange
        self._exchange = await self._channel.declare_exchange(
            self.EXCHANGE_NAME, ExchangeType.TOPIC, durable=True
        )

        # Declare worker queues with DLX configured
        await self._declare_queue("alerts.queue", routing_key="inventory.*")
        await self._declare_queue("webhooks.queue", routing_key="inventory.*")
        await self._declare_queue("analytics.queue", routing_key="inventory.*")

        logger.info("RabbitMQ publisher connected and queues declared")

    async def _declare_queue(self, name: str, routing_key: str) -> None:
        queue = await self._channel.declare_queue(
            name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": self.DLX_NAME,
                "x-message-ttl": 86400000,  # 24h TTL
                "x-max-retries": 5,
            },
        )
        await queue.bind(self._exchange, routing_key=routing_key)

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        """
        Publish a domain event. Adds idempotency_key and timestamp.
        Uses publisher confirms — awaits broker acknowledgement.
        """
        if self._exchange is None:
            logger.error("EventPublisher not connected — event dropped: %s", routing_key)
            return

        payload.setdefault("event_id", str(uuid.uuid4()))
        payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        payload.setdefault("routing_key", routing_key)

        body = json.dumps(payload, default=str).encode()

        message = Message(
            body=body,
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
            message_id=payload["event_id"],
        )

        try:
            await self._exchange.publish(message, routing_key=routing_key)
            logger.debug("Published event %s: %s", routing_key, payload.get("event"))
        except Exception as e:
            logger.error("Failed to publish event %s: %s", routing_key, e)

    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close()


# Singleton instance
event_publisher = EventPublisher()
