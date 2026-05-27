"""
Analytics and Predictive Inventory Service.

Implements:
  - Consumption rate calculation
  - Days-to-depletion prediction
  - Exponential Moving Average (EMA) for trend smoothing
  - Anomaly detection (usage spike)
"""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional

from app.repositories.inventory_repository import InventoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.infrastructure.cache.redis_client import RedisClient


class AnalyticsService:
    EMA_ALPHA = 0.3  # smoothing factor — higher = more weight to recent data

    def __init__(
        self,
        inventory_repo: InventoryRepository,
        transaction_repo: TransactionRepository,
        cache: RedisClient,
    ):
        self._inv = inventory_repo
        self._txn = transaction_repo
        self._cache = cache

    async def get_consumption_rate(
        self, item_id: uuid.UUID, days: int = 30
    ) -> float:
        """
        Returns average daily consumption rate over the past `days` days.
        Formula: rate = total_issued / days
        """
        cache_key = f"analytics:consumption_rate:{item_id}:{days}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return float(cached)

        stats = await self._txn.get_consumption_stats(item_id, days)
        rate = stats["total_issued"] / days if days > 0 else 0.0

        await self._cache.set(cache_key, str(rate), ttl=300)
        return rate

    async def get_predicted_depletion_days(self, item_id: uuid.UUID) -> Optional[float]:
        """
        Predicted days until stock hits zero.
        Formula: days_left = current_quantity / daily_rate
        Returns None if consumption rate is zero (item not moving).
        """
        item = await self._inv.get_by_id(item_id)
        if item is None:
            return None

        rate = await self.get_consumption_rate(item_id, days=30)
        if rate <= 0:
            return None

        days_left = float(item.quantity) / rate
        return round(days_left, 2)

    async def compute_ema(
        self, item_id: uuid.UUID, window_days: int = 7
    ) -> list[dict]:
        """
        Compute Exponential Moving Average of daily consumption.
        EMA_t = α * actual_t + (1 - α) * EMA_(t-1)
        """
        from app.domain.models.transaction import InventoryTransaction, TransactionType, TransactionStatus
        from sqlalchemy import select, func, text

        # Get daily consumption for the past window
        # This is a simplified version — production would use a proper time-series query
        stats = await self._txn.get_consumption_stats(item_id, days=window_days)
        daily_avg = stats["total_issued"] / window_days if window_days > 0 else 0

        ema = daily_avg
        result = []
        for day in range(window_days):
            date = (datetime.now(timezone.utc) - timedelta(days=window_days - day)).date()
            ema = self.EMA_ALPHA * daily_avg + (1 - self.EMA_ALPHA) * ema
            result.append({"date": str(date), "ema": round(ema, 3)})

        return result

    async def detect_anomaly(self, item_id: uuid.UUID) -> dict:
        """
        Detect anomalous usage spike.
        Compares last 7-day rate vs 30-day baseline.
        Spike threshold: last 7d rate > 2x baseline.
        """
        rate_30d = await self.get_consumption_rate(item_id, days=30)
        rate_7d = await self.get_consumption_rate(item_id, days=7)

        is_spike = rate_30d > 0 and rate_7d > 2 * rate_30d

        return {
            "item_id": str(item_id),
            "rate_7d": round(rate_7d, 3),
            "rate_30d": round(rate_30d, 3),
            "is_anomaly": is_spike,
            "ratio": round(rate_7d / rate_30d, 2) if rate_30d > 0 else 0,
        }

    async def get_dashboard_summary(self) -> dict:
        """
        Aggregated dashboard metrics.
        Cached for 60 seconds to handle burst dashboard loads.
        """
        cache_key = "analytics:dashboard_summary"
        cached = await self._cache.get_json(cache_key)
        if cached:
            return cached

        low_stock_items = await self._inv.get_low_stock_items()
        critical_items = await self._inv.get_critical_stock_items()
        _, total_items = await self._inv.list_items(limit=1)

        summary = {
            "low_stock_count": len(low_stock_items),
            "critical_stock_count": len(critical_items),
            "total_items_count": total_items,
            "critical_items": [
                {
                    "id": str(item.id),
                    "name": item.name,
                    "sku": item.sku,
                    "quantity": float(item.quantity),
                    "threshold": float(item.critical_stock_threshold),
                }
                for item in critical_items[:10]
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        await self._cache.set_json(cache_key, summary, ttl=60)
        return summary
