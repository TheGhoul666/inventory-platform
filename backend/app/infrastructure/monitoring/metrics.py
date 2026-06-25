"""
Prometheus metrics definitions.

All business-level metrics are defined here.
FastAPI instrumentation metrics (request count, latency histograms)
are added automatically by prometheus_fastapi_instrumentator.
"""
from prometheus_client import Counter, Gauge, Histogram

# --- Inventory metrics ---

inventory_transactions_total = Counter(
    "inventory_transactions_total",
    "Total number of inventory transactions",
    ["transaction_type", "status", "warehouse_id"],
)

inventory_quantity_gauge = Gauge(
    "inventory_item_quantity",
    "Current quantity of an inventory item",
    ["item_id", "sku", "warehouse_id"],
)

low_stock_items_gauge = Gauge(
    "inventory_low_stock_items_count",
    "Number of items below low stock threshold",
)

critical_stock_items_gauge = Gauge(
    "inventory_critical_stock_items_count",
    "Number of items below critical stock threshold",
)

# --- Alert metrics ---

alerts_created_total = Counter(
    "alerts_created_total",
    "Total alerts created",
    ["alert_type", "severity"],
)

alerts_open_gauge = Gauge(
    "alerts_open_count",
    "Currently open alerts by severity",
    ["severity"],
)

# --- Webhook metrics ---

webhook_deliveries_total = Counter(
    "webhook_deliveries_total",
    "Total webhook delivery attempts",
    ["status", "event_type"],
)

webhook_delivery_duration = Histogram(
    "webhook_delivery_duration_seconds",
    "Webhook delivery latency",
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# --- Queue metrics ---

queue_messages_published_total = Counter(
    "queue_messages_published_total",
    "Total messages published to RabbitMQ",
    ["routing_key"],
)

queue_messages_consumed_total = Counter(
    "queue_messages_consumed_total",
    "Total messages consumed from RabbitMQ",
    ["queue", "status"],
)

# --- Auth metrics ---

auth_login_total = Counter(
    "auth_login_total",
    "Total login attempts",
    ["status"],  # success | failure | locked
)
