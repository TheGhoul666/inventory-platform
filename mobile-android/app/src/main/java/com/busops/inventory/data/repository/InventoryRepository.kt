package com.busops.inventory.data.repository

import com.busops.inventory.data.api.BusOpsApiService
import com.busops.inventory.data.model.*
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.realtime.channel
import io.github.jan.supabase.realtime.postgresChangeFlow
import io.github.jan.supabase.realtime.PostgresAction
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.onStart
import javax.inject.Inject
import javax.inject.Singleton

sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String, val code: Int? = null) : Result<Nothing>()
    data object Loading : Result<Nothing>()
}

@Singleton
class InventoryRepository @Inject constructor(
    val api: BusOpsApiService,
    private val supabase: SupabaseClient,
) {
    private val _items = MutableStateFlow<List<InventoryItemDto>>(emptyList())
    val items: Flow<List<InventoryItemDto>> = _items.asStateFlow()

    // ── Reads via Supabase PostgREST (bypasses FastAPI — dev host has no IPv6) ─

    suspend fun fetchItems(
        page: Int = 1,
        search: String? = null,
        warehouseId: String? = null,
        lowStock: Boolean? = null,
    ): Result<PaginatedResponseDto<InventoryItemDto>> = try {
        var all = supabase.from("inventory_items").select {
            filter {
                eq("is_deleted", false)
                warehouseId?.let { eq("warehouse_id", it) }
            }
        }.decodeList<InventoryItemDto>()

        if (search != null) all = all.filter {
            it.name.contains(search, ignoreCase = true) || it.sku.contains(search, ignoreCase = true)
        }
        if (lowStock == true) all = all.filter { it.isLowStock }

        if (page == 1) _items.value = all else _items.value = _items.value + all
        Result.Success(PaginatedResponseDto(items = all, total = all.size))
    } catch (e: Exception) {
        Result.Error(e.message ?: "Failed to fetch items")
    }

    suspend fun fetchAlerts(status: String? = "OPEN"): Result<List<AlertDto>> = try {
        val alerts = supabase.from("alerts").select {
            filter {
                eq("is_deleted", false)
                status?.let { eq("status", it) }
            }
        }.decodeList<AlertDto>()
        Result.Success(alerts)
    } catch (e: Exception) {
        Result.Error(e.message ?: "Failed to fetch alerts")
    }

    suspend fun getDashboard(): Result<DashboardDto> = try {
        val items = supabase.from("inventory_items").select {
            filter { eq("is_deleted", false) }
        }.decodeList<InventoryItemDto>()
        val alerts = supabase.from("alerts").select {
            filter { eq("is_deleted", false); eq("status", "OPEN") }
        }.decodeList<AlertDto>()
        Result.Success(DashboardDto(
            totalItems = items.size,
            lowStockCount = items.count { it.isLowStock },
            criticalStockCount = items.count { it.isCriticalStock },
            activeAlerts = alerts.size,
            transactionsToday = 0,
        ))
    } catch (e: Exception) {
        Result.Error(e.message ?: "Failed to get dashboard")
    }

    // ── Writes via FastAPI (business rule enforcement) ─────────────────────────

    suspend fun issueItems(request: IssueRequestDto): Result<TransactionDto> {
        val response = api.issueItems(request)
        return if (response.isSuccessful) Result.Success(response.body()!!)
        else Result.Error(response.message(), response.code())
    }

    suspend fun restockItems(request: RestockRequestDto): Result<TransactionDto> {
        val response = api.restockItems(request)
        return if (response.isSuccessful) Result.Success(response.body()!!)
        else Result.Error(response.message(), response.code())
    }

    // ── Supabase Realtime — patches in-memory list, no re-fetch needed ─────────

    suspend fun subscribeToInventoryChanges(): Flow<PostgresAction> {
        val channel = supabase.channel("inventory-items-channel")
        val changeFlow = channel.postgresChangeFlow<PostgresAction>(schema = "public") {
            table = "inventory_items"
        }
        channel.subscribe()
        return changeFlow.onStart { fetchItems() }
    }

    fun applyRealtimeChange(action: PostgresAction) {
        when (action) {
            is PostgresAction.Update -> {
                val updated = action.decodeRecord<InventoryItemDto>()
                _items.value = _items.value.map { if (it.id == updated.id) updated else it }
            }
            is PostgresAction.Insert -> {
                val inserted = action.decodeRecord<InventoryItemDto>()
                if (_items.value.none { it.id == inserted.id }) _items.value = _items.value + inserted
            }
            is PostgresAction.Delete -> {
                val deletedId = action.oldRecord["id"]?.toString()?.trim('"')
                _items.value = _items.value.filter { it.id != deletedId }
            }
            else -> Unit
        }
    }
}
