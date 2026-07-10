# aideo-ipad (`packages/aideo-ipad/Aideo/Aideo/`)

SwiftUI canvas-based AI video generation. Not in uv workspace.

## Models/

| File | Purpose |
|------|---------|
| `PromptBlock.swift` | Card node: 7 `BlockType`s, `cardSize`, `sceneTag`, inline `GenerationParams` |
| `MediaOutputNode.swift` | Result node: `NodeContentType` (text/image/video), `OutputStatus`, chainable via `asInputText` |
| `ReferenceNode.swift` | PhotosPicker import, local file storage |
| `AIEnhanceNode.swift` | input→LLM→output, `AIStatus`, local fallback |
| `CanvasNode.swift` | `AnyCanvasNode` enum (4 types), unified id/position/color |
| `CanvasProject.swift` | SwiftData `@Model`, JSON-encoded node arrays + connections |
| `BlockConnection.swift` | sourceId→targetId between any node types |
| `Task.swift` | Backend mirror: 6 `TaskStatus`, snake_case CodingKeys |
| `WSEvent.swift` | WS event + `AnyCodable` for dynamic JSON |
| `GenerationParams.swift` | duration/resolution/style/seed/fps/cfgScale/steps, `asDictionary()` |
| `AssistModels.swift` | Structurize/Complete/Inspire request/response |

## Services/

| File | Purpose |
|------|---------|
| `APIClient.swift` | `actor`: REST (tasks/results/assist/health) |
| `WebSocketClient.swift` | `actor`: `AsyncStream<WSEvent>`, exponential backoff |
| `DownloadManager.swift` | `actor`: `Documents/AideoDownloads/`, progress callback |
| `PromptSerializer.swift` | Cards → `[场景]: content` format |

## ViewModels/

- **CanvasViewModel** (@Observable): 4 node arrays + connections, `collectInputs()` BFS trace-back, `submitGeneration()`, `autoLayout()` Kahn sort with per-node sizing
- **ProjectListViewModel** (@Observable): SwiftData CRUD, `duplicateProject()`
- **TaskDetailViewModel** (@Observable): WS subscribe, event timeline

## Views/Canvas/

- **CanvasView**: infinite ScrollView, dynamic sizing, `MagnificationGesture` + double-tap reset, 4-type dispatch
- **PromptCardView**: drag + resize handle, type-colored
- **MediaOutputNodeView**: 4-state (idle/generating/completed/failed), type `Picker`, glow highlight
- **ReferenceNodeView**: `PhotosPicker` + thumbnail
- **AIEnhanceNodeView**: TextField→process→output `ScrollView`
- **CardEditorView**: type grid + content + params `Picker`s
- **CanvasToolbar**: add node `Menu`, template/storyboard/auto-layout/clear
- **HandwritingOverlay**: `PencilOnlyCanvasView` (`hitTest` for finger passthrough), 3-stroke/5s auto-commit
- **TemplateLibraryView**: 18 presets × 6 categories
- **StoryboardBarView**: horizontal position clustering, scene cards

## Key Design Decisions

- **MVVM + @Observable**: iOS 17+, no Combine
- **SwiftData**: `CanvasProject` @Model with 4 JSON node arrays
- **Actor isolation**: `SWIFT_DEFAULT_ACTOR_ISOLATION` removed; `@Observable` auto-@MainActor
- **Canvas sizing**: `max(viewport, bbox + 600pt, 3000×2000)`, NaN guarded
- **Connections**: edge-to-edge `intersectRect()`, `TimelineView` flow animation (30px/s)
- **Generate flow**: BFS trace-back → serialize → `createTask()` → WS `AsyncStream` → update output node
- **Reference images**: base64-encoded as `reference_images` extraParams
- **Auto-layout**: Kahn sort → per-level max width + cumulated heights → center offset
