import Foundation
import Supabase

@MainActor
final class AppContainer: ObservableObject {

    // ── Supabase ──────────────────────────────────────────────────────────────
    let supabase: SupabaseClient = {
        guard
            let urlString = Bundle.main.infoDictionary?["SUPABASE_URL"] as? String,
            let url = URL(string: urlString),
            let key = Bundle.main.infoDictionary?["SUPABASE_ANON_KEY"] as? String
        else { fatalError("Missing Supabase config in Info.plist") }
        return SupabaseClient(supabaseURL: url, supabaseKey: key)
    }()

    // ── Networking ────────────────────────────────────────────────────────────
    lazy var apiClient: APIClient = APIClient(supabase: supabase)

    // ── Repositories ──────────────────────────────────────────────────────────
    lazy var inventoryRepo: InventoryRepository = InventoryRepository(api: apiClient, supabase: supabase)
    lazy var authRepo: AuthRepository = AuthRepository(supabase: supabase)

    // ── ViewModels ────────────────────────────────────────────────────────────
    lazy var authViewModel: AuthViewModel = AuthViewModel(repo: authRepo)
    lazy var inventoryViewModel: InventoryViewModel = InventoryViewModel(repo: inventoryRepo)
    lazy var alertsViewModel: AlertsViewModel = AlertsViewModel(supabase: supabase, api: apiClient)
}
