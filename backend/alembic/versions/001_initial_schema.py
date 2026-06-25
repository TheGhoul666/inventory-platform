"""Initial schema — Supabase edition.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-05-17

Changes vs. self-hosted edition:
  - users table removed (auth is managed by Supabase auth.users)
  - roles/permissions/refresh_tokens tables removed (stored in app_metadata)
  - All FK references to users now reference auth.users(id) via UUID
  - Row Level Security (RLS) policies added where appropriate
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- warehouses ----
    op.create_table(
        "warehouses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), unique=True, nullable=False),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="IL"),
        sa.Column("phone", sa.String(30), nullable=True),
        # References Supabase auth.users — no FK constraint (auth schema is separate)
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("capacity_sqm", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_warehouses_code", "warehouses", ["code"])

    # ---- warehouse_locations ----
    op.create_table(
        "warehouse_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("aisle", sa.String(10), nullable=False),
        sa.Column("rack", sa.String(10), nullable=False),
        sa.Column("shelf", sa.String(10), nullable=False),
        sa.Column("bin", sa.String(10), nullable=False),
        sa.Column("label", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("max_weight_kg", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("warehouse_id", "aisle", "rack", "shelf", "bin", name="uq_wh_location_coords"),
    )

    # ---- inventory_categories ----
    op.create_table(
        "inventory_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_categories.id"), nullable=True),
        sa.Column("color_hex", sa.String(7), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ---- buses ----
    op.create_table(
        "buses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("fleet_number", sa.String(20), unique=True, nullable=False),
        sa.Column("license_plate", sa.String(20), unique=True, nullable=False),
        sa.Column("make", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("vin", sa.String(50), unique=True, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("depot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id"), nullable=True),
        sa.Column("mileage_km", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_service_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_buses_fleet_number", "buses", ["fleet_number"])

    # ---- inventory_items ----
    op.create_table(
        "inventory_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sku", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("unit", sa.String(30), nullable=False, server_default="piece"),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("reserved_quantity", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("low_stock_threshold", sa.Numeric(12, 3), nullable=False, server_default="10"),
        sa.Column("critical_stock_threshold", sa.Numeric(12, 3), nullable=False, server_default="3"),
        sa.Column("reorder_quantity", sa.Numeric(12, 3), nullable=False, server_default="50"),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_categories.id"), nullable=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouse_locations.id"), nullable=True),
        sa.Column("supplier_name", sa.String(200), nullable=True),
        sa.Column("supplier_part_number", sa.String(100), nullable=True),
        sa.Column("lead_time_days", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("quantity >= 0", name="ck_inventory_items_quantity_non_negative"),
        sa.CheckConstraint("low_stock_threshold >= 0", name="ck_threshold_non_negative"),
        sa.CheckConstraint("reorder_quantity > 0", name="ck_reorder_positive"),
    )
    op.create_index("ix_inventory_items_sku", "inventory_items", ["sku"])
    op.create_index("ix_inventory_items_warehouse_id", "inventory_items", ["warehouse_id"])
    op.create_index("ix_inventory_items_category_id", "inventory_items", ["category_id"])
    # Partial index for low-stock dashboard queries
    op.execute("""
        CREATE INDEX ix_inventory_items_low_stock
        ON inventory_items (quantity, low_stock_threshold)
        WHERE is_deleted = false
    """)

    # ---- maintenance_events ----
    op.create_table(
        "maintenance_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("buses.id"), nullable=False),
        # technician_id references Supabase auth.users — no FK constraint
        sa.Column("technician_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("odometer_km", sa.Integer, nullable=True),
        sa.Column("labor_hours", sa.Float, nullable=True),
        sa.Column("is_warranty", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_maintenance_events_bus_id", "maintenance_events", ["bus_id"])

    # ---- inventory_transactions ----
    op.create_table(
        "inventory_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id"), nullable=False),
        # user_id references Supabase auth.users — no FK constraint
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="COMPLETED"),
        sa.Column("quantity_delta", sa.Numeric(12, 3), nullable=False),
        sa.Column("quantity_before", sa.Numeric(12, 3), nullable=False),
        sa.Column("quantity_after", sa.Numeric(12, 3), nullable=False),
        sa.Column("bus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("buses.id"), nullable=True),
        sa.Column("maintenance_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("maintenance_events.id"), nullable=True),
        sa.Column("destination_warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id"), nullable=True),
        sa.Column("rollback_of_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_transactions.id"), nullable=True),
        sa.Column("reason_code", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("reference_number", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("quantity_delta > 0", name="ck_transaction_delta_positive"),
        sa.CheckConstraint("quantity_before >= 0", name="ck_transaction_before_non_negative"),
        sa.CheckConstraint("quantity_after >= 0", name="ck_transaction_after_non_negative"),
    )
    for col in ["item_id", "warehouse_id", "user_id", "created_at", "transaction_type", "bus_id"]:
        op.create_index(f"ix_transactions_{col}", "inventory_transactions", [col])

    # ---- inventory_snapshots ----
    op.create_table(
        "inventory_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("snapshot_date", sa.String(10), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("reserved_quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("created_at", sa.String(30), nullable=False),
    )
    op.create_index("ix_inventory_snapshots_item_date", "inventory_snapshots", ["item_id", "snapshot_date"])

    # ---- alerts ----
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_items.id"), nullable=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id"), nullable=True),
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalation_count", sa.Integer, default=0),
        sa.Column("webhook_dispatched", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    # Partial index for open alerts (most common query)
    op.execute("CREATE INDEX ix_alerts_open ON alerts (created_at DESC) WHERE status = 'OPEN' AND is_deleted = false")

    # ---- webhook_endpoints ----
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("secret", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("event_types", postgresql.JSONB, nullable=False),
        sa.Column("timeout_seconds", sa.Integer, default=10),
        sa.Column("max_retries", sa.Integer, default=5),
        sa.Column("headers", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ---- webhook_deliveries ----
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("idempotency_key", sa.String(100), unique=True, nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("attempt_number", sa.Integer, default=1),
        sa.Column("max_attempts", sa.Integer, default=5),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("response_body", sa.Text, nullable=True),
        sa.Column("success", sa.Boolean, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_dead_letter", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ---- audit_logs (INSERT-only) ----
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("old_values", postgresql.JSONB, nullable=True),
        sa.Column("new_values", postgresql.JSONB, nullable=True),
        sa.Column("diff", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.String(30), nullable=False),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # ---- Enable Row Level Security ----
    # Supabase uses RLS to enforce data access per authenticated user.
    # These policies allow the service_role (backend) full access
    # while restricting anon/authenticated direct access.
    for table in [
        "warehouses", "warehouse_locations", "inventory_categories",
        "inventory_items", "inventory_transactions", "inventory_snapshots",
        "buses", "maintenance_events", "alerts",
        "webhook_endpoints", "webhook_deliveries", "audit_logs",
    ]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        # service_role bypasses RLS by default in Supabase
        # This policy allows authenticated users read access (restrict further per-table as needed)
        op.execute(f"""
            CREATE POLICY "{table}_service_role_all"
            ON {table}
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true)
        """)


def downgrade() -> None:
    tables = [
        "audit_logs", "webhook_deliveries", "webhook_endpoints", "alerts",
        "inventory_snapshots", "inventory_transactions", "maintenance_events",
        "inventory_items", "inventory_categories", "warehouse_locations",
        "buses", "warehouses",
    ]
    for t in tables:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
