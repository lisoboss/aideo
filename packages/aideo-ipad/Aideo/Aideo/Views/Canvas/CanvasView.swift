import SwiftUI
import AVKit
import PencilKit

/// 创作画布主视图 — 无限扩展 + 缩放 + 4 种节点
struct CanvasView: View {
    let project: CanvasProject

    @Environment(AppState.self) private var appState
    @State private var vm = CanvasViewModel()
    @State private var canvasSize: CGSize = CGSize(width: 3000, height: 2000)
    @State private var showPlayer = false
    @State private var playerVideoURL: URL?
    @State private var showDetail = false
    @State private var detailTaskId: UUID?
    @State private var detailPrompt: String = ""
    @State private var pkCanvas = PencilOnlyCanvasView()
    @State private var showTemplates = false
    @State private var showStoryboard = false
    @State private var scale: CGFloat = 1.0
    @State private var lastScale: CGFloat = 1.0

    /// 画布中心（用于新节点默认位置）
    private var canvasCenter: CGPoint {
        CGPoint(x: dynamicCanvasSize.width / 2, y: dynamicCanvasSize.height / 2)
    }

    /// 节点包围盒 padding
    private let canvasPadding: CGFloat = 600

    /// 动态画布尺寸：至少包裹所有节点 + padding，不小于可视区
    private var dynamicCanvasSize: CGSize {
        let nodes = vm.allNodes
        guard !nodes.isEmpty else {
            return CGSize(width: max(canvasSize.width, 3000),
                          height: max(canvasSize.height, 2000))
        }
        var minX = CGFloat.infinity, maxX = -CGFloat.infinity
        var minY = CGFloat.infinity, maxY = -CGFloat.infinity
        for node in nodes {
            let p = node.position
            if p.x < minX { minX = p.x }
            if p.x > maxX { maxX = p.x }
            if p.y < minY { minY = p.y }
            if p.y > maxY { maxY = p.y }
        }
        let w = max(canvasSize.width,  (maxX - minX) + canvasPadding * 2)
        let h = max(canvasSize.height, (maxY - minY) + canvasPadding * 2)
        // 防止 NaN/Inf 导致 crash
        let safeW = w.isFinite ? max(w, 3000) : 3000
        let safeH = h.isFinite ? max(h, 2000) : 2000
        return CGSize(width: safeW, height: safeH)
    }

