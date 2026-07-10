import SwiftUI
import SwiftData

/// 项目列表侧边栏
struct ProjectListView: View {
    @Environment(AppState.self) private var appState
    @Environment(ProjectListViewModel.self) private var viewModel
    @Environment(\.modelContext) private var modelContext

    @State private var showRenameAlert = false
    @State private var renameText = ""
    @State private var projectToRename: CanvasProject?
    @State private var showSettings = false

    var body: some View {
        @Bindable var appState = appState
        @Bindable var viewModel = viewModel

        List(selection: Binding(
            get: { viewModel.selectedProject },
            set: { viewModel.selectedProject = $0 }
        )) {
            Section {
                ForEach(viewModel.projects) { project in
                    Label {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(project.name)
                                .font(.subheadline)
                                .lineLimit(1)
                            Text("\(project.nodeCount) 个节点")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    } icon: {
                        Image(systemName: "square.grid.2x2")
                            .foregroundStyle(.tint)
                    }
                    .tag(project)
                    .contextMenu {
                        Button {
                            projectToRename = project
                            renameText = project.name
                            showRenameAlert = true
                        } label: {
                            Label("重命名", systemImage: "pencil")
                        }
                        Button {
                            viewModel.duplicateProject(project)
                        } label: {
                            Label("复制", systemImage: "doc.on.doc")
                        }
                        Divider()
                        Button(role: .destructive) {
                            viewModel.deleteProject(project)
                        } label: {
                            Label("删除", systemImage: "trash")
                        }
                    }
                }
            } header: {
                Text("项目")
                    .font(.headline)
                    .foregroundStyle(.primary)
            }

            // 连接状态
            Section {
                Button {
                    appState.showHealthSheet = true
                } label: {
                    HStack {
                        Circle()
                            .fill(appState.isConnected ? Color.green : Color.red)
                            .frame(width: 8, height: 8)
                        Text(appState.isConnected ? "已连接" : "未连接")
                            .font(.caption)
                            .foregroundStyle(.secondary)

                        if appState.isCheckingHealth {
                            ProgressView()
                                .scaleEffect(0.6)
                                .frame(width: 8, height: 8)
                        }
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.caption2)
                            .foregroundStyle(.tertiary)
                    }
                }
                .buttonStyle(.plain)

                if let lastCheck = appState.lastCheckTime {
                    Text("上次检查 \(lastCheckText(lastCheck))")
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
            } header: {
                HStack {
                    Text("服务器")
                    Spacer()
                    Button {
                        showSettings = true
                    } label: {
                        Image(systemName: "gearshape")
                            .font(.caption)
                    }
                }
            }
        }
        .listStyle(.sidebar)
        .sheet(isPresented: $appState.showHealthSheet) {
            HealthSheetView()
        }
        .navigationTitle("Aideo")
        .safeAreaInset(edge: .bottom) {
            Button {
                viewModel.createProject()
            } label: {
                Label("新建项目", systemImage: "plus")
                    .font(.subheadline)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
            }
            .buttonStyle(.bordered)
            .padding(.horizontal, 12)
            .padding(.bottom, 8)
        }
        .alert("重命名项目", isPresented: $showRenameAlert) {
            TextField("项目名称", text: $renameText)
            Button("取消", role: .cancel) {}
            Button("确定") {
                if let p = projectToRename {
                    viewModel.renameProject(p, to: renameText)
                }
            }
        }
        .sheet(isPresented: $showSettings) {
            SettingsSheet()
        }
        .task {
            viewModel.configure(context: modelContext)
            viewModel.loadProjects()
            if viewModel.projects.isEmpty {
                viewModel.createProject()
            }
        }
    }

    private func lastCheckText(_ date: Date) -> String {
        let seconds = Date().timeIntervalSince(date)
        if seconds < 5 { return "刚刚" }
        return date.formatted(.relative(presentation: .named))
    }
}

/// 设置 Sheet
private struct SettingsSheet: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss

    @State private var serverURL: String = ""
    @State private var downloads: [DownloadedFile] = []

    var body: some View {
        NavigationStack {
            Form {
                Section("服务器地址") {
                    TextField("http://192.168.x.x:8000", text: $serverURL)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                        .onAppear { serverURL = appState.serverURL }
                }

                Section("AI 语言偏好") {
                    Picker("生成语言", selection: Binding(
                        get: { appState.language ?? "" },
                        set: { appState.language = $0.isEmpty ? nil : $0 }
                    )) {
                        Text("自动检测").tag("")
                        Text("中文").tag("zh")
                        Text("English").tag("en")
                        Text("日本語").tag("ja")
                        Text("한국어").tag("ko")
                    }
                }

                Section {
                    Button("保存并重连") {
                        appState.serverURL = serverURL
                        Task { await appState.checkHealth() }
                        dismiss()
                    }
                    .disabled(serverURL.isEmpty)
                }

                Section("下载管理") {
                    if downloads.isEmpty {
                        Label("暂无下载文件", systemImage: "folder")
                            .foregroundStyle(.secondary)
                    } else {
                        ForEach(downloads) { file in
                            VStack(alignment: .leading) {
                                Text(file.fileName).font(.caption)
                                Text(file.fileSizeFormatted).font(.caption2).foregroundStyle(.secondary)
                            }
                        }
                    }
                }
                .task {
                    downloads = await appState.downloadManager.listDownloads()
                }

                Section("关于") {
                    Label("Aideo v1.0", systemImage: "sparkles")
                    Label("iPad 画布式 AI 视频生成", systemImage: "paintbrush.pointed")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            .navigationTitle("设置")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("完成") { dismiss() }
                }
            }
        }
        .presentationDetents([.medium, .large])
    }
}

#Preview {
    ProjectListView()
        .environment(AppState())
        .environment(ProjectListViewModel())
}
