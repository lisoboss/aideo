import Foundation

// MARK: - DTOs (Data Transfer Objects)

/// 画布 PromptBlock → API 提交格式
struct PromptBlockDTO: Codable, Sendable {
    let id: String
    let type: String
    let content: String
    let scene_tag: Int?
    let params: GenerationParams?

    init(from block: PromptBlock) {
        self.id = block.id.uuidString
        self.type = block.type.rawValue
        self.content = block.content
        self.scene_tag = block.sceneTag
        self.params = block.params.isEmpty ? nil : block.params
    }
}

/// 连线 → API 提交格式
struct BlockConnectionDTO: Codable, Sendable {
    let source_id: String
    let target_id: String

    init(from conn: BlockConnection) {
        self.source_id = conn.sourceId.uuidString
        self.target_id = conn.targetId.uuidString
    }
}

/// 已上传素材引用
struct ReferenceAssetDTO: Codable, Sendable {
    let asset_id: String
    let usage: String?
}

/// 上游输出节点结果
struct UpstreamResultDTO: Codable, Sendable {
    let node_id: String
    let content_type: String
    var text: String?
    var asset_id: String?
}

// MARK: - Generate (结构化画布提交)

struct GenerateRequest: Codable, Sendable {
    let project_id: String?
    let output_node_id: String
    let output_content_type: String
    let blocks: [PromptBlockDTO]
    let connections: [BlockConnectionDTO]
    var reference_assets: [ReferenceAssetDTO] = []
    var upstream_context: [UpstreamResultDTO] = []
    var ai_enhance_context: [String] = []
    var output_params: GenerationParams? = nil
    var ai_provider: String? = nil
    var language: String? = nil  // 生成文本主语言（zh/en/ja/ko），nil=自动

    enum CodingKeys: String, CodingKey {
        case project_id, output_node_id, output_content_type
        case blocks, connections
        case reference_assets, upstream_context, ai_enhance_context
        case output_params, ai_provider, language
    }
}

struct GenerateResponse: Codable, Sendable {
    let task_id: String
    let task: TaskModel
}

// MARK: - Project

struct Project: Codable, Identifiable, Sendable {
    let id: String
    var name: String
    var canvas_data: CanvasData?
    var metadata: [String: AnyCodable]?
    var task_count: Int
    let created_at: String
    let updated_at: String
}

struct CanvasData: Codable, Sendable {
    var prompt_blocks: [PromptBlockDTO]
    var media_outputs: [MediaOutputDTO]
    var reference_nodes: [ReferenceNodeDTO]
    var ai_enhance_nodes: [AIEnhanceDTO]
    var connections: [BlockConnectionDTO]
    var viewport: ViewportState?
}

struct MediaOutputDTO: Codable, Sendable {
    let id: String
    let position: CGPointDTO
    let content_type: String
    let task_id: String?
    let status: String
    let progress: Double
    let prompt_summary: String
    let preview_frames: [String]
}

struct ReferenceNodeDTO: Codable, Sendable {
    let id: String
    let position: CGPointDTO
    let media_type: String
    let source_label: String
}

struct AIEnhanceDTO: Codable, Sendable {
    let id: String
    let position: CGPointDTO
    let input_text: String
    let output_text: String
    let status: String
}

struct CGPointDTO: Codable, Sendable {
    let x: Double
    let y: Double
}

struct ViewportState: Codable, Sendable {
    let center_x: Double
    let center_y: Double
    let scale: Double
}

struct ProjectListResponse: Codable, Sendable {
    let items: [Project]
    let total: Int
    let offset: Int
    let limit: Int
}

// MARK: - Asset

struct Asset: Codable, Identifiable, Sendable {
    let id: String
    let project_id: String?
    let filename: String
    let content_type: String
    let size: Int
    let media_type: String
    let uploaded_at: String
    let url: String
    let metadata: [String: AnyCodable]?
}

struct AssetListResponse: Codable, Sendable {
    let items: [Asset]
    let total: Int
    let offset: Int
    let limit: Int
}

// MARK: - Health

