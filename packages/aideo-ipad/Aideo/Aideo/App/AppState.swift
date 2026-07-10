import SwiftUI
import Observation

/// 全局应用状态
@Observable
final class AppState {
    /// 后端服务器地址
    var serverURL: String = "http://192.168.31.3:8000" {
        didSet {
            apiClient = APIClient(baseURL: serverURL)
            wsClient = WebSocketClient(serverURL: serverURL)
        }
    }

    /// API 客户端
    private(set) var apiClient: APIClient

    /// WebSocket 客户端
    private(set) var wsClient: WebSocketClient

    /// 下载管理器
    let downloadManager = DownloadManager()

    /// 后端连接状态
    var isConnected: Bool = false
    var isCheckingHealth: Bool = false

    /// v2: 健康检查详情（版本号 + 各服务状态）
    var healthInfo: HealthInfo?
    var showHealthSheet: Bool = false

    /// 健康检查间隔
    var healthCheckInterval: TimeInterval = 30.0

    /// 上一次检查时间
    var lastCheckTime: Date?

    /// 连接失败次数
    var consecutiveFailures: Int = 0

    /// v2: 当前云端项目 ID，用于项目级 WS 和同步
    var currentProjectId: UUID?

    /// 语言偏好（传给 AI assist/generate 端点）。nil = 自动检测
    var language: String? {
        get { UserDefaults.standard.string(forKey: "ai_language") }
        set { UserDefaults.standard.set(newValue, forKey: "ai_language") }
    }

    /// 私有轮询 Task
    private var monitorTask: Task<Void, Never>?

    init() {
        let url = "http://192.168.31.3:8000"
        self.apiClient = APIClient(baseURL: url)
        self.wsClient = WebSocketClient(serverURL: url)
    }

    // MARK: - Health Monitor

    func startHealthMonitor() {
        stopHealthMonitor()
        monitorTask = Task { [weak self] in
            while !Task.isCancelled {
                await self?.checkHealth()
                try? await Task.sleep(for: .seconds(self?.healthCheckInterval ?? 5))
            }
        }
    }

    func stopHealthMonitor() {
        monitorTask?.cancel()
        monitorTask = nil
    }

    func checkHealth() async {
        isCheckingHealth = true
        defer {
            isCheckingHealth = false
            lastCheckTime = Date()
        }
        if let info = await apiClient.healthCheck() {
            healthInfo = info
            isConnected = info.status == "ok"
            consecutiveFailures = 0
        } else {
            isConnected = false
            consecutiveFailures += 1
        }
    }
}
