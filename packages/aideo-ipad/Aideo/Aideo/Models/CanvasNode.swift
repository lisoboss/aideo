import Foundation
import CoreGraphics

/// 画布节点协议
protocol CanvasNode: Identifiable {
    var id: UUID { get }
    var position: CGPoint { get set }
}

/// 统一节点枚举 — 用来在画布上统一管理 4 种节点
enum AnyCanvasNode: Identifiable, Codable, Equatable {
    case promptBlock(PromptBlock)
    case mediaOutput(MediaOutputNode)
    case reference(ReferenceNode)
    case aiEnhance(AIEnhanceNode)

    // MARK: - Identifiable

    var id: UUID {
        switch self {
        case .promptBlock(let n):  n.id
        case .mediaOutput(let n):  n.id
        case .reference(let n):    n.id
        case .aiEnhance(let n):    n.id
        }
    }

    // MARK: - Position

    var position: CGPoint {
        get {
            switch self {
            case .promptBlock(let n):  n.position
            case .mediaOutput(let n):  n.position
            case .reference(let n):    n.position
            case .aiEnhance(let n):    n.position
            }
        }
        set {
            switch self {
            case .promptBlock(var n):
                n.position = newValue
                self = .promptBlock(n)
            case .mediaOutput(var n):
                n.position = newValue
                self = .mediaOutput(n)
            case .reference(var n):
                n.position = newValue
                self = .reference(n)
            case .aiEnhance(var n):
                n.position = newValue
                self = .aiEnhance(n)
            }
        }
    }

    // MARK: - Display

    var displayName: String {
        switch self {
        case .promptBlock(let n):  n.type.displayName
        case .mediaOutput:         "输出"
        case .reference(let n):    n.mediaType == .image ? "参考图" : "参考视频"
        case .aiEnhance:           "AI 增强"
        }
    }

    var iconName: String {
        switch self {
        case .promptBlock(let n):  n.type.iconName
        case .mediaOutput(let n):  n.status.iconName
        case .reference(let n):    n.mediaType == .image ? "photo" : "video"
        case .aiEnhance(let n):
            n.status == .processing ? "sparkles" : "text.bubble"
        }
    }

    var colorHex: String {
        switch self {
        case .promptBlock(let n):  n.colorHex
        case .mediaOutput:         "#2ECC71"
        case .reference:           "#E67E22"
        case .aiEnhance:           "#9B59B6"
        }
    }

    // MARK: - Codable

    enum CodingKeys: String, CodingKey { case type }
    enum NodeType: String, Codable {
        case promptBlock, mediaOutput, reference, aiEnhance
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        // 尝试按顺序解码
        if let node = try? container.decode(PromptBlock.self) {
            self = .promptBlock(node)
        } else if let node = try? container.decode(MediaOutputNode.self) {
            self = .mediaOutput(node)
        } else if let node = try? container.decode(ReferenceNode.self) {
            self = .reference(node)
        } else if let node = try? container.decode(AIEnhanceNode.self) {
            self = .aiEnhance(node)
        } else {
            throw DecodingError.dataCorrupted(
                DecodingError.Context(codingPath: decoder.codingPath, debugDescription: "Unknown node type")
            )
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .promptBlock(let n):  try container.encode(n)
        case .mediaOutput(let n):  try container.encode(n)
        case .reference(let n):    try container.encode(n)
        case .aiEnhance(let n):    try container.encode(n)
        }
    }
}
