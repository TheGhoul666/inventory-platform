"""
Tests: create_item sets initial quantity correctly.

Pure unit tests — repositories are mocked, no DB needed.
Verifies that CreateItemDTO.initial_quantity flows through
InventoryService.create_item into the created InventoryItem.
"""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.inventory_dto import CreateItemDTO
from app.application.services.inventory_service import InventoryService


def _make_service():
    inv_repo = AsyncMock()
    inv_repo.create = AsyncMock()
    txn_repo = AsyncMock()
    audit_repo = AsyncMock()
    audit_repo.log = AsyncMock()
    publisher = AsyncMock()
    publisher.publish = AsyncMock()
    return InventoryService(
        inventory_repo=inv_repo,
        transaction_repo=txn_repo,
        audit_repo=audit_repo,
        event_publisher=publisher,
    )


def _dto(initial_quantity: Decimal) -> CreateItemDTO:
    return CreateItemDTO(
        sku=f"TEST-{uuid.uuid4().hex[:6].upper()}",
        name="Test Part",
        unit="pcs",
        warehouse_id=uuid.uuid4(),
        initial_quantity=initial_quantity,
    )


@pytest.mark.asyncio
async def test_initial_quantity_zero():
    svc = _make_service()
    item = await svc.create_item(_dto(Decimal("0")), uuid.uuid4())
    assert item.quantity == Decimal("0"), f"expected 0, got {item.quantity}"


@pytest.mark.asyncio
async def test_initial_quantity_five():
    svc = _make_service()
    item = await svc.create_item(_dto(Decimal("5")), uuid.uuid4())
    assert item.quantity == Decimal("5"), f"expected 5, got {item.quantity}"


@pytest.mark.asyncio
async def test_initial_quantity_hundred():
    svc = _make_service()
    item = await svc.create_item(_dto(Decimal("100")), uuid.uuid4())
    assert item.quantity == Decimal("100"), f"expected 100, got {item.quantity}"
