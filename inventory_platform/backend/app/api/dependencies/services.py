"""
Service factory dependencies — wires repositories and services for each request.
"""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.queue.publisher import event_publisher
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository, RefreshTokenRepository
from app.repositories.audit_repository import AuditRepository
from app.application.services.inventory_service import InventoryService
from app.application.services.analytics_service import AnalyticsService
from app.auth.service import AuthService


def get_inventory_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> InventoryService:
    return InventoryService(
        inventory_repo=InventoryRepository(db),
        transaction_repo=TransactionRepository(db),
        audit_repo=AuditRepository(db),
        event_publisher=event_publisher,
    )


def get_analytics_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> AnalyticsService:
    return AnalyticsService(
        inventory_repo=InventoryRepository(db),
        transaction_repo=TransactionRepository(db),
        cache=redis_client,
    )


def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> AuthService:
    return AuthService(
        user_repo=UserRepository(db),
        token_repo=RefreshTokenRepository(db),
    )


def get_transaction_repo(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TransactionRepository:
    return TransactionRepository(db)


def get_inventory_repo(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> InventoryRepository:
    return InventoryRepository(db)


def get_audit_repo(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> AuditRepository:
    return AuditRepository(db)
