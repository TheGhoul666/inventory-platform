"""
Redis client wrapper.

Provides typed helpers for common cache patterns.
Wraps redis-py async client with JSON serialization,
TTL enforcement, and error resilience.

CONSISTENCY STRATEGY:
  - Cache entries have a hard TTL (max 5 min for hot data).
  - On write operations (issue/restock), the affected item's
    cache key is explicitly invalidated.
  - We accept eventual consistency for read-heavy dashboards
    but require freshness for stock-level decisions (bypass cache
    for locked reads — SELECT FOR UPDATE goes directly to DB).
"""
import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisClient:
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self._client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        await self._client.ping()
        logger.info("Redis connected")

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()

    async def get(self, key: str) -> Optional[str]:
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.warning(f"Redis GET failed for {key}: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        try:
            await self._client.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Redis SET failed for {key}: {e}")

    async def get_json(self, key: str) -> Optional[Any]:
        raw = await self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def set_json(self, key: str, value: Any, ttl: int = 300) -> None:
        await self.set(key, json.dumps(value, default=str), ttl)

    async def delete(self, *keys: str) -> None:
        try:
            await self._client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis DELETE failed: {e}")

    async def invalidate_item_cache(self, item_id: str) -> None:
        """Evict all cache entries related to an inventory item."""
        pattern = f"*{item_id}*"
        try:
            cursor = 0
            while True:
                cursor, keys = await self._client.scan(cursor, match=pattern, count=100)
                if keys:
                    await self._client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Cache invalidation failed for item {item_id}: {e}")

    async def rate_limit_check(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Sliding window rate limiter using Redis INCR + EXPIRE.
        Returns True if request is allowed, False if rate limited.
        """
        try:
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            results = await pipe.execute()
            count = results[0]
            return count <= limit
        except Exception:
            return True  # fail open — don't block on Redis failure

    async def health_check(self) -> bool:
        try:
            return await self._client.ping()
        except Exception:
            return False


# Singleton instance
redis_client = RedisClient()
