import SwiftUI

/// 任务详情页 — v2: REST 获取 + 静态展示
struct TaskDetailView: View {
    @Environment(AppState.self) private var appState
    @State private var viewModel: TaskDetailViewModel

    init(task: TaskModel) {
        _viewModel = State(initialValue: TaskDetailViewModel(task: task))
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                statusCard

                if !viewModel.task.status.isTerminal {
                    progressSection
                }

                promptSection

                if !viewModel.task.previews.isEmpty {
                    previewsSection
                }
            }
            .padding()
        }
        .background(Color(uiColor: .systemGroupedBackground))
        .navigationTitle("任务详情")
        .navigationBarTitleDisplayMode(.inline)
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
}
