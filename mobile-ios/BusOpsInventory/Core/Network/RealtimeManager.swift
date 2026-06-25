import Foundation
import Realtime
import Supabase

/// Manages Supabase Realtime subscriptions. All changes flow through here,
/// then get applied to the in-memory stores in each repository.
@MainActor
final class RealtimeManager {
    private let supabase: SupabaseClient
    private var inventoryChannel: RealtimeChannelV2?
    private var alertsChannel: RealtimeChannelV2?

    var onInventoryChange: ((AnyAction) -> Void)?
    var onAlertChange: ((AnyAction) -> Void)?

    init(supabase: SupabaseClient) {
        self.supabase = supabase
    }

    func connect() async {
        await subscribeInventory()
        await subscribeAlerts()
    }

    func disconnect() async {
        await inventoryChannel?.unsubscribe()
        await alertsChannel?.unsubscribe()
    }

    // ── Inventory items subscription ──────────────────────────────────────────

    private func subscribeInventory() async {
        inventoryChannel = await supabase.realtimeV2.channel("inventory-items")
        let changes = await inventoryChannel!.postgresChange(AnyAction.self, schema: "public", table: "inventory_items")

        await inventoryChannel!.subscribe()

        Task {
            for await action in changes {
                onInventoryChange?(action)
            }
        }
    }

    // ── Alerts subscription ───────────────────────────────────────────────────

    private func subscribeAlerts() async {
        alertsChannel = await supabase.realtimeV2.channel("alerts")
        let changes = await alertsChannel!.postgresChange(AnyAction.self, schema: "public", table: "alerts")

        await alertsChannel!.subscribe()

        Task {
            for await action in changes {
                onAlertChange?(action)
            }
        }
    }
}
