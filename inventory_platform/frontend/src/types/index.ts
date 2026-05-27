// ============================================================
// Shared TypeScript types mirroring the backend Pydantic models
// ============================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface InventoryItem {
  id: string;
  sku: string;
  name: string;
  unit: string;
  quantity: number;
  available_quantity: number;
  reserved_quantity: number;
  low_stock_threshold: number;
  critical_stock_threshold: number;
  is_low_stock: boolean;
  is_critical_stock: boolean;
  warehouse_id: string;
  category_id: string | null;
  description?: string;
  supplier_name?: string;
  lead_time_days?: number;
  unit_cost?: number;
}

export interface Warehouse {
  id: string;
  name: string;
  code: string;
  city?: string;
  country: string;
  is_active: boolean;
}

export interface Transaction {
  id: string;
  type: TransactionType;
  status: TransactionStatus;
  quantity_delta: number;
  quantity_before: number;
  quantity_after: number;
  created_at: string;
  notes?: string;
  reason_code?: string;
  bus_id?: string;
}

export type TransactionType =
  | "ISSUE"
  | "RESTOCK"
  | "TRANSFER"
  | "ADJUSTMENT"
  | "RESERVATION"
  | "RELEASE"
  | "WRITE_OFF";

export type TransactionStatus = "PENDING" | "COMPLETED" | "ROLLED_BACK" | "FAILED";

export interface Alert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  message: string;
  item_id?: string;
  warehouse_id?: string;
  created_at: string;
  acknowledged_at?: string;
}

export type AlertType =
  | "LOW_STOCK"
  | "CRITICAL_STOCK"
  | "PREDICTED_DEPLETION"
  | "ABNORMAL_USAGE"
  | "WEBHOOK_FAILURE"
  | "WAREHOUSE_ANOMALY"
  | "SYSTEM";

export type AlertSeverity = "INFO" | "WARNING" | "CRITICAL" | "EMERGENCY";
export type AlertStatus = "OPEN" | "ACKNOWLEDGED" | "RESOLVED" | "ESCALATED";

export interface DashboardSummary {
  low_stock_count: number;
  critical_stock_count: number;
  critical_items: Array<{
    id: string;
    name: string;
    sku: string;
    quantity: number;
    threshold: number;
  }>;
  generated_at: string;
}

export interface UsageAnalytics {
  item_id: string;
  daily_consumption_rate: number;
  predicted_depletion_days: number | null;
  period_days: number;
}

export interface AnomalyResult {
  item_id: string;
  rate_7d: number;
  rate_30d: number;
  is_anomaly: boolean;
  ratio: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  roles: string[];
  permissions: string[];
}

// API error shape
export interface ApiError {
  detail: string;
  status?: number;
}
