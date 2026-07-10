import Foundation

/// 任务状态枚举，与后端 TaskStatus 对齐
enum TaskStatus: String, Codable, CaseIterable {
    case queued
    case running
    case generating
    case completed
    case failed
    case cancelled

    /// 显示名称
    var displayName: String {
        switch self {
        case .queued:     "排队中"
        case .running:    "运行中"
        case .generating: "生成中"
        case .completed:  "已完成"
        case .failed:     "失败"
        case .cancelled:  "已取消"
        }
    }

    /// SF Symbol 图标
    var iconName: String {
        switch self {
        case .queued:     "hourglass"
        case .running:    "play.circle"
        case .generating: "wand.and.stars"
        case .completed:  "checkmark.circle.fill"
        case .failed:     "xmark.circle.fill"
        case .cancelled:  "slash.circle"
        }
    }

    /// 是否终态
    var isTerminal: Bool {
        self == .completed || self == .failed || self == .cancelled
    }
}

/// 任务模型，对应后端 GenerationTask
struct TaskModel: Identifiable, Codable, Equatable, Sendable {
    let id: UUID
    var prompt: String
    var params: GenerationParams?
    var status: TaskStatus
    var progress: Double
    var createdAt: Date
    var updatedAt: Date
    var resultPath: String?
    var resultURL: URL?
    var previews: [String]
    var errorMessage: String?

    // v2: 结构化提交 & 项目关联
    var projectId: UUID?
    var outputNodeId: UUID?
    var promptStructured: [String: AnyCodable]?

    enum CodingKeys: String, CodingKey {
        case id, prompt, params, status, progress
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case resultPath = "result_path"
        case resultURL = "result_url"
        case previews
        case errorMessage = "error_message"
        case projectId = "project_id"
        case outputNodeId = "output_node_id"
        case promptStructured = "prompt_structured"
    }

    static func == (lhs: TaskModel, rhs: TaskModel) -> Bool {
        lhs.id == rhs.id
    }
}

/// 任务列表响应
struct TaskListResponse: Codable, Sendable {
    let tasks: [TaskModel]
    let total: Int
    let offset: Int
    let limit: Int
}
