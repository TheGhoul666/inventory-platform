"""Audit log repository — INSERT only."""
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.audit import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def log(self, entry: AuditLog) -> None:
        """Append an immutable audit entry."""
        self._session.add(entry)
        # No flush — caller controls the transaction boundary.

    async def list(
        self,
        resource_type: str | None = None,
        resource_id: str | None = None,
        user_id: uuid.UUID | None = None,
        action: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[AuditLog]:
        query = select(AuditLog)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.where(AuditLog.resource_id == resource_id)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return result.scalars().all()
