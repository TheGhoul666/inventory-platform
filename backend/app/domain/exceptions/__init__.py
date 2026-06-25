"""
Domain exceptions.

Using typed exceptions lets the API layer map them to appropriate
HTTP status codes without business logic leaking into the API layer.
"""


class DomainError(Exception):
    """Base for all domain errors."""


class InsufficientStockError(DomainError):
    """Raised when an issue/transfer would result in negative stock."""
    def __init__(self, item_id: str, requested: float, available: float):
        self.item_id = item_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for item {item_id}: "
            f"requested={requested}, available={available}"
        )


class ItemNotFoundError(DomainError):
    def __init__(self, item_id: str):
        super().__init__(f"Inventory item not found: {item_id}")


class WarehouseNotFoundError(DomainError):
    def __init__(self, warehouse_id: str):
        super().__init__(f"Warehouse not found: {warehouse_id}")


class BusNotFoundError(DomainError):
    def __init__(self, bus_id: str):
        super().__init__(f"Bus not found: {bus_id}")


class UserNotFoundError(DomainError):
    def __init__(self, identifier: str):
        super().__init__(f"User not found: {identifier}")


class InvalidTransactionError(DomainError):
    """Raised when a transaction violates business rules."""


class TransactionRollbackError(DomainError):
    """Raised when a rollback cannot be performed (e.g. already rolled back)."""


class PermissionDeniedError(DomainError):
    def __init__(self, user_id: str, permission: str):
        super().__init__(f"User {user_id} lacks permission: {permission}")


class InvalidCredentialsError(DomainError):
    pass


class TokenExpiredError(DomainError):
    pass


class AccountLockedError(DomainError):
    pass


class DuplicateResourceError(DomainError):
    def __init__(self, resource: str, field: str, value: str):
        super().__init__(f"{resource} with {field}='{value}' already exists.")


class ValidationError(DomainError):
    """Raised when a value object validation fails."""
