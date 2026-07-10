import SwiftUI
import Observation

/// 创作画布状态 — v2 支持 4 种节点
@Observable
final class CanvasViewModel {
    /// 4 种节点数组
    var promptBlocks: [PromptBlock] = []
    var mediaOutputs: [MediaOutputNode] = []
    var referenceNodes: [ReferenceNode] = []
    var aiEnhanceNodes: [AIEnhanceNode] = []

    /// 连线
    var connections: [BlockConnection] = []

    /// 当前编辑的节点 ID
    var editingNodeId: UUID?

    /// 连线模式源节点 ID
    var connectingFromNodeId: UUID?

    /// 是否正在提交
    var isSubmitting: Bool = false
    var resultMessage: String?

    /// 当前高亮的节点 ID（生成流程中）
    var highlightedNodeId: UUID?

    /// 故事板模式
    var showStoryboard: Bool = false
    var storyboardScenes: [StoryboardScene] = []

    /// 自动分镜：按水平位置聚类 → 分配 sceneTag
    func autoAssignScenes() {
        let scenes = StoryboardBuilder.build(from: promptBlocks)
        storyboardScenes = scenes
        for (idx, block) in promptBlocks.enumerated() {
            // 找到所属场景
            for scene in scenes {
                if block.position.x >= scene.minX && block.position.x < scene.minX + StoryboardBuilder.clusterThreshold {
                    promptBlocks[idx].sceneTag = scene.index
                    break
                }
            }
        }
    }

    /// 跳转到指定场景（返回场景中心坐标）
    func focusScene(_ index: Int) -> CGPoint? {
        let sceneBlocks = promptBlocks.filter { $0.sceneTag == index }
        guard !sceneBlocks.isEmpty else { return nil }
        let avgX = sceneBlocks.map(\.position.x).reduce(0, +) / CGFloat(sceneBlocks.count)
        let avgY = sceneBlocks.map(\.position.y).reduce(0, +) / CGFloat(sceneBlocks.count)
        return CGPoint(x: avgX, y: avgY)
    }

    // MARK: - Project Persistence

    func load(from project: CanvasProject) {
        promptBlocks = project.promptBlocks
        mediaOutputs = project.mediaOutputs
        referenceNodes = project.referenceNodes
        aiEnhanceNodes = project.aiEnhanceNodes
        connections = project.connections
    }

    func save(to project: CanvasProject) {
        project.promptBlocks = promptBlocks
        project.mediaOutputs = mediaOutputs
        project.referenceNodes = referenceNodes
        project.aiEnhanceNodes = aiEnhanceNodes
        project.connections = connections
    }

    // MARK: - Node CRUD

    func addPromptBlock(type: BlockType = .custom, at position: CGPoint? = nil) {
        let pos = position ?? defaultPosition()
        let block = PromptBlock(type: type, content: "", position: pos)
        promptBlocks.append(block)
        editingNodeId = block.id
    }

    func addMediaOutput(at position: CGPoint? = nil) {
        let pos = position ?? defaultPosition()
        let node = MediaOutputNode(position: pos)
        mediaOutputs.append(node)
        editingNodeId = node.id
    }

    func addReferenceNode(at position: CGPoint? = nil) {
        let pos = position ?? defaultPosition()
        let node = ReferenceNode(position: pos, sourceLabel: "拖入素材")
        referenceNodes.append(node)
        editingNodeId = node.id
    }

    func addAIEnhanceNode(at position: CGPoint? = nil) {
        let pos = position ?? defaultPosition()
        let node = AIEnhanceNode(position: pos)
        aiEnhanceNodes.append(node)
        editingNodeId = node.id
    }

    func deleteNode(id: UUID) {
        promptBlocks.removeAll { $0.id == id }
        mediaOutputs.removeAll { $0.id == id }
        referenceNodes.removeAll { $0.id == id }
        aiEnhanceNodes.removeAll { $0.id == id }
        connections.removeAll { $0.sourceId == id || $0.targetId == id }
        if editingNodeId == id { editingNodeId = nil }
        if connectingFromNodeId == id { connectingFromNodeId = nil }
    }

