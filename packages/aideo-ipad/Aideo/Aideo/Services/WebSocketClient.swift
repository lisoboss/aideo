import Foundation

// MARK: - Client

/// WebSocket 客户端 — 封装 aideo-serv 项目级实时进度连接
actor WebSocketClient {
    private let serverURL: String
    private var projectTask: URLSessionWebSocketTask?
    private var projectSession: URLSession?

    init(serverURL: String) {
        self.serverURL = serverURL
    }

    // MARK: - Project-Level WebSocket

    /// 连接项目 WebSocket，单连接承载项目内所有任务事件。
    /// 发送 connected 快照 + 流式推送类型化事件。
    func connectProject(projectId: UUID) -> AsyncStream<ProjectWSEvent> {
        AsyncStream { continuation in
            let wsURL = serverURL
                .replacingOccurrences(of: "http://", with: "ws://")
                .replacingOccurrences(of: "https://", with: "wss://")

            guard let url = URL(string: "\(wsURL)/api/v1/ws/projects/\(projectId.uuidString)") else {
                continuation.finish()
                return
            }

            let session = URLSession(configuration: .default)
            let task = session.webSocketTask(with: url)

            projectSession = session
            projectTask = task

            task.resume()

            Task { [weak self] in
                await self?.projectReceiveLoop(projectId: projectId, task: task, continuation: continuation)
            }
        }
    }

    /// 断开项目 WebSocket
    func disconnectProject() {
        projectTask?.cancel(with: .normalClosure, reason: nil)
        projectTask = nil
        projectSession = nil
    }

    /// 断开所有连接
    func disconnectAll() {
        disconnectProject()
    }

    // MARK: - Private: Project Receive Loop

    private let v2EventDecoder = ProjectWSEventDecoder()

    private func projectReceiveLoop(
        projectId: UUID,
        task: URLSessionWebSocketTask,
        continuation: AsyncStream<ProjectWSEvent>.Continuation
    ) async {
        var retryCount = 0
        let maxRetries = 10

        while !Task.isCancelled && retryCount < maxRetries {
            do {
                let message = try await task.receive()

                switch message {
                case .string(let text):
                    if let event = v2EventDecoder.decode(from: text) {
                        continuation.yield(event)

                        if case .error = event {
                            continuation.finish()
                            disconnectProject()
                            return
                        }
                    }
                    retryCount = 0

                case .data(let data):
                    if let text = String(data: data, encoding: .utf8),
                       let event = v2EventDecoder.decode(from: text) {
                        continuation.yield(event)
                    }
                    retryCount = 0

                @unknown default:
                    break
                }
            } catch {
                retryCount += 1
                let delay = min(1.0 * pow(2.0, Double(retryCount - 1)), 16.0)
                try? await Task.sleep(for: .seconds(delay))
            }
        }

        continuation.finish()
        disconnectProject()
    }
}
