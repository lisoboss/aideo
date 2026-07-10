import SwiftUI
import PhotosUI

/// 参考素材节点 — 从相册导入图片/视频
struct ReferenceNodeView: View {
    let node: ReferenceNode
    let isConnectMode: Bool
    let onDelete: () -> Void
    let onConnect: () -> Void
    let onUpdate: (ReferenceNode) -> Void
    let onResize: (CGSize) -> Void
    let onDrag: (CGPoint) -> Void

    @State private var dragOffset: CGSize = .zero
    @State private var selectedPhoto: PhotosPickerItem?
    @State private var thumbnail: Image?

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            // 头部
            HStack {
                Image(systemName: node.mediaType == .image ? "photo" : "video")
                    .font(.caption)
                Text(node.mediaType == .image ? "参考图" : "参考视频")
                    .font(.caption).fontWeight(.medium)
                Spacer()
                Button(action: onConnect) {
                    Image(systemName: "arrow.triangle.pull")
                        .font(.caption2).foregroundStyle(.white.opacity(0.6))
                }.buttonStyle(.plain)
                Button(action: onDelete) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.caption).foregroundStyle(.white.opacity(0.7))
                }.buttonStyle(.plain)
            }.foregroundStyle(.white)

            // 内容 — 缩略图或导入按钮
            if let thumb = thumbnail {
                thumb
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 156, height: 70)
                    .clipShape(RoundedRectangle(cornerRadius: 6))

                Text(node.sourceLabel)
                    .font(.caption2).foregroundStyle(.white.opacity(0.6))
            } else {
                PhotosPicker(selection: $selectedPhoto, matching: .any(of: [.images, .videos])) {
                    VStack(spacing: 4) {
                        Image(systemName: "photo.badge.plus")
                            .font(.title2).foregroundStyle(.white.opacity(0.6))
                        Text("点击导入")
                            .font(.caption2).foregroundStyle(.white.opacity(0.5))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                }
                .onChange(of: selectedPhoto) { _, item in
                    handleImport(item)
                }
            }
            Spacer(minLength: 0)
        }
        .padding(10)
        .frame(width: max(node.nodeSize.width, 100), height: max(node.nodeSize.height, 80))
        .background(RoundedRectangle(cornerRadius: 12).fill(Color(hex: "#E67E22")))
        .overlay(alignment: .bottomTrailing) {
            ResizeHandle(canvasScale: 1.0, currentSize: node.nodeSize, onResize: onResize)
        }
        .shadow(color: .black.opacity(0.2), radius: 4, y: 2)
        .onTapGesture {}
        .offset(dragOffset)
        .gesture(
            DragGesture()
                .onChanged { dragOffset = $0.translation }
                .onEnded { v in
                    let new = CGPoint(x: node.position.x + v.translation.width,
                                      y: node.position.y + v.translation.height)
                    dragOffset = .zero; onDrag(new)
                }
        )
    }

    private func handleImport(_ item: PhotosPickerItem?) {
        guard let item else { return }
        Task {
            if let data = try? await item.loadTransferable(type: Data.self),
               let uiImage = UIImage(data: data) {
                await MainActor.run {
                    thumbnail = Image(uiImage: uiImage)
                    // 保存到本地并更新节点
                    let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
                    let refDir = docs.appendingPathComponent("AideoReferences", isDirectory: true)
                    try? FileManager.default.createDirectory(at: refDir, withIntermediateDirectories: true)
                    let fileURL = refDir.appendingPathComponent("\(node.id.uuidString).jpg")
                    try? data.write(to: fileURL)

                    var updated = node
                    updated.localPath = fileURL.path
                    updated.sourceLabel = "相册"
                    onUpdate(updated)
                }
            }
        }
    }
}
