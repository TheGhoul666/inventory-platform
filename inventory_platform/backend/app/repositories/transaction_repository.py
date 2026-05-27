"""
Transaction Repository.

Transactions are INSERT-only after creation — never mutated
(except for status changes on rollback).
"""
import uuid
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.transaction import InventoryTransaction, TransactionType, TransactionStatus


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, tx: InventoryTransaction) -> InventoryTransaction:
        self._session.add(tx)
        await self._session.flush()
        return tx

    async def get_by_id(self, tx_id: uuid.UUID) -> Optional[InventoryTransaction]:
        return await self._session.get(
            InventoryTransaction,
            tx_id,
            options=[
                selectinload(InventoryTransaction.item),
                selectinload(InventoryTransaction.user),
                selectinload(InventoryTransaction.warehouse),
            ],
        )

    async def list_by_item(
        self,
        item_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[InventoryTransaction]:
        result = await self._session.execute(
            select(InventoryTransaction)
            .where(InventoryTransaction.item_id == item_id)
            .options(selectinload(InventoryTransaction.user))
            .order_by(InventoryTransaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def list_by_warehouse(
        self,
        warehouse_id: uuid.UUID,
        transaction_type: Optional[TransactionType] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[InventoryTransaction], int]:
        query = (
            select(InventoryTransaction)
            .where(InventoryTransaction.warehouse_id == warehouse_id)
            .options(
                selectinload(InventoryTransaction.item),
                selectinload(InventoryTransaction.user),
            )
        )
        if transaction_type:
            query = query.where(InventoryTransaction.transaction_type == transaction_type)

        count = (await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )).scalar_one()

        query = query.order_by(InventoryTransaction.created_at.desc()).offset(offset).limit(limit)
        txns = (await self._session.execute(query)).scalars().all()
        return txns, count

    async def mark_rolled_back(self, tx_id: uuid.UUID) -> None:
        from sqlalchemy import update
        await self._session.execute(
            update(InventoryTransaction)
            .where(InventoryTransaction.id == tx_id)
            .values(status=TransactionStatus.ROLLED_BACK)
        )

    async def get_consumption_stats(
        self,
        item_id: uuid.UUID,
        days: int = 30,
    ) -> dict:
        """Aggregate ISSUE transactions for predictive analytics."""
        from sqlalchemy import text
        from datetime import datetime, timezone, timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self._session.execute(
            select(
                func.sum(InventoryTransaction.quantity_delta).label("total_issued"),
                func.count(InventoryTransaction.id).label("issue_count"),
            ).where(
                InventoryTransaction.item_id == item_id,
                InventoryTransaction.transaction_type == TransactionType.ISSUE,
                InventoryTransaction.status == TransactionStatus.COMPLETED,
                InventoryTransaction.created_at >= cutoff,
            )
        )
        row = result.one()
        return {
            "total_issued": float(row.total_issued or 0),
            "issue_count": row.issue_count or 0,
            "days": days,
        }
