import api from "./api";
import type {
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
    const { data } = await api.get("/inventory/items", { params });
    return data;
  },

  getItem: async (id: string): Promise<InventoryItem> => {
    const { data } = await api.get(`/inventory/items/${id}`);
    return data;
  },

  createItem: async (payload: Partial<InventoryItem>): Promise<InventoryItem> => {
    const { data } = await api.post("/inventory/items", payload);
    return data;
  },

  issueItem: async (payload: {
    item_id: string;
    quantity: number;
    reason_code?: string;
    notes?: string;
    reference_number?: string;
    bus_id?: string;
    maintenance_event_id?: string;
  }): Promise<{ transaction_id: string; status: string }> => {
    const { data } = await api.post("/inventory/transactions/issue", payload);
    return data;
  },

  restockItem: async (payload: {
    item_id: string;
    quantity: number;
    reason_code?: string;
    notes?: string;
    reference_number?: string;
  }): Promise<{ transaction_id: string; status: string }> => {
    const { data } = await api.post("/inventory/transactions/restock", payload);
    return data;
  },

  transferItem: async (payload: {
    source_item_id: string;
    dest_item_id: string;
    source_warehouse_id: string;
    dest_warehouse_id: string;
    quantity: number;
    reason_code?: string;
    notes?: string;
  }): Promise<{ transaction_id: string; status: string }> => {
    const { data } = await api.post("/inventory/transactions/transfer", payload);
    return data;
  },

  listTransactions: async (params?: {
    item_id?: string;
    offset?: number;
    limit?: number;
  }): Promise<{ transactions: Transaction[] }> => {
    const { data } = await api.get("/inventory/transactions", { params });
    return data;
  },

  deleteItem: async (id: string): Promise<void> => {
    await api.delete(`/inventory/items/${id}`);
  },

  writeOffItem: async (item_id: string, quantity: number, notes?: string): Promise<{ transaction_id: string; status: string }> => {
    const { data } = await api.post("/inventory/transactions/issue", {
      item_id,
      quantity,
      reason_code: "WRITE_OFF",
      notes: notes ?? "Write-off: removed from warehouse",
    });
    return data;
  },

  rollbackTransaction: async (tx_id: string, reason: string) => {
    const { data } = await api.post(
      `/inventory/transactions/${tx_id}/rollback`,
      null,
      { params: { reason } }
    );
    return data;
  },
};

export const analyticsService = {
  getDashboardSummary: async () => {
    const { data } = await api.get("/analytics/dashboard");
    return data;
  },

  getItemUsage: async (item_id: string, days = 30) => {
    const { data } = await api.get(`/analytics/usage/${item_id}`, { params: { days } });
    return data;
  },

  getPredictedDepletion: async (item_id: string) => {
    const { data } = await api.get(`/analytics/depletion/${item_id}`);
    return data;
  },

  getAnomalies: async (item_id: string) => {
    const { data } = await api.get(`/analytics/anomalies/${item_id}`);
    return data;
  },
};

export const alertService = {
  listAlerts: async (params?: { status?: string; severity?: string; offset?: number; limit?: number }) => {
    const { data } = await api.get("/alerts", { params });
    return data;
  },

  acknowledgeAlert: async (alert_id: string) => {
    const { data } = await api.post(`/alerts/${alert_id}/acknowledge`);
    return data;
  },

  resolveAlert: async (alert_id: string) => {
    const { data } = await api.post(`/alerts/${alert_id}/resolve`);
    return data;
  },
};

export const authService = {
  login: async (email: string, password: string) => {
    const { data } = await api.post("/auth/login", { email, password });
    return data;
  },

  register: async (payload: {
    email: string;
    username: string;
    password: string;
    full_name: string;
  }) => {
    const { data } = await api.post("/auth/register", payload);
    return data;
  },
};

export const warehouseService = {
  listWarehouses: async (activeOnly = false) => {
    const { data } = await api.get("/warehouses", {
      params: activeOnly ? { active_only: true } : {},
    });
    return data as Array<{
      id: string;
      name: string;
      code: string;
      city?: string;
      country: string;
      address?: string;
      phone?: string;
      capacity_sqm?: number;
      is_active: boolean;
    }>;
  },

  createWarehouse: async (payload: {
    name: string;
    code: string;
    city?: string;
    country?: string;
    address?: string;
    phone?: string;
    capacity_sqm?: number;
  }) => {
    const { data } = await api.post("/warehouses", payload);
    return data;
  },

  getWarehouse: async (id: string) => {
    const { data } = await api.get(`/warehouses/${id}`);
    return data as {
      id: string; name: string; code: string; city?: string;
      country: string; address?: string; phone?: string;
      capacity_sqm?: number; is_active: boolean;
    };
  },

  updateWarehouse: async (
    id: string,
    patch: Partial<{
      name: string;
      address: string;
      city: string;
      country: string;
      phone: string;
      capacity_sqm: number;
      is_active: boolean;
    }>
  ) => {
    const { data } = await api.patch(`/warehouses/${id}`, patch);
    return data;
  },
};

export const busService = {
  listBuses: async (statusFilter?: string) => {
    const { data } = await api.get("/buses", {
      params: statusFilter ? { status: statusFilter } : {},
    });
    return data as Array<{
      id: string;
      fleet_number: string;
      license_plate: string;
      make: string;
      model: string;
      year: number;
      status: string;
      depot_id?: string;
      mileage_km: number;
    }>;
  },

  createBus: async (payload: {
    fleet_number: string;
    license_plate: string;
    make: string;
    model: string;
    year: number;
    vin?: string;
    depot_id?: string;
    mileage_km?: number;
    status?: string;
  }) => {
    const { data } = await api.post("/buses", payload);
    return data;
  },

  updateBus: async (
    id: string,
    patch: Partial<{ status: string; mileage_km: number; notes: string; depot_id: string }>
  ) => {
    const { data } = await api.patch(`/buses/${id}`, patch);
    return data;
  },
};

export const auditService = {
  listAuditLogs: async (params?: {
    resource_type?: string;
    action?: string;
    offset?: number;
    limit?: number;
  }) => {
    const { data } = await api.get("/audit", { params });
    return data as {
      logs: Array<{
        id: string;
        user_id?: string;
        username?: string;
        action: string;
        resource_type: string;
        resource_id?: string;
        created_at: string;
        notes?: string;
      }>;
    };
  },
};

export const usersService = {
  listUsers: async (): Promise<{ users: any[] }> => {
    const { data } = await api.get("/auth/users");
    return data;
  },

  createUser: async (payload: {
    email: string;
    username: string;
    password: string;
    full_name: string;
    role: string;
  }) => {
    const { data } = await api.post("/auth/users", payload);
    return data;
  },

  assignRole: async (userId: string, role: string) => {
    const { data } = await api.put(`/auth/users/${userId}/role`, { role });
    return data;
  },

  deleteUser: async (userId: string) => {
    await api.delete(`/auth/users/${userId}`);
  },
};
