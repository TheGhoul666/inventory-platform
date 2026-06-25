import SwiftUI

@MainActor
final class InventoryViewModel: ObservableObject {
    @Published var items: [InventoryItem] = []
    @Published var isLoading = true
    @Published var error: String? = nil
    @Published var searchText = ""
    @Published var showIssueSheet = false
    @Published var selectedItem: InventoryItem? = nil

    private let repo: InventoryRepository

    var filteredItems: [InventoryItem] {
        guard !searchText.isEmpty else { return items }
        return items.filter {
            $0.name.localizedCaseInsensitiveContains(searchText) ||
            $0.sku.localizedCaseInsensitiveContains(searchText)
        }
    }

    init(repo: InventoryRepository) {
        self.repo = repo
        // Mirror realtime-updated list
        repo.$items.assign(to: &$items)
        Task { await load() }
    }

    func load() async {
        isLoading = true
        error = nil
        do { try await repo.fetchItems() } catch { self.error = error.localizedDescription }
        isLoading = false
    }

    func select(_ item: InventoryItem) {
        selectedItem = item
        showIssueSheet = true
    }

    func issueItem(quantity: Int, notes: String?) async {
        guard let item = selectedItem else { return }
        do {
            _ = try await repo.issueItems(itemId: item.id, quantity: quantity, notes: notes)
            showIssueSheet = false
        } catch {
            self.error = error.localizedDescription
        }
    }
}

struct InventoryListView: View {
    @EnvironmentObject var viewModel: InventoryViewModel

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading {
                    ProgressView("טוען מלאי...")
                } else {
                    List(viewModel.filteredItems) { item in
                        InventoryRow(item: item)
                            .contentShape(Rectangle())
                            .onTapGesture { viewModel.select(item) }
                    }
                    .listStyle(.plain)
                    .searchable(text: $viewModel.searchText, prompt: "חיפוש לפי שם או SKU")
                    .refreshable { await viewModel.load() }
                }
            }
            .navigationTitle("מלאי")
        }
        .sheet(isPresented: $viewModel.showIssueSheet) {
            if let item = viewModel.selectedItem {
                IssueItemSheet(item: item) { qty, notes in
                    await viewModel.issueItem(quantity: qty, notes: notes)
                }
            }
        }
    }
}

struct InventoryRow: View {
    let item: InventoryItem

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(item.name).font(.headline)
                Text(item.sku).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 4) {
                Text("\(item.quantity) \(item.unit)")
                    .font(.title3).bold()
                    .foregroundStyle(item.isCriticalStock ? .red : item.isLowStock ? .orange : .primary)
                if item.isLowStock {
                    Label("מלאי נמוך", systemImage: "exclamationmark.triangle.fill")
                        .font(.caption2)
                        .foregroundStyle(.orange)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

struct IssueItemSheet: View {
    let item: InventoryItem
    let onConfirm: (Int, String?) async -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var quantityText = "1"
    @State private var notes = ""
    @State private var isSubmitting = false

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    LabeledContent("פריט", value: item.name)
                    LabeledContent("זמין", value: "\(item.quantity) \(item.unit)")
                }
                Section("הוצאה") {
                    TextField("כמות", text: $quantityText)
                        .keyboardType(.numberPad)
                    TextField("הערות (אופציונלי)", text: $notes)
                }
            }
            .navigationTitle("הוצאת פריט")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("ביטול") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("אשר") {
                        guard let qty = Int(quantityText), qty > 0, qty <= item.quantity else { return }
                        isSubmitting = true
                        Task {
                            await onConfirm(qty, notes.isEmpty ? nil : notes)
                            isSubmitting = false
                        }
                    }
                    .disabled(isSubmitting)
                }
            }
        }
    }
}
