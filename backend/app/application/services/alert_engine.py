"""
Alert Engine — synchronous alert creation + SuperAdmin notification.

This is the heart of the alerting system. It runs INLINE inside the
inventory route handlers (which use the Supabase SDK as the source of
truth), so an alert is created in the same request that changed stock.
This guarantees alerts fire even when the async RabbitMQ worker is not
running.

Responsibilities
----------------
1. Evaluate an inventory change and decide which alerts to raise:
     - OUT_OF_STOCK   (quantity == 0)
     - CRITICAL_STOCK (quantity <= critical_stock_threshold)
     - LOW_STOCK      (quantity <= low_stock_threshold)
     - STOCK_ISSUE / INVENTORY_TRANSFER / INVENTORY_RESTOCK  (change events)
2. Persist alert rows into the `alerts` table (Supabase).
3. Notify all SuperAdmins via the NotificationService (SMS to their phone +
   email). The SuperAdmin's phone lives in Supabase Auth user_metadata.phone.

De-duplication
--------------
Stock-condition alerts (LOW/CRITICAL/OUT) are de-duped per (item, type)
within a TTL window so operators are not flooded. Change notifications
(issue/transfer/restock) are NOT de-duped — every significant change is
reported, per the SuperAdmin requirement.

Failure isolation
------------------
Nothing here ever raises into the caller. Alerting must never break the
underlying inventory transaction.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from app.config.settings import get_settings
from app.domain.models.alert import AlertType, AlertSeverity, AlertStatus
from app.infrastructure.notifications.service import (
    get_notification_service,
    Recipient,
)
from app.infrastructure.supabase.client import get_supabase_admin

logger = logging.getLogger(__name__)
settings = get_settings()


# ── In-process TTL dedup cache (works without Redis) ─────────────────────────
_dedup: dict[str, float] = {}


def _dedup_seen(key: str, ttl: int) -> bool:
    """Return True if `key` was seen within `ttl` seconds; otherwise record it."""
    now = time.monotonic()
    # opportunistic cleanup
    if len(_dedup) > 2000:
        for k, exp in list(_dedup.items()):
            if exp < now:
                _dedup.pop(k, None)
    exp = _dedup.get(key)
    if exp and exp > now:
        return True
    _dedup[key] = now + ttl
    return False


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:26] + "Z"


def _d(v: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(v if v is not None else default))
    except Exception:  # noqa: BLE001
        return Decimal(default)


# ── Recipient resolution (SuperAdmins) ───────────────────────────────────────

async def _get_superadmin_recipients() -> list[Recipient]:
    """List all SuperAdmin users from Supabase Auth with their phone/email.

    Phone is read from user_metadata.phone (set via the Users admin UI).
    """
    def _list() -> list[Recipient]:
        admin = get_supabase_admin()
        recipients: list[Recipient] = []
        # paginate defensively (most deployments have few admins)
        for page in range(1, 6):
            users = admin.auth.admin.list_users(page=page, per_page=100)
            if not users:
                break
            for u in users:
                app_meta = u.app_metadata or {}
                user_meta = u.user_metadata or {}
                roles = app_meta.get("roles", [])
                if app_meta.get("is_superadmin") or "SuperAdmin" in roles:
                    recipients.append(
                        Recipient(
                            user_id=u.id,
                            name=user_meta.get("full_name") or user_meta.get("username") or u.email,
                            email=u.email,
                            phone=user_meta.get("phone"),
                        )
                    )
            if len(users) < 100:
                break
        return recipients

    try:
        return await asyncio.to_thread(_list)
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to resolve SuperAdmin recipients: %s", e)
        return []


# ── Alert persistence ─────────────────────────────────────────────────────────

async def _insert_alert(
    sb: Any,
    *,
    alert_type: AlertType,
    severity: AlertSeverity,
    title: str,
    message: str,
    item_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional[str]:
    alert_id = str(uuid.uuid4())
    row = {
        "id": alert_id,
        "alert_type": alert_type.value,
        "severity": severity.value,
        "status": AlertStatus.OPEN.value,
        "title": title,
        "message": message,
        "item_id": item_id,
        "warehouse_id": warehouse_id,
        "metadata": metadata or {},
        "escalation_count": 0,
        "webhook_dispatched": False,
        "is_deleted": False,
        "created_at": _now_iso(),
    }
    try:
        await sb.table("alerts").insert(row).execute()
        return alert_id
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to insert alert: %s", e)
        return None


# ── Notification dispatch ──────────────────────────────────────────────────────

async def _notify_superadmins(subject: str, message: str) -> None:
    if not settings.NOTIFICATIONS_ENABLED:
        return
    svc = get_notification_service()
    recipients = await _get_superadmin_recipients()
    if not recipients:
        logger.warning("No SuperAdmin recipients found for notification: %s", subject)
        return
    for r in recipients:
        try:
            results = await svc.notify(r, subject, message)
            for res in results:
                logger.info(
                    "Notify %s via %s: success=%s detail=%s",
                    r.name, res.channel, res.success, res.detail,
                )
        except Exception as e:  # noqa: BLE001
            logger.error("Notification dispatch failed for %s: %s", r.name, e)


# ── Public API ──────────────────────────────────────────────────────────────

async def evaluate_stock_condition(
    sb: Any,
    *,
    item: dict,
    actor_name: str = "system",
) -> list[str]:
    """Raise stock-condition alerts (OUT/CRITICAL/LOW) for an item if needed.

    Returns the list of alert ids created. De-duped per (item, type).
    """
    qty = _d(item.get("quantity"))
    low = _d(item.get("low_stock_threshold"), "10")
    crit = _d(item.get("critical_stock_threshold"), "3")
    item_id = str(item.get("id"))
    warehouse_id = item.get("warehouse_id")
    name = item.get("name", item_id)
    sku = item.get("sku", "")
    ttl = settings.ALERT_DEDUP_TTL_SECONDS

    created: list[str] = []
    plan: list[tuple[AlertType, AlertSeverity, str, str]] = []

    if qty <= 0:
        plan.append((
            AlertType.OUT_OF_STOCK, AlertSeverity.EMERGENCY,
            f"OUT OF STOCK: {name}",
            f"Item {name} (SKU {sku}) is OUT OF STOCK. Immediate restock required.",
        ))
    elif qty <= crit:
        plan.append((
            AlertType.CRITICAL_STOCK, AlertSeverity.CRITICAL,
            f"CRITICAL stock: {name}",
            f"Item {name} (SKU {sku}) has only {qty} units left "
            f"(critical threshold {crit}). Restock urgently.",
        ))
    elif qty <= low:
        plan.append((
            AlertType.LOW_STOCK, AlertSeverity.WARNING,
            f"Low stock: {name}",
            f"Item {name} (SKU {sku}) is low: {qty} units left "
            f"(low threshold {low}).",
        ))

    for atype, severity, title, message in plan:
        dedup_key = f"{item_id}:{atype.value}"
        if _dedup_seen(dedup_key, ttl):
            continue
        alert_id = await _insert_alert(
            sb,
            alert_type=atype, severity=severity, title=title, message=message,
            item_id=item_id, warehouse_id=warehouse_id,
            metadata={
                "quantity": float(qty),
                "low_stock_threshold": float(low),
                "critical_stock_threshold": float(crit),
                "sku": sku, "actor": actor_name,
            },
        )
        if alert_id:
            created.append(alert_id)
            await _notify_superadmins(title, message)

    return created


async def record_inventory_change(
    sb: Any,
    *,
    change_type: str,             # "ISSUE" | "RESTOCK" | "TRANSFER"
    item: dict,
    quantity_delta: Decimal,
    quantity_before: Decimal,
    quantity_after: Decimal,
    actor_name: str = "system",
    extra: Optional[dict] = None,
) -> list[str]:
    """Record a significant inventory change as an alert + notify SuperAdmins.

    This fires on EVERY issue / restock / transfer (not de-duped), then also
    evaluates the resulting stock condition for low/critical/out alerts.
    """
    created: list[str] = []
    name = item.get("name", str(item.get("id")))
    sku = item.get("sku", "")
    item_id = str(item.get("id"))
    warehouse_id = item.get("warehouse_id")

    type_map = {
        "ISSUE": (AlertType.STOCK_ISSUE, AlertSeverity.INFO, "Stock issued"),
        "RESTOCK": (AlertType.INVENTORY_RESTOCK, AlertSeverity.INFO, "Stock restocked"),
        "TRANSFER": (AlertType.INVENTORY_TRANSFER, AlertSeverity.INFO, "Stock transferred"),
    }
    atype, severity, label = type_map.get(
        change_type, (AlertType.INVENTORY_CHANGE, AlertSeverity.INFO, "Inventory change")
    )

    if settings.NOTIFY_ON_EVERY_CHANGE:
        title = f"{label}: {name}"
        message = (
            f"{actor_name} performed {change_type} on {name} (SKU {sku}). "
            f"Quantity {quantity_before} -> {quantity_after} (delta {quantity_delta})."
        )
        alert_id = await _insert_alert(
            sb,
            alert_type=atype, severity=severity, title=title, message=message,
            item_id=item_id, warehouse_id=warehouse_id,
            metadata={
                "change_type": change_type,
                "quantity_before": float(quantity_before),
                "quantity_after": float(quantity_after),
                "quantity_delta": float(quantity_delta),
                "sku": sku, "actor": actor_name,
                **(extra or {}),
            },
        )
        if alert_id:
            created.append(alert_id)
            await _notify_superadmins(title, message)

    # Always evaluate the resulting stock level for shortage alerts.
    created += await evaluate_stock_condition(sb, item=item, actor_name=actor_name)
    return created
