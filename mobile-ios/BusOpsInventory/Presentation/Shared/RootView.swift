import SwiftUI

struct RootView: View {
    @EnvironmentObject var authVM: AuthViewModel
    @EnvironmentObject var container: AppContainer

    var body: some View {
        if authVM.isLoggedIn {
            MainTabView()
        } else {
            LoginView()
        }
    }
}

struct MainTabView: View {
    @EnvironmentObject var inventoryVM: InventoryViewModel
    @EnvironmentObject var alertsVM: AlertsViewModel
    @EnvironmentObject var container: AppContainer

    var body: some View {
        TabView {
            DashboardView(
                supabase: container.supabase,
                onNavigateToInventory: {},
                onNavigateToAlerts: {},
            )
            .tabItem { Label("לוח בקרה", systemImage: "square.grid.2x2") }

            InventoryListView()
                .tabItem { Label("מלאי", systemImage: "archivebox") }

            AlertsView()
                .tabItem { Label("התראות", systemImage: "bell") }
        }
        .environment(\.layoutDirection, .rightToLeft)
    }
}
