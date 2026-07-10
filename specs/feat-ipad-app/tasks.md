# Tasks v2: feat-ipad-app

> 生成时间：2026-07-02
> 基于：[spec.md](./spec.md) v2 + [plan.md](./plan.md) v2

## 进度
- [ ] 0 / 42 任务完成

---

## Phase 1 — 模型 + 项目系统

### Task 1: 创建 `AideoTests/Models/NodeModelsTests.swift`
- **文件**：`AideoTests/Models/NodeModelsTests.swift`
- **类型**：测试
- **依赖**：无
- **描述**：为 MediaOutputNode、ReferenceNode、AIEnhanceNode 编写 Codable 往返测试；为 CanvasNode 协议和 AnyCanvasNode 枚举编写 switch 覆盖测试
- **验收**：红灯

---

### Task 2: 实现 `Aideo/Models/MediaOutputNode.swift` + `ReferenceNode.swift` + `AIEnhanceNode.swift`
- **文件**：`Aideo/Models/MediaOutputNode.swift`
- **类型**：实现
- **依赖**：Task 1
- **描述**：创建 3 个节点模型：MediaOutputNode（status/progress/videoLocalPath/previewFrames）、ReferenceNode（mediaType/localURL/thumbnailData）、AIEnhanceNode（inputText/outputText/status）+ 各自状态枚举
- **验收**：Task 1 测试绿灯

---

### Task 3: 创建 `AideoTests/Models/CanvasNodeProtocolTests.swift`
- **文件**：`AideoTests/Models/CanvasNodeProtocolTests.swift`
- **类型**：测试
- **依赖**：Task 2（节点模型存在）, PromptBlock 已有
- **描述**：为 AnyCanvasNode 枚举编写测试：wrap/unwrap 四种节点类型、id/position 读写
- **验收**：红灯

---

### Task 4: 实现 `Aideo/Models/CanvasNode.swift`
- **文件**：`Aideo/Models/CanvasNode.swift`
- **类型**：实现
- **依赖**：Task 3
- **描述**：创建 CanvasNode 协议（id/position）+ AnyCanvasNode 枚举（4 cases），实现 id/position 计算属性
- **验收**：Task 3 测试绿灯

---

### Task 5: 创建 `AideoTests/Models/CanvasProjectTests.swift`
- **文件**：`AideoTests/Models/CanvasProjectTests.swift`
- **类型**：测试
- **依赖**：Task 4（AnyCanvasNode）
- **描述**：为 CanvasProject SwiftData @Model 编写 CRUD 测试：创建项目、序列化/反序列化四种节点列表、更新名称、删除项目
- **验收**：红灯

---

### Task 6: 实现 `Aideo/Models/CanvasProject.swift` + `BlockConnection.swift`
- **文件**：`Aideo/Models/CanvasProject.swift`
- **类型**：实现
- **依赖**：Task 5
- **描述**：创建 @Model CanvasProject（name + 4 个节点 JSON 字段 + connectionsJSON + 时间戳）+ BlockConnection（通用连线 sourceId/targetId）
- **验收**：Task 5 测试绿灯

---

### Task 7: 创建 `AideoTests/ViewModels/ProjectListViewModelTests.swift`
- **文件**：`AideoTests/ViewModels/ProjectListViewModelTests.swift`
- **类型**：测试
- **依赖**：Task 6（CanvasProject 模型）
- **描述**：为 ProjectListViewModel 编写测试：loadProjects、createProject（默认名称）、deleteProject、renameProject、空列表状态
- **验收**：红灯

---

### Task 8: 实现 `Aideo/ViewModels/ProjectListViewModel.swift`
- **文件**：`Aideo/ViewModels/ProjectListViewModel.swift`
- **类型**：实现
- **依赖**：Task 7
- **描述**：创建 @Observable ProjectListViewModel：projects/selectedProject、CRUD 方法、SwiftData context 注入
- **验收**：Task 7 测试绿灯

---

### Task 9: 删除旧侧边栏文件 + 实现 `Aideo/Views/Sidebar/ProjectListView.swift`
- **文件**：`Aideo/Views/Sidebar/ProjectListView.swift`
- **类型**：实现
- **依赖**：Task 8
- **描述**：创建项目列表视图：List 显示所有项目（名称+节点数+更新时间）、选中高亮、底部新建按钮、ContextMenu（重命名/删除）、连接状态指示灯
- **验收**：侧边栏显示项目列表 → 新建项目 → 重命名 → 删除

---

