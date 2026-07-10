import Foundation
import CoreGraphics

// MARK: - Content Type

/// 节点输出内容类型
enum NodeContentType: String, Codable {
    case text
    case image
    case video

    var iconName: String {
        switch self {
        case .text:  "text.alignleft"
        case .image: "photo"
        case .video: "play.rectangle"
        }
    }

    var displayName: String {
        switch self {
        case .text:  "文本"
        case .image: "图片"
        case .video: "视频"
        }
    }
}

// MARK: - Status

enum OutputStatus: String, Codable {
    case idle
    case generating
    case completed
    case failed

    var displayName: String {
        switch self {
        case .idle: "就绪"; case .generating: "生成中"
        case .completed: "已完成"; case .failed: "失败"
        }
    }

    var iconName: String {
        switch self {
        case .idle: "play.rectangle"; case .generating: "wand.and.stars"
        case .completed: "checkmark.rectangle"; case .failed: "xmark.rectangle"
        }
    }
}

// MARK: - Result Node

/// 结果节点 — 产出文本/图片/视频，可连入下游节点作为输入
struct MediaOutputNode: Identifiable, Codable, Equatable {
    var id: UUID = UUID()
    var position: CGPoint = .zero
    var nodeSize: CGSize = CGSize(width: 210, height: 140)

    /// 产出类型
    var contentType: NodeContentType = .video

    /// 任务 ID（生成时关联）
    var taskId: UUID?
    var status: OutputStatus = .idle
    var progress: Double = 0
    var errorMessage: String?
    var promptSummary: String = ""
    var previewFrames: [String] = []

    /// 产出内容
    var textContent: String = ""       // .text 类型
    var imageLocalPath: String = ""    // .image 类型
    var videoLocalPath: String = ""    // .video 类型

    /// 把当前产出作为下一个节点的输入文本
    var asInputText: String {
        switch contentType {
        case .text:  return textContent
        case .image: return "[参考图片: \(imageLocalPath)]"
        case .video: return "[参考视频: \(videoLocalPath)]"
        }
    }

    var hasOutput: Bool {
        switch contentType {
        case .text:  return !textContent.isEmpty
        case .image: return !imageLocalPath.isEmpty
        case .video: return !videoLocalPath.isEmpty
        }
    }

    // MARK: - Init

    init(id: UUID = UUID(), position: CGPoint = .zero, nodeSize: CGSize = CGSize(width: 210, height: 140),
         contentType: NodeContentType = .video, taskId: UUID? = nil, status: OutputStatus = .idle, videoLocalPath: String? = nil,
         previewFrames: [String] = [], promptSummary: String = "", progress: Double = 0,
         errorMessage: String? = nil, textContent: String = "", imageLocalPath: String = "") {
        self.id = id; self.position = position; self.nodeSize = nodeSize; self.contentType = contentType
        self.taskId = taskId; self.status = status
        self.videoLocalPath = videoLocalPath ?? ""
        self.previewFrames = previewFrames; self.promptSummary = promptSummary
        self.progress = progress; self.errorMessage = errorMessage
        self.textContent = textContent; self.imageLocalPath = imageLocalPath
    }

    // MARK: - Codable

    enum CodingKeys: String, CodingKey {
        case id, contentType, taskId, status, progress, errorMessage
        case promptSummary, previewFrames
        case textContent, imageLocalPath, videoLocalPath
        case x, y, w, h
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(UUID.self, forKey: .id)
        contentType = try c.decodeIfPresent(NodeContentType.self, forKey: .contentType) ?? .video
        taskId = try c.decodeIfPresent(UUID.self, forKey: .taskId)
        status = try c.decode(OutputStatus.self, forKey: .status)
        progress = try c.decode(Double.self, forKey: .progress)
        errorMessage = try c.decodeIfPresent(String.self, forKey: .errorMessage)
        promptSummary = try c.decode(String.self, forKey: .promptSummary)
        previewFrames = try c.decode([String].self, forKey: .previewFrames)
        textContent = try c.decodeIfPresent(String.self, forKey: .textContent) ?? ""
        imageLocalPath = try c.decodeIfPresent(String.self, forKey: .imageLocalPath) ?? ""
        videoLocalPath = try c.decodeIfPresent(String.self, forKey: .videoLocalPath) ?? ""
        let x = try c.decode(CGFloat.self, forKey: .x)
        let y = try c.decode(CGFloat.self, forKey: .y)
        position = CGPoint(x: x, y: y)
        let w = try c.decodeIfPresent(CGFloat.self, forKey: .w) ?? 210
        let h = try c.decodeIfPresent(CGFloat.self, forKey: .h) ?? 140
        nodeSize = CGSize(width: w, height: h)
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(id, forKey: .id)
        try c.encode(contentType, forKey: .contentType)
        try c.encodeIfPresent(taskId, forKey: .taskId)
        try c.encode(status, forKey: .status)
        try c.encode(progress, forKey: .progress)
        try c.encodeIfPresent(errorMessage, forKey: .errorMessage)
        try c.encode(promptSummary, forKey: .promptSummary)
        try c.encode(previewFrames, forKey: .previewFrames)
        try c.encode(textContent, forKey: .textContent)
        try c.encode(imageLocalPath, forKey: .imageLocalPath)
        try c.encode(videoLocalPath, forKey: .videoLocalPath)
        try c.encode(position.x, forKey: .x)
        try c.encode(position.y, forKey: .y)
        try c.encode(nodeSize.width, forKey: .w)
        try c.encode(nodeSize.height, forKey: .h)
    }
}
