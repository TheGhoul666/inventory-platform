-- Revoke the blanket "authenticated" write policies added in 001.
--
-- WHY: every write in this app goes through FastAPI, whose Supabase client
-- (get_supabase_db -> get_async_admin) uses the SERVICE ROLE key, which
-- bypasses RLS entirely. No legitimate client ever writes to PostgREST with
-- its own user JWT — web writes via axios -> FastAPI, iOS/Android write via
-- their APIClient -> FastAPI. The 001 policies below therefore granted every
-- authenticated user (not just permitted ones) direct INSERT/UPDATE/DELETE
-- on every table via PostgREST + their own session token, fully bypassing
-- require_permission() checks, business-rule validation, and audit logging.
--
-- Read policies from 001 are untouched — reads are intentionally direct
-- per the documented architecture (all 3 clients query PostgREST for reads).
--
-- Applied: 2026-09-14

DROP POLICY IF EXISTS "auth_insert_inventory_items" ON inventory_items;
DROP POLICY IF EXISTS "auth_update_inventory_items" ON inventory_items;
DROP POLICY IF EXISTS "auth_delete_inventory_items" ON inventory_items;

DROP POLICY IF EXISTS "auth_insert_warehouses" ON warehouses;
DROP POLICY IF EXISTS "auth_update_warehouses" ON warehouses;
DROP POLICY IF EXISTS "auth_delete_warehouses" ON warehouses;

DROP POLICY IF EXISTS "auth_insert_buses" ON buses;
DROP POLICY IF EXISTS "auth_update_buses" ON buses;
DROP POLICY IF EXISTS "auth_delete_buses" ON buses;

DROP POLICY IF EXISTS "auth_insert_alerts" ON alerts;
DROP POLICY IF EXISTS "auth_update_alerts" ON alerts;
DROP POLICY IF EXISTS "auth_delete_alerts" ON alerts;

DROP POLICY IF EXISTS "auth_insert_inventory_transactions" ON inventory_transactions;
DROP POLICY IF EXISTS "auth_update_inventory_transactions" ON inventory_transactions;
DROP POLICY IF EXISTS "auth_delete_inventory_transactions" ON inventory_transactions;

DROP POLICY IF EXISTS "auth_insert_inventory_categories" ON inventory_categories;
DROP POLICY IF EXISTS "auth_update_inventory_categories" ON inventory_categories;
DROP POLICY IF EXISTS "auth_delete_inventory_categories" ON inventory_categories;

DROP POLICY IF EXISTS "auth_insert_maintenance_events" ON maintenance_events;
DROP POLICY IF EXISTS "auth_update_maintenance_events" ON maintenance_events;
DROP POLICY IF EXISTS "auth_delete_maintenance_events" ON maintenance_events;

DROP POLICY IF EXISTS "auth_insert_warehouse_locations" ON warehouse_locations;
DROP POLICY IF EXISTS "auth_update_warehouse_locations" ON warehouse_locations;
DROP POLICY IF EXISTS "auth_delete_warehouse_locations" ON warehouse_locations;

DROP POLICY IF EXISTS "auth_insert_inventory_snapshots" ON inventory_snapshots;
DROP POLICY IF EXISTS "auth_update_inventory_snapshots" ON inventory_snapshots;
DROP POLICY IF EXISTS "auth_delete_inventory_snapshots" ON inventory_snapshots;

-- audit_logs: also revoked. FastAPI's write_audit_log() uses the service-role
-- client too, so this policy only let any authenticated user insert forged
-- audit rows (e.g. attributing actions to another user_id) directly.
DROP POLICY IF EXISTS "auth_insert_audit_logs" ON audit_logs;

-- After this migration, writes to these tables are possible only via the
-- service_role policies already defined in schema.sql (i.e. the backend).
-- If a future feature genuinely needs a client to write directly via
-- PostgREST, add a scoped policy for it then — don't restore the blanket one.
