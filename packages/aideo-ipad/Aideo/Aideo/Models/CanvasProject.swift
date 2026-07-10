import Foundation
import SwiftData

/// SwiftData 画布项目模型
@Model
final class CanvasProject {
    var id: UUID
    var name: String
    var createdAt: Date
    var updatedAt: Date

    /// 各类型节点 JSON 存储
    var promptBlocksJSON: String
    var mediaOutputsJSON: String
    var referenceNodesJSON: String
    var aiEnhanceNodesJSON: String

    /// 连线 JSON 存储
    var connectionsJSON: String

    // MARK: - Init

    init(
        id: UUID = UUID(),
        name: String = "未命名项目",
        promptBlocks: [PromptBlock] = [],
        mediaOutputs: [MediaOutputNode] = [],
        referenceNodes: [ReferenceNode] = [],
        aiEnhanceNodes: [AIEnhanceNode] = [],
        connections: [BlockConnection] = []
    ) {
        self.id = id
        self.name = name
        self.createdAt = Date()
        self.updatedAt = Date()
        self.promptBlocksJSON = Self.encode(promptBlocks)
        self.mediaOutputsJSON = Self.encode(mediaOutputs)
        self.referenceNodesJSON = Self.encode(referenceNodes)
        self.aiEnhanceNodesJSON = Self.encode(aiEnhanceNodes)
        self.connectionsJSON = Self.encode(connections)
    }

    // MARK: - JSON Accessors

    var promptBlocks: [PromptBlock] {
        get { Self.decode(promptBlocksJSON) }
        set { promptBlocksJSON = Self.encode(newValue); touch() }
    }

    var mediaOutputs: [MediaOutputNode] {
        get { Self.decode(mediaOutputsJSON) }
        set { mediaOutputsJSON = Self.encode(newValue); touch() }
    }

    var referenceNodes: [ReferenceNode] {
        get { Self.decode(referenceNodesJSON) }
        set { referenceNodesJSON = Self.encode(newValue); touch() }
    }

    var aiEnhanceNodes: [AIEnhanceNode] {
        get { Self.decode(aiEnhanceNodesJSON) }
        set { aiEnhanceNodesJSON = Self.encode(newValue); touch() }
    }

    var connections: [BlockConnection] {
        get { Self.decode(connectionsJSON) }
        set { connectionsJSON = Self.encode(newValue); touch() }
    }

    /// 所有节点统一列表
    var allNodes: [AnyCanvasNode] {
        promptBlocks.map(AnyCanvasNode.promptBlock) +
        mediaOutputs.map(AnyCanvasNode.mediaOutput) +
        referenceNodes.map(AnyCanvasNode.reference) +
        aiEnhanceNodes.map(AnyCanvasNode.aiEnhance)
    }

    /// 节点总数
    var nodeCount: Int {
        promptBlocks.count + mediaOutputs.count + referenceNodes.count + aiEnhanceNodes.count
    }

    // MARK: - Helpers

    private func touch() {
        updatedAt = Date()
    }

    private static func encode<T: Encodable>(_ value: T) -> String {
        guard let data = try? JSONEncoder().encode(value) else { return "[]" }
        return String(data: data, encoding: .utf8) ?? "[]"
    }

    private static func decode<T: Decodable>(_ json: String) -> T {
        guard let data = json.data(using: .utf8),
              let value = try? JSONDecoder().decode(T.self, from: data)
        else {
            // 安全回退：JSON 为空/损坏时返回空数组（所有 node 字段都是数组类型）
            return "[]".data(using: .utf8).flatMap { try? JSONDecoder().decode(T.self, from: $0) }!
        }
        return value
    }
}
