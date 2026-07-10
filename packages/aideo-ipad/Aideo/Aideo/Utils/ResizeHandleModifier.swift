import SwiftUI

/// 节点右下角缩放把手
struct ResizeHandle: View {
    let canvasScale: CGFloat
    let minSize: CGSize
    let currentSize: CGSize
    let onResize: (CGSize) -> Void

    @State private var isResizing = false
    @State private var startSize: CGSize = .zero
    @State private var current: CGSize

    init(canvasScale: CGFloat, minSize: CGSize = CGSize(width: 100, height: 80),
         currentSize: CGSize, onResize: @escaping (CGSize) -> Void) {
        self.canvasScale = canvasScale
        self.minSize = minSize
        self.currentSize = currentSize
        self.onResize = onResize
        _current = State(initialValue: currentSize)
    }

    var body: some View {
        Image(systemName: "arrow.up.backward.and.arrow.down.forward")
            .font(.system(size: 10))
            .foregroundStyle(.white.opacity(0.4))
            .padding(4)
            .background(Circle().fill(.white.opacity(0.15)))
            .padding(2)
            .gesture(
                DragGesture()
                    .onChanged { v in
                        if !isResizing { isResizing = true; startSize = currentSize }
                        current = CGSize(
                            width: max(minSize.width, startSize.width + v.translation.width / canvasScale),
                            height: max(minSize.height, startSize.height + v.translation.height / canvasScale)
                        )
                    }
                    .onEnded { _ in
                        isResizing = false
                        onResize(current)
                    }
            )
    }
}