### Task 10: 修改 `Aideo/App/AppState.swift`
- **文件**：`Aideo/App/AppState.swift`
- **类型**：实现
- **依赖**：Task 8
- **描述**：selectedItem → selectedProject（CanvasProject?），移除 NavigationItem 依赖
- **验收**：编译通过

---

### Task 11: 修改 `Aideo/ContentView.swift`
- **文件**：`Aideo/ContentView.swift`
- **类型**：实现
- **依赖**：Task 9, Task 10
- **描述**：NavigationSplitView 改为 sidebar=ProjectListView / detail=CanvasView，根据 selectedProject 加载画布
- **验收**：侧边栏切换项目 → 画布更新

---

### Task 12: 修改 `Aideo/AideoApp.swift`
- **文件**：`Aideo/AideoApp.swift`
- **类型**：实现
- **依赖**：Task 11
- **描述**：注入 SwiftData modelContainer，创建默认项目（如果无项目），注入 ProjectListViewModel
- **验收**：App 首次启动自动创建默认项目 → 画布显示空引导

---

### Task 13: 清理旧文件
- **文件**：删除 `NavigationItem.swift`, `SidebarView.swift`, `TaskListView.swift`, `TaskRowView.swift`, `TaskListViewModel.swift`, `DownloadsView.swift`
- **类型**：清理
- **依赖**：Task 12（确保新架构已跑通）
- **描述**：移除 v1 架构残留文件
- **验收**：编译通过，无未使用引用

---

## Phase 2 — 输出节点 + 生成流程

### Task 14: 创建 `AideoTests/ViewModels/CanvasViewModelV2Tests.swift`
- **文件**：`AideoTests/ViewModels/CanvasViewModelV2Tests.swift`
- **类型**：测试
- **依赖**：Task 6（所有节点模型）
- **描述**：为 CanvasViewModel v2 编写测试：多节点管理（addNode/deleteNode/moveNode）、submitGeneration（追溯连线→提交任务）、节点高亮状态
- **验收**：红灯

---

### Task 15: 重写 `Aideo/ViewModels/CanvasViewModel.swift`
- **文件**：`Aideo/ViewModels/CanvasViewModel.swift`
- **类型**：实现
- **依赖**：Task 14
- **描述**：重写为 v2：管理 4 种节点数组 + 连线数组、AnyCanvasNode 统一操作、submitGeneration 追溯连线提交、高亮状态管理
- **验收**：Task 14 测试绿灯

---

### Task 16: 实现 `Aideo/Views/Canvas/MediaOutputNodeView.swift`
- **文件**：`Aideo/Views/Canvas/MediaOutputNodeView.swift`
- **类型**：实现
- **依赖**：Task 2（MediaOutputNode 模型）
- **描述**：输出节点 UI：空闲态（生成按钮+连线插槽）、生成中态（进度条+高亮脉冲动画）、完成态（视频缩略图+播放+下载按钮）、失败态（错误信息+重试按钮）
- **验收**：节点在画布上渲染 → 各状态切换正确 → 动画流畅

---

### Task 17: 修改 `Aideo/Views/Canvas/CanvasView.swift`
- **文件**：`Aideo/Views/Canvas/CanvasView.swift`
- **类型**：实现
- **依赖**：Task 15, Task 16
- **描述**：更新画布渲染：AnyCanvasNode 分发 4 种节点视图、连线层保留、项目加载/保存
- **验收**：画布显示已有提示词卡片+输出节点 → 拖拽正常 → 连线正常

---

### Task 18: 修改 `Aideo/Views/Canvas/CanvasToolbar.swift`
- **文件**：`Aideo/Views/Canvas/CanvasToolbar.swift`
- **类型**：实现
- **依赖**：Task 16
- **描述**：工具栏增加"输出节点""参考素材""AI增强"三个添加按钮
- **验收**：点击按钮 → 对应节点出现在画布上

---

### Task 19: 生成流程端到端 — 临时移除旧测试
- **文件**：`Aideo/Views/Canvas/CanvasView.swift`
- **类型**：集成
- **依赖**：Task 17, Task 18
- **描述**：确保完整生成流程跑通：输出节点 + 提示词卡片 → 点击生成 → WS 实时进度 → 视频出现在输出节点中
- **验收**：手动测试全流程

---

## Phase 3 — 参考素材 + AI 增强节点

### Task 20: 创建 `AideoTests/Views/ReferenceNodeViewModelTests.swift`
- **文件**：`AideoTests/Views/ReferenceNodeViewModelTests.swift`
- **类型**：测试
- **依赖**：Task 2（ReferenceNode）
- **描述**：为参考素材节点编写测试：importFromPhotoLibrary、生成缩略图、删除素材
- **验收**：红灯

