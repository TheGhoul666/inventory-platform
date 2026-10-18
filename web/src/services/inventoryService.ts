/**
 * All READ operations go directly to Supabase (bypasses FastAPI ג€” no IPv6 on this host).
 * WRITE operations (issue/restock/transfer) still route through FastAPI for business-rule enforcement.
 */
import api from "./api";
import { supabase } from "@/lib/supabase";
import {
  averageRate,
  consumptionRateByItem,
  sortByUrgency,
  toStockLevel,
  dailyConsumption,
  detectAnomaly,
  emaSeries,
  predictedDaysLeft,
} from "@/utils/analytics";
import type {
  AnomalyResult,
  DepletionForecast,
  UsageAnalytics,
  InventoryItem,
  PaginatedResponse,
  Transaction,
} from "@/types";

export interface ListItemsParams {
  warehouse_id?: string;
  category_id?: string;
  low_stock_only?: boolean;
  search?: string;
  offset?: number;
  limit?: number;
}

export const inventoryService = {
  listItems: async (params: ListItemsParams = {}): Promise<PaginatedResponse<InventoryItem>> => {
    const offset = params.offset ?? 0;
    const limit = params.limit ?? 50;

    let query = supabase
      .from("inventory_items")
      .select("*, category:inventory_categories(*), warehouse:warehouses(*)", { count: "exact" })
      .eq("is_deleted", false);

    if (params.warehouse_id) query = query.eq("warehouse_id", params.warehouse_id) as typeof query;
    if (params.category_id) query = query.eq("category_id", params.category_id) as typeof query;
    if (params.search) {
      query = query.or(`name.ilike.%${params.search}%,sku.ilike.%${params.search}%`) as typeof query;
    }

    const { data, count, error } = await query.order("name").range(offset, offset + limit - 1);
    if (error) throw error;

    let items = (data as any[]) ?? [];
    if (params.low_stock_only) {
      items = items.filter((i: any) => Number(i.quantity) <= Number(i.low_stock_threshold));
    }
    return { items: items as InventoryItem[], total: count ?? items.length, offset, limit };
  },

  getItem: async (id: string): Promise<InventoryItem> => {
    const { data, error } = await supabase.from("inventory_items")
      .select("*, category:inventory_categories(*), warehouse:warehouses(*)")
      .eq("id", id)
      .eq("is_deleted", false)
      .single();
    if (error) throw error;
    return data as InventoryItem;
  },

  createItem: async (payload: Partial<InventoryItem>): Promise<InventoryItem> => {
    const { data } = await api.post("/inventory/items", payload);
    return data;
  },

  issueItem: async (payload: {
    item_id: string; quantity: number; reason_code?: string;
    notes?: string; reference_number?: string; bus_id?: string; maintenance_event_id?: string;
  }): Promise<{ transaction_id: string; status: string }> => {
    const { data } = await api.post("/inventory/transactions/issue", payload);
    return data;
  },

  restockItem: async (payload: {
    item_id: string; quantity: number; reason_code?: string;
    notes?: string; reference_number?: string;
  }): Promise<{ transaction_id: string; status: string }> => {
    const { data } = await api.post("/inventory/transactions/restock", payload);
    return data;
  },

  transferItem: async (payload: {
    source_item_id: string; dest_item_id: string; source_warehouse_id: string;
    dest_warehouse_id: string; quantity: number; reason_code?: string; notes?: string;
  }): Promise<{ transaction_id: string; status: string }> => {
    const { data } = await api.post("/inventory/transactions/transfer", payload);
    return data;
  },

  listTransactions: async (params?: { item_id?: string; offset?: number; limit?: number; }): Promise<{ transactions: Transaction[] }> => {
    let query = supabase.from("inventory_transactions")
      .select("*, item:inventory_items(sku, name), warehouse:warehouses!inventory_transactions_warehouse_id_fkey(name, code)")
      .eq("is_deleted", false);
    if (params?.item_id) query = query.eq("item_id", params.item_id) as typeof query;
    const { data, error } = await query.order("created_at", { ascending: false }).range(params?.offset ?? 0, (params?.offset ?? 0) + (params?.limit ?? 50) - 1);
    if (error) throw error;
    const transactions = ((data as any[]) ?? []).map((t: any) => ({
      ...t,
      type: t.type ?? t.transaction_type,
      item_name: t.item?.name,
      item_sku: t.item?.sku,
      warehouse_name: t.warehouse?.name,
      warehouse_code: t.warehouse?.code,
    }));
    return { transactions: transactions as Transaction[] };
  },

  deleteItem: async (id: string): Promise<void> => { await api.delete(`/inventory/items/${id}`); },

  writeOffItem: async (item_id: string, quantity: number, notes?: string): Promise<{ transaction_id: string; status: string }> => {
    const { data } = await api.post("/inventory/transactions/issue", { item_id, quantity, reason_code: "WRITE_OFF", notes: notes ?? "Write-off" });
    return data;
  },

  rollbackTransaction: async (tx_id: string, reason: string) => {
    const { data } = await api.post(`/inventory/transactions/${tx_id}/rollback`, null, { params: { reason } });
    return data;
  },
};

