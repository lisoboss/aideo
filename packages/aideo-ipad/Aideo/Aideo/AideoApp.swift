import SwiftUI
import SwiftData

@main
struct AideoApp: App {
    @State private var appState = AppState()
    @State private var projectVM = ProjectListViewModel()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(appState)
                .environment(projectVM)
                .onAppear {
                    appState.startHealthMonitor()
                }
        }
        .modelContainer(for: [CanvasProject.self])
    }
}
