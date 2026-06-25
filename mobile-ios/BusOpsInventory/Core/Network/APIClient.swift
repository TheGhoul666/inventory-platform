import Foundation
import Supabase

enum APIError: LocalizedError {
    case invalidURL
    case unauthorized
    case serverError(Int, String)
    case decodingFailed(Error)
    case unknown(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .unauthorized: return "Session expired — please log in again"
        case .serverError(let code, let msg): return "Server error \(code): \(msg)"
        case .decodingFailed(let e): return "Decoding error: \(e.localizedDescription)"
        case .unknown(let e): return e.localizedDescription
        }
    }
}

final class APIClient {
    private let baseURL: URL
    private let supabase: SupabaseClient
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(supabase: SupabaseClient) {
        guard let url = URL(string: Bundle.main.infoDictionary?["API_BASE_URL"] as? String ?? "http://localhost:8000/api/v1") else {
            fatalError("Invalid API_BASE_URL")
        }
        self.baseURL = url
        self.supabase = supabase
        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.encoder = JSONEncoder()
        self.encoder.keyEncodingStrategy = .convertToSnakeCase
    }

    // ── Generic request builder ───────────────────────────────────────────────

    func get<T: Decodable>(_ path: String, queryItems: [URLQueryItem] = []) async throws -> T {
        var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        if !queryItems.isEmpty { components.queryItems = queryItems }
        var request = URLRequest(url: components.url!)
        request.httpMethod = "GET"
        return try await execute(request)
    }

    func post<Body: Encodable, Response: Decodable>(_ path: String, body: Body) async throws -> Response {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.httpBody = try encoder.encode(body)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        return try await execute(request)
    }

    // ── Request executor ──────────────────────────────────────────────────────

    private func execute<T: Decodable>(_ request: URLRequest) async throws -> T {
        var req = request
        // Inject Supabase JWT
        if let session = try? await supabase.auth.session {
            req.setValue("Bearer \(session.accessToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await URLSession.shared.data(for: req)
        guard let http = response as? HTTPURLResponse else { throw APIError.unknown(URLError(.badServerResponse)) }

        switch http.statusCode {
        case 200...299:
            do {
                return try decoder.decode(T.self, from: data)
            } catch {
                throw APIError.decodingFailed(error)
            }
        case 401:
            throw APIError.unauthorized
        default:
            let message = String(data: data, encoding: .utf8) ?? "Unknown"
            throw APIError.serverError(http.statusCode, message)
        }
    }
}

// ── Typed API calls ───────────────────────────────────────────────────────────

extension APIClient {
    func getDashboard() async throws -> DashboardResponse {
        try await get("analytics/dashboard")
    }

    func getInventoryItems(page: Int = 1, search: String? = nil, lowStock: Bool? = nil) async throws -> PaginatedResponse<InventoryItem> {
        var query: [URLQueryItem] = [URLQueryItem(name: "page", value: "\(page)"), URLQueryItem(name: "per_page", value: "50")]
        search.map { query.append(URLQueryItem(name: "search", value: $0)) }
        lowStock.map { query.append(URLQueryItem(name: "low_stock", value: "\($0)")) }
        return try await get("inventory/items", queryItems: query)
    }

    func issueItems(_ request: IssueRequest) async throws -> Transaction {
        try await post("inventory/transactions/issue", body: request)
    }

    func restockItems(_ request: RestockRequest) async throws -> Transaction {
        try await post("inventory/transactions/restock", body: request)
    }

    func getAlerts(status: String? = nil) async throws -> PaginatedResponse<Alert> {
        var query: [URLQueryItem] = [URLQueryItem(name: "per_page", value: "50")]
        status.map { query.append(URLQueryItem(name: "status", value: $0)) }
        return try await get("alerts", queryItems: query)
    }

    func acknowledgeAlert(id: String) async throws -> Alert {
        try await post("alerts/\(id)/acknowledge", body: EmptyBody())
    }

    func getMe() async throws -> User {
        try await get("auth/me")
    }
}

struct EmptyBody: Encodable {}
