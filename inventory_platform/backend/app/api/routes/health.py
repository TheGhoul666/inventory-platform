"""Health check and readiness probes."""
from fastapi import APIRouter

from app.infrastructure.supabase.client import get_async_admin
from app.infrastructure.cache.redis_client import redis_client

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def readiness():
    """Check all critical dependencies are reachable."""
    checks = {}

    try:
        sb = await get_async_admin()
        result = await sb.table("warehouses").select("id").limit(1).execute()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        redis_ok = await redis_client.health_check()
        checks["redis"] = "ok" if redis_ok else "error"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = checks.get("database") == "ok"
    return {"status": "ready" if all_ok else "degraded", "checks": checks}


@router.get("/metrics/health")
async def metrics_health():
    return {"status": "ok"}
