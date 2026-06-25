"""
Inventory Application Service.

Orchestrates use cases, enforces business rules, coordinates
repositories, emits domain events, and writes the audit log.

This is the ONLY place allowed to call get_item_with_lock().
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.exc import OperationalError

from app.domain.models.inventory import InventoryItem, InventoryCategory
from app.domain.models.transaction import (
    InventoryTransaction,
    TransactionType,
    TransactionStatus,
)
from app.domain.models.audit import AuditLog
from app.domain.rules.inventory_rules import (
    assert_sufficient_stock,
    assert_positive_quantity,
    assert_transfer_different_warehouses,
)
from app.domain.exceptions import (
    InsufficientStockError,
    InvalidTransactionError,
    ItemNotFoundError,
)
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.audit_repository import AuditRepository
from app.infrastructure.queue.publisher import EventPublisher
from app.application.dto.inventory_dto import (
    CreateItemDTO,
    IssueItemDTO,
    RestockItemDTO,
    TransferItemDTO,
)


class InventoryService:
    def __init__(
        self,
        inventory_repo: InventoryRepository,
        transaction_repo: TransactionRepository,
        audit_repo: AuditRepository,
        event_publisher: EventPublisher,
    ):
        self._inv = inventory_repo
        self._txn = transaction_repo
        self._audit = audit_repo
        self._pub = event_publisher

    # ----------------------------------------------------------------
    # CREATE / UPDATE / DELETE
    # ----------------------------------------------------------------

    async def create_item(self, dto: CreateItemDTO, actor_id: uuid.UUID) -> InventoryItem:
        item = InventoryItem(
            sku=dto.sku,
            name=dto.name,
            description=dto.description,
            unit=dto.unit,
            quantity=dto.initial_quantity,
            low_stock_threshold=dto.low_stock_threshold,
            critical_stock_threshold=dto.critical_stock_threshold,
            reorder_quantity=dto.reorder_quantity,
            unit_cost=dto.unit_cost,
            category_id=dto.category_id,
            warehouse_id=dto.warehouse_id,
            location_id=dto.location_id,
            supplier_name=dto.supplier_name,
            supplier_part_number=dto.supplier_part_number,
            lead_time_days=dto.lead_time_days,
        )
        await self._inv.create(item)
        await self._audit.log(AuditLog(
            user_id=actor_id,
            action="CREATE",
            resource_type="InventoryItem",
            resource_id=str(item.id),
            new_values={"sku": dto.sku, "name": dto.name, "initial_quantity": str(dto.initial_quantity)},
            created_at=datetime.now(timezone.utc).isoformat(),
        ))
        return item

    # ----------------------------------------------------------------
    # ISSUE — inventory leaves warehouse
    # ----------------------------------------------------------------

    async def issue_item(self, dto: IssueItemDTO, actor_id: uuid.UUID) -> InventoryTransaction:
        """
        Issue inventory items to a maintenance job.

        CONCURRENCY: Uses SELECT FOR UPDATE NOWAIT so simultaneous
        issue requests for the same item are serialized at the DB
        level. If the row is already locked, raises HTTP 409.
        """
        assert_positive_quantity(dto.quantity)

        try:
            item = await self._inv.get_item_with_lock(dto.item_id)
        except OperationalError:
            # Another transaction holds the lock right now.
            raise InvalidTransactionError(
                f"Item {dto.item_id} is currently locked by another operation. Retry shortly."
            )

        assert_sufficient_stock(
            item_id=str(item.id),
            current_quantity=item.quantity,
            reserved_quantity=item.reserved_quantity,
            requested=dto.quantity,
        )

        before = item.quantity
        item.quantity -= dto.quantity

        txn = InventoryTransaction(
            item_id=item.id,
            warehouse_id=item.warehouse_id,
            user_id=actor_id,
            transaction_type=TransactionType.ISSUE,
            status=TransactionStatus.COMPLETED,
            quantity_delta=dto.quantity,
            quantity_before=before,
            quantity_after=item.quantity,
            bus_id=dto.bus_id,
            maintenance_event_id=dto.maintenance_event_id,
            reason_code=dto.reason_code,
            notes=dto.notes,
            reference_number=dto.reference_number,
        )
        await self._txn.create(txn)
        await self._audit.log(AuditLog(
            user_id=actor_id,
            action="ISSUE",
            resource_type="InventoryItem",
            resource_id=str(item.id),
            old_values={"quantity": float(before)},
            new_values={"quantity": float(item.quantity)},
            created_at=datetime.now(timezone.utc).isoformat(),
        ))

        # Publish domain event for async alert/webhook processing
        await self._pub.publish("inventory.updated", {
            "event": "ITEM_ISSUED",
            "item_id": str(item.id),
            "quantity_after": float(item.quantity),
            "low_stock_threshold": float(item.low_stock_threshold),
            "critical_stock_threshold": float(item.critical_stock_threshold),
            "warehouse_id": str(item.warehouse_id),
        })

        return txn

    # ----------------------------------------------------------------
    # RESTOCK — inventory arrives
    # ----------------------------------------------------------------

    async def restock_item(self, dto: RestockItemDTO, actor_id: uuid.UUID) -> InventoryTransaction:
        assert_positive_quantity(dto.quantity)

        try:
            item = await self._inv.get_item_with_lock(dto.item_id)
        except OperationalError:
            raise InvalidTransactionError(
                f"Item {dto.item_id} is currently locked. Retry shortly."
            )

        before = item.quantity
        item.quantity += dto.quantity

        txn = InventoryTransaction(
            item_id=item.id,
            warehouse_id=item.warehouse_id,
            user_id=actor_id,
            transaction_type=TransactionType.RESTOCK,
            status=TransactionStatus.COMPLETED,
            quantity_delta=dto.quantity,
            quantity_before=before,
            quantity_after=item.quantity,
            reason_code=dto.reason_code,
            notes=dto.notes,
            reference_number=dto.reference_number,
        )
        await self._txn.create(txn)
        await self._audit.log(AuditLog(
            user_id=actor_id,
            action="RESTOCK",
            resource_type="InventoryItem",
            resource_id=str(item.id),
            old_values={"quantity": float(before)},
            new_values={"quantity": float(item.quantity)},
            created_at=datetime.now(timezone.utc).isoformat(),
        ))
        await self._pub.publish("inventory.updated", {
            "event": "ITEM_RESTOCKED",
            "item_id": str(item.id),
            "quantity_after": float(item.quantity),
            "warehouse_id": str(item.warehouse_id),
        })
        return txn

    # ----------------------------------------------------------------
    # TRANSFER — move between warehouses
    # ----------------------------------------------------------------

    async def transfer_item(self, dto: TransferItemDTO, actor_id: uuid.UUID) -> InventoryTransaction:
        """
        Transfer requires locking BOTH the source and destination items.

        Lock ordering: always lock the lower UUID first to avoid deadlocks
        when two concurrent transfers go in opposite directions.
        """
        assert_positive_quantity(dto.quantity)
        assert_transfer_different_warehouses(
            str(dto.source_warehouse_id), str(dto.dest_warehouse_id)
        )

        ids_sorted = sorted([dto.source_item_id, dto.dest_item_id])
        first_id, second_id = ids_sorted[0], ids_sorted[1]

        try:
            first = await self._inv.get_item_with_lock(first_id)
            second = await self._inv.get_item_with_lock(second_id)
        except OperationalError:
            raise InvalidTransactionError("Transfer items are locked. Retry shortly.")

        source = first if first.id == dto.source_item_id else second
        dest = first if first.id == dto.dest_item_id else second

        assert_sufficient_stock(
            item_id=str(source.id),
            current_quantity=source.quantity,
            reserved_quantity=source.reserved_quantity,
            requested=dto.quantity,
        )

        before_source = source.quantity
        before_dest = dest.quantity

        source.quantity -= dto.quantity
        dest.quantity += dto.quantity

        # Record the outbound leg (the canonical transaction)
        txn = InventoryTransaction(
            item_id=source.id,
            warehouse_id=source.warehouse_id,
            user_id=actor_id,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            quantity_delta=dto.quantity,
            quantity_before=before_source,
            quantity_after=source.quantity,
            destination_warehouse_id=dto.dest_warehouse_id,
            reason_code=dto.reason_code,
            notes=dto.notes,
        )
        await self._txn.create(txn)

        # Record the inbound leg
        inbound_txn = InventoryTransaction(
            item_id=dest.id,
            warehouse_id=dest.warehouse_id,
            user_id=actor_id,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            quantity_delta=dto.quantity,
            quantity_before=before_dest,
            quantity_after=dest.quantity,
            reason_code=dto.reason_code,
            notes=f"Inbound transfer from {dto.source_warehouse_id}",
        )
        await self._txn.create(inbound_txn)
        return txn

    # ----------------------------------------------------------------
    # ROLLBACK
    # ----------------------------------------------------------------

    async def rollback_transaction(
        self, tx_id: uuid.UUID, actor_id: uuid.UUID, reason: str
    ) -> InventoryTransaction:
        """
        Reverse a completed transaction.

        Only ISSUE and RESTOCK can be rolled back.
        Creates a compensating transaction and marks the original ROLLED_BACK.
        """
        original = await self._txn.get_by_id(tx_id)
        if original is None:
            raise InvalidTransactionError(f"Transaction {tx_id} not found")
        if original.status != TransactionStatus.COMPLETED:
            raise InvalidTransactionError(
                f"Cannot roll back transaction in status {original.status}"
            )
        if original.transaction_type not in (TransactionType.ISSUE, TransactionType.RESTOCK):
            raise InvalidTransactionError(
                f"Rollback is not supported for {original.transaction_type}"
            )

        try:
            item = await self._inv.get_item_with_lock(original.item_id)
        except OperationalError:
            raise InvalidTransactionError("Item locked. Retry shortly.")

        before = item.quantity
        # Invert the original operation
        if original.transaction_type == TransactionType.ISSUE:
            item.quantity += original.quantity_delta  # restore
        else:
            # Restock rollback — ensure we don't go negative
            assert_sufficient_stock(
                str(item.id), item.quantity, item.reserved_quantity, original.quantity_delta
            )
            item.quantity -= original.quantity_delta

        compensating = InventoryTransaction(
            item_id=item.id,
            warehouse_id=item.warehouse_id,
            user_id=actor_id,
            transaction_type=original.transaction_type,
            status=TransactionStatus.COMPLETED,
            quantity_delta=original.quantity_delta,
            quantity_before=before,
            quantity_after=item.quantity,
            rollback_of_id=original.id,
            reason_code="ROLLBACK",
            notes=reason,
        )
        await self._txn.create(compensating)
        await self._txn.mark_rolled_back(original.id)
        await self._audit.log(AuditLog(
            user_id=actor_id,
            action="ROLLBACK",
            resource_type="InventoryTransaction",
            resource_id=str(original.id),
            new_values={"rollback_tx_id": str(compensating.id), "reason": reason},
            created_at=datetime.now(timezone.utc).isoformat(),
        ))
        return compensating
