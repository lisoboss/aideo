import SwiftUI

/// 结果节点 — 产出文本/图片/视频，可连入下游
struct MediaOutputNodeView: View {
    let node: MediaOutputNode
    let isHighlighted: Bool
    let isConnectMode: Bool
    let onTap: () -> Void
    let onDelete: () -> Void
    let onConnect: () -> Void
    let onGenerate: () -> Void
    let onDownload: () -> Void
    let onPlay: () -> Void
    let onChangeType: (NodeContentType) -> Void
    let onDetail: () -> Void
    let onResize: (CGSize) -> Void
    let onDrag: (CGPoint) -> Void

    @State private var dragOffset: CGSize = .zero

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            // 头部
            HStack {
                Image(systemName: node.contentType.iconName).font(.caption)
                Text(node.contentType.displayName).font(.caption).fontWeight(.medium)
                Spacer()
                Button(action: onConnect) {
                    Image(systemName: "arrow.triangle.pull").font(.caption2).foregroundStyle(.white.opacity(0.6))
                }.buttonStyle(.plain)
                Button(action: onDelete) {
                    Image(systemName: "xmark.circle.fill").font(.caption).foregroundStyle(.white.opacity(0.7))
                }.buttonStyle(.plain)
            }.foregroundStyle(.white)

            // 类型选择器（idle 时显示）
            if node.status == .idle {
                Picker("类型", selection: Binding(
                    get: { node.contentType },
                    set: { onChangeType($0) }
                )) {
                    ForEach([NodeContentType.text, .image, .video], id: \.rawValue) { t in
                        Label(t.displayName, systemImage: t.iconName).tag(t)
                    }
                }
                .pickerStyle(.segmented)
                .colorMultiply(.white)
                .scaleEffect(0.85)
            }

