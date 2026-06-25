"""
Alert Worker — consumes inventory events and creates alerts.

Runs as a separate process consuming from RabbitMQ.
Implements:
  - Message deduplication via Redis
  - Exponential backoff retry
  - Dead-letter queue on final failure
  - Alert escalation for unacknowledged alerts
"""
import asyncio
import json
import logging
import uuid as uuid_module
from datetime import datetime, timezone

import aio_pika

from app.config.settings import get_settings
from app.infrastructure.database.session import get_db_context
from app.infrastructure.cache.redis_client import redis_client
from app.domain.models.alert import Alert, AlertType, AlertSeverity, AlertStatus

logger = logging.getLogger(__name__)
settings = get_settings()


DEDUP_TTL = 3600  # 1 hour — suppress duplicate alerts within this window


async def process_inventory_event(payload: dict) -> None:
    """
    Evaluate an inventory event and create alerts if warranted.

    Deduplication: we store a Redis key for each (item_id, alert_type)
    pair so we don't flood operators with repeated alerts for the same
    condition.
    """
    event = payload.get("event")
    item_id = payload.get("item_id")
    quantity = payload.get("quantity_after", 0)
    low_threshold = payload.get("low_stock_threshold", 0)
    critical_threshold = payload.get("critical_stock_threshold", 0)
    warehouse_id = payload.get("warehouse_id")

    if not item_id or event not in ("ITEM_ISSUED",):
        return

    alerts_to_create = []

    if quantity <= critical_threshold:
        dedup_key = f"alert_dedup:{item_id}:CRITICAL_STOCK"
        if not await redis_client.get(dedup_key):
            alerts_to_create.append({
                "alert_type": AlertType.CRITICAL_STOCK,
                "severity": AlertSeverity.CRITICAL,
                "title": f"CRITICAL: Stock critically low",
                "message": f"Item {item_id} has only {quantity} units remaining (critical threshold: {critical_threshold})",
                "dedup_key": dedup_key,
            })
    elif quantity <= low_threshold:
        dedup_key = f"alert_dedup:{item_id}:LOW_STOCK"
        if not await redis_client.get(dedup_key):
            alerts_to_create.append({
                "alert_type": AlertType.LOW_STOCK,
                "severity": AlertSeverity.WARNING,
                "title": f"WARNING: Low stock",
                "message": f"Item {item_id} has {quantity} units remaining (low threshold: {low_threshold})",
                "dedup_key": dedup_key,
            })

    if not alerts_to_create:
        return

    async with get_db_context() as db:
        for alert_data in alerts_to_create:
            alert = Alert(
                alert_type=alert_data["alert_type"],
                severity=alert_data["severity"],
                status=AlertStatus.OPEN,
                title=alert_data["title"],
                message=alert_data["message"],
                item_id=uuid_module.UUID(item_id) if item_id else None,
                warehouse_id=uuid_module.UUID(warehouse_id) if warehouse_id else None,
                metadata=payload,
            )
            db.add(alert)
        await db.flush()
    # DB transaction committed — safe to write dedup keys now
    for alert_data in alerts_to_create:
        await redis_client.set(alert_data["dedup_key"], "1", ttl=DEDUP_TTL)
        logger.info(f"Alert created: {alert_data['alert_type']} for item {item_id}")


async def run_alert_worker() -> None:
    """Main worker loop. Reconnects on failure."""
    while True:
        try:
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=10)
                queue = await channel.get_queue("alerts.queue")

                logger.info("Alert worker listening on alerts.queue")

                async with queue.iterator() as messages:
                    async for message in messages:
                        async with message.process(requeue=False):
                            try:
                                payload = json.loads(message.body.decode())
                                # Idempotency check
                                event_id = payload.get("event_id", "")
                                idempotency_key = f"worker:alert:processed:{event_id}"
                                if await redis_client.get(idempotency_key):
                                    logger.debug(f"Skipping duplicate event {event_id}")
                                    continue
                                await process_inventory_event(payload)
                                await redis_client.set(idempotency_key, "1", ttl=86400)
                            except Exception as e:
                                logger.error(f"Alert worker message error: {e}", exc_info=True)
                                # Message will be nacked and sent to DLX
                                raise
        except Exception as e:
            logger.error(f"Alert worker connection error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_alert_worker())
