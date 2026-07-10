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

/// REST API 客户端 — 封装 aideo-serv 全部接口 (v1 + v2)
actor APIClient {
    let baseURL: String
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(baseURL: String) {
        self.baseURL = baseURL.hasSuffix("/") ? String(baseURL.dropLast()) : baseURL

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 120  // v2: 素材上传可能较大
        self.session = URLSession(configuration: config)

        self.decoder = JSONDecoder()
        self.encoder = JSONEncoder()
    }

    // MARK: - Health

    func healthCheck() async -> HealthInfo? {
        try? await get("/api/v1/health")
    }

    // MARK: - Generate (v2 结构化画布提交)

    /// 结构化画布提交 — 发送完整 subgraph 结构，后端负责序列化
    func generate(request: GenerateRequest) async throws -> GenerateResponse {
        let body = try encoder.asDictionary(request)
        return try await post("/api/v1/generate", body: body)
    }

    // MARK: - Projects (v2)

    func createProject(name: String, canvasData: CanvasData? = nil, metadata: [String: Any]? = nil) async throws -> Project {
        var body: [String: Any] = ["name": name]
        if let canvasData { body["canvas_data"] = try encoder.asDictionary(canvasData) }
        if let metadata { body["metadata"] = metadata }
        return try await post("/api/v1/projects", body: body)
    }

    func listProjects(offset: Int = 0, limit: Int = 20) async throws -> ProjectListResponse {
        try await get("/api/v1/projects?offset=\(offset)&limit=\(limit)")
    }

    func getProject(id: UUID) async throws -> Project {
        try await get("/api/v1/projects/\(id.uuidString)")
    }

    func updateProject(id: UUID, name: String? = nil, canvasData: CanvasData? = nil, metadata: [String: Any]? = nil) async throws -> Project {
        var body: [String: Any] = [:]
        if let name { body["name"] = name }
        if let canvasData { body["canvas_data"] = try encoder.asDictionary(canvasData) }
        if let metadata { body["metadata"] = metadata }
        return try await patch("/api/v1/projects/\(id.uuidString)", body: body)
    }

    func deleteProject(id: UUID) async throws {
        let _: EmptyResponse = try await delete("/api/v1/projects/\(id.uuidString)")
    }

    func listProjectTasks(projectId: UUID, status: TaskStatus? = nil, offset: Int = 0, limit: Int = 20) async throws -> TaskListResponse {
        var query = "?offset=\(offset)&limit=\(limit)"
        if let status { query += "&status=\(status.rawValue)" }
        return try await get("/api/v1/projects/\(projectId.uuidString)/tasks\(query)")
    }

    func listProjectAssets(projectId: UUID, mediaType: String? = nil, offset: Int = 0, limit: Int = 20) async throws -> AssetListResponse {
        var query = "?offset=\(offset)&limit=\(limit)"
        if let mediaType { query += "&media_type=\(mediaType)" }
        return try await get("/api/v1/projects/\(projectId.uuidString)/assets\(query)")
    }

    // MARK: - Assets (v2)

    /// 上传素材文件。返回 Asset 含 asset_id 供 generate 引用。
    func uploadAsset(fileURL: URL, projectId: UUID? = nil, mediaType: String? = nil) async throws -> Asset {
        var fields: [String: String] = [:]
        if let pid = projectId { fields["project_id"] = pid.uuidString }
        if let mt = mediaType { fields["media_type"] = mt }
        return try await upload("/api/v1/assets", fileURL: fileURL, fields: fields)
    }

    func getAsset(id: String) async throws -> Asset {
        try await get("/api/v1/assets/\(id)")
    }

    nonisolated func assetDownloadURL(id: String) -> URL {
        URL(string: "\(baseURL)/api/v1/assets/\(id)/download")!
    }

    func deleteAsset(id: String) async throws {
        let _: EmptyResponse = try await delete("/api/v1/assets/\(id)")
    }

    // MARK: - Image Edit (v2)

    /// 图片编辑：合图/角色替换/局部重绘/风格迁移
    func editImage(request: EditImageRequest) async throws -> EditImageResponse {
        let body = try encoder.asDictionary(request)
        return try await post("/api/v1/canvas/edit-image", body: body)
    }

    /// 图片超分
    func upscaleImage(assetId: String, scale: Int) async throws -> GenerateResponse {
        try await post("/api/v1/canvas/upscale", body: ["asset_id": assetId, "scale": scale])
    }

    // MARK: - Transcript Correction (v2)

    /// 智能纠错 + 繁简转换
    func correctTranscript(text: String, language: String? = nil, aiProvider: String? = nil) async throws -> CorrectResponse {
        var body: [String: Any] = ["text": text]
        if let lang = language { body["language"] = lang }
        if let provider = aiProvider { body["ai_provider"] = provider }
        return try await post("/api/v1/canvas/correct", body: body)
    }

    // MARK: - Canvas Assist (v2)

    /// 自由文本 → 类型化 PromptBlock 数组
    func structurize(description: String, aiProvider: String? = nil, language: String? = nil) async throws -> StructurizeResponse {
        var body: [String: Any] = ["description": description]
        if let provider = aiProvider { body["ai_provider"] = provider }
        if let lang = language { body["language"] = lang }
        return try await post("/api/v1/canvas/structure", body: body)
    }

    /// 上下文补全 — 返回结构化建议组
    func complete(context: String, mode: String = "suggestion", existingBlocks: [PromptBlockDTO]? = nil, aiProvider: String? = nil, language: String? = nil) async throws -> CompletionResponse {
        var body: [String: Any] = ["context": context, "mode": mode]
        if let blocks = existingBlocks { body["existing_blocks"] = try encoder.asDictionary(blocks) }
        if let provider = aiProvider { body["ai_provider"] = provider }
        if let lang = language { body["language"] = lang }
        return try await post("/api/v1/canvas/complete", body: body)
    }

    /// 主题灵感 — 返回含 blocks 的主题列表
    func inspire(theme: String? = nil, aiProvider: String? = nil, language: String? = nil) async throws -> InspireResponse {
        var body: [String: Any] = [:]
        if let theme { body["theme"] = theme }
        if let provider = aiProvider { body["ai_provider"] = provider }
        if let lang = language { body["language"] = lang }
        return try await post("/api/v1/canvas/inspire", body: body)
    }

    // MARK: - AI Providers (v2)

    /// 列出所有已配置的 AI 供应商
    func listAIProviders() async throws -> AIProvidersResponse {
        try await get("/api/v1/ai/providers")
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

    private func patch<T: Decodable>(_ path: String, body: [String: Any]) async throws -> T {
        let url = URL(string: "\(baseURL)\(path)")!
        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
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

    /// Multipart 文件上传
    private func upload<T: Decodable>(_ path: String, fileURL: URL, fields: [String: String]) async throws -> T {
        let url = URL(string: "\(baseURL)\(path)")!
        let boundary = UUID().uuidString

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        request.httpBody = try buildMultipartBody(fileURL: fileURL, fields: fields, boundary: boundary)
        // 上传使用更长超时
        request.timeoutInterval = 120

        return try await perform(request)
    }

    private func buildMultipartBody(fileURL: URL, fields: [String: String], boundary: String) throws -> Data {
        var body = Data()
        let filename = fileURL.lastPathComponent
        let mimeType = mimeTypeFor(fileURL)

        // 文本字段
        for (key, value) in fields {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }

        // 文件字段
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)

        let fileData = try Data(contentsOf: fileURL)
        body.append(fileData)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        return body
    }

    private func mimeTypeFor(_ url: URL) -> String {
        switch url.pathExtension.lowercased() {
        case "jpg", "jpeg": return "image/jpeg"
        case "png": return "image/png"
        case "gif": return "image/gif"
        case "webp": return "image/webp"
        case "mp4": return "video/mp4"
        case "mov": return "video/quicktime"
        case "wav": return "audio/wav"
        default: return "application/octet-stream"
        }
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
            // Try v2 error format first, then v1
            let v2Msg = (try? JSONDecoder().decode(ErrorResponse.self, from: data))?.error.message
            let v1Msg = (try? JSONDecoder().decode([String: String].self, from: data))?["detail"]
            throw APIClientError.requestFailed(statusCode: httpResponse.statusCode, message: v2Msg ?? v1Msg ?? "")
        }

        // Handle 204 No Content
        if T.self == EmptyResponse.self, data.isEmpty {
            return EmptyResponse() as! T
        }

        return try decodeResponse(data, as: T.self)
    }
}

// MARK: - Private Helpers

private struct ErrorResponse: Codable {
    struct ErrorBody: Codable {
        let code: String
        let message: String
    }
    let error: ErrorBody
}

/// 空响应体 — 用于 204 / void 返回
private struct EmptyResponse: Codable {}

// MARK: - JSONEncoder extension

private extension JSONEncoder {
    func asDictionary<T: Encodable>(_ value: T) throws -> [String: Any] {
        let data = try encode(value)
        let obj = try JSONSerialization.jsonObject(with: data)
        guard let dict = obj as? [String: Any] else {
            throw APIClientError.decodingFailed(NSError(domain: "APIClient", code: -1,
                userInfo: [NSLocalizedDescriptionKey: "Encoded value is not a dictionary"]))
        }
        return dict
    }
}
