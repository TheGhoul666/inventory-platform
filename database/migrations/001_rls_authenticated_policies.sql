-- RLS policies for authenticated role (read + write on all operational tables)
-- Applied: 2026-06-25

-- READ
CREATE POLICY "auth_read_inventory_items" ON inventory_items FOR SELECT TO authenticated USING (true);
CREATE POLICY "auth_read_warehouses" ON warehouses FOR SELECT TO authenticated USING (true);
CREATE POLICY "auth_read_buses" ON buses FOR SELECT TO authenticated USING (true);
CREATE POLICY "auth_read_alerts" ON alerts FOR SELECT TO authenticated USING (true);
CREATE POLICY "auth_read_inventory_transactions" ON inventory_transactions FOR SELECT TO authenticated USING (true);
CREATE POLICY "auth_read_inventory_categories" ON inventory_categories FOR SELECT TO authenticated USING (true);
CREATE POLICY "auth_read_maintenance_events" ON maintenance_events FOR SELECT TO authenticated USING (true);
CREATE POLICY "auth_read_warehouse_locations" ON warehouse_locations FOR SELECT TO authenticated USING (true);
CREATE POLICY "auth_read_inventory_snapshots" ON inventory_snapshots FOR SELECT TO authenticated USING (true);

-- WRITE
CREATE POLICY "auth_insert_inventory_items" ON inventory_items FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "auth_update_inventory_items" ON inventory_items FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_delete_inventory_items" ON inventory_items FOR DELETE TO authenticated USING (true);

CREATE POLICY "auth_insert_warehouses" ON warehouses FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "auth_update_warehouses" ON warehouses FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_delete_warehouses" ON warehouses FOR DELETE TO authenticated USING (true);

CREATE POLICY "auth_insert_buses" ON buses FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "auth_update_buses" ON buses FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_delete_buses" ON buses FOR DELETE TO authenticated USING (true);

CREATE POLICY "auth_insert_alerts" ON alerts FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "auth_update_alerts" ON alerts FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_delete_alerts" ON alerts FOR DELETE TO authenticated USING (true);

CREATE POLICY "auth_insert_inventory_transactions" ON inventory_transactions FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "auth_update_inventory_transactions" ON inventory_transactions FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_delete_inventory_transactions" ON inventory_transactions FOR DELETE TO authenticated USING (true);

CREATE POLICY "auth_insert_inventory_categories" ON inventory_categories FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "auth_update_inventory_categories" ON inventory_categories FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_delete_inventory_categories" ON inventory_categories FOR DELETE TO authenticated USING (true);

CREATE POLICY "auth_insert_maintenance_events" ON maintenance_events FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "auth_update_maintenance_events" ON maintenance_events FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_delete_maintenance_events" ON maintenance_events FOR DELETE TO authenticated USING (true);

CREATE POLICY "auth_insert_warehouse_locations" ON warehouse_locations FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "auth_update_warehouse_locations" ON warehouse_locations FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_delete_warehouse_locations" ON warehouse_locations FOR DELETE TO authenticated USING (true);

CREATE POLICY "auth_insert_inventory_snapshots" ON inventory_snapshots FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "auth_update_inventory_snapshots" ON inventory_snapshots FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_delete_inventory_snapshots" ON inventory_snapshots FOR DELETE TO authenticated USING (true);

-- audit_logs: insert only (no update/delete on audit trail)
CREATE POLICY "auth_insert_audit_logs" ON audit_logs FOR INSERT TO authenticated WITH CHECK (true);
