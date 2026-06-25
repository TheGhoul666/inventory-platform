package com.busops.inventory.ui.screens.alerts

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
import com.busops.inventory.data.model.AlertDto
import com.busops.inventory.data.repository.InventoryRepository
import com.busops.inventory.data.repository.Result
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

// ── ViewModel ──────────────────────────────────────────────────────────────────

data class AlertsUiState(
    val alerts: List<AlertDto> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class AlertsViewModel @Inject constructor(
    private val repo: InventoryRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(AlertsUiState(isLoading = true))
    val state: StateFlow<AlertsUiState> = _state.asStateFlow()

    // Supabase realtime subscription for alerts table
    private val _alerts = MutableStateFlow<List<AlertDto>>(emptyList())

    init { load() }

    fun load() = viewModelScope.launch {
        _state.update { it.copy(isLoading = true, error = null) }
        when (val r = repo.fetchAlerts(status = "OPEN")) {
            is Result.Success -> {
                _alerts.value = r.data
                _state.update { it.copy(alerts = r.data, isLoading = false) }
            }
            is Result.Error -> _state.update { it.copy(error = r.message, isLoading = false) }
            else -> Unit
        }
    }

    fun acknowledge(alertId: String) = viewModelScope.launch {
        // Acknowledge goes through FastAPI for business logic
        runCatching { repo.api.acknowledgeAlert(alertId) }
        load()
    }
}

// ── Screen ─────────────────────────────────────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AlertsScreen(
    viewModel: AlertsViewModel,
    onBack: () -> Unit,
) {
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("התראות") },
                navigationIcon = { IconButton(onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back") } },
            )
        },
    ) { padding ->
        if (state.isLoading) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else if (state.alerts.isEmpty()) {
            Box(Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(Icons.Filled.CheckCircle, null, modifier = Modifier.size(48.dp), tint = MaterialTheme.colorScheme.primary)
                    Spacer(Modifier.height(8.dp))
                    Text("אין התראות פעילות")
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                items(state.alerts, key = { it.id }) { alert ->
                    AlertCard(alert = alert, onAcknowledge = { viewModel.acknowledge(alert.id) })
                }
            }
        }
    }
}

@Composable
private fun AlertCard(alert: AlertDto, onAcknowledge: () -> Unit) {
    val containerColor = when (alert.severity) {
        "critical" -> MaterialTheme.colorScheme.errorContainer
        "warning" -> MaterialTheme.colorScheme.tertiaryContainer
        else -> MaterialTheme.colorScheme.surfaceVariant
    }
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = containerColor),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.Warning, null, modifier = Modifier.size(20.dp))
                Spacer(Modifier.width(8.dp))
                Text(alert.alertType ?: "ALERT", style = MaterialTheme.typography.labelMedium)
            }
            alert.title?.let { Text(it, style = MaterialTheme.typography.bodyMedium) }
            Text(alert.message, style = MaterialTheme.typography.bodySmall)
            TextButton(
                onClick = onAcknowledge,
                modifier = Modifier.align(Alignment.End),
            ) { Text("אשר") }
        }
    }
}
