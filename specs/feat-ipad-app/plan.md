# Technical Plan v2: feat-ipad-app

> 基于 spec v2（画布中心化 + 多项目）

## 架构概览

```
┌──────────────────────────────────────────────────────────┐
│                    Aideo iPad App                         │
│                                                           │
│  NavigationSplitView                                      │
│  ┌──────────┬─────────────────────────────────────────┐   │
│  │ Sidebar  │              Canvas                      │   │
│  │          │                                         │   │
│  │ 项目列表  │  ┌────┐  ┌──────┐  ┌────────┐         │   │
│  │          │  │提示│  │参考图 │  │输出节点│         │   │
│  │ 🎬 短片  │  │词卡│╌╌│ 📷   │╌╌│ [生成] │         │   │
│  │ 🌅 风景  │  └────┘  └──────┘  │ [预览] │         │   │
│  │ 🐱 猫咪  │                    └────────┘         │   │
│  │ [+ 新建] │  ┌──────────┐                         │   │
│  │          │  │ AI 增强  │                         │   │
│  │ 连接状态  │  │ 描述→详细│                         │   │
│  └──────────┘  └──────────┘                         │   │
│                                        2000×1500 画布 │
└──────────────────────────────────────────────────────────┘
```

**核心模式**：MVVM（@Observable）+ SwiftData 持久化

**关键变更 vs v1**：
| v1 | v2 |
|----|----|
| 侧边栏固定3个Tab | 侧边栏 = 项目列表（动态） |
| TaskListView 独立页面 | 生成记录在画布上=输出节点 |
| DownloadsView 独立页面 | 下载功能内嵌输出节点 |
| 只有提示词卡片 | 4种节点类型 |

---

## 目录结构

```
Aideo/
├── App/
│   ├── AideoApp.swift                 # [修改] 注入 AppState + modelContainer
│   └── AppState.swift                 # [修改] selectedProject 替代 selectedItem
│
├── Models/
│   ├── CanvasProject.swift            # [新增] SwiftData @Model — 项目
│   ├── PromptBlock.swift              # [已有修改] 节点基类型
│   ├── BlockConnection.swift          # [新增] 通用连线（任意节点间）
│   ├── MediaOutputNode.swift          # [新增] 媒体输出节点模型
│   ├── ReferenceNode.swift            # [新增] 参考素材节点模型
│   ├── AIEnhanceNode.swift            # [新增] AI增强节点模型
│   ├── CanvasNode.swift               # [新增] 节点协议 + 枚举
│   ├── Task.swift                     # [已有] 后端任务模型
│   ├── GenerationParams.swift         # [已有] 参数内嵌到卡片
│   └── WSEvent.swift                  # [已有]
│
├── Services/
│   ├── APIClient.swift                # [已有]
│   ├── WebSocketClient.swift          # [已有]
│   ├── DownloadManager.swift          # [已有]
│   └── PromptSerializer.swift         # [已有]
│
├── ViewModels/
│   ├── CanvasViewModel.swift          # [重写] 管理4种节点 + 连线 + 生成流程
│   └── ProjectListViewModel.swift     # [新增] 项目 CRUD
│
├── Views/
│   ├── ContentView.swift              # [修改] NavigationSplitView 绑定项目
│   │
│   ├── Sidebar/
│   │   └── ProjectListView.swift      # [重写] 替代 SidebarView
│   │
│   ├── Canvas/
│   │   ├── CanvasView.swift           # [修改] 渲染4种节点
│   │   ├── PromptCardView.swift       # [已有]
│   │   ├── MediaOutputNodeView.swift  # [新增] 输出节点：生成按钮+预览+下载
│   │   ├── ReferenceNodeView.swift    # [新增] 参考素材节点：缩略图+来源
│   │   ├── AIEnhanceNodeView.swift    # [新增] AI节点：输入+输出+处理动画
│   │   ├── CardEditorView.swift       # [已有]
│   │   └── CanvasToolbar.swift        # [修改] 适配4种节点添加入口
│   │
│   └── Player/
│       └── VideoPlayerView.swift       # [已有]
│
└── Utils/
    └── ColorHex.swift                  # [已有]
```

---

## 核心数据模型

### CanvasProject（SwiftData）
```swift
@Model
final class CanvasProject {
    var id: UUID
    var name: String
    var promptBlocksJSON: String       // [PromptBlock]
    var mediaOutputsJSON: String       // [MediaOutputNode]
    var referenceNodesJSON: String     // [ReferenceNode]
    var aiEnhanceNodesJSON: String     // [AIEnhanceNode]
    var connectionsJSON: String        // [BlockConnection]
    var createdAt: Date
    var updatedAt: Date
}
```

### 节点系统
```swift
// 节点协议
protocol CanvasNode: Identifiable {
    var id: UUID { get }
    var position: CGPoint { get set }
}

// 4 种节点
struct PromptBlock: CanvasNode, Codable { ... }       // 已有
struct MediaOutputNode: CanvasNode, Codable { ... }   // 新增
struct ReferenceNode: CanvasNode, Codable { ... }     // 新增
struct AIEnhanceNode: CanvasNode, Codable { ... }     // 新增

// 统一枚举（画布渲染用）
enum AnyCanvasNode: Identifiable {
    case promptBlock(PromptBlock)
    case mediaOutput(MediaOutputNode)
    case reference(ReferenceNode)
    case aiEnhance(AIEnhanceNode)

    var id: UUID { ... }
    var position: CGPoint { get set }
}
```

