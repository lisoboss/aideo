import SwiftUI
import PencilKit

/// PKCanvasView 子类 — 手指触摸穿透，仅响应 Apple Pencil
class PencilOnlyCanvasView: PKCanvasView {
    override func hitTest(_ point: CGPoint, with event: UIEvent?) -> UIView? {
        // 检测触摸类型：仅 Pencil 事件正常处理
        if let event, event.allTouches?.first?.type == .pencil {
            return super.hitTest(point, with: event)
        }
        return nil  // 手指触摸穿透
    }
}

/// PencilKit 手写层
struct HandwritingOverlay: UIViewRepresentable {
    @Binding var canvasView: PencilOnlyCanvasView
    var onStrokeEnd: (HandwritingResult) -> Void

    func makeUIView(context: Context) -> PencilOnlyCanvasView {
        canvasView.drawingPolicy = .pencilOnly
        canvasView.tool = PKInkingTool(.pen, color: UIColor(red: 1, green: 1, blue: 1, alpha: 0.9), width: 4)
        canvasView.backgroundColor = .clear
        canvasView.isOpaque = false
        canvasView.delegate = context.coordinator
        return canvasView
    }

    func updateUIView(_ uiView: PencilOnlyCanvasView, context: Context) {
        // 确保每次更新也保持正确的 tool
        uiView.tool = PKInkingTool(.pen, color: UIColor(red: 1, green: 1, blue: 1, alpha: 0.9), width: 4)
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(onStrokeEnd: onStrokeEnd)
    }

    class Coordinator: NSObject, PKCanvasViewDelegate {
        let onStrokeEnd: (HandwritingResult) -> Void
        private var strokeCount = 0
        private weak var targetView: PencilOnlyCanvasView?

        init(onStrokeEnd: @escaping (HandwritingResult) -> Void) {
            self.onStrokeEnd = onStrokeEnd
        }

        func canvasViewDidEndUsingTool(_ canvasView: PKCanvasView) {
            targetView = canvasView as? PencilOnlyCanvasView
            strokeCount += 1
            if strokeCount >= 3 { commit(canvasView) }
        }

        func canvasViewDrawingDidChange(_ canvasView: PKCanvasView) {
            targetView = canvasView as? PencilOnlyCanvasView
            NSObject.cancelPreviousPerformRequests(withTarget: self, selector: #selector(autoCommit), object: nil)
            if !canvasView.drawing.strokes.isEmpty {
                perform(#selector(autoCommit), with: nil, afterDelay: 5)
            }
        }

        private func commit(_ view: PKCanvasView) {
            let result = HandwritingTool.extract(from: view)
            HandwritingTool.clear(view)
            strokeCount = 0
            onStrokeEnd(result)
        }

        @objc private func autoCommit() {
            if let view = targetView, !view.drawing.strokes.isEmpty {
                commit(view)
            }
        }
    }
}

/// 手写结果
struct HandwritingResult {
    let imageData: Data?
    let recognizedText: String
    let boundsCenter: CGPoint
}

/// 手写工具
enum HandwritingTool {
    static func extract(from canvas: PKCanvasView) -> HandwritingResult {
        let bounds = canvas.drawing.bounds
        let center = CGPoint(x: bounds.midX, y: bounds.midY)
        let imageData = canvas.drawing.image(from: bounds, scale: 2.0).pngData()
        return HandwritingResult(imageData: imageData, recognizedText: "[手写]", boundsCenter: center)
    }

    static func clear(_ canvas: PKCanvasView) {
        canvas.drawing = PKDrawing()
    }
}