    var body: some View {
        ZStack {
            Color(uiColor: .systemGroupedBackground).ignoresSafeArea()

            ScrollView([.horizontal, .vertical], showsIndicators: true) {
                ZStack {
                    Rectangle().fill(.clear)
                        .frame(width: dynamicCanvasSize.width,
                               height: dynamicCanvasSize.height)

                    GridLines()
                        .frame(width: dynamicCanvasSize.width,
                               height: dynamicCanvasSize.height)

                    // 连线层
                    ConnectionsLayer(connections: vm.connections, allNodes: vm.allNodes)

                    // 连线中临时指示
                    if let sourceId = vm.connectingFromNodeId,
                       let sourcePos = vm.position(for: sourceId) {
                        TemporaryConnectionLine(from: sourcePos)
                    }

                    // 节点层
                    ForEach(vm.allNodes) { node in
                        nodeView(for: node)
                            .position(node.position)
                    }

                    // 手写层嵌入画布内部 — Pencil 写 / Finger 穿透
                    HandwritingOverlay(canvasView: $pkCanvas, onStrokeEnd: { result in
                        vm.addPromptBlock(type: .custom, at: canvasCenter)
                        if let newId = vm.promptBlocks.last?.id {
                            vm.updatePromptBlock(id: newId, content: result.recognizedText)
                        }
                    })
                    .frame(width: dynamicCanvasSize.width, height: dynamicCanvasSize.height)
                }
                .scaleEffect(scale)
            }
            .defaultScrollAnchor(.center)
            .gesture(
                MagnificationGesture()
                    .onChanged { value in
                        scale = min(max(lastScale * value, 0.3), 3.0)
                    }
                    .onEnded { _ in
                        lastScale = scale
                    }
            )
            // 双击重置缩放
            .onTapGesture(count: 2) {
                withAnimation(.spring) { scale = 1.0; lastScale = 1.0 }
            }


            // 底部
            VStack {
                Spacer()

                if vm.connectingFromNodeId != nil {
                    Text("点击目标节点完成连线")
                        .font(.caption)
                        .foregroundStyle(.white)
                        .padding(.vertical, 6).padding(.horizontal, 14)
                        .background(Capsule().fill(Color.accentColor))
                        .padding(.bottom, 4)
                }

                if let msg = vm.resultMessage {
                    HStack {
                        Image(systemName: msg.contains("完成") || msg.contains("已提交") ? "checkmark.circle.fill" : "exclamationmark.circle.fill")
                        Text(msg).font(.subheadline)
                    }
                    .foregroundStyle(msg.contains("完成") || msg.contains("已提交") ? .green : .orange)
                    .padding(.vertical, 8).padding(.horizontal, 16)
                    .background(.regularMaterial).clipShape(Capsule())
                    .padding(.bottom, 4)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                    .onAppear {
                        Task {
                            try? await Task.sleep(for: .seconds(3))
                            if vm.resultMessage == msg { vm.resultMessage = nil }
                        }
                    }
                }

                // 故事板时间轴
                if showStoryboard {
                    StoryboardBarView(
                        scenes: vm.storyboardScenes,
                        onSelectScene: { idx in
                            let _ = vm.focusScene(idx)
                            vm.resultMessage = "场景 \(idx + 1): \(vm.promptBlocks.filter{$0.sceneTag == idx}.count) 张卡片"
                        },
                        onAutoAssign: { vm.autoAssignScenes() }
                    )
                }

                CanvasToolbar(
                    onAddCard: { type in vm.addPromptBlock(type: type, at: canvasCenter) },
                    onAddOutput: { vm.addMediaOutput(at: canvasCenter) },
                    onAddReference: { vm.addReferenceNode(at: canvasCenter) },
                    onAddAI: { vm.addAIEnhanceNode(at: canvasCenter) },
                    onAutoLayout: { vm.autoLayout(canvasCenter: CGPoint(x: dynamicCanvasSize.width / 2, y: dynamicCanvasSize.height / 2)) },
                    onClear: { vm.clearAll() },
                    onTemplates: { showTemplates = true },
                    isStoryboard: showStoryboard,
                    onToggleStoryboard: {
                        showStoryboard.toggle()
                        if showStoryboard { vm.autoAssignScenes() }
                    }
                )
            }
        }
        .navigationTitle(project.name)
        .onGeometryChange(for: CGSize.self) { $0.size } action: { canvasSize = $0 }
        .onAppear { vm.load(from: project, ws: appState.wsClient) }
        .onDisappear {
            vm.save(to: project)
            vm.disconnectProjectWS()
        }
        .onReceive(NotificationCenter.default.publisher(for: UIApplication.willResignActiveNotification)) { _ in
            vm.save(to: project)
        }
        // 卡片编辑浮层
        .sheet(isPresented: Binding(
            get: { vm.editingNodeId != nil && vm.promptBlocks.contains(where: { $0.id == vm.editingNodeId }) },
            set: { if !$0 { vm.editingNodeId = nil } }
        )) {
            if let blockId = vm.editingNodeId {
                CardEditorView(
                    block: Binding(
                        get: { vm.promptBlocks.first(where: { $0.id == blockId }) ?? PromptBlock() },
                        set: { newValue in
                            if let idx = vm.promptBlocks.firstIndex(where: { $0.id == blockId }) {
                                vm.promptBlocks[idx] = newValue
                            }
                        }
                    ),
                    onDelete: { vm.deleteNode(id: blockId) },
                    onDone: { vm.editingNodeId = nil }
                )
            }
        }
        // 任务详情
        .sheet(isPresented: $showDetail) {
            if let tid = detailTaskId {
                let task = TaskModel(
                    id: tid, prompt: detailPrompt, params: nil,
                    status: .generating, progress: 0,
                    createdAt: Date(), updatedAt: Date(),
                    resultPath: nil, resultURL: nil, previews: [], errorMessage: nil
                )
                TaskDetailView(task: task)
            }
        }
        // 模板库
        .sheet(isPresented: $showTemplates) {
            TemplateLibraryView { template in
                vm.addPromptBlock(type: template.type, at: canvasCenter)
                if let newId = vm.promptBlocks.last?.id {
                    vm.updatePromptBlock(id: newId, content: template.content)
                    if let idx = vm.promptBlocks.firstIndex(where: { $0.id == newId }) {
                        vm.promptBlocks[idx].params = template.params
                    }
                }
            }
        }
        // 视频播放
        .sheet(isPresented: $showPlayer) {
            if let url = playerVideoURL {
                NavigationStack {
                    VideoPlayer(player: AVPlayer(url: url))
                        .ignoresSafeArea()
                        .toolbar {
                            ToolbarItem(placement: .confirmationAction) {
                                Button("完成") { showPlayer = false }
                            }
                        }
                }
            }
        }
        // 空画布引导
        .overlay {
            if vm.allNodes.isEmpty {
                EmptyCanvasGuide(
                    onPrompt: { vm.addPromptBlock(type: .scene, at: canvasCenter) },
                    onOutput: { vm.addMediaOutput(at: canvasCenter) },
                    onReference: { vm.addReferenceNode(at: canvasCenter) },
                    onAI: { vm.addAIEnhanceNode(at: canvasCenter) }
                )
            }
        }
    }