            // 内容区
            switch node.status {
            case .idle:       idleContent
            case .generating: generatingContent
            case .completed:  completedContent
            case .failed:     failedContent
            }
            Spacer(minLength: 0)
        }
        .padding(10)
        .frame(width: max(node.nodeSize.width, 100), height: max(node.nodeSize.height, 80))
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(hex: node.contentType == .text ? "#3498DB" :
                                  node.contentType == .image ? "#E67E22" : "#2ECC71"))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(highlightStroke, lineWidth: isHighlighted ? 3 : 0)
        )
        .shadow(color: isHighlighted ? .green.opacity(0.6) : .black.opacity(0.15),
                radius: isHighlighted ? 20 : 4, y: 2)
        .scaleEffect(isHighlighted ? 1.05 : 1.0)
        .overlay {
            if isHighlighted {
                RoundedRectangle(cornerRadius: 12)
                    .stroke(.green.opacity(0.4), lineWidth: 4).blur(radius: 6)
            }
        }
        .overlay(alignment: .bottomTrailing) {
            ResizeHandle(canvasScale: 1.0, currentSize: node.nodeSize, onResize: onResize)
        }
        .animation(.spring(response: 0.3), value: isHighlighted)
        .onTapGesture { onTap() }
        .offset(dragOffset)
        .gesture(
            DragGesture()
                .onChanged { dragOffset = $0.translation }
                .onEnded { v in
                    let n = CGPoint(x: node.position.x + v.translation.width,
                                    y: node.position.y + v.translation.height)
                    dragOffset = .zero; onDrag(n)
                }
        )
    }

    // MARK: - Idle

    private var idleContent: some View {
        VStack(spacing: 6) {
            Image(systemName: "arrow.down.to.line")
                .font(.title3).foregroundStyle(.white.opacity(0.5))
            Text("连线输入节点后生成")
                .font(.caption2).foregroundStyle(.white.opacity(0.5))
            Button(action: onGenerate) {
                Label("生成", systemImage: "wand.and.stars")
                    .font(.caption.weight(.semibold)).foregroundStyle(.white)
                    .padding(.horizontal, 16).padding(.vertical, 6)
                    .background(Capsule().fill(.white.opacity(0.25)))
            }.buttonStyle(.plain)
        }
    }

    // MARK: - Generating

    private var generatingContent: some View {
        VStack(spacing: 6) {
            HStack(spacing: 4) {
                ProgressView().tint(.white).scaleEffect(0.7)
                Text("生成中...").font(.caption).foregroundStyle(.white.opacity(0.8))
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4).fill(.white.opacity(0.2)).frame(height: 6)
                    RoundedRectangle(cornerRadius: 4).fill(.white)
                        .frame(width: geo.size.width * CGFloat(node.progress / 100), height: 6)
                        .animation(.easeInOut(duration: 0.5), value: node.progress)
                }
            }.frame(height: 6)
            Text("\(Int(node.progress))%").font(.caption2).foregroundStyle(.white.opacity(0.7))
            if node.taskId != nil {
                Button(action: onDetail) { Label("详情", systemImage: "info.circle").font(.caption2).foregroundStyle(.white) }
                    .buttonStyle(.plain).padding(.horizontal, 8).padding(.vertical, 3)
                    .background(Capsule().fill(.white.opacity(0.2)))
            }
        }
    }

    // MARK: - Completed

    @ViewBuilder
    private var completedContent: some View {
        switch node.contentType {
        case .text:
            if !node.textContent.isEmpty {
                Text(node.textContent)
                    .font(.caption).foregroundStyle(.white)
                    .lineLimit(6).padding(6)
                    .background(RoundedRectangle(cornerRadius: 6).fill(.white.opacity(0.15)))
            } else {
                Image(systemName: "checkmark.text.page").font(.title2).foregroundStyle(.white)
                Text("文本已就绪").font(.caption2).foregroundStyle(.white.opacity(0.6))
            }
            HStack(spacing: 8) {
                Button(action: {
                    UIPasteboard.general.string = node.textContent
                }) { Label("复制", systemImage: "doc.on.doc").font(.caption2).foregroundStyle(.white) }
                    .buttonStyle(.plain).padding(.horizontal, 8).padding(.vertical, 4)
                    .background(Capsule().fill(.white.opacity(0.2)))
            }

        case .image:
            if !node.imageLocalPath.isEmpty, let uiImage = UIImage(contentsOfFile: node.imageLocalPath) {
                Image(uiImage: uiImage)
                    .resizable().aspectRatio(contentMode: .fill)
                    .frame(width: 186, height: 100).clipShape(RoundedRectangle(cornerRadius: 6))
            } else {
                Image(systemName: "photo.fill").font(.title2).foregroundStyle(.white)
                Text("图片就绪").font(.caption2).foregroundStyle(.white.opacity(0.6))
            }
            HStack(spacing: 8) {
                Button(action: onPlay) { Label("预览", systemImage: "eye").font(.caption2).foregroundStyle(.white) }
                    .buttonStyle(.plain).padding(.horizontal, 8).padding(.vertical, 4)
                    .background(Capsule().fill(.white.opacity(0.2)))
                Button(action: onDownload) { Label("保存", systemImage: "square.and.arrow.down").font(.caption2).foregroundStyle(.white) }
                    .buttonStyle(.plain).padding(.horizontal, 8).padding(.vertical, 4)
                    .background(Capsule().fill(.white.opacity(0.2)))
            }

        case .video:
            Image(systemName: "play.rectangle.fill").font(.title2).foregroundStyle(.white)
            if !node.promptSummary.isEmpty {
                Text(node.promptSummary).font(.caption2).foregroundStyle(.white.opacity(0.6)).lineLimit(2)
            }
            HStack(spacing: 8) {
                Button(action: onPlay) { Label("播放", systemImage: "play.fill").font(.caption2).foregroundStyle(.white) }
                    .buttonStyle(.plain).padding(.horizontal, 8).padding(.vertical, 4)
                    .background(Capsule().fill(.white.opacity(0.2)))
                Button(action: onDownload) { Label("下载", systemImage: "arrow.down").font(.caption2).foregroundStyle(.white) }
                    .buttonStyle(.plain).padding(.horizontal, 8).padding(.vertical, 4)
                    .background(Capsule().fill(.white.opacity(0.2)))
                Button(action: onDetail) { Label("详情", systemImage: "info.circle").font(.caption2).foregroundStyle(.white) }
                    .buttonStyle(.plain).padding(.horizontal, 8).padding(.vertical, 4)
                    .background(Capsule().fill(.white.opacity(0.2)))
            }
        }
    }

    // MARK: - Failed

    private var failedContent: some View {
        VStack(spacing: 6) {
            Image(systemName: "xmark.rectangle.fill").font(.title2).foregroundStyle(.white)
            if let err = node.errorMessage {
                Text(err).font(.caption2).foregroundStyle(.white.opacity(0.7)).lineLimit(2)
            }
            Button(action: onGenerate) {
                Label("重试", systemImage: "arrow.clockwise").font(.caption2).foregroundStyle(.white)
                    .padding(.horizontal, 12).padding(.vertical, 6)
                    .background(Capsule().fill(.white.opacity(0.25)))
            }.buttonStyle(.plain)
        }
    }

    private var highlightStroke: Color { isHighlighted ? .white : .clear }
}
