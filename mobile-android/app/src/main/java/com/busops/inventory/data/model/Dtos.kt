package com.busops.inventory.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class UserDto(
    val id: String,
    val email: String,
    val username: String,
    @SerialName("full_name") val fullName: String,
    val roles: List<String> = emptyList(),
    val permissions: List<String> = emptyList(),
    @SerialName("is_superadmin") val isSuperAdmin: Boolean = false,
)

@Serializable
data class InventoryItemDto(
    val id: String,
    val name: String,
    val sku: String,
    val description: String? = null,
    val quantity: Int = 0,
    @SerialName("low_stock_threshold") val lowStockThreshold: Int = 0,
    @SerialName("critical_stock_threshold") val criticalStockThreshold: Int = 0,
    val unit: String = "",
    @SerialName("warehouse_id") val warehouseId: String = "",
    @SerialName("unit_cost") val unitCost: Double? = null,
    @SerialName("category_id") val categoryId: String? = null,
) {
    val isLowStock: Boolean get() = lowStockThreshold > 0 && quantity <= lowStockThreshold
    val isCriticalStock: Boolean get() = criticalStockThreshold > 0 && quantity <= criticalStockThreshold
}

@Serializable
data class WarehouseDto(
    val id: String,
    val name: String,
    val code: String,
    val city: String? = null,
    @SerialName("is_active") val isActive: Boolean = true,
)

@Serializable
data class AlertDto(
    val id: String,
    @SerialName("alert_type") val alertType: String? = null,
    val severity: String = "",
    val message: String = "",
    val title: String? = null,
    val status: String = "",
    @SerialName("item_id") val itemId: String? = null,
    @SerialName("created_at") val createdAt: String = "",
)

@Serializable
data class TransactionDto(
    val id: String,
    @SerialName("transaction_type") val type: String = "",
    @SerialName("quantity_delta") val quantity: Int = 0,
    @SerialName("item_id") val itemId: String = "",
    val notes: String? = null,
    @SerialName("created_at") val createdAt: String = "",
)

@Serializable
data class DashboardDto(
    @SerialName("total_items") val totalItems: Int = 0,
    @SerialName("low_stock_count") val lowStockCount: Int = 0,
    @SerialName("critical_stock_count") val criticalStockCount: Int = 0,
    @SerialName("active_alerts") val activeAlerts: Int = 0,
    @SerialName("transactions_today") val transactionsToday: Int = 0,
)

@Serializable
data class PaginatedResponseDto<T>(
    val items: List<T> = emptyList(),
    val total: Int = 0,
    val page: Int = 1,
    @SerialName("per_page") val perPage: Int = 50,
    val pages: Int = 1,
)

@Serializable
data class IssueRequestDto(
    @SerialName("item_id") val itemId: String,
    val quantity: Int,
    @SerialName("bus_id") val busId: String? = null,
    @SerialName("maintenance_event_id") val maintenanceEventId: String? = null,
    val notes: String? = null,
)

@Serializable
data class RestockRequestDto(
    @SerialName("item_id") val itemId: String,
    val quantity: Int,
    @SerialName("supplier_name") val supplierName: String? = null,
    @SerialName("purchase_order") val purchaseOrder: String? = null,
    val notes: String? = null,
)

@Serializable
data class TransferRequestDto(
    @SerialName("item_id") val itemId: String,
    val quantity: Int,
    @SerialName("source_warehouse_id") val sourceWarehouseId: String,
    @SerialName("destination_warehouse_id") val destinationWarehouseId: String,
    val notes: String? = null,
)

@Serializable
data class LoginResponseDto(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String? = null,
    @SerialName("token_type") val tokenType: String = "bearer",
)
