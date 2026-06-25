import uuid
from datetime import datetime, timezone
from typing import Any, Optional


async def write_audit_log(
    sb: Any,
    user_id: str,
    username: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    notes: Optional[str] = None,
    new_values: Optional[dict] = None,
) -> None:
    """Insert one audit record. Never raises — audit failure must not break the main operation."""
    try:
        await sb.table("audit_logs").insert({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "username": username,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "new_values": new_values,
            "notes": notes,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:26] + "Z",
        }).execute()
    except Exception:
        pass
