import SwiftUI
import Supabase

@MainActor
final class AlertsViewModel: ObservableObject {
    @Published var alerts: [Alert] = []
    @Published var isLoading = true
    @Published var error: String? = nil

    private let supabase: SupabaseClient
    private let api: APIClient

    init(supabase: SupabaseClient, api: APIClient) {
        self.supabase = supabase
        self.api = api
        Task { await load() }
    }

    func load() async {
        isLoading = true
        error = nil
        do {
            let all: [Alert] = try await supabase
                .from("alerts")
                .select()
                .eq("is_deleted", false)
                .eq("status", "OPEN")
                .order("created_at", ascending: false)
                .execute()
                .value
            alerts = all
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }

    func acknowledge(id: String) {
        Task {
            _ = try? await api.acknowledgeAlert(id: id)
            await load()
        }
    }
}

struct AlertsView: View {
    @EnvironmentObject var viewModel: AlertsViewModel

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading {
                    ProgressView("טוען התראות...")
                } else if viewModel.alerts.isEmpty {
                    ContentUnavailableView("אין התראות", systemImage: "checkmark.circle.fill", description: Text("כל הפריטים בסדר"))
                } else {
                    List(viewModel.alerts) { alert in
                        AlertRow(alert: alert, onAcknowledge: { viewModel.acknowledge(id: alert.id) })
                    }
                    .listStyle(.plain)
                    .refreshable { await viewModel.load() }
                }
            }
            .navigationTitle("התראות")
        }
    }
}

struct AlertRow: View {
    let alert: Alert
    let onAcknowledge: () -> Void

    var severityColor: Color {
        switch alert.severity.lowercased() {
        case "critical": return .red
        case "high":     return .orange
        default:         return .yellow
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(severityColor)
                Text(alert.alertType ?? "ALERT")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
                Text(alert.severity.uppercased())
                    .font(.caption2).bold()
                    .foregroundStyle(severityColor)
                Button("אשר", action: onAcknowledge)
                    .font(.caption)
                    .buttonStyle(.bordered)
                    .controlSize(.mini)
            }
            if let title = alert.title {
                Text(title).font(.subheadline).bold()
            }
            Text(alert.message).font(.caption).foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }
}
