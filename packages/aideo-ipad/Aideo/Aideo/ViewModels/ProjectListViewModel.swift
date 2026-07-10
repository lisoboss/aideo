import SwiftUI
import SwiftData
import Observation

/// 项目列表状态管理
@Observable
final class ProjectListViewModel {
    var projects: [CanvasProject] = []
    var selectedProject: CanvasProject?
    var errorMessage: String?

    private var modelContext: ModelContext?

    func configure(context: ModelContext) {
        self.modelContext = context
    }

    // MARK: - CRUD

    @MainActor
    func loadProjects() {
        guard let context = modelContext else { return }
        let descriptor = FetchDescriptor<CanvasProject>(
            sortBy: [SortDescriptor(\.updatedAt, order: .reverse)]
        )
        do {
            projects = try context.fetch(descriptor)
            if selectedProject == nil, let first = projects.first {
                selectedProject = first
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    @MainActor
    func createProject(name: String = "未命名项目") {
        guard let context = modelContext else { return }
        let project = CanvasProject(name: name)
        context.insert(project)
        try? context.save()
        projects.insert(project, at: 0)
        selectedProject = project
    }

    @MainActor
    func deleteProject(_ project: CanvasProject) {
        guard let context = modelContext else { return }
        context.delete(project)
        try? context.save()
        projects.removeAll { $0.id == project.id }
        if selectedProject?.id == project.id {
            selectedProject = projects.first
        }
    }

    @MainActor
    func renameProject(_ project: CanvasProject, to name: String) {
        project.name = name
        try? modelContext?.save()
        // 触发 UI 刷新
        if let idx = projects.firstIndex(where: { $0.id == project.id }) {
            projects[idx] = project
        }
    }

    @MainActor
    func duplicateProject(_ project: CanvasProject) {
        let copy = CanvasProject(
            name: "\(project.name) 副本",
            promptBlocks: project.promptBlocks,
            mediaOutputs: project.mediaOutputs,
            referenceNodes: project.referenceNodes,
            aiEnhanceNodes: project.aiEnhanceNodes,
            connections: project.connections
        )
        modelContext?.insert(copy)
        try? modelContext?.save()
        projects.insert(copy, at: 0)
        selectedProject = copy
    }
}
