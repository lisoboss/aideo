import SwiftUI

/// 任务详情页 — 实时进度 + 事件时间线
struct TaskDetailView: View {
    @Environment(AppState.self) private var appState
    @State private var viewModel: TaskDetailViewModel

    init(task: TaskModel) {
        _viewModel = State(initialValue: TaskDetailViewModel(task: task))
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // 状态卡片
                statusCard

                // 进度条
                if !viewModel.task.status.isTerminal {
                    progressSection
                }

                // 提示词
                promptSection

                // 预览帧
                if !viewModel.task.previews.isEmpty {
                    previewsSection
                }

                // 事件时间线
                if !viewModel.events.isEmpty {
                    eventsTimeline
                }

                // 操作按钮
                actionsSection
            }
            .padding()
        }
        .background(Color(uiColor: .systemGroupedBackground))
        .navigationTitle("任务详情")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .principal) {
                // WS 连接指示灯
                HStack(spacing: 6) {
                    Circle()
                        .fill(viewModel.isLive ? Color.green : Color.secondary)
                        .frame(width: 6, height: 6)
                        .pulseAnimation(isActive: viewModel.isLive)
                    Text(viewModel.isLive ? "实时" : "离线")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .task {
            // 先 fetch 最新 task 数据
            if let fresh = try? await appState.apiClient.getTask(id: viewModel.task.id) {
                viewModel.task = fresh
            }
            // 订阅 WS
            viewModel.subscribe(ws: appState.wsClient)
        }
        .onDisappear {
            viewModel.unsubscribe(ws: appState.wsClient)
        }
    }

    // MARK: - Status Card

    private var statusCard: some View {
        HStack(spacing: 16) {
            Image(systemName: viewModel.task.status.iconName)
                .font(.largeTitle)
                .foregroundStyle(statusColor)

            VStack(alignment: .leading, spacing: 4) {
                Text(viewModel.task.status.displayName)
                    .font(.title3)
                    .fontWeight(.semibold)

                if let error = viewModel.task.errorMessage, viewModel.task.status == .failed {
                    Text(error)
                        .font(.caption)
                        .foregroundStyle(.red)
                }

                Text("创建于 \(viewModel.task.createdAt.formatted(.relative(presentation: .named)))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()
        }
        .padding()
        .background(Color(uiColor: .systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Progress

    private var progressSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("生成进度", systemImage: "wand.and.stars")
                .font(.headline)

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color(uiColor: .systemGray5))
                        .frame(height: 12)

                    RoundedRectangle(cornerRadius: 6)
                        .fill(statusColor)
                        .frame(width: geo.size.width * CGFloat(viewModel.task.progress / 100), height: 12)
                        .animation(.easeInOut(duration: 0.5), value: viewModel.task.progress)
                }
            }
            .frame(height: 12)

            HStack {
                Text("\(Int(viewModel.task.progress))%")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundStyle(statusColor)
                Spacer()
                if viewModel.isLive {
                    HStack(spacing: 4) {
                        ProgressView()
                            .scaleEffect(0.6)
                        Text("实时更新中")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .padding()
        .background(Color(uiColor: .systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Prompt

    private var promptSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("提示词", systemImage: "text.alignleft")
                .font(.headline)

            Text(viewModel.task.prompt)
                .font(.body)
                .foregroundStyle(.primary)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding()
        .background(Color(uiColor: .systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Previews

    private var previewsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("预览帧 (\(viewModel.task.previews.count))", systemImage: "photo.on.rectangle.angled")
                .font(.headline)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(viewModel.task.previews, id: \.self) { frame in
                        AsyncImage(url: appState.apiClient.previewURL(taskId: viewModel.task.id, frame: frame)) { phase in
                            switch phase {
                            case .success(let image):
                                image
                                    .resizable()
                                    .aspectRatio(contentMode: .fill)
                                    .frame(width: 120, height: 80)
                                    .clipShape(RoundedRectangle(cornerRadius: 6))
                            case .failure:
                                RoundedRectangle(cornerRadius: 6)
                                    .fill(Color(uiColor: .systemGray5))
                                    .frame(width: 120, height: 80)
                                    .overlay(Image(systemName: "photo.badge.exclamationmark").foregroundStyle(.secondary))
                            case .empty:
                                RoundedRectangle(cornerRadius: 6)
                                    .fill(Color(uiColor: .systemGray5))
                                    .frame(width: 120, height: 80)
                                    .overlay(ProgressView().scaleEffect(0.7))
                            @unknown default:
                                EmptyView()
                            }
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(uiColor: .systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Events Timeline

    private var eventsTimeline: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("事件时间线", systemImage: "clock.arrow.trianglehead.counterclockwise.rotate.90")
                .font(.headline)

            ForEach(viewModel.events.reversed()) { event in
                HStack(spacing: 10) {
                    Image(systemName: eventIcon(event.type))
                        .font(.caption)
                        .foregroundStyle(eventColor(event.type))
                        .frame(width: 20)

                    Text(eventTitle(event))
                        .font(.caption)
                        .foregroundStyle(.primary)

                    Spacer()

                    Text(event.timestamp.formatted(.dateTime.hour().minute().second()))
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
            }
        }
        .padding()
        .background(Color(uiColor: .systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Actions

    private var actionsSection: some View {
        HStack(spacing: 12) {
            // 取消
            if !viewModel.task.status.isTerminal {
                Button {
                    Task { await viewModel.cancelTask(client: appState.apiClient) }
                } label: {
                    Label("取消任务", systemImage: "xmark.circle")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .tint(.red)
            }

            // 下载（完成后显示）
            if viewModel.task.status == .completed {
                Button {
                    // 下载逻辑 Phase 4 实现
                } label: {
                    Label("下载视频", systemImage: "arrow.down.to.line")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            }
        }
    }

    // MARK: - Helpers

    private var statusColor: Color {
        switch viewModel.task.status {
        case .queued: .blue
        case .running: .cyan
        case .generating: .purple
        case .completed: .green
        case .failed: .red
        case .cancelled: .orange
        }
    }

    private func eventIcon(_ type: String) -> String {
        switch type {
        case "status_change": "arrow.triangle.branch"
        case "progress": "chart.line.uptrend.xyaxis"
        case "preview": "photo"
        case "completed": "checkmark.circle.fill"
        case "error": "xmark.octagon.fill"
        default: "circle"
        }
    }

    private func eventColor(_ type: String) -> Color {
        switch type {
        case "status_change": .blue
        case "progress": .purple
        case "preview": .orange
        case "completed": .green
        case "error": .red
        default: .secondary
        }
    }

    private func eventTitle(_ event: WSEvent) -> String {
        switch event.type {
        case "status_change":
            "状态更新: \(event.statusValue ?? "—")"
        case "progress":
            "进度: \(Int(event.progressValue ?? 0))%"
        case "preview":
            "预览帧就绪"
        case "completed":
            "生成完成"
        case "error":
            "错误: \(event.errorMessage ?? "未知")"
        default:
            event.type
        }
    }
}

// MARK: - Pulse Animation Modifier

private struct PulseModifier: ViewModifier {
    let isActive: Bool

    func body(content: Content) -> some View {
        content
            .scaleEffect(isActive ? 1.3 : 1.0)
            .opacity(isActive ? 0.6 : 1.0)
            .animation(
                isActive ? .easeInOut(duration: 0.8).repeatForever(autoreverses: true) : .default,
                value: isActive
            )
    }
}

extension View {
    func pulseAnimation(isActive: Bool) -> some View {
        modifier(PulseModifier(isActive: isActive))
    }
}
