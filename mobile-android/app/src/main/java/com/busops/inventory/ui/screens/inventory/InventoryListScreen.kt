package com.busops.inventory.ui.screens.inventory

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.busops.inventory.data.model.InventoryItemDto
import com.busops.inventory.data.repository.InventoryRepository
import com.busops.inventory.data.repository.Result
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

// ── ViewModel ──────────────────────────────────────────────────────────────────

data class InventoryUiState(
    val items: List<InventoryItemDto> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val searchQuery: String = "",
    val showIssueDialog: Boolean = false,
    val selectedItem: InventoryItemDto? = null,
)

@OptIn(FlowPreview::class)
@HiltViewModel
class InventoryViewModel @Inject constructor(
    private val repo: InventoryRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(InventoryUiState(isLoading = true))
    val state: StateFlow<InventoryUiState> = _state.asStateFlow()

    init {
        // Feed realtime items into state
        viewModelScope.launch {
            repo.items.collect { items ->
                _state.update { it.copy(items = applySearch(items, it.searchQuery)) }
            }
        }
        // Subscribe to realtime changes and apply them to the repo's in-memory list
        viewModelScope.launch {
            repo.subscribeToInventoryChanges().collect { action ->
                repo.applyRealtimeChange(action)
            }
        }
        load()
    }

    fun load() = viewModelScope.launch {
        _state.update { it.copy(isLoading = true, error = null) }
        when (val r = repo.fetchItems(search = _state.value.searchQuery.ifBlank { null })) {
            is Result.Success -> _state.update { it.copy(isLoading = false) }
            is Result.Error -> _state.update { it.copy(isLoading = false, error = r.message) }
            else -> Unit
        }
    }

    fun onSearch(query: String) {
        _state.update { state ->
            state.copy(
                searchQuery = query,
                items = applySearch(state.items, query),
            )
        }
    }

    fun onSelectItem(item: InventoryItemDto) = _state.update { it.copy(selectedItem = item, showIssueDialog = true) }
    fun onDismissDialog() = _state.update { it.copy(showIssueDialog = false, selectedItem = null) }

    fun issueItem(itemId: String, quantity: Int, notes: String) = viewModelScope.launch {
        repo.issueItems(com.busops.inventory.data.model.IssueRequestDto(itemId, quantity, notes = notes.ifBlank { null }))
        onDismissDialog()
    }

    private fun applySearch(items: List<InventoryItemDto>, query: String) =
        if (query.isBlank()) items
        else items.filter { it.name.contains(query, ignoreCase = true) || it.sku.contains(query, ignoreCase = true) }
}

// ── Screen ─────────────────────────────────────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InventoryListScreen(
    viewModel: InventoryViewModel,
    onBack: () -> Unit,
) {
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("מלאי") },
                navigationIcon = { IconButton(onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back") } },
            )
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            // Search bar
            OutlinedTextField(
                value = state.searchQuery,
                onValueChange = viewModel::onSearch,
                placeholder = { Text("חיפוש לפי שם או SKU...") },
                leadingIcon = { Icon(Icons.Filled.Search, null) },
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
                singleLine = true,
            )

            if (state.isLoading) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    items(state.items, key = { it.id }) { item ->
                        InventoryItemCard(item = item, onClick = { viewModel.onSelectItem(item) })
                    }
                }
            }
        }
    }

    if (state.showIssueDialog && state.selectedItem != null) {
        IssueItemDialog(
            item = state.selectedItem!!,
            onDismiss = viewModel::onDismissDialog,
            onConfirm = { qty, notes -> viewModel.issueItem(state.selectedItem!!.id, qty, notes) },
        )
    }
}

@Composable
private fun InventoryItemCard(item: InventoryItemDto, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = when {
                item.isCriticalStock -> MaterialTheme.colorScheme.errorContainer
                item.isLowStock -> MaterialTheme.colorScheme.tertiaryContainer
                else -> MaterialTheme.colorScheme.surfaceVariant
            },
        ),
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(item.name, style = MaterialTheme.typography.titleMedium)
                Text(item.sku, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                item.warehouseName?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    "${item.quantity} ${item.unit}",
                    style = MaterialTheme.typography.titleMedium,
                    color = if (item.isCriticalStock) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface,
                )
                if (item.isLowStock) {
                    Text("מלאי נמוך", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.error)
                }
            }
        }
    }
}

@Composable
private fun IssueItemDialog(
    item: InventoryItemDto,
    onDismiss: () -> Unit,
    onConfirm: (Int, String) -> Unit,
) {
    var quantity by remember { mutableStateOf("1") }
    var notes by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("הוצאת פריט") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("${item.name} — זמין: ${item.quantity} ${item.unit}")
                OutlinedTextField(
                    value = quantity,
                    onValueChange = { quantity = it.filter { c -> c.isDigit() } },
                    label = { Text("כמות") },
                    singleLine = true,
                )
                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("הערות (אופציונלי)") },
                    singleLine = true,
                )
            }
        },
        confirmButton = {
            TextButton(onClick = {
                val qty = quantity.toIntOrNull() ?: return@TextButton
                if (qty > 0 && qty <= item.quantity) onConfirm(qty, notes)
            }) { Text("אשר") }
        },
        dismissButton = { TextButton(onDismiss) { Text("ביטול") } },
    )
}