---

### Task 21: 实现 `Aideo/Views/Canvas/ReferenceNodeView.swift`
- **文件**：`Aideo/Views/Canvas/ReferenceNodeView.swift`
- **类型**：实现
- **依赖**：Task 20
- **描述**：参考素材节点 UI：图片/视频缩略图、来源标签、PhotosPicker 导入、连线插槽
- **验收**：点击导入 → 相册选择 → 缩略图显示 → 可在画布上拖拽连线

---

### Task 22: 创建 `AideoTests/Views/AIEnhanceNodeViewModelTests.swift`
- **文件**：`AideoTests/Views/AIEnhanceNodeViewModelTests.swift`
- **类型**：测试
- **依赖**：Task 2（AIEnhanceNode）
- **描述**：为 AI 增强节点编写测试：输入→调用assist API→获取详细提示词、输出连接到提示词卡片
- **验收**：红灯

---

### Task 23: 实现 `Aideo/Views/Canvas/AIEnhanceNodeView.swift`
- **文件**：`Aideo/Views/Canvas/AIEnhanceNodeView.swift`
- **类型**：实现
- **依赖**：Task 22
- **描述**：AI 增强节点 UI：TextEditor 输入简单描述、处理按钮、加载动画、输出详细提示词预览、连线插槽
- **验收**：输入描述→点处理→显示生成的详细提示词→连线到卡片

---

## Phase 4 — 打磨

### Task 24: 节点高亮动画
- **文件**：`Aideo/Views/Canvas/`
- **类型**：实现
- **依赖**：Task 19（生成流程已通）
- **描述**：生成流程中当前节点脉冲发光动画（glow + scale）、连线高亮
- **验收**：点生成 → 相关节点顺序高亮 → 动画流畅

---

### Task 25: 空画布引导
- **文件**：`Aideo/Views/Canvas/CanvasView.swift`
- **类型**：实现
- **依赖**：Task 17
- **描述**：空画布显示引导：四种节点类型快捷入口 + 提示"添加节点开始创作"
- **验收**：新建项目 → 引导显示 → 点击入口添加节点 → 引导消失

---

### Task 26: 项目重命名/删除 UI
- **文件**：`Aideo/Views/Sidebar/ProjectListView.swift`
- **类型**：实现
- **依赖**：Task 9
- **描述**：完善项目操作：Alert 重命名、删除确认、复制项目
- **验收**：长按项目 → ContextMenu → 各操作正常

---

### Task 27: 错误处理与空状态
- **文件**：`Aideo/Views/`
- **类型**：实现
- **依赖**：Task 19
- **描述**：网络错误 Toast、生成失败节点显示错误、项目空状态、输出节点各状态转换平滑
- **验收**：断网 → Toast → 恢复 → 正常

---

### Task 28: 画布自动布局
- **文件**：`Aideo/ViewModels/CanvasViewModel.swift`
- **类型**：实现
- **依赖**：Task 15
- **描述**：自动整理按钮：按连线关系自动排列节点（拓扑排序 → 层级布局）
- **验收**：点"整理" → 节点按流程自动排列整齐

---

## 依赖关系图

```
Phase 1 (基础重构)
Task 1→2    (NodeModels)
Task 3→4    (CanvasNode protocol) ─── depends on Task 2
Task 5→6    (CanvasProject) ──────── depends on Task 4
Task 7→8    (ProjectListVM) ──────── depends on Task 6
Task 9        (ProjectListView) ───── depends on Task 8
Task 10       (AppState) ──────────── depends on Task 8
Task 11       (ContentView) ───────── depends on Task 9,10
Task 12       (AideoApp) ──────────── depends on Task 11
Task 13       (清理旧文件) ──────────── depends on Task 12

Phase 2 (输出节点)
Task 14→15  (CanvasVM v2) ────────── depends on Task 6
Task 16       (MediaOutputNodeView) ── depends on Task 2
Task 17       (CanvasView) ────────── depends on Task 15,16
Task 18       (CanvasToolbar) ──────── depends on Task 16
Task 19       (端到端集成) ──────────── depends on Task 17,18

Phase 3 (参考素材+AI)
Task 20→21  (ReferenceNode) ──────── depends on Task 2
Task 22→23  (AIEnhanceNode) ──────── depends on Task 2

Phase 4 (打磨)
Task 24-28 ─ all depend on Phase 2-3 核心完成
```
