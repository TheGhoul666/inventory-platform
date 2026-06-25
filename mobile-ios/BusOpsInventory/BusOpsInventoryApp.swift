import SwiftUI

@main
struct BusOpsInventoryApp: App {

    @StateObject private var container = AppContainer()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(container)
                .environmentObject(container.authViewModel)
                .environmentObject(container.inventoryViewModel)
                .environmentObject(container.alertsViewModel)
        }
    }
}
