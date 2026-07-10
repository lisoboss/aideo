import SwiftUI

/// 画布上的单张提示词卡片 — 可拖拽 + 可调整大小
struct PromptCardView: View {
    let block: PromptBlock
    let isEditing: Bool
    let isConnecting: Bool
    let isConnectMode: Bool
    let onTap: () -> Void
    let onDelete: () -> Void
    let onConnect: () -> Void
    let onDrag: (CGPoint) -> Void
    let onResize: (CGSize) -> Void
    let canvasScale: CGFloat

    @State private var dragOffset: CGSize = .zero
    @State private var isResizing = false
    @State private var resizeStart: CGSize = .zero
    @State private var currentSize: CGSize

    init(block: PromptBlock, isEditing: Bool, isConnecting: Bool, isConnectMode: Bool,
         onTap: @escaping () -> Void, onDelete: @escaping () -> Void,
         onConnect: @escaping () -> Void, onDrag: @escaping (CGPoint) -> Void,
         onResize: @escaping (CGSize) -> Void, canvasScale: CGFloat) {
        self.block = block; self.isEditing = isEditing
        self.isConnecting = isConnecting; self.isConnectMode = isConnectMode
        self.onTap = onTap; self.onDelete = onDelete; self.onConnect = onConnect
        self.onDrag = onDrag; self.onResize = onResize; self.canvasScale = canvasScale
        _currentSize = State(initialValue: block.cardSize)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            // 头部
            HStack {
                Label(block.type.displayName, systemImage: block.type.iconName)
                    .font(.caption2).foregroundStyle(.white.opacity(0.9))
                Spacer()
                Button(action: onConnect) {
                    Image(systemName: "arrow.triangle.pull")
                        .font(.caption).foregroundStyle(.white.opacity(0.5))
                        .padding(4).background(Circle().fill(.white.opacity(isConnecting ? 0.3 : 0.1)))
                }.buttonStyle(.plain)
                Button(action: onDelete) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.caption).foregroundStyle(.white.opacity(0.6))
                }.buttonStyle(.plain)
            }

            // 内容
            Text(block.content.isEmpty ? "点击编辑..." : block.content)
                .font(.caption)
                .foregroundStyle(block.content.isEmpty ? .white.opacity(0.5) : .white)
                .lineLimit(20)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            Spacer(minLength: 0)
        }
        .padding(10)
        .frame(width: max(currentSize.width, 100), height: max(currentSize.height, 80))
        .background(RoundedRectangle(cornerRadius: 10).fill(Color(hex: block.colorHex)))
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(strokeColor, lineWidth: isConnecting ? 3 : (isEditing ? 2 : 0))
        )
        .overlay(alignment: .bottomTrailing) {
            // 缩放把手
            Image(systemName: "arrow.up.backward.and.arrow.down.forward")
                .font(.system(size: 10)).foregroundStyle(.white.opacity(0.4))
                .padding(4)
                .background(Circle().fill(.white.opacity(0.15)))
                .offset(x: 6, y: 6)
                .gesture(
                    DragGesture()
                        .onChanged { v in
                            if !isResizing {
                                isResizing = true
                                resizeStart = currentSize
                            }
                            let newW = max(100, resizeStart.width + v.translation.width / canvasScale)
                            let newH = max(80, resizeStart.height + v.translation.height / canvasScale)
                            currentSize = CGSize(width: newW, height: newH)
                        }
                        .onEnded { _ in
                            isResizing = false
                            onResize(currentSize)
                        }
                )
        }
        .shadow(color: .black.opacity(0.2), radius: isEditing || isConnecting ? 8 : 4, y: 2)
        .scaleEffect(isEditing || isConnecting ? 1.03 : 1.0)
        .animation(.spring(response: 0.3), value: isEditing)
        .animation(.spring(response: 0.3), value: isConnecting)
        .onTapGesture { onTap() }
        .offset(dragOffset)
        .gesture(
            DragGesture()
                .onChanged { dragOffset = $0.translation }
                .onEnded { v in
                    let scaled = CGPoint(
                        x: block.position.x + v.translation.width / canvasScale,
                        y: block.position.y + v.translation.height / canvasScale
                    )
                    dragOffset = .zero; onDrag(scaled)
                }
        )
    }

    private var strokeColor: Color {
        if isConnecting { .white }
        else if isConnectMode { .white.opacity(0.4) }
        else if isEditing { .white }
        else { .clear }
    }
}
