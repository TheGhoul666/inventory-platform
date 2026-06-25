import Foundation
import Supabase

// ponytail: reads via Supabase PostgREST, writes via FastAPI — same pattern as web app
@MainActor
final class InventoryRepository: ObservableObject {
    @Published var items: [InventoryItem] = []

    let supabase: SupabaseClient
    private let api: APIClient
    private let realtime: RealtimeManager

    init(api: APIClient, supabase: SupabaseClient) {
        self.api = api
        self.supabase = supabase
        self.realtime = RealtimeManager(supabase: supabase)
        setupRealtimeHandlers()
        Task { await realtime.connect() }
    }

    // ── Reads via Supabase PostgREST ───────────────────────────────────────────

    func fetchItems(page: Int = 1, search: String? = nil, lowStock: Bool? = nil) async throws {
        var all: [InventoryItem] = try await supabase
            .from("inventory_items")
            .select()
            .eq("is_deleted", false)
            .execute()
            .value

        if let q = search?.lowercased(), !q.isEmpty {
            all = all.filter { $0.name.lowercased().contains(q) || $0.sku.lowercased().contains(q) }
        }
        if lowStock == true { all = all.filter { $0.isLowStock } }
        if page == 1 { items = all } else { items.append(contentsOf: all) }
    }

    // ── Writes via FastAPI (business rules) ────────────────────────────────────

    func issueItems(itemId: String, quantity: Int, notes: String?) async throws -> Transaction {
        try await api.issueItems(IssueRequest(itemId: itemId, quantity: quantity, busId: nil, notes: notes))
    }

    func restockItems(itemId: String, quantity: Int, supplierName: String?, notes: String?) async throws -> Transaction {
        try await api.restockItems(RestockRequest(itemId: itemId, quantity: quantity, supplierName: supplierName, notes: notes))
    }

    // ── Realtime — patches in-memory list, no re-fetch ─────────────────────────

    private func setupRealtimeHandlers() {
        realtime.onInventoryChange = { [weak self] action in
            Task { @MainActor in self?.applyChange(action) }
        }
    }

    private func applyChange(_ action: AnyAction) {
        switch action {
        case .update(let record):
            guard let updated = try? record.decodeRecord(as: InventoryItem.self) else { return }
            if let i = items.firstIndex(where: { $0.id == updated.id }) { items[i] = updated }
        case .insert(let record):
            guard let inserted = try? record.decodeRecord(as: InventoryItem.self) else { return }
            if !items.contains(where: { $0.id == inserted.id }) { items.append(inserted) }
        case .delete(let record):
            if let id = record.oldRecord["id"]?.value as? String { items.removeAll { $0.id == id } }
        default:
            break
        }
    }
}
