import SwiftUI

/// 根布局 — 项目列表 + 画布
struct ContentView: View {
    @Environment(AppState.self) private var appState
    @Environment(ProjectListViewModel.self) private var projectVM

    var body: some View {
        NavigationSplitView {
            ProjectListView()
        } detail: {
            if let project = projectVM.selectedProject {
                NavigationStack {
                    CanvasView(project: project)
                }
            } else {
                VStack(spacing: 16) {
                    Image(systemName: "square.grid.2x2")
                        .font(.system(size: 48))
                        .foregroundStyle(.quaternary)
                    Text("选择一个项目或新建项目")
                        .font(.title3)
                        .foregroundStyle(.secondary)
                    Button("新建项目") {
                        projectVM.createProject()
                    }
                    .buttonStyle(.borderedProminent)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color(uiColor: .systemGroupedBackground))
            }
        }
    }
}

#Preview {
    ContentView()
        .environment(AppState())
        .environment(ProjectListViewModel())
}