    // MARK: - Node Dispatch

    @ViewBuilder
    private func nodeView(for node: AnyCanvasNode) -> some View {
        switch node {
        case .promptBlock(let block):
            PromptCardView(
                block: block,
                isEditing: vm.editingNodeId == block.id,
                isConnecting: vm.connectingFromNodeId == block.id,
                isConnectMode: vm.connectingFromNodeId != nil,
                onTap: {
                    if vm.connectingFromNodeId != nil {
                        vm.toggleConnecting(nodeId: block.id)
                    } else {
                        vm.editingNodeId = block.id
                    }
                },
                onDelete: { vm.deleteNode(id: block.id) },
                onConnect: { vm.toggleConnecting(nodeId: block.id) },
                onDrag: { vm.moveNode(id: block.id, to: $0) },
                onResize: { vm.updatePromptBlock(id: block.id, size: $0) },
                canvasScale: scale
            )

        case .mediaOutput(let outputNode):
            MediaOutputNodeView(
                node: outputNode,
                isHighlighted: vm.highlightedNodeId == outputNode.id,
                isConnectMode: vm.connectingFromNodeId != nil,
                onTap: {
                    if vm.connectingFromNodeId != nil {
                        vm.toggleConnecting(nodeId: outputNode.id)
                    }
                },
                onDelete: { vm.deleteNode(id: outputNode.id) },
                onConnect: { vm.toggleConnecting(nodeId: outputNode.id) },
                onGenerate: {
                    Task { await vm.submitGeneration(
                        outputNodeId: outputNode.id,
                        client: appState.apiClient,
                        ws: appState.wsClient,
                        language: appState.language
                    )}
                },
                onDownload: {
                    Task {
                        let url = appState.apiClient.downloadURL(taskId: outputNode.taskId ?? outputNode.id)
                        let file = try? await appState.downloadManager.download(taskId: outputNode.taskId ?? outputNode.id, from: url)
                        if let file { vm.resultMessage = "已下载: \(file.fileName)" }
                    }
                },
                onPlay: {
                    if !outputNode.videoLocalPath.isEmpty {
                        playerVideoURL = URL(fileURLWithPath: outputNode.videoLocalPath)
                    } else if !outputNode.imageLocalPath.isEmpty {
                        playerVideoURL = URL(fileURLWithPath: outputNode.imageLocalPath)
                    } else if let tid = outputNode.taskId {
                        playerVideoURL = appState.apiClient.downloadURL(taskId: tid)
                    }
                    showPlayer = true
                },
                onChangeType: { vm.updateMediaOutputType(id: outputNode.id, to: $0) },
                onDetail: {
                    detailTaskId = outputNode.taskId ?? outputNode.id
                    detailPrompt = outputNode.promptSummary
                    showDetail = true
                },
                onResize: { vm.updateNodeSize(id: outputNode.id, size: $0) },
                onDrag: { vm.moveNode(id: outputNode.id, to: $0) }
            )

        case .reference(let refNode):
            ReferenceNodeView(
                node: refNode,
                isConnectMode: vm.connectingFromNodeId != nil,
                onDelete: { vm.deleteNode(id: refNode.id) },
                onConnect: { vm.toggleConnecting(nodeId: refNode.id) },
                onUpdate: { vm.updateReferenceNode(id: refNode.id, with: $0) },
                onResize: { vm.updateNodeSize(id: refNode.id, size: $0) },
                onDrag: { vm.moveNode(id: refNode.id, to: $0) }
            )

        case .aiEnhance(let aiNode):
            AIEnhanceNodeView(
                node: aiNode,
                isConnectMode: vm.connectingFromNodeId != nil,
                onDelete: { vm.deleteNode(id: aiNode.id) },
                onConnect: { vm.toggleConnecting(nodeId: aiNode.id) },
                onUpdate: { vm.updateAIEnhanceNode(id: aiNode.id, with: $0) },
                onResize: { vm.updateNodeSize(id: aiNode.id, size: $0) },
                onProcess: { input in await vm.processAIEnhance(input: input, client: appState.apiClient, language: appState.language) },
                onDrag: { vm.moveNode(id: aiNode.id, to: $0) }
            )
        }
    }
}

