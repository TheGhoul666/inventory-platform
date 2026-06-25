"""
Bus and Maintenance Event ORM models.

Buses are the primary consumers of inventory. Maintenance events
link directly to transactions so you can answer "which parts were
used in bus #42's overhaul on 2026-03-15?"
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Enum as SAEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, AuditMixin, UUIDPKMixin


class BusStatus(str, Enum):
    ACTIVE = "ACTIVE"
    IN_MAINTENANCE = "IN_MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    DECOMMISSIONED = "DECOMMISSIONED"


class MaintenanceEventType(str, Enum):
    SCHEDULED = "SCHEDULED"
    CORRECTIVE = "CORRECTIVE"
    EMERGENCY = "EMERGENCY"
    INSPECTION = "INSPECTION"
    OVERHAUL = "OVERHAUL"


class MaintenanceEventStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Bus(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "buses"

    fleet_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    license_plate: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    make: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    vin: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    status: Mapped[BusStatus] = mapped_column(
        SAEnum(BusStatus), nullable=False, default=BusStatus.ACTIVE
    )
    depot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True,
        comment="Warehouse/depot that services this bus"
    )
    mileage_km: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_service_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    maintenance_events: Mapped[list["MaintenanceEvent"]] = relationship(
        "MaintenanceEvent", back_populates="bus", order_by="MaintenanceEvent.created_at.desc()"
    )


class MaintenanceEvent(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "maintenance_events"

    bus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buses.id"), nullable=False, index=True
    )
    technician_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    event_type: Mapped[MaintenanceEventType] = mapped_column(
        SAEnum(MaintenanceEventType), nullable=False
    )
    status: Mapped[MaintenanceEventStatus] = mapped_column(
        SAEnum(MaintenanceEventStatus), nullable=False, default=MaintenanceEventStatus.OPEN
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    odometer_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    labor_hours: Mapped[float | None] = mapped_column(nullable=True)
    is_warranty: Mapped[bool] = mapped_column(Boolean, default=False)

    bus: Mapped[Bus] = relationship("Bus", back_populates="maintenance_events")
    technician: Mapped["User"] = relationship("User")