async function loadConsumption(item_id: string, days: number) {
  const since = new Date(Date.now() - days * 86_400_000).toISOString();
  const { data, error } = await supabase.from("inventory_transactions")
    .select("transaction_type, quantity_delta, created_at")
    .eq("item_id", item_id)
    .eq("is_deleted", false)
    .gte("created_at", since)
    .limit(1000);
  if (error) throw error;
  return dailyConsumption(data ?? [], days);
}

export const analyticsService = {
  getDashboardSummary: async () => {
    const { data: items, error } = await supabase.from("inventory_items")
      .select("id, name, sku, quantity, low_stock_threshold, critical_stock_threshold, unit_cost, unit")
      .eq("is_deleted", false);
    if (error) throw error;

    const allItems = items ?? [];
    const lowStock = allItems.filter(i => Number(i.quantity) <= Number(i.low_stock_threshold));
    const critical = allItems.filter(i => Number(i.quantity) <= Number(i.critical_stock_threshold));

    return {
      total_items_count: allItems.length,
      low_stock_count: lowStock.length,
      critical_stock_count: critical.length,
      critical_items: critical.slice(0, 10),
      generated_at: new Date().toISOString(),
    };
  },

  /** Stock levels with a days-left forecast, plus the latest movements, for the dashboard. */
  getDashboardOverview: async (days = 14) => {
    const since = new Date(Date.now() - days * 86_400_000).toISOString();
    const [itemsRes, txRes, recentRes] = await Promise.all([
      supabase.from("inventory_items")
        .select("id, name, sku, unit, quantity, low_stock_threshold, critical_stock_threshold")
        .eq("is_deleted", false),
      supabase.from("inventory_transactions")
        .select("item_id, transaction_type, quantity_delta, created_at")
        .eq("is_deleted", false)
        .gte("created_at", since)
        .limit(2000),
      supabase.from("inventory_transactions")
        .select("id, transaction_type, quantity_delta, created_at, item:inventory_items(name, unit)")
        .eq("is_deleted", false)
        .order("created_at", { ascending: false })
        .limit(4),
    ]);
    if (itemsRes.error) throw itemsRes.error;
    const rates = consumptionRateByItem(txRes.data ?? [], days);
    const levels = (itemsRes.data ?? []).map((i) => toStockLevel(i, rates));
    return {
      levels: sortByUrgency(levels).slice(0, 5),
      counts: {
        total: levels.length,
        critical: levels.filter((l) => l.status === "critical").length,
        low: levels.filter((l) => l.status === "low").length,
        ok: levels.filter((l) => l.status === "ok").length,
      },
      recent: (recentRes.data ?? []) as unknown as Array<{
        id: string; transaction_type: string; quantity_delta: number; created_at: string; item: { name: string; unit?: string } | null;
      }>,
    };
  },

  getItemUsage: async (item_id: string, days = 30): Promise<UsageAnalytics> => {
    const series = await loadConsumption(item_id, days);
    return { item_id, period_days: days, daily_consumption_rate: averageRate(series) };
  },

  getPredictedDepletion: async (item_id: string, quantity: number, days = 30): Promise<DepletionForecast> => {
    const series = await loadConsumption(item_id, days);
    return {
      item_id,
      predicted_days_left: predictedDaysLeft(quantity, averageRate(series)),
      ema_trend: emaSeries(series),
    };
  },

  getAnomalies: async (item_id: string, days = 30): Promise<AnomalyResult> =>
    detectAnomaly(await loadConsumption(item_id, days), item_id),
};

export const alertService = {
  listAlerts: async (params?: { status?: string; severity?: string; offset?: number; limit?: number }) => {
    let query = supabase.from("alerts")
      .select("*, item:inventory_items(sku, name), warehouse:warehouses(name, code)")
      .eq("is_deleted", false);
    if (params?.status) query = query.eq("status", params.status) as typeof query;
    if (params?.severity) query = query.eq("severity", params.severity) as typeof query;
    const { data, error } = await query.order("created_at", { ascending: false }).range(params?.offset ?? 0, (params?.offset ?? 0) + (params?.limit ?? 50) - 1);
    if (error) throw error;
    return { alerts: data ?? [] };
  },

  acknowledgeAlert: async (alert_id: string) => { const { data } = await api.post(`/alerts/${alert_id}/acknowledge`); return data; },
  resolveAlert: async (alert_id: string) => { const { data } = await api.post(`/alerts/${alert_id}/resolve`); return data; },
};

