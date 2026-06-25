import Foundation

// ── Domain models — mapped from Supabase column names via CodingKeys ──────────

struct User: Codable, Identifiable {
    let id: String
    let email: String
    let username: String
    let fullName: String
    let roles: [String]
    let permissions: [String]
    let isSuperadmin: Bool
}

struct InventoryItem: Codable, Identifiable {
    let id: String
    let name: String
    let sku: String
    let description: String?
    let quantity: Int
    let lowStockThreshold: Int
    let criticalStockThreshold: Int
    let unit: String
    let warehouseId: String
    let unitCost: Double?
    let categoryId: String?

    var isLowStock: Bool { lowStockThreshold > 0 && quantity <= lowStockThreshold }
    var isCriticalStock: Bool { criticalStockThreshold > 0 && quantity <= criticalStockThreshold }

    enum CodingKeys: String, CodingKey {
        case id, name, sku, description, quantity, unit
        case lowStockThreshold = "low_stock_threshold"
        case criticalStockThreshold = "critical_stock_threshold"
        case warehouseId = "warehouse_id"
        case unitCost = "unit_cost"
        case categoryId = "category_id"
    }
}

struct Warehouse: Codable, Identifiable {
    let id: String
    let name: String
    let code: String
    let city: String?
    let isActive: Bool

    enum CodingKeys: String, CodingKey {
        case id, name, code, city
        case isActive = "is_active"
    }
}

struct Alert: Codable, Identifiable {
    let id: String
    let alertType: String?
    let severity: String
    let message: String
    let title: String?
    let status: String
    let itemId: String?
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id, severity, message, title, status
        case alertType = "alert_type"
        case itemId = "item_id"
        case createdAt = "created_at"
    }
}

struct Transaction: Codable, Identifiable {
    let id: String
    let transactionType: String
    let quantityDelta: Int
    let itemId: String
    let notes: String?
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id, notes
        case transactionType = "transaction_type"
        case quantityDelta = "quantity_delta"
        case itemId = "item_id"
        case createdAt = "created_at"
    }
}

struct DashboardResponse: Codable {
    let totalItems: Int
    let lowStockCount: Int
    let criticalStockCount: Int
    let activeAlerts: Int
    let transactionsToday: Int
}

struct PaginatedResponse<T: Codable>: Codable {
    let items: [T]
    let total: Int
    let page: Int
    let perPage: Int
    let pages: Int
}

// ── Request models ─────────────────────────────────────────────────────────────

struct IssueRequest: Codable {
    let itemId: String
    let quantity: Int
    let busId: String?
    let notes: String?

    enum CodingKeys: String, CodingKey {
        case quantity, notes
        case itemId = "item_id"
        case busId = "bus_id"
    }
}

struct RestockRequest: Codable {
    let itemId: String
    let quantity: Int
    let supplierName: String?
    let notes: String?

    enum CodingKeys: String, CodingKey {
        case quantity, notes
        case itemId = "item_id"
        case supplierName = "supplier_name"
    }
}
