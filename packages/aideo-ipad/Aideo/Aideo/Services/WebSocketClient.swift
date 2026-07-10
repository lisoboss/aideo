import Foundation

// MARK: - Client

/// WebSocket 客户端 — 封装 aideo-serv 实时进度连接
actor WebSocketClient {
    private let serverURL: String
    private var activeTasks: [UUID: URLSessionWebSocketTask] = [:]
    private var activeSessions: [UUID: URLSession] = [:]

    init(serverURL: String) {
        self.serverURL = serverURL
    }

    /// 连接指定任务的 WebSocket，返回 AsyncStream<WSEvent>
    func connect(taskId: UUID) -> AsyncStream<WSEvent> {
        AsyncStream { continuation in
            let wsURL = serverURL
                .replacingOccurrences(of: "http://", with: "ws://")
                .replacingOccurrences(of: "https://", with: "wss://")

            guard let url = URL(string: "\(wsURL)/api/v1/ws/tasks/\(taskId.uuidString)") else {
                continuation.finish()
                return
            }

            let session = URLSession(configuration: .default)
            let task = session.webSocketTask(with: url)

            activeSessions[taskId] = session
            activeTasks[taskId] = task

            task.resume()

            // 启动消息接收循环
            Task { [weak self] in
                await self?.receiveLoop(taskId: taskId, task: task, continuation: continuation)
            }
        }
    }

    /// 断开指定任务连接
    func disconnect(taskId: UUID) {
        activeTasks[taskId]?.cancel(with: .normalClosure, reason: nil)
        activeTasks[taskId] = nil
        activeSessions[taskId] = nil
    }

    /// 断开所有连接
    func disconnectAll() {
        for (_, wsTask) in activeTasks {
            wsTask.cancel(with: .normalClosure, reason: nil)
        }
        activeTasks.removeAll()
        activeSessions.removeAll()
    }

    // MARK: - Private

    private func receiveLoop(
        taskId: UUID,
        task: URLSessionWebSocketTask,
        continuation: AsyncStream<WSEvent>.Continuation
    ) async {
        var retryCount = 0
        let maxRetries = 5
        let decoder = JSONDecoder()

        while !Task.isCancelled && retryCount < maxRetries {
            do {
                let message = try await task.receive()

                switch message {
                case .string(let text):
                    if let data = text.data(using: .utf8),
                       let event = try? decoder.decode(WSEvent.self, from: data) {
                        continuation.yield(event)

                        // 终态事件后结束
                        if event.type == "completed" || event.type == "error" {
                        continuation.finish()
                        disconnect(taskId: taskId)
                        return
                    }
                    }
                    retryCount = 0 // 重置重试计数

                case .data(let data):
                    if let event = try? decoder.decode(WSEvent.self, from: data) {
                        continuation.yield(event)
                    }
                    retryCount = 0

                @unknown default:
                    break
                }
            } catch {
                retryCount += 1
                // Exponential backoff
                let delay = min(1.0 * pow(2.0, Double(retryCount - 1)), 16.0)
                try? await Task.sleep(for: .seconds(delay))
            }
        }

        continuation.finish()
        disconnect(taskId: taskId)
    }
}
