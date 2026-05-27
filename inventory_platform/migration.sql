BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 001_initial_schema

CREATE TABLE warehouses (
    id UUID NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    code VARCHAR(20) NOT NULL, 
    address TEXT, 
    city VARCHAR(100), 
    country VARCHAR(100) DEFAULT 'IL' NOT NULL, 
    phone VARCHAR(30), 
    manager_id UUID, 
    is_active BOOLEAN, 
    capacity_sqm INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    is_deleted BOOLEAN, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    UNIQUE (name), 
    UNIQUE (code)
);

CREATE INDEX ix_warehouses_code ON warehouses (code);

CREATE TABLE warehouse_locations (
    id UUID NOT NULL, 
    warehouse_id UUID NOT NULL, 
    aisle VARCHAR(10) NOT NULL, 
    rack VARCHAR(10) NOT NULL, 
    shelf VARCHAR(10) NOT NULL, 
    bin VARCHAR(10) NOT NULL, 
    label VARCHAR(50) NOT NULL, 
    is_active BOOLEAN, 
    max_weight_kg INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    is_deleted BOOLEAN, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_wh_location_coords UNIQUE (warehouse_id, aisle, rack, shelf, bin), 
    FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE CASCADE
);

CREATE TABLE inventory_categories (
    id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    description TEXT, 
    parent_id UUID, 
    color_hex VARCHAR(7), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    is_deleted BOOLEAN, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    UNIQUE (name), 
    FOREIGN KEY(parent_id) REFERENCES inventory_categories (id)
);

CREATE TABLE buses (
    id UUID NOT NULL, 
    fleet_number VARCHAR(20) NOT NULL, 
    license_plate VARCHAR(20) NOT NULL, 
    make VARCHAR(50) NOT NULL, 
    model VARCHAR(100) NOT NULL, 
    year INTEGER NOT NULL, 
    vin VARCHAR(50), 
    status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
    depot_id UUID, 
    mileage_km INTEGER DEFAULT '0' NOT NULL, 
    last_service_date TIMESTAMP WITH TIME ZONE, 
    notes TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    is_deleted BOOLEAN, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    UNIQUE (fleet_number), 
    UNIQUE (license_plate), 
    UNIQUE (vin), 
    FOREIGN KEY(depot_id) REFERENCES warehouses (id)
);

CREATE INDEX ix_buses_fleet_number ON buses (fleet_number);

CREATE TABLE inventory_items (
    id UUID NOT NULL, 
    sku VARCHAR(100) NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    description TEXT, 
    unit VARCHAR(30) DEFAULT 'piece' NOT NULL, 
    quantity NUMERIC(12, 3) DEFAULT '0' NOT NULL, 
    reserved_quantity NUMERIC(12, 3) DEFAULT '0' NOT NULL, 
    low_stock_threshold NUMERIC(12, 3) DEFAULT '10' NOT NULL, 
    critical_stock_threshold NUMERIC(12, 3) DEFAULT '3' NOT NULL, 
    reorder_quantity NUMERIC(12, 3) DEFAULT '50' NOT NULL, 
    unit_cost NUMERIC(12, 2), 
    category_id UUID, 
    warehouse_id UUID NOT NULL, 
    location_id UUID, 
    supplier_name VARCHAR(200), 
    supplier_part_number VARCHAR(100), 
    lead_time_days INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    is_deleted BOOLEAN, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_inventory_items_quantity_non_negative CHECK (quantity >= 0), 
    CONSTRAINT ck_threshold_non_negative CHECK (low_stock_threshold >= 0), 
    CONSTRAINT ck_reorder_positive CHECK (reorder_quantity > 0), 
    UNIQUE (sku), 
    FOREIGN KEY(category_id) REFERENCES inventory_categories (id), 
    FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
    FOREIGN KEY(location_id) REFERENCES warehouse_locations (id)
);

CREATE INDEX ix_inventory_items_sku ON inventory_items (sku);