    func moveNode(id: UUID, to position: CGPoint) {
        if let idx = promptBlocks.firstIndex(where: { $0.id == id }) { promptBlocks[idx].position = position }
        else if let idx = mediaOutputs.firstIndex(where: { $0.id == id }) { mediaOutputs[idx].position = position }
        else if let idx = referenceNodes.firstIndex(where: { $0.id == id }) { referenceNodes[idx].position = position }
        else if let idx = aiEnhanceNodes.firstIndex(where: { $0.id == id }) { aiEnhanceNodes[idx].position = position }
    }

    func clearAll() {
        promptBlocks.removeAll()
        mediaOutputs.removeAll()
        referenceNodes.removeAll()
        aiEnhanceNodes.removeAll()
        connections.removeAll()
        resultMessage = nil
    }

    /// 默认新节点位置（画布中央 + 随机偏移，避免重叠）
    func defaultPosition(center: CGPoint = CGPoint(x: 1500, y: 1000)) -> CGPoint {
        CGPoint(x: center.x + CGFloat.random(in: -100...100),
                y: center.y + CGFloat.random(in: -80...80))
    }

    // MARK: - Connections

    func toggleConnecting(nodeId: UUID) {
        if connectingFromNodeId == nil {
            connectingFromNodeId = nodeId
        } else if connectingFromNodeId == nodeId {
            connectingFromNodeId = nil
        } else {
            let conn = BlockConnection(sourceId: connectingFromNodeId!, targetId: nodeId)
            if !connections.contains(where: {
                ($0.sourceId == conn.sourceId && $0.targetId == conn.targetId) ||
                ($0.sourceId == conn.targetId && $0.targetId == conn.sourceId)
            }) {
                connections.append(conn)
            }
            connectingFromNodeId = nil
        }
    }

    // MARK: - Update Reference/AI Nodes

    func updateNodeSize(id: UUID, size: CGSize) {
        if let idx = promptBlocks.firstIndex(where: { $0.id == id }) { promptBlocks[idx].cardSize = size }
        else if let idx = mediaOutputs.firstIndex(where: { $0.id == id }) { mediaOutputs[idx].nodeSize = size }
        else if let idx = referenceNodes.firstIndex(where: { $0.id == id }) { referenceNodes[idx].nodeSize = size }
        else if let idx = aiEnhanceNodes.firstIndex(where: { $0.id == id }) { aiEnhanceNodes[idx].nodeSize = size }
    }

    func updatePromptBlock(id: UUID, content: String? = nil, type: BlockType? = nil, size: CGSize? = nil) {
        if let s = size { updateNodeSize(id: id, size: s) }
        if let idx = promptBlocks.firstIndex(where: { $0.id == id }) {
            if let c = content { promptBlocks[idx].content = c }
            if let t = type { promptBlocks[idx].type = t }
        }
    }

    func updateMediaOutputType(id: UUID, to type: NodeContentType) {
        if let idx = mediaOutputs.firstIndex(where: { $0.id == id }) {
            mediaOutputs[idx].contentType = type
        }
    }

    func updateReferenceNode(id: UUID, with updated: ReferenceNode) {
        if let idx = referenceNodes.firstIndex(where: { $0.id == id }) {
            referenceNodes[idx] = updated
        }
    }

    func updateAIEnhanceNode(id: UUID, with updated: AIEnhanceNode) {
        if let idx = aiEnhanceNodes.firstIndex(where: { $0.id == id }) {
            aiEnhanceNodes[idx] = updated
        }
    }

    func processAIEnhance(input: String, client: APIClient) async -> String? {
        // 尝试调用后端 API
        if let response = try? await client.structurize(description: input) {
            return response.blocks.map { "[\($0.type)]: \($0.content)" }.joined(separator: "\n")
        }
        // Fallback：本地生成结构化提示词
        return """
        [场景]: \(input)，高质量画面，电影级光影
        [角色]: 主角，细节丰富
        [动作]: 流畅动作，自然表情
        [风格]: cinematic, 4K, highly detailed
        [镜头]: 中景，浅景深
        [氛围]: 根据描述营造
        """
    }

    // MARK: - Auto Layout