export const authService = {
  login: async (email: string, password: string) => { const { data } = await api.post("/auth/login", { email, password }); return data; },
  register: async (payload: { email: string; username: string; password: string; full_name: string; }) => { const { data } = await api.post("/auth/register", payload); return data; },
};

export const warehouseService = {
  listWarehouses: async (_activeOnly = false) => {
    const { data, error } = await supabase.from("warehouses")
      .select("*")
      .eq("is_deleted", false)
      .order("name");
    if (error) throw error;
    return (data ?? []) as Array<{ id: string; name: string; code: string; city?: string; country: string; address?: string; phone?: string; capacity_sqm?: number; is_active: boolean; }>;
  },

  createWarehouse: async (payload: { name: string; code: string; city?: string; country?: string; address?: string; phone?: string; capacity_sqm?: number; }) => {
    const { data } = await api.post("/warehouses", payload); return data;
  },

  getWarehouse: async (id: string) => {
    const { data, error } = await supabase.from("warehouses").select("*").eq("id", id).single();
    if (error) throw error;
    return data as { id: string; name: string; code: string; city?: string; country: string; address?: string; phone?: string; capacity_sqm?: number; is_active: boolean; };
  },

  updateWarehouse: async (id: string, patch: Partial<{ name: string; address: string; city: string; country: string; phone: string; capacity_sqm: number; is_active: boolean; }>) => {
    const { data } = await api.patch(`/warehouses/${id}`, patch); return data;
  },
};

export const busService = {
  listBuses: async (statusFilter?: string) => {
    let query = supabase.from("buses").select("*, depot:warehouses(name, code)").or("is_deleted.eq.false,is_deleted.is.null");
    if (statusFilter) query = query.eq("status", statusFilter) as typeof query;
    const { data, error } = await query.order("fleet_number");
    if (error) throw error;
    return (data ?? []) as Array<{ id: string; fleet_number: string; license_plate: string; make: string; model: string; year: number; status: string; depot_id?: string; mileage_km: number; }>;
  },

  createBus: async (payload: { fleet_number: string; license_plate: string; make: string; model: string; year: number; vin?: string; depot_id?: string; mileage_km?: number; status?: string; }) => {
    const { data } = await api.post("/buses", payload); return data;
  },

  updateBus: async (id: string, patch: Partial<{ status: string; mileage_km: number; notes: string; depot_id: string }>) => {
    const { data } = await api.patch(`/buses/${id}`, patch); return data;
  },
};

export const auditService = {
  listAuditLogs: async (params?: { resource_type?: string; action?: string; offset?: number; limit?: number; }) => {
    let query = supabase.from("audit_logs").select("*");
    if (params?.resource_type) query = query.eq("resource_type", params.resource_type) as typeof query;
    if (params?.action) query = query.eq("action", params.action) as typeof query;
    const { data, error } = await query.order("created_at", { ascending: false }).range(params?.offset ?? 0, (params?.offset ?? 0) + (params?.limit ?? 50) - 1);
    if (error) throw error;
    return { logs: data ?? [] };
  },
};

export const usersService = {
  listUsers: async (_page = 1, _perPage = 50): Promise<{ users: any[] }> => {
    const { data } = await api.get("/auth/users", { params: { page: _page, per_page: _perPage } });
    return data;
  },
  createUser: async (payload: any) => { const { data } = await api.post("/auth/users", payload); return data; },
  assignRole: async (userId: string, role: string) => { const { data } = await api.put(`/auth/users/${userId}/role`, { role }); return data; },
  updateUserProfile: async (userId: string, patch: any) => { const { data } = await api.patch(`/auth/users/${userId}/profile`, patch); return data; },
  updateMyProfile: async (patch: any) => { const { data } = await api.patch("/auth/me/profile", patch); return data; },
  updateUserPermissions: async (userId: string, add: string[], remove: string[]) => { const { data } = await api.patch(`/auth/users/${userId}/permissions`, { add, remove }); return data; },
  deleteUser: async (userId: string) => { await api.delete(`/auth/users/${userId}`); },
};

export const rolesService = {
  listRoles: async (): Promise<{ roles: any[]; all_permissions: string[] }> => { const { data } = await api.get("/auth/roles"); return data; },
  createRole: async (payload: { name: string; description?: string; permissions: string[]; }) => { const { data } = await api.post("/auth/roles", payload); return data; },
  deleteRole: async (name: string) => { await api.delete(`/auth/roles/${name}`); },
};