CREATE INDEX ix_inventory_items_warehouse_id ON inventory_items (warehouse_id);

CREATE INDEX ix_inventory_items_category_id ON inventory_items (category_id);

CREATE INDEX ix_inventory_items_low_stock
        ON inventory_items (quantity, low_stock_threshold)
        WHERE is_deleted = false;

CREATE TABLE maintenance_events (
    id UUID NOT NULL, 
    bus_id UUID NOT NULL, 
    technician_id UUID NOT NULL, 
    event_type VARCHAR(30) NOT NULL, 
    status VARCHAR(30) DEFAULT 'OPEN' NOT NULL, 
    title VARCHAR(200) NOT NULL, 
    description TEXT, 
    scheduled_date TIMESTAMP WITH TIME ZONE, 
    started_at TIMESTAMP WITH TIME ZONE, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    odometer_km INTEGER, 
    labor_hours FLOAT, 
    is_warranty BOOLEAN, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    is_deleted BOOLEAN, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(bus_id) REFERENCES buses (id)
);

CREATE INDEX ix_maintenance_events_bus_id ON maintenance_events (bus_id);

CREATE TABLE inventory_transactions (
    id UUID NOT NULL, 
    item_id UUID NOT NULL, 
    warehouse_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    transaction_type VARCHAR(30) NOT NULL, 
    status VARCHAR(30) DEFAULT 'COMPLETED' NOT NULL, 
    quantity_delta NUMERIC(12, 3) NOT NULL, 
    quantity_before NUMERIC(12, 3) NOT NULL, 
    quantity_after NUMERIC(12, 3) NOT NULL, 
    bus_id UUID, 
    maintenance_event_id UUID, 
    destination_warehouse_id UUID, 
    rollback_of_id UUID, 
    reason_code VARCHAR(50), 
    notes TEXT, 
    reference_number VARCHAR(100), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    is_deleted BOOLEAN, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_transaction_delta_positive CHECK (quantity_delta > 0), 
    CONSTRAINT ck_transaction_before_non_negative CHECK (quantity_before >= 0), 
    CONSTRAINT ck_transaction_after_non_negative CHECK (quantity_after >= 0), 
    FOREIGN KEY(item_id) REFERENCES inventory_items (id), 
    FOREIGN KEY(warehouse_id) REFERENCES warehouses (id), 
    FOREIGN KEY(bus_id) REFERENCES buses (id), 
    FOREIGN KEY(maintenance_event_id) REFERENCES maintenance_events (id), 
    FOREIGN KEY(destination_warehouse_id) REFERENCES warehouses (id), 
    FOREIGN KEY(rollback_of_id) REFERENCES inventory_transactions (id)
);

CREATE INDEX ix_transactions_item_id ON inventory_transactions (item_id);

CREATE INDEX ix_transactions_warehouse_id ON inventory_transactions (warehouse_id);

CREATE INDEX ix_transactions_user_id ON inventory_transactions (user_id);

CREATE INDEX ix_transactions_created_at ON inventory_transactions (created_at);

CREATE INDEX ix_transactions_transaction_type ON inventory_transactions (transaction_type);

CREATE INDEX ix_transactions_bus_id ON inventory_transactions (bus_id);

CREATE TABLE inventory_snapshots (
    id UUID NOT NULL, 
    item_id UUID NOT NULL, 
    snapshot_date VARCHAR(10) NOT NULL, 
    quantity NUMERIC(12, 3) NOT NULL, 
    reserved_quantity NUMERIC(12, 3) NOT NULL, 
    created_at VARCHAR(30) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(item_id) REFERENCES inventory_items (id)
);

CREATE INDEX ix_inventory_snapshots_item_date ON inventory_snapshots (item_id, snapshot_date);