    /// 自动整理画布节点（拓扑排序 → 层级布局 → 居中到画布中心）
    func autoLayout(canvasCenter: CGPoint) {
        // 1. 拓扑排序
        var inDegree: [UUID: Int] = [:]
        var outEdges: [UUID: [UUID]] = [:]
        for node in allNodes { inDegree[node.id] = 0; outEdges[node.id] = [] }
        for conn in connections {
            outEdges[conn.sourceId, default: []].append(conn.targetId)
            inDegree[conn.targetId, default: 0] += 1
        }

        var queue = inDegree.filter { $0.value == 0 }.map { $0.key }
        var levels: [UUID: Int] = [:]
        for id in queue { levels[id] = 0 }

        while let current = queue.first {
            queue.removeFirst()
            for target in outEdges[current, default: []] {
                inDegree[target, default: 0] -= 1
                levels[target] = max(levels[target, default: 0], levels[current, default: 0] + 1)
                if inDegree[target, default: 0] == 0 { queue.append(target) }
            }
        }
        for node in allNodes where levels[node.id] == nil { levels[node.id] = 0 }

        // 2. 按层级分组
        var levelGroups: [Int: [UUID]] = [:]
        for (id, level) in levels { levelGroups[level, default: []].append(id) }
        let sortedLevels = levelGroups.keys.sorted()

        // 3. 计算布局（使用实际节点尺寸）
        let gapX: CGFloat = 60, gapY: CGFloat = 40
        var rawPositions: [UUID: CGPoint] = [:]
        var levelX: CGFloat = 0

        for level in sortedLevels {
            let ids = levelGroups[level]!
            // 计算该层节点总高度和最大宽度
            var totalH: CGFloat = 0
            var maxW: CGFloat = 0
            for id in ids {
                let sz = nodeSize(for: id)
                totalH += sz.height
                if sz.width > maxW { maxW = sz.width }
            }
            totalH += CGFloat(ids.count - 1) * gapY

            var y: CGFloat = -totalH / 2
            for id in ids {
                let sz = nodeSize(for: id)
                rawPositions[id] = CGPoint(x: levelX + maxW / 2, y: y + sz.height / 2)
                y += sz.height + gapY
            }
            levelX += maxW + gapX
        }

        // 4. 计算布局包围盒
        guard !rawPositions.isEmpty else { return }
        let xs = rawPositions.values.map { $0.x }
        let ys = rawPositions.values.map { $0.y }
        let bboxCenter = CGPoint(x: (xs.min()! + xs.max()!) / 2,
                                  y: (ys.min()! + ys.max()!) / 2)

        // 5. 偏移到画布中心
        let offsetX = canvasCenter.x - bboxCenter.x
        let offsetY = canvasCenter.y - bboxCenter.y

        for (id, pos) in rawPositions {
            moveNode(id: id, to: CGPoint(x: pos.x + offsetX, y: pos.y + offsetY))
        }
    }

    // MARK: - Node Lookup

    /// 获取所有节点的统一列表
    var allNodes: [AnyCanvasNode] {
        promptBlocks.map(AnyCanvasNode.promptBlock) +
        mediaOutputs.map(AnyCanvasNode.mediaOutput) +
        referenceNodes.map(AnyCanvasNode.reference) +
        aiEnhanceNodes.map(AnyCanvasNode.aiEnhance)
    }

    /// 根据 ID 查找节点
    func node(for id: UUID) -> AnyCanvasNode? {
        allNodes.first { $0.id == id }
    }

    /// 根据 ID 获取节点尺寸
    func nodeSize(for id: UUID) -> CGSize {
        if let b = promptBlocks.first(where: { $0.id == id }) { return b.cardSize }
        if let m = mediaOutputs.first(where: { $0.id == id }) { return m.nodeSize }
        if let r = referenceNodes.first(where: { $0.id == id }) { return r.nodeSize }
        if let a = aiEnhanceNodes.first(where: { $0.id == id }) { return a.nodeSize }
        return CGSize(width: 180, height: 120)
    }

    /// 根据 ID 查找位置
    func position(for id: UUID) -> CGPoint? {
        node(for: id)?.position
    }

    // MARK: - Generation Flow