// MARK: - Empty Canvas Guide

private struct EmptyCanvasGuide: View {
    let onPrompt: () -> Void
    let onOutput: () -> Void
    let onReference: () -> Void
    let onAI: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "square.grid.2x2").font(.system(size: 48)).foregroundStyle(.quaternary)
            Text("空白画布").font(.title2).fontWeight(.medium).foregroundStyle(.secondary)
            Text("添加节点开始创作")
                .font(.subheadline).foregroundStyle(.tertiary)
            HStack(spacing: 12) {
                QuickAddBtn(icon: "paintbrush.pointed", label: "提示词", color: "#4A90D9", action: onPrompt)
                QuickAddBtn(icon: "play.rectangle", label: "输出", color: "#2ECC71", action: onOutput)
                QuickAddBtn(icon: "photo", label: "参考", color: "#E67E22", action: onReference)
                QuickAddBtn(icon: "sparkles", label: "AI", color: "#9B59B6", action: onAI)
            }
        }.allowsHitTesting(true)
    }
}

private struct QuickAddBtn: View {
    let icon: String; let label: String; let color: String; let action: () -> Void
    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Image(systemName: icon).font(.title2)
                Text(label).font(.caption2)
            }
            .foregroundStyle(Color(hex: color))
            .frame(width: 64, height: 64)
            .background(Color(hex: color).opacity(0.1))
            .clipShape(RoundedRectangle(cornerRadius: 10))
        }.buttonStyle(.plain)
    }
}

// MARK: - Connections

private struct ConnectionsLayer: View {
    let connections: [BlockConnection]
    let allNodes: [AnyCanvasNode]

    var body: some View {
        ForEach(connections) { conn in
            if let src = allNodes.first(where: { $0.id == conn.sourceId }),
               let dst = allNodes.first(where: { $0.id == conn.targetId }) {
                let srcSize = nodeSize(src)
                let dstSize = nodeSize(dst)
                let pts = edgePoints(from: src.position, to: dst.position, srcSize: srcSize, dstSize: dstSize)
                ConnectionLine(from: pts.src, to: pts.dst, colorHex: src.colorHex)
            }
        }
    }

    private func nodeSize(_ node: AnyCanvasNode) -> CGSize {
        switch node {
        case .promptBlock(let b): return b.cardSize
        case .mediaOutput(let m): return m.nodeSize
        case .reference(let r):   return r.nodeSize
        case .aiEnhance(let a):   return a.nodeSize
        }
    }

    private func edgePoints(from s: CGPoint, to d: CGPoint, srcSize: CGSize, dstSize: CGSize) -> (src: CGPoint, dst: CGPoint) {
        let dx = d.x - s.x, dy = d.y - s.y
        return (
            intersect(center: s, size: srcSize, dx: dx, dy: dy),
            intersect(center: d, size: dstSize, dx: -dx, dy: -dy)
        )
    }

