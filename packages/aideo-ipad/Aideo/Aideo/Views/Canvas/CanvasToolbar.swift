import SwiftUI

/// 画布底部工具栏
struct CanvasToolbar: View {
    let onAddCard: (BlockType) -> Void
    let onAddOutput: () -> Void
    let onAddReference: () -> Void
    let onAddAI: () -> Void
    let onAutoLayout: () -> Void
    let onClear: () -> Void
    let onTemplates: () -> Void
    let isStoryboard: Bool
    let onToggleStoryboard: () -> Void

    var body: some View {
        HStack(spacing: 8) {
            // 添加节点菜单
            Menu {
                Section("提示词卡片") {
                    ForEach(BlockType.allCases, id: \.rawValue) { type in
                        Button { onAddCard(type) } label: {
                            Label(type.displayName, systemImage: type.iconName)
                        }
                    }
                }
                Section("其他节点") {
                    Button { onAddOutput() } label: {
                        Label("输出节点", systemImage: "play.rectangle")
                    }
                    Button { onAddReference() } label: {
                        Label("参考素材", systemImage: "photo")
                    }
                    Button { onAddAI() } label: {
                        Label("AI 增强", systemImage: "sparkles")
                    }
                }
            } label: {
                Label("添加", systemImage: "plus.square")
                    .font(.subheadline)
            }

            Divider().frame(height: 20)

            Button { onTemplates() } label: {
                Label("模板", systemImage: "square.grid.3x3").font(.subheadline)
            }

            Button { onToggleStoryboard() } label: {
                Label("分镜", systemImage: isStoryboard ? "film.fill" : "film")
                    .font(.subheadline)
            }
            .tint(isStoryboard ? .accentColor : nil)

            Button { onAutoLayout() } label: {
                Label("整理", systemImage: "rectangle.3.group").font(.subheadline)
            }

            Button(role: .destructive) { onClear() } label: {
                Label("清空", systemImage: "trash").font(.subheadline)
            }

            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(.regularMaterial)
    }
}
