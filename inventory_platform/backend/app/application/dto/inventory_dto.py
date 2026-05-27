"""
Data Transfer Objects for inventory operations.

Pydantic v2 models used as immutable command objects.
These cross the API→Application boundary.
"""
import uuid
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CreateItemDTO(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    unit: str = Field(default="piece", max_length=30)
    low_stock_threshold: Decimal = Field(default=Decimal("10"), ge=0)
    critical_stock_threshold: Decimal = Field(default=Decimal("3"), ge=0)
    reorder_quantity: Decimal = Field(default=Decimal("50"), gt=0)
    unit_cost: Optional[Decimal] = Field(default=None, ge=0)
    category_id: Optional[uuid.UUID] = None
    warehouse_id: uuid.UUID
    location_id: Optional[uuid.UUID] = None
    supplier_name: Optional[str] = Field(default=None, max_length=200)
    supplier_part_number: Optional[str] = Field(default=None, max_length=100)
    lead_time_days: Optional[int] = Field(default=None, ge=0)
    initial_quantity: Decimal = Field(default=Decimal("0"), ge=0)


class UpdateItemDTO(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    unit: Optional[str] = Field(default=None, max_length=30)
    low_stock_threshold: Optional[Decimal] = Field(default=None, ge=0)
    critical_stock_threshold: Optional[Decimal] = Field(default=None, ge=0)
    reorder_quantity: Optional[Decimal] = Field(default=None, gt=0)
    unit_cost: Optional[Decimal] = Field(default=None, ge=0)
    category_id: Optional[uuid.UUID] = None
    location_id: Optional[uuid.UUID] = None
    supplier_name: Optional[str] = None
    supplier_part_number: Optional[str] = None
    lead_time_days: Optional[int] = None


class IssueItemDTO(BaseModel):
    item_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    reason_code: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = None
    reference_number: Optional[str] = Field(default=None, max_length=100)
    bus_id: Optional[uuid.UUID] = None
    maintenance_event_id: Optional[uuid.UUID] = None


class RestockItemDTO(BaseModel):
    item_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    reason_code: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = None
    reference_number: Optional[str] = Field(default=None, max_length=100)


class TransferItemDTO(BaseModel):
    source_item_id: uuid.UUID
    dest_item_id: uuid.UUID
    source_warehouse_id: uuid.UUID
    dest_warehouse_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    reason_code: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("dest_warehouse_id")
    @classmethod
    def warehouses_must_differ(cls, v: uuid.UUID, info) -> uuid.UUID:
        if "source_warehouse_id" in info.data and v == info.data["source_warehouse_id"]:
            raise ValueError("Source and destination warehouses must differ")
        return v
