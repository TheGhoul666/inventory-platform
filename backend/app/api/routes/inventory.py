"""
Inventory REST API routes — Supabase SDK edition.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.dependencies.auth import CurrentUser, require_permission
from app.infrastructure.supabase.client import get_supabase_db
from app.infrastructure.audit_helper import write_audit_log
from app.application.services.alert_engine import record_inventory_change

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ---- Response schemas ----

class ItemResponse(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    unit: str
    quantity: Decimal
    available_quantity: Decimal
    reserved_quantity: Decimal
    low_stock_threshold: Decimal
    critical_stock_threshold: Decimal
    is_low_stock: bool
    is_critical_stock: bool
    warehouse_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class PaginatedItems(BaseModel):
    items: list[ItemResponse]
    total: int
    offset: int
    limit: int


def _enrich(d: dict) -> dict:
    qty = Decimal(str(d.get("quantity") or "0"))
    reserved = Decimal(str(d.get("reserved_quantity") or "0"))
    low = Decimal(str(d.get("low_stock_threshold") or "10"))
    crit = Decimal(str(d.get("critical_stock_threshold") or "3"))
    return {
        **d,
        "available_quantity": qty - reserved,
        "is_low_stock": qty <= low,
        "is_critical_stock": qty <= crit,
    }


# ---- Read endpoints ----

@router.get("/items", response_model=PaginatedItems)
async def list_items(
    warehouse_id: Optional[uuid.UUID] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    low_stock_only: bool = Query(False),
    search: Optional[str] = Query(None, max_length=100),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(require_permission("inventory:read")),
    sb: Any = Depends(get_supabase_db),
):
    query = sb.table("inventory_items").select("*", count="exact").eq("is_deleted", False)
    if warehouse_id:
        query = query.eq("warehouse_id", str(warehouse_id))
    if category_id:
        query = query.eq("category_id", str(category_id))
    if search:
        query = query.or_(f"name.ilike.%{search}%,sku.ilike.%{search}%")

    if low_stock_only:
        # The low-stock threshold is per-item, so we cannot express it as a single
        # server-side comparison. Fetch the full filtered set (ordered), apply the
        # real per-item threshold in Python, then paginate the result so `total`
        # and the returned page stay consistent.
        result = await query.order("name").execute()
        all_rows = result.data or []
        filtered = [
            r for r in all_rows
            if Decimal(str(r.get("quantity") or 0)) <= Decimal(str(r.get("low_stock_threshold") or 10))
        ]
        total = len(filtered)
        rows = filtered[offset:offset + limit]
    else:
        result = await query.order("name").range(offset, offset + limit - 1).execute()
        rows = result.data or []
        total = result.count if result.count is not None else len(rows)

    return PaginatedItems(
        items=[ItemResponse.model_validate(_enrich(r)) for r in rows],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_permission("inventory:read")),
    sb: Any = Depends(get_supabase_db),
):
    result = await sb.table("inventory_items").select("*").eq("id", str(item_id)).eq("is_deleted", False).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemResponse.model_validate(_enrich(result.data[0]))


@router.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(
    body: dict,
    current_user: CurrentUser = Depends(require_permission("inventory:write")),
    sb: Any = Depends(get_supabase_db),
):
    required = {"sku", "name", "warehouse_id"}
    missing = required - body.keys()
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required fields: {missing}")

    item_id = str(uuid.uuid4())
    row = {
        "id": item_id,
        "sku": body["sku"],
        "name": body["name"],
        "description": body.get("description"),
        "unit": body.get("unit", "piece"),
        "quantity": str(body.get("initial_quantity") or body.get("quantity") or 0),
        "reserved_quantity": "0",
        "low_stock_threshold": str(body.get("low_stock_threshold", 10)),
        "critical_stock_threshold": str(body.get("critical_stock_threshold", 3)),
        "reorder_quantity": str(body.get("reorder_quantity", 50)),
        "unit_cost": str(body["unit_cost"]) if body.get("unit_cost") is not None else None,
        "category_id": str(body["category_id"]) if body.get("category_id") else None,
        "warehouse_id": str(body["warehouse_id"]),
        "location_id": str(body["location_id"]) if body.get("location_id") else None,
        "supplier_name": body.get("supplier_name"),
        "supplier_part_number": body.get("supplier_part_number"),
        "lead_time_days": body.get("lead_time_days"),
        "is_deleted": False,
    }

    try:
        result = await sb.table("inventory_items").insert(row).select().execute()
    except Exception as e:
        msg = str(e).lower()
        if "unique" in msg or "duplicate" in msg:
            raise HTTPException(status_code=409, detail="SKU already exists")
        raise HTTPException(status_code=400, detail=str(e))

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create item")

    await write_audit_log(
        sb, str(current_user.id), current_user.username or current_user.email,
        "CREATE", "inventory_items", item_id,
        notes=f"Created item SKU={body['sku']} name={body['name']}",
        new_values={"sku": body["sku"], "name": body["name"], "warehouse_id": str(body["warehouse_id"])},
    )
    return ItemResponse.model_validate(_enrich(result.data[0]))


# ---- Transaction request schemas ----

class IssueRequest(BaseModel):
    item_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    reason_code: Optional[str] = None
    notes: Optional[str] = None
    reference_number: Optional[str] = None
    bus_id: Optional[uuid.UUID] = None
    maintenance_event_id: Optional[uuid.UUID] = None


class RestockRequest(BaseModel):
    item_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    reason_code: Optional[str] = None
    notes: Optional[str] = None
    reference_number: Optional[str] = None


class TransferRequest(BaseModel):
    source_item_id: uuid.UUID
    dest_item_id: uuid.UUID
    dest_warehouse_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    reason_code: Optional[str] = None
    notes: Optional[str] = None


async def _get_item_or_404(sb: Any, item_id: uuid.UUID) -> dict:
    result = await sb.table("inventory_items").select("*").eq("id", str(item_id)).eq("is_deleted", False).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return result.data[0]


async def _insert_transaction(sb: Any, txn: dict) -> str:
    txn_id = str(uuid.uuid4())
    txn["id"] = txn_id
    txn["is_deleted"] = False
    await sb.table("inventory_transactions").insert(txn).select().execute()
    return txn_id


@router.post("/transactions/issue", status_code=201)
async def issue_item(
    body: IssueRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:write")),
    sb: Any = Depends(get_supabase_db),
):
    item = await _get_item_or_404(sb, body.item_id)
    qty = Decimal(str(item["quantity"]))
    reserved = Decimal(str(item.get("reserved_quantity") or "0"))
    available = qty - reserved

    if available < body.quantity:
        raise HTTPException(
            status_code=422,
            detail=f"Insufficient stock: available={available}, requested={body.quantity}",
        )

    new_qty = qty - body.quantity
    # Conditional UPDATE: only applies if quantity hasn't changed since we read it (prevents TOCTOU race)
    updated = await sb.table("inventory_items")\
        .update({"quantity": str(new_qty)})\
        .eq("id", str(body.item_id))\
        .eq("quantity", str(qty))\
        .select("id")\
        .execute()
    if not updated.data:
        raise HTTPException(status_code=409, detail="Stock changed concurrently — please retry")

    txn_id = await _insert_transaction(sb, {
        "item_id": str(body.item_id),
        "warehouse_id": item["warehouse_id"],
        "user_id": str(current_user.id),
        "transaction_type": "ISSUE",
        "status": "COMPLETED",
        "quantity_delta": str(body.quantity),
        "quantity_before": str(qty),
        "quantity_after": str(new_qty),
        "bus_id": str(body.bus_id) if body.bus_id else None,
        "maintenance_event_id": str(body.maintenance_event_id) if body.maintenance_event_id else None,
        "reason_code": body.reason_code,
        "notes": body.notes,
        "reference_number": body.reference_number,
    })

    await write_audit_log(
        sb, str(current_user.id), current_user.username or current_user.email,
        "ISSUE", "inventory_items", str(body.item_id),
        notes=f"Issued {body.quantity} units; txn={txn_id}",
        new_values={"quantity_before": str(qty), "quantity_after": str(new_qty)},
    )

    # Fire alerts + SuperAdmin notifications (never breaks the transaction)
    item["quantity"] = str(new_qty)
    await record_inventory_change(
        sb, change_type="ISSUE", item=item,
        quantity_delta=body.quantity, quantity_before=qty, quantity_after=new_qty,
        actor_name=current_user.username or current_user.email,
        extra={"reason_code": body.reason_code, "transaction_id": txn_id},
    )
    return {"transaction_id": txn_id, "status": "COMPLETED"}


@router.post("/transactions/restock", status_code=201)
async def restock_item(
    body: RestockRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:write")),
    sb: Any = Depends(get_supabase_db),
):
    item = await _get_item_or_404(sb, body.item_id)
    qty = Decimal(str(item["quantity"]))
    new_qty = qty + body.quantity

    await sb.table("inventory_items").update({"quantity": str(new_qty)}).eq("id", str(body.item_id)).execute()

    txn_id = await _insert_transaction(sb, {
        "item_id": str(body.item_id),
        "warehouse_id": item["warehouse_id"],
        "user_id": str(current_user.id),
        "transaction_type": "RESTOCK",
        "status": "COMPLETED",
        "quantity_delta": str(body.quantity),
        "quantity_before": str(qty),
        "quantity_after": str(new_qty),
        "reason_code": body.reason_code,
        "notes": body.notes,
        "reference_number": body.reference_number,
    })

    await write_audit_log(
        sb, str(current_user.id), current_user.username or current_user.email,
        "RESTOCK", "inventory_items", str(body.item_id),
        notes=f"Restocked {body.quantity} units; txn={txn_id}",
        new_values={"quantity_before": str(qty), "quantity_after": str(new_qty)},
    )

    item["quantity"] = str(new_qty)
    await record_inventory_change(
        sb, change_type="RESTOCK", item=item,
        quantity_delta=body.quantity, quantity_before=qty, quantity_after=new_qty,
        actor_name=current_user.username or current_user.email,
        extra={"reason_code": body.reason_code, "transaction_id": txn_id},
    )
    return {"transaction_id": txn_id, "status": "COMPLETED"}


@router.post("/transactions/transfer", status_code=201)
async def transfer_item(
    body: TransferRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:write")),
    sb: Any = Depends(get_supabase_db),
):
    source = await _get_item_or_404(sb, body.source_item_id)
    dest = await _get_item_or_404(sb, body.dest_item_id)

    if source["warehouse_id"] == str(body.dest_warehouse_id):
        raise HTTPException(status_code=422, detail="Source and destination warehouses must differ")

    src_qty = Decimal(str(source["quantity"]))
    src_reserved = Decimal(str(source.get("reserved_quantity") or "0"))
    available = src_qty - src_reserved

    if available < body.quantity:
        raise HTTPException(
            status_code=422,
            detail=f"Insufficient stock in source: available={available}, requested={body.quantity}",
        )

    new_src = src_qty - body.quantity
    dest_qty = Decimal(str(dest["quantity"]))
    new_dest = dest_qty + body.quantity

    await sb.table("inventory_items").update({"quantity": str(new_src)}).eq("id", str(body.source_item_id)).execute()
    await sb.table("inventory_items").update({"quantity": str(new_dest)}).eq("id", str(body.dest_item_id)).execute()

    txn_id = await _insert_transaction(sb, {
        "item_id": str(body.source_item_id),
        "warehouse_id": source["warehouse_id"],
        "user_id": str(current_user.id),
        "transaction_type": "TRANSFER",
        "status": "COMPLETED",
        "quantity_delta": str(body.quantity),
        "quantity_before": str(src_qty),
        "quantity_after": str(new_src),
        "destination_warehouse_id": str(body.dest_warehouse_id),
        "reason_code": body.reason_code,
        "notes": body.notes,
    })
    await _insert_transaction(sb, {
        "item_id": str(body.dest_item_id),
        "warehouse_id": str(body.dest_warehouse_id),
        "user_id": str(current_user.id),
        "transaction_type": "TRANSFER",
        "status": "COMPLETED",
        "quantity_delta": str(body.quantity),
        "quantity_before": str(dest_qty),
        "quantity_after": str(new_dest),
        "reason_code": body.reason_code,
        "notes": f"Inbound transfer from warehouse {source['warehouse_id']}",
    })

    await write_audit_log(
        sb, str(current_user.id), current_user.username or current_user.email,
        "TRANSFER", "inventory_items", str(body.source_item_id),
        notes=f"Transferred {body.quantity} to warehouse {body.dest_warehouse_id}",
        new_values={"dest_item_id": str(body.dest_item_id), "dest_warehouse_id": str(body.dest_warehouse_id)},
    )

    # Alert on the source item (it loses stock and may fall low/critical)
    source["quantity"] = str(new_src)
    await record_inventory_change(
        sb, change_type="TRANSFER", item=source,
        quantity_delta=body.quantity, quantity_before=src_qty, quantity_after=new_src,
        actor_name=current_user.username or current_user.email,
        extra={
            "dest_item_id": str(body.dest_item_id),
            "dest_warehouse_id": str(body.dest_warehouse_id),
            "transaction_id": txn_id,
        },
    )
    return {"transaction_id": txn_id, "status": "COMPLETED"}


@router.get("/transactions")
async def list_transactions(
    item_id: Optional[uuid.UUID] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(require_permission("inventory:read")),
    sb: Any = Depends(get_supabase_db),
):
    query = sb.table("inventory_transactions").select("*, inventory_items(name,sku)")
    if item_id:
        query = query.eq("item_id", str(item_id))
    result = await query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

    rows = result.data or []
    return {"transactions": [
        {
            "id": r["id"],
            "type": r["transaction_type"],
            "status": r["status"],
            "quantity_delta": float(r["quantity_delta"]),
            "quantity_before": float(r["quantity_before"]),
            "quantity_after": float(r["quantity_after"]),
            "created_at": r.get("created_at"),
            "notes": r.get("notes"),
            "item_id": r.get("item_id"),
            "item_name": (r.get("inventory_items") or {}).get("name") if isinstance(r.get("inventory_items"), dict) else None,
            "item_sku": (r.get("inventory_items") or {}).get("sku") if isinstance(r.get("inventory_items"), dict) else None,
        }
        for r in rows
    ]}


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_permission("inventory:write")),
    sb: Any = Depends(get_supabase_db),
):
    txn_check = await sb.table("inventory_transactions").select("id").eq("item_id", str(item_id)).limit(1).execute()
    if txn_check.data:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete item with existing transactions. Write off all stock first.",
        )
    result = await sb.table("inventory_items").delete().eq("id", str(item_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Item not found")

    await write_audit_log(
        sb, str(current_user.id), current_user.username or current_user.email,
        "DELETE", "inventory_items", str(item_id),
    )


@router.post("/transactions/{tx_id}/rollback", status_code=200)
async def rollback_transaction(
    tx_id: uuid.UUID,
    reason: str = Query(..., min_length=1),
    current_user: CurrentUser = Depends(require_permission("inventory:admin")),
    sb: Any = Depends(get_supabase_db),
):
    txn_res = await sb.table("inventory_transactions").select("*").eq("id", str(tx_id)).execute()
    if not txn_res.data:
        raise HTTPException(status_code=404, detail="Transaction not found")
    txn = txn_res.data[0]

    if txn["status"] != "COMPLETED":
        raise HTTPException(status_code=422, detail=f"Cannot roll back transaction in status {txn['status']}")
    if txn["transaction_type"] not in ("ISSUE", "RESTOCK"):
        raise HTTPException(status_code=422, detail=f"Rollback not supported for {txn['transaction_type']}")

    item = await _get_item_or_404(sb, uuid.UUID(txn["item_id"]))
    qty = Decimal(str(item["quantity"]))
    delta = Decimal(str(txn["quantity_delta"]))

    if txn["transaction_type"] == "ISSUE":
        new_qty = qty + delta
    else:
        new_qty = qty - delta
        if new_qty < 0:
            raise HTTPException(status_code=422, detail="Rollback would result in negative stock")

    await sb.table("inventory_items").update({"quantity": str(new_qty)}).eq("id", item["id"]).execute()
    await sb.table("inventory_transactions").update({"status": "ROLLED_BACK"}).eq("id", str(tx_id)).execute()

    rollback_id = await _insert_transaction(sb, {
        "item_id": item["id"],
        "warehouse_id": item["warehouse_id"],
        "user_id": str(current_user.id),
        "transaction_type": txn["transaction_type"],
        "status": "COMPLETED",
        "quantity_delta": str(delta),
        "quantity_before": str(qty),
        "quantity_after": str(new_qty),
        "rollback_of_id": str(tx_id),
        "reason_code": "ROLLBACK",
        "notes": reason,
    })

    await write_audit_log(
        sb, str(current_user.id), current_user.username or current_user.email,
        "ROLLBACK", "inventory_transactions", str(tx_id),
        notes=reason,
    )
    return {"rollback_transaction_id": rollback_id}
