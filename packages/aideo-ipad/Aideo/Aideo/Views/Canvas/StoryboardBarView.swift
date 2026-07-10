import SwiftUI

/// 底部故事板时间轴
struct StoryboardBarView: View {
    let scenes: [StoryboardScene]
    let onSelectScene: (Int) -> Void
    let onAutoAssign: () -> Void

    @State private var showAllScenes = false

    var body: some View {
        VStack(spacing: 0) {
            Divider()

            HStack(spacing: 4) {
                Button { onAutoAssign() } label: {
                    Label("自动分镜", systemImage: "rectangle.split.3x1")
                        .font(.caption)
                }
                .buttonStyle(.bordered)
                .controlSize(.small)

                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        if scenes.isEmpty {
                            Text("点击「自动分镜」生成场景")
                                .font(.caption).foregroundStyle(.tertiary)
                                .padding(.horizontal)
                        }

                        ForEach(scenes) { scene in
                            Button {
                                onSelectScene(scene.index)
                            } label: {
                                VStack(spacing: 2) {
                                    Text("S\(scene.index + 1)")
                                        .font(.caption.weight(.bold))
                                    Text("\(scene.cardCount)卡")
                                        .font(.caption2)
                                    Text(scene.summary)
                                        .font(.system(size: 9))
                                        .lineLimit(1)
                                        .frame(width: 70)
                                }
                                .padding(.vertical, 6).padding(.horizontal, 8)
                                .background(
                                    RoundedRectangle(cornerRadius: 8)
                                        .fill(Color(hex: "#4A90D9").opacity(0.15))
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.horizontal, 4)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(.regularMaterial)
        }
    }
}

// MARK: - Scene Model

/// 故事板场景
struct StoryboardScene: Identifiable {
    var id: Int { index }
    let index: Int
    let cardCount: Int
    let summary: String
    let minX: CGFloat       // 画布上最左位置
}

// MARK: - Scene Builder

/// 按水平位置自动分组卡片为场景
enum StoryboardBuilder {
    /// 聚类阈值：同一场景内卡片水平间距不超过此值
    static let clusterThreshold: CGFloat = 300

    /// 根据水平位置自动分组
    static func build(from blocks: [PromptBlock]) -> [StoryboardScene] {
        guard !blocks.isEmpty else { return [] }

        // 按 x 排序
        let sorted = blocks.sorted { $0.position.x < $1.position.x }

        var clusters: [[PromptBlock]] = []
        var current: [PromptBlock] = [sorted[0]]

        for block in sorted.dropFirst() {
            let lastX = current.last!.position.x
            if block.position.x - lastX < clusterThreshold {
                current.append(block)
            } else {
                clusters.append(current)
                current = [block]
            }
        }
        clusters.append(current)

        return clusters.enumerated().map { idx, group in
            let summary = group.prefix(2).map { $0.content }.joined(separator: " ")
            return StoryboardScene(
                index: idx,
                cardCount: group.count,
                summary: String(summary.prefix(20)),
                minX: group.first!.position.x
            )
        }
    }
}
