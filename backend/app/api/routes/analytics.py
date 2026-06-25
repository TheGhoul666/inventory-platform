"""Analytics routes — Supabase SDK edition."""
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import CurrentUser, require_permission
from app.infrastructure.supabase.client import get_supabase_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def dashboard_summary(
    current_user: CurrentUser = Depends(require_permission("analytics:read")),
    sb: Any = Depends(get_supabase_db),
):
    try:
        items_res = await sb.table("inventory_items").select("*").eq("is_deleted", False).execute()
        items = items_res.data or []

        total_items = len(items)
        low_stock = []
        critical = []

        for item in items:
            qty = Decimal(str(item.get("quantity") or "0"))
            low_thresh = Decimal(str(item.get("low_stock_threshold") or "10"))
            crit_thresh = Decimal(str(item.get("critical_stock_threshold") or "3"))
            if qty <= crit_thresh:
                critical.append(item)
            elif qty <= low_thresh:
                low_stock.append(item)

        return {
            "low_stock_count": len(low_stock) + len(critical),
            "critical_stock_count": len(critical),
            "total_items_count": total_items,
            "critical_items": [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "sku": item["sku"],
                    "quantity": float(item["quantity"]),
                    "threshold": float(item.get("critical_stock_threshold") or 3),
                }
                for item in critical[:10]
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "low_stock_count": 0,
            "critical_stock_count": 0,
            "total_items_count": 0,
            "critical_items": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }


@router.get("/usage/{item_id}")
async def item_usage(
    item_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: CurrentUser = Depends(require_permission("analytics:read")),
    sb: Any = Depends(get_supabase_db),
):
    try:
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        txn_res = await sb.table("inventory_transactions").select("quantity_delta") \
            .eq("item_id", str(item_id)) \
            .eq("transaction_type", "ISSUE") \
            .gte("created_at", since) \
            .execute()
        total_issued = sum(float(t["quantity_delta"]) for t in (txn_res.data or []))
        rate = total_issued / days if days > 0 else 0.0

        item_res = await sb.table("inventory_items").select("quantity").eq("id", str(item_id)).execute()
        qty = float((item_res.data or [{}])[0].get("quantity", 0))
        depletion = round(qty / rate, 2) if rate > 0 else None

        return {
            "item_id": str(item_id),
            "daily_consumption_rate": round(rate, 4),
            "predicted_depletion_days": depletion,
            "period_days": days,
        }
    except Exception as e:
        return {"item_id": str(item_id), "error": str(e)}


@router.get("/depletion/{item_id}")
async def predicted_depletion(
    item_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_permission("analytics:read")),
    sb: Any = Depends(get_supabase_db),
):
    try:
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        since = (now - timedelta(days=30)).isoformat()
        txn_res = await sb.table("inventory_transactions").select("quantity_delta,created_at") \
            .eq("item_id", str(item_id)).eq("transaction_type", "ISSUE").gte("created_at", since).execute()
        txns = txn_res.data or []
        total = sum(float(t["quantity_delta"]) for t in txns)
        rate = total / 30

        item_res = await sb.table("inventory_items").select("quantity").eq("id", str(item_id)).execute()
        qty = float((item_res.data or [{}])[0].get("quantity", 0))
        days = round(qty / rate, 2) if rate > 0 else None

        # Build a 30-day daily-consumption series, then smooth it with a 7-day EMA
        # so the frontend always has a trend line to plot.
        today = now.date()
        daily: dict[str, float] = {
            (today - timedelta(days=i)).isoformat(): 0.0 for i in range(29, -1, -1)
        }
        for t in txns:
            created = t.get("created_at")
            if not created:
                continue
            day_key = created[:10]
            if day_key in daily:
                daily[day_key] += float(t["quantity_delta"])

        ema_trend = []
        alpha = 2 / (7 + 1)  # 7-day exponential moving average
        ema: Optional[float] = None
        for day_key in sorted(daily.keys()):
            value = daily[day_key]
            ema = value if ema is None else alpha * value + (1 - alpha) * ema
            ema_trend.append({"date": day_key[5:], "ema": round(ema, 3)})

        return {"item_id": str(item_id), "predicted_days_left": days, "ema_trend": ema_trend}
    except Exception as e:
        return {"item_id": str(item_id), "error": str(e)}


@router.get("/anomalies/{item_id}")
async def detect_anomaly(
    item_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_permission("analytics:read")),
    sb: Any = Depends(get_supabase_db),
):
    try:
        from datetime import timedelta

        async def get_rate(days: int) -> float:
            since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            res = await sb.table("inventory_transactions").select("quantity_delta") \
                .eq("item_id", str(item_id)).eq("transaction_type", "ISSUE").gte("created_at", since).execute()
            total = sum(float(t["quantity_delta"]) for t in (res.data or []))
            return total / days if days > 0 else 0.0

        rate_30 = await get_rate(30)
        rate_7 = await get_rate(7)
        is_spike = rate_30 > 0 and rate_7 > 2 * rate_30

        return {
            "item_id": str(item_id),
            "rate_7d": round(rate_7, 3),
            "rate_30d": round(rate_30, 3),
            "is_anomaly": is_spike,
            "ratio": round(rate_7 / rate_30, 2) if rate_30 > 0 else 0,
        }
    except Exception as e:
        return {"item_id": str(item_id), "error": str(e)}
