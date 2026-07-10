import SwiftUI

struct HealthSheetView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        NavigationStack {
            List {
                // 连接状态
                Section("服务器") {
                    LabeledContent("地址", value: appState.serverURL)
                    LabeledContent("API 版本", value: appState.healthInfo?.version ?? "—")
                    LabeledContent("状态") {
                        HStack(spacing: 4) {
                            Circle()
                                .fill(appState.isConnected ? Color.green : Color.red)
                                .frame(width: 6, height: 6)
                            Text(appState.isConnected ? "已连接" : "未连接")
                        }
                    }
                }

                // 服务状态
                if let services = appState.healthInfo?.services, !services.isEmpty {
                    Section("服务") {
                        ForEach(services.sorted(by: { $0.key < $1.key }), id: \.key) { name, status in
                            LabeledContent(name) {
                                HStack(spacing: 4) {
                                    Circle()
                                        .fill(status == "ok" || status == "connected" ? Color.green : Color.red)
                                        .frame(width: 6, height: 6)
                                    Text(status)
                                }
                            }
                        }
                    }
                }

                // 检查历史
                Section {
                    if let lastCheck = appState.lastCheckTime {
                        LabeledContent("上次检查", value: lastCheck.formatted(.dateTime.hour().minute().second()))
                    }
                    if appState.consecutiveFailures > 0 {
                        LabeledContent("连续失败", value: "\(appState.consecutiveFailures) 次")
                    }
                }
            }
            .navigationTitle("服务器状态")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("完成") { appState.showHealthSheet = false }
                }
            }
        }
        .presentationDetents([.medium, .large])
    }
}
