import Foundation
import Supabase

@MainActor
final class AppContainer: ObservableObject {

    // ── Supabase ──────────────────────────────────────────────────────────────
    let supabase: SupabaseClient = SupabaseClient(
        supabaseURL: URL(string: SupabaseConfig.url)!,
        supabaseKey: SupabaseConfig.anonKey
    )

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
