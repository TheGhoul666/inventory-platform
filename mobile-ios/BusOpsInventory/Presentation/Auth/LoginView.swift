import SwiftUI

@MainActor
final class AuthViewModel: ObservableObject {
    @Published var email = ""
    @Published var password = ""
    @Published var isLoading = false
    @Published var error: String? = nil
    @Published var isLoggedIn = false

    private let repo: AuthRepository

    init(repo: AuthRepository) {
        self.repo = repo
        self.isLoggedIn = repo.isLoggedIn
        // Mirror repository state
        repo.$isLoggedIn.assign(to: &$isLoggedIn)
    }

    func login() {
        guard !email.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        isLoading = true
        error = nil
        Task {
            do {
                try await repo.login(email: email.trimmingCharacters(in: .whitespaces), password: password)
            } catch {
                self.error = error.localizedDescription
            }
            isLoading = false
        }
    }

    func logout() {
        Task { try? await repo.logout() }
    }
}

struct LoginView: View {
    @EnvironmentObject var viewModel: AuthViewModel
    @State private var showPassword = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Spacer()

                // Logo
                VStack(spacing: 8) {
                    Image(systemName: "bus.fill")
                        .font(.system(size: 56))
                        .foregroundStyle(.blue)
                    Text("BusOps מלאי")
                        .font(.largeTitle).bold()
                    Text("פלטפורמת ניהול תחזוקה")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                Spacer().frame(height: 48)

                // Form
                VStack(spacing: 16) {
                    TextField("אימייל", text: $viewModel.email)
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .textFieldStyle(.roundedBorder)

                    HStack {
                        Group {
                            if showPassword {
                                TextField("סיסמה", text: $viewModel.password)
                            } else {
                                SecureField("סיסמה", text: $viewModel.password)
                            }
                        }
                        .textFieldStyle(.roundedBorder)

                        Button(action: { showPassword.toggle() }) {
                            Image(systemName: showPassword ? "eye.slash" : "eye")
                                .foregroundStyle(.secondary)
                        }
                    }

                    if let error = viewModel.error {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                    }

                    Button(action: viewModel.login) {
                        if viewModel.isLoading {
                            ProgressView()
                                .frame(maxWidth: .infinity)
                        } else {
                            Text("התחבר")
                                .frame(maxWidth: .infinity)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                    .disabled(viewModel.isLoading)
                }
                .padding(.horizontal, 32)

                Spacer()

                Text("Powered by Supabase · Bus Inventory Platform v1.0")
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
                    .padding(.bottom, 16)
            }
            .environment(\.layoutDirection, .rightToLeft)
        }
    }
}
