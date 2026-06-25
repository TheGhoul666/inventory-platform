"""Audit log routes — read-only."""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import CurrentUser, require_permission
from app.infrastructure.supabase.client import get_supabase_db

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("")
async def list_audit_logs(
    resource_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(require_permission("audit:read")),
    sb: Any = Depends(get_supabase_db),
):
    query = sb.table("audit_logs").select("*")
    if resource_type:
        query = query.eq("resource_type", resource_type)
    if action:
        query = query.eq("action", action)
    result = await query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    rows = result.data or []

    return {
        "logs": [
            {
                "id": r["id"],
                "user_id": r.get("user_id"),
                "username": r.get("username"),
                "action": r["action"],
                "resource_type": r["resource_type"],
                "resource_id": r.get("resource_id"),
                "created_at": r.get("created_at"),
                "notes": r.get("notes"),
            }
            for r in rows
        ]
    }
