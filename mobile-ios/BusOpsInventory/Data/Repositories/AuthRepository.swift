import Foundation
import Supabase
import Auth

@MainActor
final class AuthRepository: ObservableObject {
    @Published var currentUser: User? = nil
    @Published var isLoggedIn: Bool = false

    private let supabase: SupabaseClient

    init(supabase: SupabaseClient) {
        self.supabase = supabase
        Task { await restoreSession() }
    }

    func login(email: String, password: String) async throws {
        try await supabase.auth.signIn(email: email, password: password)
        isLoggedIn = true
    }

    func logout() async throws {
        try await supabase.auth.signOut()
        currentUser = nil
        isLoggedIn = false
    }

    func restoreSession() async {
        do {
            _ = try await supabase.auth.session
            isLoggedIn = true
        } catch {
            isLoggedIn = false
        }
    }

    func currentAccessToken() async -> String? {
        try? await supabase.auth.session.accessToken
    }
}
