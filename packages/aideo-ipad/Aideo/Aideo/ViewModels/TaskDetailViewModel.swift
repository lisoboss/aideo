import SwiftUI
import Observation

/// 任务详情 — v2: REST 获取，项目 WS 由 CanvasViewModel 管理
@Observable
final class TaskDetailViewModel {
    var task: TaskModel
    var isLoading: Bool = false
    var errorMessage: String?

    init(task: TaskModel) {
        self.task = task
    }
}
