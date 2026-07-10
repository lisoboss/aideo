import SwiftUI
import Observation

/// 任务详情 + WebSocket 实时进度
@Observable
final class TaskDetailViewModel {
    var task: TaskModel
    var isLoading: Bool = false
    var errorMessage: String?

    /// WebSocket 事件历史（用于时间线展示）
    var events: [WSEvent] = []

    /// WS 连接状态
    var isLive: Bool = false

    @ObservationIgnored
    private var wsTask: Task<Void, Never>?

    init(task: TaskModel) {
        self.task = task
    }

    // MARK: - WebSocket

    /// 订阅实时进度
    @MainActor
    func subscribe(ws: WebSocketClient) {
        isLive = true
        events.removeAll()

        wsTask = Task {
            let stream = await ws.connect(taskId: task.id)
            for await event in stream {
                await MainActor.run { handleEvent(event) }
            }
            await MainActor.run { isLive = false }
        }
    }

    /// 取消订阅
    func unsubscribe(ws: WebSocketClient) {
        wsTask?.cancel()
        wsTask = nil
        Task { await ws.disconnect(taskId: task.id) }
        isLive = false
    }

    // MARK: - Actions

    @MainActor
    func cancelTask(client: APIClient) async {
        do {
            let updated = try await client.cancelTask(id: task.id)
            task = updated
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Private

    private func handleEvent(_ event: WSEvent) {
        events.append(event)

        switch event.type {
        case "status_change":
            if let statusStr = event.statusValue,
               let newStatus = TaskStatus(rawValue: statusStr) {
                task.status = newStatus
            }
        case "progress":
            if let progress = event.progressValue {
                task.progress = progress
            }
        case "preview":
            if let frame = event.data?["frame"]?.stringValue {
                task.previews.append(frame)
            }
        case "completed":
            task.status = .completed
            if let path = event.data?["result_path"]?.stringValue {
                task.resultPath = path
            }
        case "error":
            task.status = .failed
            task.errorMessage = event.errorMessage
        default:
            break
        }
    }
}