### MediaOutputNode
```swift
struct MediaOutputNode: Identifiable, Codable {
    var id: UUID
    var position: CGPoint
    var taskId: UUID?          // 关联的后端任务
    var status: OutputStatus   // idle / generating / completed / failed
    var videoLocalPath: String?
    var previewFrames: [String]
    var promptSummary: String  // 关联的提示词摘要
    var progress: Double       // 0-100
    var errorMessage: String?
}

enum OutputStatus: String, Codable {
    case idle, generating, completed, failed
}
```

### ReferenceNode
```swift
struct ReferenceNode: Identifiable, Codable {
    var id: UUID
    var position: CGPoint
    var mediaType: ReferenceMediaType  // image / video
    var localURL: String               // 本地文件路径
    var thumbnailData: Data?           // 缩略图缓存
    var sourceLabel: String            // "相册" / "文件"
}
```

### AIEnhanceNode
```swift
struct AIEnhanceNode: Identifiable, Codable {
    var id: UUID
    var position: CGPoint
    var inputText: String          // 简单描述
    var outputText: String         // LLM 输出详细提示词
    var status: AIStatus           // idle / processing / done / error
}

enum AIStatus: String, Codable {
    case idle, processing, done, error
}
```

### BlockConnection（通用化）
```swift
struct BlockConnection: Identifiable, Codable {
    var id: UUID
    var sourceId: UUID    // 任意 CanvasNode.id
    var targetId: UUID    // 任意 CanvasNode.id
}
```

---

## 侧边栏 — 项目列表

```
┌────────────────────┐
│ Aideo              │
│ ────────────────── │
│ ● 赛博朋克短片      │  ← 选中态高亮
│   3 个节点 · 2h前   │
│                     │
│   夕阳海滩          │
│   5 个节点 · 昨天   │
│                     │
│   猫咪日常          │
│   1 个节点 · 3天前  │
│                     │
│ ────────────────── │
│ ＋ 新建项目         │
│                     │
│ 服务器 ● 已连接     │
└────────────────────┘
```

- **选中项目**：画布切换到该项目
- **新建**：创建空白项目，自动选中
- **长按/右键**：ContextMenu → 重命名、复制、删除
- **连接状态**：底部保留

---

## 数据流

### 生成流程
```
1. 用户在画布上排列节点，连线到输出节点
2. 点击输出节点的 [生成] 按钮
                     │
3. CanvasViewModel.submitGeneration(outputNodeId)
   ├─ 沿连线追溯到所有提示词/参考/AI节点
   ├─ PromptSerializer.serialize(提示词卡片们)
   ├─ APIClient.createTask(prompt, params)
   │       │
   │   ← TaskModel (queued)
   │       │
   ├─ WebSocketClient.connect(taskId)
   │       │
   │   AsyncStream<WSEvent> ──→ 更新:
   │       ├─ status_change → 高亮当前处理中的节点
   │       ├─ progress      → 更新输出节点进度条
   │       ├─ preview       → 添加预览帧到输出节点
   │       ├─ completed     → 输出节点状态=completed，视频就绪
   │       └─ error         → 输出节点显示错误信息
   │
4. 用户点击 [预览] → 播放视频
5. 用户点击 [下载] → DownloadManager.download() → 本地保存
```

### 项目切换
```
侧边栏点击项目
  └─ AppState.selectedProject = project
       └─ CanvasViewModel.load(project)
            ├─ 反序列化所有节点 JSON
            ├─ 渲染画布
            └─ 画布滚动到合适位置
```

---

## 实施阶段

### Phase 1 — 模型 + 项目系统（Foundation v2）
**目标**：项目 CRUD 可用，侧边栏显示项目列表，画布随项目切换

**产出**：
- `CanvasProject.swift` — SwiftData @Model
- `MediaOutputNode.swift`, `ReferenceNode.swift`, `AIEnhanceNode.swift` — 3 个新节点模型
- `CanvasNode.swift` — 协议 + AnyCanvasNode 枚举
- `BlockConnection.swift` — 通用连线模型
- `ProjectListViewModel.swift` — 项目 CRUD
- `ProjectListView.swift` — 侧边栏项目列表（替代 SidebarView）
- `AppState.swift` [修改] — selectedProject 替代 selectedItem
- `ContentView.swift` [修改] — 绑定项目
- `AideoApp.swift` [修改] — modelContainer + 默认项目创建
- 删除不再需要的文件：TaskListView, TaskRowView, TaskListViewModel, DownloadsView, NavigationItem, SidebarView

**验证**：侧边栏显示项目 → 新建/切换/删除项目 → 画布内容随项目切换

### Phase 2 — 输出节点 + 生成流程（Output Node）
**目标**：媒体输出节点完整可用，能触发生成、实时进度、预览视频

**产出**：
- `MediaOutputNodeView.swift` — 输出节点 UI（生成按钮/进度/预览/下载）
- `CanvasViewModel.swift` [重写] — 多节点管理 + 提交生成逻辑
- `CanvasToolbar.swift` [修改] — 添加"输出节点"入口
- `CanvasView.swift` [修改] — 渲染4种节点类型

**验证**：添加输出节点 → 连提示词卡片 → 点生成 → WS 实时进度 → 视频出现在节点中

### Phase 3 — 参考素材 + AI 增强节点（Remaining Nodes）
**目标**：4 种节点全部可用

**产出**：
- `ReferenceNodeView.swift` — 参考素材 UI（相册选择/缩略图/拖入）
- `AIEnhanceNodeView.swift` — AI 增强 UI（输入框/处理动画/输出预览）

**验证**：导入相册图片作为参考节点 → AI增强节点输入→输出详细提示词 → 全部可在画布上连线组合

### Phase 4 — 打磨（Polish）
**目标**：体验优化

**产出**：
- 节点高亮动画（处理中脉冲发光）
- 项目复制/重命名
- 画布自动布局（整理节点）
- 空画布引导
- 错误/加载状态完善
