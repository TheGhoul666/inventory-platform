"""
Warehouse and warehouse location ORM models.

A Warehouse is a physical building. It has one or more Locations
(aisle/shelf/bin coordinates). Items are placed at locations.
"""
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, AuditMixin, UUIDPKMixin


class Warehouse(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "warehouses"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="IL")
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    capacity_sqm: Mapped[int | None] = mapped_column(Integer, nullable=True)

    locations: Mapped[list["WarehouseLocation"]] = relationship(
        "WarehouseLocation", back_populates="warehouse", cascade="all, delete-orphan"
    )
    items: Mapped[list["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="warehouse"
    )


class WarehouseLocation(UUIDPKMixin, AuditMixin, Base):
    """
    Physical shelf/bin location within a warehouse.
    Coordinates are aisle / rack / shelf / bin.
    """
    __tablename__ = "warehouse_locations"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "aisle", "rack", "shelf", "bin", name="uq_wh_location_coords"),
    )

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False
    )
    aisle: Mapped[str] = mapped_column(String(10), nullable=False)
    rack: Mapped[str] = mapped_column(String(10), nullable=False)
    shelf: Mapped[str] = mapped_column(String(10), nullable=False)
    bin: Mapped[str] = mapped_column(String(10), nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)  # human-readable e.g. "A-01-03-B"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_weight_kg: Mapped[int | None] = mapped_column(Integer, nullable=True)

    warehouse: Mapped[Warehouse] = relationship("Warehouse", back_populates="locations")
    items: Mapped[list["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="location"
    )
