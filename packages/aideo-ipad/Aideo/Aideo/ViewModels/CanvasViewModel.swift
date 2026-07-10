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

    // v2: 项目关联
    /// 当前项目 ID（云端 Project），用于项目级 WS 和同步
    var projectId: UUID?

    /// 是否正在使用项目级 WS
    private var usingProjectWS: Bool = false

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

    // MARK: - AI Enhance (v2)

    /// v2: 调用 /canvas/structure，返回 [AssistBlock] 直接落画布
    func processAIEnhance(input: String, client: APIClient) async -> [AssistBlock]? {
        // 尝试调用后端 API
        if let response = try? await client.structurize(description: input) {
            return response.blocks
        }
        // Fallback：本地生成结构化块（v2: 返回 AssistBlock 而非字符串）
        return [
            AssistBlock(type: "scene", content: "\(input)，高质量画面，电影级光影", params: nil),
            AssistBlock(type: "character", content: "主角，细节丰富", params: nil),
            AssistBlock(type: "action", content: "流畅动作，自然表情", params: nil),
            AssistBlock(type: "style", content: "cinematic, 4K, highly detailed", params: GenerationParams(style: "cinematic")),
            AssistBlock(type: "camera", content: "中景，浅景深", params: nil),
            AssistBlock(type: "mood", content: "根据描述营造", params: nil)
        ]
    }

    /// 将 AssistBlock 列表创建为画布 PromptBlock 卡片
    func createBlocksFromAssist(_ blocks: [AssistBlock], near position: CGPoint) {
        let startX = position.x
        let startY = position.y
        for (i, block) in blocks.enumerated() {
            let blockType = BlockType(rawValue: block.type) ?? .custom
            let pos = CGPoint(x: startX + CGFloat(i) * 20, y: startY + CGFloat(i) * 100)
            var promptBlock = PromptBlock(type: blockType, content: block.content, position: pos)
            if let params = block.params {
                promptBlock.params = params
            }
            promptBlocks.append(promptBlock)
        }
    }

    // MARK: - Project Sync (v2)

    /// 从云端 Project 恢复画布状态
    func syncFromProject(_ project: Project) {
        self.projectId = UUID(uuidString: project.id)
        guard let cd = project.canvas_data else { return }

        // 重建 PromptBlocks
        promptBlocks = cd.prompt_blocks.map { dto in
            let pos = CGPoint(x: 0, y: 0) // canvas_data 不含 position，后续可扩展
            return PromptBlock(type: BlockType(rawValue: dto.type) ?? .custom,
                               content: dto.content, position: pos, params: dto.params ?? GenerationParams())
        }

        // 重建 MediaOutputs
        mediaOutputs = cd.media_outputs.map { dto in
            var node = MediaOutputNode(
                position: CGPoint(x: 0, y: 0),
                contentType: NodeContentType(rawValue: dto.content_type) ?? .video)
            if let tid = UUID(uuidString: dto.task_id ?? "") { node.taskId = tid }
            return node
        }

        // 重建 ReferenceNodes
        referenceNodes = cd.reference_nodes.map { dto in
            ReferenceNode(position: CGPoint(x: 0, y: 0),
                          mediaType: ReferenceMediaType(rawValue: dto.media_type) ?? .image,
                          sourceLabel: dto.source_label)
        }

        // 重建 Connections
        connections = cd.connections.compactMap { dto in
            guard let sId = UUID(uuidString: dto.source_id),
                  let tId = UUID(uuidString: dto.target_id) else { return nil }
            return BlockConnection(sourceId: sId, targetId: tId)
        }
    }

    /// 序列化当前画布为 CanvasData（用于 project sync）
    func exportCanvasData() -> CanvasData {
        CanvasData(
            prompt_blocks: promptBlocks.map { PromptBlockDTO(from: $0) },
            media_outputs: mediaOutputs.map { MediaOutputDTO(
                id: $0.id.uuidString, position: CGPointDTO(x: $0.position.x, y: $0.position.y),
                content_type: $0.contentType.rawValue, task_id: $0.taskId?.uuidString,
                status: String(describing: $0.status), progress: $0.progress,
                prompt_summary: $0.promptSummary, preview_frames: $0.previewFrames) },
            reference_nodes: referenceNodes.map { ReferenceNodeDTO(
                id: $0.id.uuidString, position: CGPointDTO(x: $0.position.x, y: $0.position.y),
                media_type: $0.mediaType == .image ? "image" : "video",
                source_label: $0.sourceLabel) },
            ai_enhance_nodes: aiEnhanceNodes.map { AIEnhanceDTO(
                id: $0.id.uuidString, position: CGPointDTO(x: $0.position.x, y: $0.position.y),
                input_text: $0.inputText, output_text: $0.outputText,
                status: String(describing: $0.status)) },
            connections: connections.map { BlockConnectionDTO(from: $0) },
            viewport: nil
        )
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

    // MARK: - Input Collection

    /// 收集结果类型（v2 扩展）
    struct CollectedInputs {
        var promptBlocks: [PromptBlock] = []
        var connections: [BlockConnection] = []
        var upstreamText: String = ""
        var upstreamResults: [UpstreamResultDTO] = []
        var refAssets: [ReferenceAssetDTO] = []
        var aiTexts: [String] = []
    }

    /// 追溯连线，收集所有连接到输出节点的输入（提示词 + AI + 上游结果 + 参考图）
    private func collectInputs(from outputNodeId: UUID) -> CollectedInputs {
        var visited: Set<UUID> = []
        var result = CollectedInputs()
        var queue: [UUID] = [outputNodeId]

        while let current = queue.popLast() {
            guard !visited.contains(current) else { continue }
            visited.insert(current)

            for conn in connections where conn.targetId == current {
                queue.append(conn.sourceId)
                result.connections.append(conn)

                // 提示词卡片
                if let block = promptBlocks.first(where: { $0.id == conn.sourceId }) {
                    result.promptBlocks.append(block)
                }
                // AI 增强节点
                if let ai = aiEnhanceNodes.first(where: { $0.id == conn.sourceId }), !ai.outputText.isEmpty {
                    result.promptBlocks.append(PromptBlock(type: .custom, content: ai.outputText, position: ai.position))
                    result.aiTexts.append(ai.outputText)
                }
                // 上游结果节点（文本/图片/视频）
                if let upstream = mediaOutputs.first(where: { $0.id == conn.sourceId }), upstream.hasOutput {
                    result.upstreamText += (result.upstreamText.isEmpty ? "" : "\n") + upstream.asInputText
                    // v2: 结构化上游引用
                    var dto = UpstreamResultDTO(node_id: conn.sourceId.uuidString,
                        content_type: upstream.contentType.rawValue, text: nil, asset_id: nil)
                    switch upstream.contentType {
                    case .text:
                        dto.text = upstream.textContent
                    case .image:
                        dto.asset_id = nil // TODO: 上传图片后填充
                    case .video:
                        dto.asset_id = nil // TODO: 上传视频后填充
                    }
                    result.upstreamResults.append(dto)
                }
                // 参考素材节点 → asset_id 引用
                if let ref = referenceNodes.first(where: { $0.id == conn.sourceId }),
                   !ref.localPath.isEmpty {
                    result.refAssets.append(ReferenceAssetDTO(
                        asset_id: ref.id.uuidString, // 客户端 ID 占位，后续上传
                        usage: ref.mediaType == .image ? "style_reference" : "motion_reference"))
                }
            }
        }
        return result
    }

    /// 提交生成任务 — v2 优先（结构化提交），fallback v1（扁平 prompt）
    @MainActor
    func submitGeneration(outputNodeId: UUID, client: APIClient, ws: WebSocketClient) async {
        guard let idx = mediaOutputs.firstIndex(where: { $0.id == outputNodeId }) else { return }

        let collected = collectInputs(from: outputNodeId)
        guard !collected.promptBlocks.isEmpty || !collected.upstreamText.isEmpty else {
            resultMessage = "请先将提示词卡片或结果节点连线到输出节点"
            return
        }

        let outputContentType = mediaOutputs[idx].contentType.rawValue
        let cardParams: GenerationParams? = collected.promptBlocks.first(where: { !$0.params.isEmpty })?.params

        isSubmitting = true
        resultMessage = nil
        mediaOutputs[idx].status = .generating
        mediaOutputs[idx].progress = 0
        highlightedNodeId = outputNodeId

        do {
            let task: TaskModel

            // v2: 尝试结构化提交
            let v2Request = GenerateRequest(
                project_id: projectId?.uuidString,
                output_node_id: outputNodeId.uuidString,
                output_content_type: outputContentType,
                blocks: collected.promptBlocks.map { PromptBlockDTO(from: $0) },
                connections: collected.connections.map { BlockConnectionDTO(from: $0) },
                reference_assets: collected.refAssets,
                upstream_context: collected.upstreamResults,
                ai_enhance_context: collected.aiTexts,
                output_params: cardParams
            )

            let v2Response = try await client.generate(request: v2Request)
            task = v2Response.task

            mediaOutputs[idx].taskId = task.id
            mediaOutputs[idx].promptSummary = task.prompt

            // 项目级 WS
            if let pid = projectId {
                usingProjectWS = true
                let stream = await ws.connectProject(projectId: pid)
                for await event in stream {
                    await MainActor.run {
                        if event.outputNodeId == outputNodeId.uuidString || event.outputNodeId == nil {
                            handleV2WSEvent(event, outputNodeId: outputNodeId)
                        }
                    }
                }
            }
        } catch {
            mediaOutputs[idx].status = .failed
            mediaOutputs[idx].errorMessage = error.localizedDescription
            resultMessage = error.localizedDescription
            highlightedNodeId = nil
        }

        isSubmitting = false
        usingProjectWS = false
    }

    // MARK: - WS Event Handler

    /// 类型化事件处理（项目级 WS）
    private func handleV2WSEvent(_ event: ProjectWSEvent, outputNodeId: UUID) {
        guard let idx = mediaOutputs.firstIndex(where: { $0.id == outputNodeId }) else { return }

        switch event {
        case .connected(let payload):
            // 快照：恢复所有活跃任务状态
            for info in payload.snapshot.active_tasks {
                if info.output_node_id == outputNodeId.uuidString {
                    mediaOutputs[idx].progress = info.progress
                }
            }
        case .taskStatus(let payload):
            // 将后端 TaskStatus 映射到 OutputStatus
            switch payload.status {
            case "queued", "running", "generating":
                mediaOutputs[idx].status = .generating
            case "completed":
                mediaOutputs[idx].status = .completed
            case "failed":
                mediaOutputs[idx].status = .failed
            case "cancelled":
                mediaOutputs[idx].status = .idle
            default:
                break
            }
        case .taskProgress(let payload):
            if payload.output_node_id == outputNodeId.uuidString {
                mediaOutputs[idx].progress = payload.progress
            }
        case .taskPreview(let payload):
            if payload.output_node_id == outputNodeId.uuidString {
                // 提取预览帧文件名
                let frameName = URL(string: payload.frame_url)?.lastPathComponent ?? payload.frame_url
                mediaOutputs[idx].previewFrames.append(frameName)
            }
        case .taskCompleted(let payload):
            mediaOutputs[idx].status = .completed
            mediaOutputs[idx].progress = 100
            highlightedNodeId = nil
            resultMessage = "生成完成"
            // 存储 result_url
            if let urlStr = payload.result_url {
                mediaOutputs[idx].videoLocalPath = urlStr
            }
        case .taskFailed(let payload):
            mediaOutputs[idx].status = .failed
            mediaOutputs[idx].errorMessage = payload.error_message
            highlightedNodeId = nil
            resultMessage = payload.error_message
        case .taskCancelled:
            mediaOutputs[idx].status = .idle
            highlightedNodeId = nil
        case .error(let payload):
            mediaOutputs[idx].status = .failed
            mediaOutputs[idx].errorMessage = payload.message
            highlightedNodeId = nil
            resultMessage = payload.message
        }
    }
}