    private func intersect(center: CGPoint, size: CGSize, dx: CGFloat, dy: CGFloat) -> CGPoint {
        guard dx != 0 || dy != 0 else { return center }
        let hw = size.width / 2, hh = size.height / 2
        let sx = abs(dx) > 0 ? hw / abs(dx) : .infinity
        let sy = abs(dy) > 0 ? hh / abs(dy) : .infinity
        return CGPoint(x: center.x + dx * min(sx, sy), y: center.y + dy * min(sx, sy))
    }
}

// MARK: - Line Components

private struct ConnectionLine: View {
    let from: CGPoint; let to: CGPoint; let colorHex: String
    private let arrowLen: CGFloat = 12
    var body: some View {
        let dx = to.x - from.x; let dy = to.y - from.y
        let dist = hypot(dx, dy)
        if dist > 1, dist.isFinite {
            let color = Color(hex: colorHex).opacity(0.6)
            let angle = atan2(dy, dx)
            let lineEnd = CGPoint(x: to.x - arrowLen * cos(angle), y: to.y - arrowLen * sin(angle))
            ZStack {
                FlowDashLine(from: from, to: lineEnd, color: color)
                ArrowHead(from: lineEnd, to: to, color: color)
            }
        }
    }
}

private struct FlowDashLine: View {
    let from: CGPoint; let to: CGPoint; let color: Color
    var body: some View {
        let total = hypot(to.x - from.x, to.y - from.y)
        if total > 1, total.isFinite {
            TimelineView(.animation) { timeline in
                let now = timeline.date.timeIntervalSinceReferenceDate
                let speed: CGFloat = 30; let dL: CGFloat = 8; let gL: CGFloat = 6
                let pL = dL + gL
                Canvas { ctx, _ in
                    let angle = atan2(to.y - from.y, to.x - from.x)
                    let raw = CGFloat(now) * speed
                    let off = raw.truncatingRemainder(dividingBy: pL)
                    var pos: CGFloat = off - pL
                    while pos < total {
                        let s = max(0, pos), e = min(total, pos + dL)
                        if s < e {
                            let p1 = CGPoint(x: from.x + s * cos(angle), y: from.y + s * sin(angle))
                            let p2 = CGPoint(x: from.x + e * cos(angle), y: from.y + e * sin(angle))
                            var p = Path(); p.move(to: p1); p.addLine(to: p2)
                            ctx.stroke(p, with: .color(color), lineWidth: 2.5)
                        }
                        pos += pL
                    }
                }
            }
        }
    }
}

private struct ArrowHead: View {
    let from: CGPoint; let to: CGPoint; let color: Color
    var body: some View {
        let angle = atan2(to.y - from.y, to.x - from.x)
        let hw: CGFloat = 5; let perp = angle + .pi / 2
        let b1 = CGPoint(x: from.x + hw * cos(perp), y: from.y + hw * sin(perp))
        let b2 = CGPoint(x: from.x - hw * cos(perp), y: from.y - hw * sin(perp))
        Path { p in p.move(to: to); p.addLine(to: b1); p.addLine(to: b2); p.closeSubpath() }.fill(color)
    }
}

private struct TemporaryConnectionLine: View {
    let from: CGPoint
    var body: some View {
        let edge = CGPoint(x: from.x + 90, y: from.y)
        Path { p in p.move(to: edge); p.addLine(to: CGPoint(x: edge.x + 120, y: edge.y)) }
            .stroke(Color.accentColor, style: StrokeStyle(lineWidth: 2, dash: [6, 6]))
    }
}

private struct GridLines: View {
    var body: some View {
        Canvas { ctx, size in
            let step: CGFloat = 100; let c = Color.gray.opacity(0.15)
            var x: CGFloat = 0
            while x < size.width {
                ctx.stroke(Path { $0.move(to: CGPoint(x: x, y: 0)); $0.addLine(to: CGPoint(x: x, y: size.height)) }, with: .color(c), lineWidth: 1)
                x += step
            }
            var y: CGFloat = 0
            while y < size.height {
                ctx.stroke(Path { $0.move(to: CGPoint(x: 0, y: y)); $0.addLine(to: CGPoint(x: size.width, y: y)) }, with: .color(c), lineWidth: 1)
                y += step
            }
        }
    }
}
