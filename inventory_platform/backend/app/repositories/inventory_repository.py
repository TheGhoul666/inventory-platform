"""
Inventory Repository.

CONCURRENCY CONTRACT
====================
All methods that modify inventory quantity MUST call
`get_item_with_lock()` first, which issues a SELECT FOR UPDATE.
This serializes concurrent transactions at the row level,
preventing lost updates and negative stock.

Transaction isolation: READ COMMITTED (PostgreSQL default).
Row-level locking via SELECT FOR UPDATE provides the additional
serialization guarantee we need for inventory mutations.

Sequence for a safe issue:
  1. BEGIN TRANSACTION (implicit via session)
  2. SELECT * FROM inventory_items WHERE id=X FOR UPDATE NOWAIT
     → blocks other writers until this transaction commits/rolls back
  3. Apply business rules (assert_sufficient_stock)
  4. UPDATE quantity
  5. INSERT transaction record
  6. COMMIT

NOWAIT vs WAIT:
  We use NOWAIT to immediately surface contention rather than
  letting requests pile up. The API returns 409 Conflict and
  the client retries with exponential backoff.
"""
import uuid
from decimal import Decimal
from typing import List, Optional, Sequence

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.inventory import InventoryItem, InventoryCategory, InventorySnapshot
from app.domain.models.transaction import InventoryTransaction, TransactionType, TransactionStatus
from app.domain.rules.inventory_rules import assert_sufficient_stock, assert_positive_quantity
from app.domain.exceptions import ItemNotFoundError


class InventoryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_by_id(self, item_id: uuid.UUID) -> Optional[InventoryItem]:
        result = await self._session.get(InventoryItem, item_id)
        return result

    async def get_by_id_or_raise(self, item_id: uuid.UUID) -> InventoryItem:
        item = await self.get_by_id(item_id)
        if item is None:
            raise ItemNotFoundError(str(item_id))
        return item

    async def get_by_sku(self, sku: str) -> Optional[InventoryItem]:
        result = await self._session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku, InventoryItem.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def list_items(
        self,
        warehouse_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        low_stock_only: bool = False,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[InventoryItem], int]:
        query = (
            select(InventoryItem)
            .where(InventoryItem.is_deleted == False)
            .options(selectinload(InventoryItem.category), selectinload(InventoryItem.warehouse))
        )
        if warehouse_id:
            query = query.where(InventoryItem.warehouse_id == warehouse_id)
        if category_id:
            query = query.where(InventoryItem.category_id == category_id)
        if low_stock_only:
            query = query.where(InventoryItem.quantity <= InventoryItem.low_stock_threshold)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                InventoryItem.name.ilike(pattern) | InventoryItem.sku.ilike(pattern)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self._session.execute(count_query)).scalar_one()

        query = query.offset(offset).limit(limit).order_by(InventoryItem.name)
        items = (await self._session.execute(query)).scalars().all()
        return items, total

    # ------------------------------------------------------------------
    # CRITICAL: Row-level locked read for mutations
    # ------------------------------------------------------------------

    async def get_item_with_lock(self, item_id: uuid.UUID) -> InventoryItem:
        """
        SELECT FOR UPDATE NOWAIT — acquires an exclusive row-level lock.

        NOWAIT: raise immediately if the row is already locked.
        The caller catches OperationalError and returns HTTP 409.

        This is the ONLY correct entry point for any write that
        changes item.quantity or item.reserved_quantity.
        """
        result = await self._session.execute(
            select(InventoryItem)
            .where(InventoryItem.id == item_id, InventoryItem.is_deleted == False)
            .with_for_update(nowait=True)
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise ItemNotFoundError(str(item_id))
        return item

    # ------------------------------------------------------------------
    # Write operations (always called AFTER get_item_with_lock)
    # ------------------------------------------------------------------

    async def create(self, item: InventoryItem) -> InventoryItem:
        self._session.add(item)
        await self._session.flush()  # get DB-generated defaults
        return item

    async def soft_delete(self, item_id: uuid.UUID, deleted_at: str) -> None:
        await self._session.execute(
            update(InventoryItem)
            .where(InventoryItem.id == item_id)
            .values(is_deleted=True, deleted_at=deleted_at)
        )

    # ------------------------------------------------------------------
    # Analytics support
    # ------------------------------------------------------------------

    async def get_low_stock_items(self) -> Sequence[InventoryItem]:
        result = await self._session.execute(
            select(InventoryItem)
            .where(
                InventoryItem.is_deleted == False,
                InventoryItem.quantity <= InventoryItem.low_stock_threshold,
            )
            .options(selectinload(InventoryItem.warehouse))
            .order_by(InventoryItem.quantity)
        )
        return result.scalars().all()

    async def get_critical_stock_items(self) -> Sequence[InventoryItem]:
        result = await self._session.execute(
            select(InventoryItem)
            .where(
                InventoryItem.is_deleted == False,
                InventoryItem.quantity <= InventoryItem.critical_stock_threshold,
            )
            .options(selectinload(InventoryItem.warehouse))
        )
        return result.scalars().all()

    async def create_snapshot(self, snapshot: InventorySnapshot) -> None:
        self._session.add(snapshot)
        await self._session.flush()
