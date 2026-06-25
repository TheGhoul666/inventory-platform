"""
Unit tests for inventory business rules.
Pure functions — no DB or async needed.
"""
from decimal import Decimal

import pytest

from app.domain.rules.inventory_rules import (
    assert_sufficient_stock,
    assert_positive_quantity,
    assert_transfer_different_warehouses,
    compute_available_quantity,
)
from app.domain.exceptions import InsufficientStockError, InvalidTransactionError


class TestAssertSufficientStock:
    def test_passes_when_enough_stock(self):
        assert_sufficient_stock("item1", Decimal("100"), Decimal("10"), Decimal("50"))

    def test_raises_when_insufficient(self):
        with pytest.raises(InsufficientStockError) as exc:
            assert_sufficient_stock("item1", Decimal("10"), Decimal("5"), Decimal("10"))
        assert exc.value.item_id == "item1"
        assert exc.value.available == 5.0

    def test_exact_available_quantity_passes(self):
        # available = 100 - 20 = 80, requesting 80 should pass
        assert_sufficient_stock("item1", Decimal("100"), Decimal("20"), Decimal("80"))

    def test_one_unit_over_raises(self):
        with pytest.raises(InsufficientStockError):
            assert_sufficient_stock("item1", Decimal("100"), Decimal("20"), Decimal("81"))

    def test_ignores_reservations_when_flag_false(self):
        # With check_reservations=False, should only check total qty
        assert_sufficient_stock(
            "item1", Decimal("100"), Decimal("95"), Decimal("90"),
            check_reservations=False
        )


class TestAssertPositiveQuantity:
    def test_positive_passes(self):
        assert_positive_quantity(Decimal("1"))

    def test_zero_raises(self):
        with pytest.raises(InvalidTransactionError):
            assert_positive_quantity(Decimal("0"))

    def test_negative_raises(self):
        with pytest.raises(InvalidTransactionError):
            assert_positive_quantity(Decimal("-1"))


class TestAssertTransferDifferentWarehouses:
    def test_different_warehouses_passes(self):
        assert_transfer_different_warehouses("wh1", "wh2")

    def test_same_warehouse_raises(self):
        with pytest.raises(InvalidTransactionError):
            assert_transfer_different_warehouses("wh1", "wh1")


class TestComputeAvailableQuantity:
    def test_basic(self):
        assert compute_available_quantity(Decimal("100"), Decimal("30")) == Decimal("70")

    def test_clamps_to_zero(self):
        # Reserved > quantity is a data anomaly but should not go negative
        assert compute_available_quantity(Decimal("10"), Decimal("15")) == Decimal("0")
