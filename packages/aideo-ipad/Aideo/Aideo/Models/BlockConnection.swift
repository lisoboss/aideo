import Foundation

/// 通用连线 — 任意画布节点之间
struct BlockConnection: Identifiable, Codable, Equatable {
    var id: UUID = UUID()
    var sourceId: UUID   // 任意 CanvasNode.id
    var targetId: UUID   // 任意 CanvasNode.id
}
