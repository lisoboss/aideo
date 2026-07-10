import Foundation

/// 画布卡片 → 提示词字符串
enum PromptSerializer {

    /// 将卡片列表序列化为提交给后端的 prompt 字符串
    /// 按 block type 分组：场景 → 角色 → 动作 → 风格 → 镜头 → 氛围 → 自定义
    static func serialize(_ blocks: [PromptBlock]) -> String {
        let ordered: [BlockType] = [.scene, .character, .action, .style, .camera, .mood, .custom]
        var parts: [String] = []

        let grouped = Dictionary(grouping: blocks.filter { !$0.content.isEmpty }) { $0.type }

        for type in ordered {
            guard let blocks = grouped[type] else { continue }
            let texts = blocks.map { $0.content }
            parts.append("[\(type.displayName)]: \(texts.joined(separator: "；"))")
        }

        // 处理不在标准顺序中的 block types（如果枚举扩展了）
        for (type, blocks) in grouped where !ordered.contains(type) {
            let texts = blocks.map { $0.content }
            parts.append("[\(type.displayName)]: \(texts.joined(separator: "；"))")
        }

        return parts.joined(separator: "\n")
    }
}
