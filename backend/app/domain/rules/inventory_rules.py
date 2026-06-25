"""
Inventory business rules.

Pure functions — no DB I/O, no side effects.
Repositories call these before committing mutations.
"""
from decimal import Decimal

from app.domain.exceptions import (
    InsufficientStockError,
    InvalidTransactionError,
)


def assert_sufficient_stock(
    item_id: str,
    current_quantity: Decimal,
    reserved_quantity: Decimal,
    requested: Decimal,
    check_reservations: bool = True,
) -> None:
    """
    Verify the issue will not produce negative available stock.

    If check_reservations=True (default), the available quantity
    excludes reserved stock. For reservation operations themselves
    we check against total quantity.
    """
    available = (
        current_quantity - reserved_quantity if check_reservations else current_quantity
    )
    if requested > available:
        raise InsufficientStockError(
            item_id=item_id,
            requested=float(requested),
            available=float(available),
        )


def assert_positive_quantity(quantity: Decimal, field: str = "quantity") -> None:
    if quantity <= Decimal("0"):
        raise InvalidTransactionError(f"{field} must be positive, got {quantity}")


def assert_non_negative_quantity(quantity: Decimal, field: str = "quantity") -> None:
    if quantity < Decimal("0"):
        raise InvalidTransactionError(f"{field} must be >= 0, got {quantity}")


def assert_transfer_same_item(source_item_id: str, dest_item_id: str) -> None:
    if source_item_id != dest_item_id:
        raise InvalidTransactionError(
            "Transfer source and destination must be the same SKU"
        )


def assert_transfer_different_warehouses(
    source_warehouse_id: str, dest_warehouse_id: str
) -> None:
    if source_warehouse_id == dest_warehouse_id:
        raise InvalidTransactionError(
            "Transfer source and destination warehouses must differ"
        )


def compute_available_quantity(
    quantity: Decimal, reserved_quantity: Decimal
) -> Decimal:
    return max(quantity - reserved_quantity, Decimal("0"))
