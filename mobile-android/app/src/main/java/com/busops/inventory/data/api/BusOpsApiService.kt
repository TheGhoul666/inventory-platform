package com.busops.inventory.data.api

import com.busops.inventory.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface BusOpsApiService {

    // ── Auth ─────────────────────────────────────────────────────────────────
    @GET("auth/me")
    suspend fun getMe(): Response<UserDto>

    // ── Inventory ─────────────────────────────────────────────────────────────
    @GET("inventory/items")
    suspend fun getInventoryItems(
        @Query("page") page: Int = 1,
        @Query("per_page") perPage: Int = 50,
        @Query("search") search: String? = null,
        @Query("warehouse_id") warehouseId: String? = null,
        @Query("low_stock") lowStock: Boolean? = null,
    ): Response<PaginatedResponseDto<InventoryItemDto>>

    @GET("inventory/items/{id}")
    suspend fun getInventoryItem(@Path("id") id: String): Response<InventoryItemDto>

    @POST("inventory/transactions/issue")
    suspend fun issueItems(@Body request: IssueRequestDto): Response<TransactionDto>

    @POST("inventory/transactions/restock")
    suspend fun restockItems(@Body request: RestockRequestDto): Response<TransactionDto>

    @POST("inventory/transactions/transfer")
    suspend fun transferItems(@Body request: TransferRequestDto): Response<TransactionDto>

    @GET("inventory/transactions")
    suspend fun getTransactions(
        @Query("page") page: Int = 1,
        @Query("per_page") perPage: Int = 30,
        @Query("item_id") itemId: String? = null,
    ): Response<PaginatedResponseDto<TransactionDto>>

    // ── Warehouses ─────────────────────────────────────────────────────────────
    @GET("warehouses")
    suspend fun getWarehouses(): Response<List<WarehouseDto>>

    // ── Alerts ─────────────────────────────────────────────────────────────────
    @GET("alerts")
    suspend fun getAlerts(
        @Query("page") page: Int = 1,
        @Query("per_page") perPage: Int = 30,
        @Query("status") status: String? = null,
    ): Response<PaginatedResponseDto<AlertDto>>

    @POST("alerts/{id}/acknowledge")
    suspend fun acknowledgeAlert(@Path("id") id: String): Response<AlertDto>

    // ── Analytics ─────────────────────────────────────────────────────────────
    @GET("analytics/dashboard")
    suspend fun getDashboard(): Response<DashboardDto>
}