struct HealthInfo: Codable, Sendable {
    let status: String
    let version: String?
    let services: [String: String]?
}

// MARK: - Image Edit

struct MaskRegion: Codable, Sendable {
    let x: Double       // 相对坐标 0.0-1.0
    let y: Double
    let width: Double
    let height: Double
    let label: String?  // 区域标签（如 "character_A"）
}

struct EditImageRequest: Codable, Sendable {
    let project_id: String?
    let mode: String                // composite | replace_character | inpainting | style_transfer
    let base_image: String          // asset_id
    var reference_images: [String] = []  // asset_id[]
    var mask_regions: [MaskRegion] = []
    var prompt_blocks: [PromptBlockDTO] = []
    var language: String?
    var ai_provider: String?
}

struct EditImageResponse: Codable, Sendable {
    let task_id: String
    let task: TaskModel
}

struct UpscaleRequest: Codable, Sendable {
    let asset_id: String
    let scale: Int  // 2, 4
}

// MARK: - Transcript Correction

struct CorrectRequest: Codable, Sendable {
    let text: String
    let language: String?
    let ai_provider: String?
}

struct CorrectResponse: Codable, Sendable {
    let corrected: String
}

// MARK: - AI Providers

struct AIProvider: Codable, Sendable {
    let name: String
    let model: String
    let is_default: Bool
}

struct AIProvidersResponse: Codable, Sendable {
    let providers: [AIProvider]
    let `default`: String
}

// MARK: - Project WebSocket Events (v2 typed)

enum ProjectWSEventType: String, Codable, Sendable {
    case connected
    case taskStatus = "task.status"
    case taskProgress = "task.progress"
    case taskPreview = "task.preview"
    case taskCompleted = "task.completed"
    case taskFailed = "task.failed"
    case taskCancelled = "task.cancelled"
    case error
}

// MARK: Payloads

struct ConnectedPayload: Codable, Sendable {
    let project_id: String
    let snapshot: ActiveTasksSnapshot
}

struct ActiveTasksSnapshot: Codable, Sendable {
    let active_tasks: [ActiveTaskInfo]
}

struct ActiveTaskInfo: Codable, Sendable {
    let task_id: String
    let output_node_id: String?
    let status: String
    let progress: Double
    let previews: [String]
    let error_message: String?
}

struct TaskStatusPayload: Codable, Sendable {
    let task_id: String
    let output_node_id: String?
    let status: String
    let timestamp: String?
}

struct TaskProgressPayload: Codable, Sendable {
    let task_id: String
    let output_node_id: String?
    let progress: Double
    let message: String?
    let timestamp: String?
}

struct TaskPreviewPayload: Codable, Sendable {
    let task_id: String
    let output_node_id: String?
    let frame_url: String
    let frame_index: Int?   // 后端当前不下发；文档保留，客户端容忍缺失
    let timestamp: String?
}

struct TaskCompletedPayload: Codable, Sendable {
    let task_id: String
    let output_node_id: String?
    let result_url: String?
    let result_data: [String: AnyCodable]?
    let previews: [String]
    let timestamp: String?
}

struct TaskFailedPayload: Codable, Sendable {
    let task_id: String
    let output_node_id: String?
    let error_message: String?
    let timestamp: String?
}

struct TaskCancelledPayload: Codable, Sendable {
    let task_id: String
    let output_node_id: String?
    let timestamp: String?
}

struct ErrorPayload: Codable, Sendable {
    let code: String
    let message: String
    let timestamp: String?
}

// MARK: - ProjectWSEvent (enum wrapper)

/// v2 类型化 WebSocket 事件 — 用于 ws/projects/{id}
enum ProjectWSEvent: Sendable {
    case connected(ConnectedPayload)
    case taskStatus(TaskStatusPayload)
    case taskProgress(TaskProgressPayload)
    case taskPreview(TaskPreviewPayload)
    case taskCompleted(TaskCompletedPayload)
    case taskFailed(TaskFailedPayload)
    case taskCancelled(TaskCancelledPayload)
    case error(ErrorPayload)

