"""Bus fleet management routes."""
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.dependencies.auth import CurrentUser, require_permission
from app.infrastructure.supabase.client import get_supabase_db

router = APIRouter(prefix="/buses", tags=["Buses"])


class BusResponse(BaseModel):
    id: uuid.UUID
    fleet_number: str
    license_plate: str
    make: str
    model: str
    year: int
    vin: Optional[str] = None
    status: str
    depot_id: Optional[uuid.UUID] = None
    mileage_km: int

    class Config:
        from_attributes = True


class CreateBusRequest(BaseModel):
    fleet_number: str
    license_plate: str
    make: str
    model: str
    year: int
    vin: Optional[str] = None
    depot_id: Optional[uuid.UUID] = None
    mileage_km: int = 0
    status: str = "ACTIVE"


class UpdateBusRequest(BaseModel):
    status: Optional[str] = None
    mileage_km: Optional[int] = None
    notes: Optional[str] = None
    depot_id: Optional[uuid.UUID] = None


VALID_STATUSES = {"ACTIVE", "MAINTENANCE", "DECOMMISSIONED", "OUT_OF_SERVICE"}


@router.get("", response_model=list[BusResponse])
async def list_buses(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: CurrentUser = Depends(require_permission("inventory:read")),
    sb: Any = Depends(get_supabase_db),
):
    query = sb.table("buses").select("*")
    if status_filter:
        query = query.eq("status", status_filter)
    result = await query.order("fleet_number").execute()
    return [BusResponse.model_validate(b) for b in result.data]


@router.post("", response_model=BusResponse, status_code=status.HTTP_201_CREATED)
async def create_bus(
    body: CreateBusRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:write")),
    sb: Any = Depends(get_supabase_db),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    try:
        result = await sb.table("buses").insert({
            "id": str(uuid.uuid4()),
            "fleet_number": body.fleet_number,
            "license_plate": body.license_plate,
            "make": body.make,
            "model": body.model,
            "year": body.year,
            "vin": body.vin,
            "depot_id": str(body.depot_id) if body.depot_id else None,
            "mileage_km": body.mileage_km,
            "status": body.status,
        }).execute()
    except Exception as e:
        msg = str(e).lower()
        if "unique" in msg or "duplicate" in msg:
            raise HTTPException(status_code=409, detail="Fleet number or license plate already exists")
        raise HTTPException(status_code=400, detail=str(e))
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create bus")
    return BusResponse.model_validate(result.data[0])


@router.patch("/{bus_id}", response_model=BusResponse)
async def update_bus(
    bus_id: uuid.UUID,
    body: UpdateBusRequest,
    current_user: CurrentUser = Depends(require_permission("inventory:write")),
    sb: Any = Depends(get_supabase_db),
):
    updates = body.model_dump(exclude_unset=True, exclude_none=True)
    if "status" in updates and updates["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {updates['status']}")
    if "depot_id" in updates:
        updates["depot_id"] = str(updates["depot_id"]) if updates["depot_id"] else None

    if not updates:
        result = await sb.table("buses").select("*").eq("id", str(bus_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Bus not found")
        return BusResponse.model_validate(result.data[0])

    result = await sb.table("buses").update(updates).eq("id", str(bus_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Bus not found")
    return BusResponse.model_validate(result.data[0])
