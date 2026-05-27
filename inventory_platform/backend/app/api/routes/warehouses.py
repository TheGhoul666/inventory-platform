"""Warehouse management routes."""
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.dependencies.auth import CurrentUser, require_permission
from app.infrastructure.supabase.client import get_supabase_db

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


class WarehouseResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    country: str
    phone: Optional[str] = None
    is_active: bool
    capacity_sqm: Optional[int] = None

    class Config:
        from_attributes = True


class CreateWarehouseRequest(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "IL"
    phone: Optional[str] = None
    capacity_sqm: Optional[int] = None


class UpdateWarehouseRequest(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    capacity_sqm: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("", response_model=list[WarehouseResponse])
async def list_warehouses(
    active_only: bool = Query(False),
    current_user: CurrentUser = Depends(require_permission("warehouse:read")),
    sb: Any = Depends(get_supabase_db),
):
    query = sb.table("warehouses").select("*")
    if active_only:
        query = query.eq("is_active", True)
    result = await query.order("name").execute()
    return [WarehouseResponse.model_validate(w) for w in result.data]


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    body: CreateWarehouseRequest,
    current_user: CurrentUser = Depends(require_permission("warehouse:admin")),
    sb: Any = Depends(get_supabase_db),
):
    try:
        result = await sb.table("warehouses").insert({
            "id": str(uuid.uuid4()),
            "name": body.name,
            "code": body.code.upper(),
            "address": body.address,
            "city": body.city,
            "country": body.country,
            "phone": body.phone,
            "capacity_sqm": body.capacity_sqm,
            "is_active": True,
        }).execute()
    except Exception as e:
        msg = str(e).lower()
        if "unique" in msg or "duplicate" in msg:
            raise HTTPException(status_code=409, detail="Warehouse name or code already exists")
        raise HTTPException(status_code=400, detail=str(e))
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create warehouse")
    return WarehouseResponse.model_validate(result.data[0])


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_permission("warehouse:read")),
    sb: Any = Depends(get_supabase_db),
):
    result = await sb.table("warehouses").select("*").eq("id", str(warehouse_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return WarehouseResponse.model_validate(result.data[0])


@router.patch("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: uuid.UUID,
    body: UpdateWarehouseRequest,
    current_user: CurrentUser = Depends(require_permission("warehouse:admin")),
    sb: Any = Depends(get_supabase_db),
):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        result = await sb.table("warehouses").select("*").eq("id", str(warehouse_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        return WarehouseResponse.model_validate(result.data[0])

    result = await sb.table("warehouses").update(updates).eq("id", str(warehouse_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return WarehouseResponse.model_validate(result.data[0])