    /// 关联的 task_id（如有）
    var taskId: String? {
        switch self {
        case .taskStatus(let p):    p.task_id
        case .taskProgress(let p):  p.task_id
        case .taskPreview(let p):   p.task_id
        case .taskCompleted(let p): p.task_id
        case .taskFailed(let p):    p.task_id
        case .taskCancelled(let p): p.task_id
        case .connected, .error:    nil
        }
    }

    /// 关联的 output_node_id（如有）
    var outputNodeId: String? {
        switch self {
        case .taskStatus(let p):    p.output_node_id
        case .taskProgress(let p):  p.output_node_id
        case .taskPreview(let p):   p.output_node_id
        case .taskCompleted(let p): p.output_node_id
        case .taskFailed(let p):    p.output_node_id
        case .taskCancelled(let p): p.output_node_id
        case .connected, .error:    nil
        }
    }

    /// 是否终态事件
    var isTerminal: Bool {
        switch self {
        case .taskCompleted, .taskFailed, .taskCancelled, .error: true
        default: false
        }
    }
}

// MARK: - ProjectWSEvent Decoding

/// ProjectWSEvent 的 Codable 解码器。从 JSON 的 `event` 字段判断类型，decode 对应 payload。
struct ProjectWSEventDecoder {
    private let decoder = JSONDecoder()

    func decode(from text: String) -> ProjectWSEvent? {
        guard let data = text.data(using: .utf8),
              let raw = try? decoder.decode(RawProjectWSEvent.self, from: data) else {
            return nil
        }
        return raw.toEvent(with: decoder, rawData: data)
    }
}

/// 原始 JSON 结构：先解析 event 字段，再按类型解析 payload
private struct RawProjectWSEvent: Codable {
    let event: String
    // 其他字段保留在后续 full-decode 中使用
}

private extension RawProjectWSEvent {
    func toEvent(with decoder: JSONDecoder, rawData: Data) -> ProjectWSEvent? {
        switch event {
        case "connected":
            return (try? decoder.decode(EventWrapper<ConnectedPayload>.self, from: rawData))
                .map { .connected($0.payload) }
        case "task.status":
            return (try? decoder.decode(EventWrapper<TaskStatusPayload>.self, from: rawData))
                .map { .taskStatus($0.payload) }
        case "task.progress":
            return (try? decoder.decode(EventWrapper<TaskProgressPayload>.self, from: rawData))
                .map { .taskProgress($0.payload) }
        case "task.preview":
            return (try? decoder.decode(EventWrapper<TaskPreviewPayload>.self, from: rawData))
                .map { .taskPreview($0.payload) }
        case "task.completed":
            return (try? decoder.decode(EventWrapper<TaskCompletedPayload>.self, from: rawData))
                .map { .taskCompleted($0.payload) }
        case "task.failed":
            return (try? decoder.decode(EventWrapper<TaskFailedPayload>.self, from: rawData))
                .map { .taskFailed($0.payload) }
        case "task.cancelled":
            return (try? decoder.decode(EventWrapper<TaskCancelledPayload>.self, from: rawData))
                .map { .taskCancelled($0.payload) }
        case "error":
            return (try? decoder.decode(EventWrapper<ErrorPayload>.self, from: rawData))
                .map { .error($0.payload) }
        default:
            return nil
        }
    }
}

/// 将 payload 包装为包含 event + 所有 payload 字段的完整 JSON 结构
private struct EventWrapper<P: Codable>: Codable {
    let event: String
    // Flatten: payload 字段与 event 同级
    let payload: P

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: RawCodingKey.self)
        self.event = try container.decode(String.self, forKey: RawCodingKey(stringValue: "event"))
        self.payload = try P(from: decoder)
    }

    func encode(to encoder: Encoder) throws {
        try payload.encode(to: encoder)
        var container = encoder.container(keyedBy: RawCodingKey.self)
        try container.encode(event, forKey: RawCodingKey(stringValue: "event"))
    }
}

private struct RawCodingKey: CodingKey {
    let stringValue: String
    let intValue: Int? = nil
    init(stringValue: String) { self.stringValue = stringValue }
    init?(intValue: Int) { nil }
}
