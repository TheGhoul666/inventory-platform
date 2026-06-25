"""
Inventory Transaction models.

Every quantity change MUST be recorded as a transaction.
This provides a complete, immutable audit trail.

Transaction types:
  ISSUE      — inventory leaves warehouse to maintenance job
  RESTOCK    — inventory arrives from supplier/internal transfer
  TRANSFER   — movement between warehouses or locations
  ADJUSTMENT — manual reconciliation correction
  RESERVATION— soft-lock for a pending work order
  RELEASE    — release of a reservation
  WRITE_OFF  — damaged/expired goods removal
"""
import uuid
from decimal import Decimal
from enum import Enum

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, AuditMixin, UUIDPKMixin


class TransactionType(str, Enum):
    ISSUE = "ISSUE"
    RESTOCK = "RESTOCK"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    RESERVATION = "RESERVATION"
    RELEASE = "RELEASE"
    WRITE_OFF = "WRITE_OFF"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"


class InventoryTransaction(UUIDPKMixin, AuditMixin, Base):
    """
    Immutable transaction record.

    quantity_delta is always POSITIVE — the type determines direction.
    quantity_before and quantity_after capture the snapshot to enable
    full audit trail reconstruction without replaying all transactions.
    """
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        CheckConstraint("quantity_delta > 0", name="ck_transaction_delta_positive"),
        CheckConstraint("quantity_before >= 0", name="ck_transaction_before_non_negative"),
        CheckConstraint("quantity_after >= 0", name="ck_transaction_after_non_negative"),
        Index("ix_transactions_item_id", "item_id"),
        Index("ix_transactions_warehouse_id", "warehouse_id"),
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_created_at", "created_at"),
        Index("ix_transactions_type", "transaction_type"),
        Index("ix_transactions_bus_id", "bus_id"),
    )

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    transaction_type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType), nullable=False
    )
    status: Mapped[TransactionStatus] = mapped_column(
        SAEnum(TransactionStatus), nullable=False, default=TransactionStatus.COMPLETED
    )

    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    quantity_before: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)

    # Optional linkages
    bus_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buses.id"), nullable=True
    )
    maintenance_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("maintenance_events.id"), nullable=True
    )
    destination_warehouse_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True,
        comment="Populated for TRANSFER type"
    )
    rollback_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_transactions.id"), nullable=True,
        comment="Points to the original transaction if this is a rollback"
    )

    # Metadata
    reason_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    item: Mapped["InventoryItem"] = relationship("InventoryItem", back_populates="transactions")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", foreign_keys=[warehouse_id])
    user: Mapped["User"] = relationship("User")
    bus: Mapped["Bus | None"] = relationship("Bus")
    maintenance_event: Mapped["MaintenanceEvent | None"] = relationship("MaintenanceEvent")
