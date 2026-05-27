"""
Inventory domain models.

Central constraint: quantity can NEVER go negative.
This is enforced at three levels:
  1. DB CHECK constraint (last resort — catches bugs)
  2. Domain rule in InventoryRules (business logic layer)
  3. SELECT FOR UPDATE in the repository (concurrency safety)
"""
import uuid
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, AuditMixin, UUIDPKMixin


class InventoryCategory(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "inventory_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_categories.id"), nullable=True
    )
    color_hex: Mapped[str | None] = mapped_column(String(7), nullable=True)

    parent: Mapped["InventoryCategory | None"] = relationship(
        "InventoryCategory", remote_side="InventoryCategory.id", back_populates="children"
    )
    children: Mapped[list["InventoryCategory"]] = relationship(
        "InventoryCategory", back_populates="parent"
    )
    items: Mapped[list["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="category"
    )


class InventoryItem(UUIDPKMixin, AuditMixin, Base):
    """
    Core inventory item.

    quantity is the AUTHORITATIVE stock number. It is only ever
    mutated via the transaction service under an explicit row-level
    lock (SELECT FOR UPDATE) to prevent lost updates under concurrency.
    """
    __tablename__ = "inventory_items"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_inventory_items_quantity_non_negative"),
        CheckConstraint("low_stock_threshold >= 0", name="ck_inventory_items_threshold_non_negative"),
        CheckConstraint("reorder_quantity > 0", name="ck_inventory_items_reorder_positive"),
        Index("ix_inventory_items_sku", "sku"),
        Index("ix_inventory_items_category_id", "category_id"),
        Index("ix_inventory_items_warehouse_id", "warehouse_id"),
    )

    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="piece")
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=Decimal("0")
    )
    reserved_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=Decimal("0"),
        comment="Quantity locked by pending work orders"
    )
    low_stock_threshold: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=Decimal("10")
    )
    critical_stock_threshold: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=Decimal("3")
    )
    reorder_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=Decimal("50")
    )
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_categories.id"), nullable=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouse_locations.id"), nullable=True
    )

    # Supplier info
    supplier_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    supplier_part_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lead_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    category: Mapped["InventoryCategory | None"] = relationship(
        "InventoryCategory", back_populates="items"
    )
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="items")
    location: Mapped["WarehouseLocation | None"] = relationship(
        "WarehouseLocation", back_populates="items"
    )
    transactions: Mapped[list["InventoryTransaction"]] = relationship(
        "InventoryTransaction", back_populates="item", order_by="InventoryTransaction.created_at.desc()"
    )
    snapshots: Mapped[list["InventorySnapshot"]] = relationship(
        "InventorySnapshot", back_populates="item"
    )

    @property
    def available_quantity(self) -> Decimal:
        """Quantity available for issue (excludes reservations)."""
        return max(self.quantity - self.reserved_quantity, Decimal("0"))

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.low_stock_threshold

    @property
    def is_critical_stock(self) -> bool:
        return self.quantity <= self.critical_stock_threshold


class InventorySnapshot(UUIDPKMixin, Base):
    """
    Point-in-time snapshot of item quantity.
    Used for trend analysis and reconciliation.
    Created nightly by a scheduled worker.
    """
    __tablename__ = "inventory_snapshots"
    __table_args__ = (
        Index("ix_inventory_snapshots_item_date", "item_id", "snapshot_date"),
    )

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False
    )
    snapshot_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    created_at: Mapped[str] = mapped_column(String(30), nullable=False)

    item: Mapped["InventoryItem"] = relationship("InventoryItem", back_populates="snapshots")