CREATE TABLE alerts (
    id UUID NOT NULL, 
    alert_type VARCHAR(50) NOT NULL, 
    severity VARCHAR(20) NOT NULL, 
    status VARCHAR(20) DEFAULT 'OPEN' NOT NULL, 
    title VARCHAR(300) NOT NULL, 
    message TEXT NOT NULL, 
    metadata JSONB, 
    item_id UUID, 
    warehouse_id UUID, 
    acknowledged_by UUID, 
    acknowledged_at TIMESTAMP WITH TIME ZONE, 
    resolved_at TIMESTAMP WITH TIME ZONE, 
    escalation_count INTEGER, 
    webhook_dispatched BOOLEAN, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    is_deleted BOOLEAN, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(item_id) REFERENCES inventory_items (id), 
    FOREIGN KEY(warehouse_id) REFERENCES warehouses (id)
);

CREATE INDEX ix_alerts_status ON alerts (status);

CREATE INDEX ix_alerts_severity ON alerts (severity);

CREATE INDEX ix_alerts_open ON alerts (created_at DESC) WHERE status = 'OPEN' AND is_deleted = false;

CREATE TABLE webhook_endpoints (
    id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    url VARCHAR(500) NOT NULL, 
    secret VARCHAR(255) NOT NULL, 
    is_active BOOLEAN, 
    event_types JSONB NOT NULL, 
    timeout_seconds INTEGER, 
    max_retries INTEGER, 
    headers JSONB, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    is_deleted BOOLEAN, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE TABLE webhook_deliveries (
    id UUID NOT NULL, 
    endpoint_id UUID NOT NULL, 
    event_type VARCHAR(100) NOT NULL, 
    idempotency_key VARCHAR(100) NOT NULL, 
    payload JSONB NOT NULL, 
    attempt_number INTEGER, 
    max_attempts INTEGER, 
    status_code INTEGER, 
    response_body TEXT, 
    success BOOLEAN, 
    error_message TEXT, 
    next_retry_at TIMESTAMP WITH TIME ZONE, 
    is_dead_letter BOOLEAN, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    delivered_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(endpoint_id) REFERENCES webhook_endpoints (id) ON DELETE CASCADE, 
    UNIQUE (idempotency_key)
);

CREATE TABLE audit_logs (
    id UUID NOT NULL, 
    user_id UUID, 
    action VARCHAR(100) NOT NULL, 
    resource_type VARCHAR(100) NOT NULL, 
    resource_id VARCHAR(100), 
    old_values JSONB, 
    new_values JSONB, 
    diff JSONB, 
    ip_address VARCHAR(45), 
    user_agent TEXT, 
    request_id VARCHAR(64), 
    created_at VARCHAR(30) NOT NULL, 
    username VARCHAR(100), 
    notes TEXT, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);

CREATE INDEX ix_audit_logs_resource ON audit_logs (resource_type, resource_id);

CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);

ALTER TABLE warehouses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "warehouses_service_role_all"
            ON warehouses
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

ALTER TABLE warehouse_locations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "warehouse_locations_service_role_all"
            ON warehouse_locations
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

ALTER TABLE inventory_categories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "inventory_categories_service_role_all"
            ON inventory_categories
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

ALTER TABLE inventory_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "inventory_items_service_role_all"
            ON inventory_items
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

ALTER TABLE inventory_transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "inventory_transactions_service_role_all"
            ON inventory_transactions
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

ALTER TABLE inventory_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "inventory_snapshots_service_role_all"
            ON inventory_snapshots
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

ALTER TABLE buses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "buses_service_role_all"
            ON buses
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

ALTER TABLE maintenance_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "maintenance_events_service_role_all"
            ON maintenance_events
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "alerts_service_role_all"
            ON alerts
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

ALTER TABLE webhook_endpoints ENABLE ROW LEVEL SECURITY;

CREATE POLICY "webhook_endpoints_service_role_all"
            ON webhook_endpoints
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

ALTER TABLE webhook_deliveries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "webhook_deliveries_service_role_all"
            ON webhook_deliveries
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "audit_logs_service_role_all"
            ON audit_logs
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);

INSERT INTO alembic_version (version_num) VALUES ('001_initial_schema') RETURNING alembic_version.version_num;

COMMIT;

