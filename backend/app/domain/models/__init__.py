# Import all models so Alembic autogenerate can discover them.
from app.domain.models.user import User, Role, Permission, RefreshToken
from app.domain.models.warehouse import Warehouse, WarehouseLocation
from app.domain.models.inventory import InventoryItem, InventoryCategory, InventorySnapshot
from app.domain.models.transaction import InventoryTransaction
from app.domain.models.bus import Bus, MaintenanceEvent
from app.domain.models.alert import Alert, WebhookEndpoint, WebhookDelivery
from app.domain.models.audit import AuditLog

__all__ = [
    "User", "Role", "Permission", "RefreshToken",
    "Warehouse", "WarehouseLocation",
    "InventoryItem", "InventoryCategory", "InventorySnapshot",
    "InventoryTransaction",
    "Bus", "MaintenanceEvent",
    "Alert", "WebhookEndpoint", "WebhookDelivery",
    "AuditLog",
]
