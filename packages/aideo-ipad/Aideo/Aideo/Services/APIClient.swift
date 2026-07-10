import Foundation

// MARK: - Errors

enum APIClientError: LocalizedError {
    case invalidURL
    case requestFailed(statusCode: Int, message: String)
    case decodingFailed(Error)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:                    "无效的服务器地址"
        case .requestFailed(let code, _):    "请求失败 (\(code))"
        case .decodingFailed:                "数据解析失败"
        case .networkError(let e):           e.localizedDescription
        }
    }
}

// MARK: - Client

/// REST API 客户端 — 封装 aideo-serv 全部接口
actor APIClient {
    let baseURL: String
    private let session: URLSession
    private let decoder: JSONDecoder

    init(baseURL: String) {
        self.baseURL = baseURL.hasSuffix("/") ? String(baseURL.dropLast()) : baseURL

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: config)

        self.decoder = JSONDecoder()
    }

    // MARK: - Health

    func healthCheck() async -> Bool {
        do {
            let _: [String: String] = try await get("/api/v1/health")
            return true
        } catch {
            return false
        }
    }

    // MARK: - Tasks

    func createTask(prompt: String, params: GenerationParams? = nil, extraParams: [String: Any] = [:]) async throws -> TaskModel {
        var body: [String: Any] = ["prompt": prompt]
        var mergedParams: [String: Any] = params?.asDictionary() ?? [:]
        for (k, v) in extraParams { mergedParams[k] = v }
        if !mergedParams.isEmpty { body["params"] = mergedParams }
        return try await post("/api/v1/tasks", body: body)
    }

    func listTasks(status: TaskStatus? = nil, offset: Int = 0, limit: Int = 20) async throws -> TaskListResponse {
        var query = "?offset=\(offset)&limit=\(limit)"
        if let status {
            query += "&status=\(status.rawValue)"
        }
        return try await get("/api/v1/tasks\(query)")
    }

    func getTask(id: UUID) async throws -> TaskModel {
        try await get("/api/v1/tasks/\(id.uuidString)")
    }

    func cancelTask(id: UUID) async throws -> TaskModel {
        try await delete("/api/v1/tasks/\(id.uuidString)")
    }

    // MARK: - Assist

    func structurize(description: String) async throws -> StructurizeResponse {
        try await post("/api/v1/assist/structure", body: ["description": description])
    }

    func complete(context: String, mode: String = "suggestion") async throws -> CompletionResponse {
        try await post("/api/v1/assist/complete", body: ["context": context, "mode": mode])
    }

    func inspire(theme: String? = nil) async throws -> InspireResponse {
        var body: [String: Any] = [:]
        if let theme { body["theme"] = theme }
        return try await post("/api/v1/assist/inspire", body: body)
    }

    // MARK: - Results

    nonisolated func downloadURL(taskId: UUID) -> URL {
        URL(string: "\(baseURL)/api/v1/results/\(taskId.uuidString)/download")!
    }

    nonisolated func previewURL(taskId: UUID, frame: String) -> URL {
        URL(string: "\(baseURL)/api/v1/results/\(taskId.uuidString)/preview/\(frame)")!
    }

    // MARK: - HTTP Helpers

    private func get<T: Decodable>(_ path: String) async throws -> T {
        let url = URL(string: "\(baseURL)\(path)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        return try await perform(request)
    }

    private func post<T: Decodable>(_ path: String, body: [String: Any]) async throws -> T {
        let url = URL(string: "\(baseURL)\(path)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        return try await perform(request)
    }

    private func delete<T: Decodable>(_ path: String) async throws -> T {
        let url = URL(string: "\(baseURL)\(path)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        return try await perform(request)
    }

    /// Nonisolated decode helper — avoids @MainActor inference for model types
    private nonisolated func decodeResponse<T: Decodable>(_ data: Data, as type: T.Type) throws -> T {
        try JSONDecoder().decode(type, from: data)
    }

    private func perform<T: Decodable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.networkError(URLError(.badServerResponse))
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            let message = (try? JSONDecoder().decode([String: String].self, from: data))?["detail"] ?? ""
            throw APIClientError.requestFailed(statusCode: httpResponse.statusCode, message: message)
        }

        return try decodeResponse(data, as: T.self)
    }
}