    /// 追溯连线，收集所有连接到输出节点的输入（提示词 + AI + 上游结果 + 参考图）
    private func collectInputs(from outputNodeId: UUID) -> (promptBlocks: [PromptBlock], upstreamText: String, refImagesBase64: [String]) {
        var visited: Set<UUID> = []
        var blocks: [PromptBlock] = []
        var upstreamTexts: [String] = []
        var refImages: [String] = []
        var queue: [UUID] = [outputNodeId]

        while let current = queue.popLast() {
            guard !visited.contains(current) else { continue }
            visited.insert(current)

            for conn in connections where conn.targetId == current {
                queue.append(conn.sourceId)

                // 提示词卡片
                if let block = promptBlocks.first(where: { $0.id == conn.sourceId }) {
                    blocks.append(block)
                }
                // AI 增强节点
                if let ai = aiEnhanceNodes.first(where: { $0.id == conn.sourceId }), !ai.outputText.isEmpty {
                    blocks.append(PromptBlock(type: .custom, content: ai.outputText, position: ai.position))
                }
                // 上游结果节点（文本/图片/视频）
                if let upstream = mediaOutputs.first(where: { $0.id == conn.sourceId }), upstream.hasOutput {
                    upstreamTexts.append(upstream.asInputText)
                }
                // 参考素材节点 → base64 编码
                if let ref = referenceNodes.first(where: { $0.id == conn.sourceId }),
                   !ref.localPath.isEmpty,
                   let data = try? Data(contentsOf: URL(fileURLWithPath: ref.localPath)) {
                    let b64 = data.base64EncodedString()
                    let prefix = ref.mediaType == .image ? "data:image/jpeg;base64," : "data:video/mp4;base64,"
                    refImages.append(prefix + b64)
                }
            }
        }
        return (blocks, upstreamTexts.joined(separator: "\n"), refImages)
    }

    /// 提交生成任务
    @MainActor
    func submitGeneration(outputNodeId: UUID, client: APIClient, ws: WebSocketClient) async {
        guard let idx = mediaOutputs.firstIndex(where: { $0.id == outputNodeId }) else { return }

        let inputs = collectInputs(from: outputNodeId)
        guard !inputs.promptBlocks.isEmpty || !inputs.upstreamText.isEmpty else {
            resultMessage = "请先将提示词卡片或结果节点连线到输出节点"
            return
        }

        var finalPrompt = PromptSerializer.serialize(inputs.promptBlocks)
        if !inputs.upstreamText.isEmpty {
            finalPrompt += "\n\n[参考上下文]:\n\(inputs.upstreamText)"
        }

        // 收集参数：卡片 params + 参考图 base64
        let cardParams = inputs.promptBlocks.first(where: { !$0.params.isEmpty })?.params
        var extraParams: [String: Any] = [:]
        if !inputs.refImagesBase64.isEmpty {
            extraParams["reference_images"] = inputs.refImagesBase64
        }

        isSubmitting = true
        resultMessage = nil
        mediaOutputs[idx].status = .generating
        mediaOutputs[idx].progress = 0
        highlightedNodeId = outputNodeId

        do {
            let task = try await client.createTask(prompt: finalPrompt, params: cardParams, extraParams: extraParams)
            mediaOutputs[idx].taskId = task.id
            mediaOutputs[idx].promptSummary = finalPrompt

            // 订阅 WS 实时进度
            let stream = await ws.connect(taskId: task.id)
            for await event in stream {
                await MainActor.run {
                    handleWSEvent(event, outputNodeId: outputNodeId)
                }
            }
        } catch {
            mediaOutputs[idx].status = .failed
            mediaOutputs[idx].errorMessage = error.localizedDescription
            resultMessage = error.localizedDescription
            highlightedNodeId = nil
        }

        isSubmitting = false
    }

    private func handleWSEvent(_ event: WSEvent, outputNodeId: UUID) {
        guard let idx = mediaOutputs.firstIndex(where: { $0.id == outputNodeId }) else { return }

        switch event.type {
        case "status_change":
            break // 状态跟随 progress/completed/error 变化
        case "progress":
            if let p = event.progressValue {
                mediaOutputs[idx].progress = p
            }
        case "preview":
            if let frame = event.data?["frame"]?.stringValue {
                mediaOutputs[idx].previewFrames.append(frame)
            }
        case "completed":
            mediaOutputs[idx].status = .completed
            mediaOutputs[idx].progress = 100
            highlightedNodeId = nil
            resultMessage = "生成完成"
        case "error":
            mediaOutputs[idx].status = .failed
            mediaOutputs[idx].errorMessage = event.errorMessage
            highlightedNodeId = nil
            resultMessage = event.errorMessage
        default:
            break
        }
    }
}
