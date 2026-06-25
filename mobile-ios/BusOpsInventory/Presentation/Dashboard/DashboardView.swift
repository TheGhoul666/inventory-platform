import SwiftUI
import Supabase

@MainActor
final class DashboardViewModel: ObservableObject {
    @Published var dashboard: DashboardResponse? = nil
    @Published var isLoading = true
    @Published var error: String? = nil

    private let supabase: SupabaseClient

    init(supabase: SupabaseClient) {
        self.supabase = supabase
        Task { await load() }
    }

    func load() async {
        isLoading = true
        error = nil
        do {
            let items: [InventoryItem] = try await supabase
                .from("inventory_items")
                .select()
                .eq("is_deleted", false)
                .execute()
                .value
            let alerts: [Alert] = try await supabase
                .from("alerts")
                .select()
                .eq("is_deleted", false)
                .eq("status", "OPEN")
                .execute()
                .value
            dashboard = DashboardResponse(
                totalItems: items.count,
                lowStockCount: items.filter { $0.isLowStock }.count,
                criticalStockCount: items.filter { $0.isCriticalStock }.count,
                activeAlerts: alerts.count,
                transactionsToday: 0
            )
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}

struct DashboardView: View {
    @EnvironmentObject var authVM: AuthViewModel
    @StateObject private var vm: DashboardViewModel
    let onNavigateToInventory: () -> Void
    let onNavigateToAlerts: () -> Void

    init(supabase: SupabaseClient, onNavigateToInventory: @escaping () -> Void, onNavigateToAlerts: @escaping () -> Void) {
        _vm = StateObject(wrappedValue: DashboardViewModel(supabase: supabase))
        self.onNavigateToInventory = onNavigateToInventory
        self.onNavigateToAlerts = onNavigateToAlerts
    }

    var body: some View {
        NavigationStack {
            Group {
                if vm.isLoading {
                    ProgressView("טוען...")
                } else if let d = vm.dashboard {
                    ScrollView {
                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                            StatCard(icon: "archivebox.fill", value: "\(d.totalItems)", label: "פריטים", color: .blue, action: onNavigateToInventory)
                            StatCard(icon: "exclamationmark.triangle.fill", value: "\(d.lowStockCount)", label: "מלאי נמוך", color: d.lowStockCount > 0 ? .orange : .green, action: onNavigateToInventory)
                            StatCard(icon: "bell.fill", value: "\(d.activeAlerts)", label: "התראות", color: d.activeAlerts > 0 ? .red : .green, action: onNavigateToAlerts)
                            StatCard(icon: "exclamationmark.octagon.fill", value: "\(d.criticalStockCount)", label: "קריטי", color: d.criticalStockCount > 0 ? .red : .green, action: onNavigateToInventory)
                        }
                        .padding()
                    }
                } else if let err = vm.error {
                    ContentUnavailableView("שגיאה", systemImage: "wifi.slash", description: Text(err))
                }
            }
            .navigationTitle("לוח בקרה")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: authVM.logout) {
                        Image(systemName: "rectangle.portrait.and.arrow.right")
                    }
                }
            }
            .refreshable { await vm.load() }
        }
    }
}

struct StatCard: View {
    let icon: String
    let value: String
    let label: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundStyle(color)
                Text(value)
                    .font(.title).bold()
                Text(label)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(.regularMaterial)
            .clipShape(.rect(cornerRadius: 12))
        }
        .buttonStyle(.plain)
    }
}
