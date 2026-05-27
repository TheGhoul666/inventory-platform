"""Alert management routes."""
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies.auth import CurrentUser, require_permission
from app.infrastructure.supabase.client import get_supabase_db

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
async def list_alerts(
    status_filter: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(require_permission("alerts:read")),
    sb: Any = Depends(get_supabase_db),
):
    query = sb.table("alerts").select("*").eq("is_deleted", False)
    if status_filter:
        query = query.eq("status", status_filter)
    if severity:
        query = query.eq("severity", severity)
    result = await query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    rows = result.data or []

    return {
        "alerts": [
            {
                "id": r["id"],
                "type": r["alert_type"],
                "severity": r["severity"],
                "status": r["status"],
                "title": r["title"],
                "message": r["message"],
                "item_id": r.get("item_id"),
                "warehouse_id": r.get("warehouse_id"),
                "created_at": r.get("created_at"),
                "acknowledged_at": r.get("acknowledged_at"),
            }
            for r in rows
        ]
    }


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_permission("alerts:write")),
    sb: Any = Depends(get_supabase_db),
):
    result = await sb.table("alerts").update({
        "status": "ACKNOWLEDGED",
        "acknowledged_by": str(current_user.id),
        "acknowledged_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", str(alert_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged"}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_permission("alerts:write")),
    sb: Any = Depends(get_supabase_db),
):
    result = await sb.table("alerts").update({
        "status": "RESOLVED",
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", str(alert_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "resolved"}
