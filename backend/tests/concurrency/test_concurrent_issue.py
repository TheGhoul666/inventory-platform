"""
Concurrency tests.

Simulates multiple concurrent issue requests for the same item.
All requests must either succeed (if stock is available) or fail
cleanly — under no circumstances should the final quantity be
negative.

Requires a real PostgreSQL instance (not SQLite).
Set INTEGRATION_DB_URL env var to run these.
"""
import asyncio
import os
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.infrastructure.database.base import Base
from app.domain.models.inventory import InventoryItem
from app.domain.models.warehouse import Warehouse
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.audit_repository import AuditRepository
from app.application.services.inventory_service import InventoryService
from app.application.dto.inventory_dto import IssueItemDTO
from app.infrastructure.queue.publisher import EventPublisher


INTEGRATION_DB_URL = os.getenv(
    "INTEGRATION_DB_URL",
    "postgresql+asyncpg://inv_user:password@localhost:5432/bus_inventory_test",
)

pytestmark = pytest.mark.skipif(
    not os.getenv("INTEGRATION_DB_URL"),
    reason="INTEGRATION_DB_URL not set — skipping concurrency tests",
)


class MockPublisher:
    async def publish(self, routing_key: str, payload: dict) -> None:
        pass


@pytest_asyncio.fixture(scope="module")
async def pg_engine():
    engine = create_async_engine(INTEGRATION_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def concurrent_item(pg_engine) -> tuple[uuid.UUID, uuid.UUID]:
    """Create warehouse + item with 50 units for concurrency test."""
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with factory() as session:
        wh = Warehouse(id=uuid.uuid4(), name="ConcTest Depot", code="CT01", country="IL", is_active=True)
        session.add(wh)
        await session.flush()

        item = InventoryItem(
            id=uuid.uuid4(),
            sku=f"CONC-{uuid.uuid4().hex[:8]}",
            name="Concurrent Test Item",
            unit="piece",
            quantity=Decimal("50"),
            reserved_quantity=Decimal("0"),
            low_stock_threshold=Decimal("5"),
            critical_stock_threshold=Decimal("2"),
            reorder_quantity=Decimal("100"),
            warehouse_id=wh.id,
        )
        session.add(item)
        await session.commit()
        return item.id, wh.id


@pytest.mark.asyncio
async def test_concurrent_issue_no_negative_stock(pg_engine, concurrent_item):
    """
    Launch 20 concurrent issue requests for 5 units each (total demand: 100).
    Stock is only 50, so exactly 10 should succeed and 10 should fail.
    Final quantity must be >= 0.
    """
    item_id, _ = concurrent_item
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    actor_id = uuid.uuid4()
    publisher = MockPublisher()

    async def attempt_issue(session_factory) -> str:
        async with session_factory() as session:
            try:
                svc = InventoryService(
                    inventory_repo=InventoryRepository(session),
                    transaction_repo=TransactionRepository(session),
                    audit_repo=AuditRepository(session),
                    event_publisher=publisher,
                )
                dto = IssueItemDTO(item_id=item_id, quantity=Decimal("5"))
                await svc.issue_item(dto, actor_id)
                await session.commit()
                return "success"
            except Exception:
                await session.rollback()
                return "failed"

    results = await asyncio.gather(
        *[attempt_issue(factory) for _ in range(20)],
        return_exceptions=False,
    )

    success_count = results.count("success")
    fail_count = results.count("failed")

    # Verify final DB state
    async with factory() as session:
        from sqlalchemy import select
        item = (await session.execute(
            select(InventoryItem).where(InventoryItem.id == item_id)
        )).scalar_one()

        assert item.quantity >= Decimal("0"), f"Quantity went negative: {item.quantity}"
        assert success_count <= 10, f"Too many successes: {success_count}"
        expected_qty = Decimal("50") - (success_count * Decimal("5"))
        assert item.quantity == expected_qty, (
            f"Quantity mismatch: expected {expected_qty}, got {item.quantity}"
        )

    print(f"Concurrent test: {success_count} succeeded, {fail_count} failed. Final qty: {item.quantity}")
