# 2026-07-10 — Aideo v2.0 Full-Stack

## API v2.0 协议设计

重新设计 API，以 iPad 画布为第一客户端（aideo-cli 降级为测试工具）。

### 新增端点（16 REST + 1 WS）

| 端点 | 用途 |
|------|------|
| `POST /projects` | 项目 CRUD（canvas_data 1:1 对应 iPad SwiftData） |
| `GET/PATCH/DELETE /projects/{id}` | 项目详情/更新/删除 |
| `GET /projects/{id}/tasks` | 项目下任务列表 |
| `GET /projects/{id}/assets` | 项目素材列表 |
| `POST /assets` | 素材上传（multipart, 50MB） |
| `GET/DELETE /assets/{id}` | 素材元数据/删除 |
| `POST /generate` | 结构化画布提交（PromptBlock[] + connections + asset_id） |
| `POST /canvas/structure` | 自由文本 → 类型化 PromptBlock |
| `POST /canvas/complete` | 上下文 → 补全建议 |
| `POST /canvas/inspire` | 主题 → 灵感模板 |
| `POST /canvas/correct` | AI 智能纠错（语音转文本后处理） |
| `POST /canvas/edit-image` | AI 图片编辑（composite / replace_character / inpainting / style_transfer） |
| `POST /canvas/upscale` | 图片超分（2x/4x） |
| `GET /ai/providers` | AI 供应商列表 |
| `WS /ws/projects/{id}` | 项目级多路复用 WebSocket（替代每任务独立 WS） |

### 删除的 v1 端点

`POST/GET/DELETE /tasks`, `WS /ws/tasks/{id}` 全部移除。不再兼容 v1。

### 关键设计变更

| 旧 | 新 |
|----|-----|
| 扁平字符串 prompt | 结构化 PromptBlock[] + connections |
| base64 图片进 JSON | asset_id 引用 |
| 每任务独立 WS | 单项目 WS 多路复用 |
| 泛型 `{type, data}` WS 事件 | 类型化 `task.progress` / `task.completed` |

> 文件：`docs/API.md`, `specs/feat-ipad-app/API.md`

---

## iPad 端全量实现

### 新建文件

| 文件 | 说明 |
|------|------|
| `Models/APIv2Models.swift` | GenerateRequest/Response, Project, CanvasData, Asset, ProjectWSEvent（8 种类型化事件）, MaskRegion, EditImageRequest, UpscaleRequest, CorrectRequest/Response, AIProvider, HealthInfo |
| `Models/AnyCodable.swift` | 动态 JSON 解码（替代 WSEvent.swift） |
| `Services/SpeechRecognizer.swift` | 录音（AVAudioEngine）→ 积攒 PCM → 停止时发完整 WAV → WS /ws/transcribe 转录 |
| `Services/TranscriptPostProcessor.swift` | 转录后 AI 纠错（调用 /canvas/correct） |
| `Views/Sidebar/HealthSheetView.swift` | 服务端状态详情 sheet（版本号 + 各服务状态） |

### 删除文件

| 文件 | 原因 |
|------|------|
| `Services/PromptSerializer.swift` | 序列化移至后端，客户端发结构化数据 |
| `Models/WSEvent.swift` | 泛型 v1 事件 → 类型化 v2 事件 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `App/AppState.swift` | +speechRecognizer, +healthInfo, +language, +currentProjectId |
| `Models/Task.swift` | +projectId, +outputNodeId, +promptStructured |
| `Models/AssistModels.swift` | AssistBlock +params, v2 Complete/Inspire shapes, +ai_provider, +language |
| `Models/GenerationParams.swift` | +aspectRatio, +imageQuality |
| `Services/APIClient.swift` | +16 v2 方法：generate, Project/Asset CRUD, Canvas Assist, correctTranscript, listAIProviders, editImage, upscaleImage |
| `Services/WebSocketClient.swift` | +connectProject（项目级 WS），删除 v1 per-task WS |
| `ViewModels/CanvasViewModel.swift` | CollectedInputs struct, v2 submitGeneration, 画布级共享 WS（connectProjectWS/disconnectProjectWS）, processAIEnhance→[AssistBlock], syncFromProject, exportCanvasData |
| `ViewModels/TaskDetailViewModel.swift` | 简化为纯 REST |
| `Views/Canvas/CardEditorView.swift` | +🎤 语音输入按钮（三态反馈） |
| `Views/Canvas/AIEnhanceNodeView.swift` | +🎤 语音输入, handleVoiceInput |
| `Views/Canvas/CanvasView.swift` | load(from:ws:), disconnectProjectWS |
| `Views/Tasks/TaskDetailView.swift` | 移除 v1 WS 事件时间线 |
| `Views/Sidebar/ProjectListView.swift` | 连接状态可点击 → HealthSheetView, 语言偏好 Picker |
| `Aideo.xcodeproj/project.pbxproj` | +NSMicrophoneUsageDescription |

---

## aideo-runtime HTTP+SSE 重构

从 WebSocket 内部协议改为 HTTP+SSE。

### 变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `provider.py` | 重写 | BaseProvider 简化为 load/unload/run + ProgressStatus + cancel/is_cancelled |
| `server.py` | 重写 | 去掉 WS client，改为 FastAPI + SSE 路由 + ProviderManager（auto load/unload + idle sweeper） |
| `speech/faster_whisper.py` | 重写 | 实现新接口，yield ProgressStatus，check is_cancelled |
| `speech/provider.py` | 更新 | 对接新 BaseProvider |
| `*/__init__.py` | 更新 | 各 category 导出 PROVIDERS 注册表 |
| `pyproject.toml` | 更新 | +sse-starlette |
| `README.md` | 新建 | 设计理念 + 编码规则 |

### 新路由

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/{category}/{name}` | 运行推理，SSE 流式返回 |
| `GET` | `/api/v1/{category}` | 列出品类下的 provider |
| `GET` | `/api/v1` | 列出所有 |
| `GET` | `/health` | 健康检查 |

### 关键特性

- **按需加载**：首次请求自动 `load()` model
- **空闲释放**：5 分钟无请求自动 `unload()`（后台 sweeper）
- **内存抢占**：`X-Memory-Preempt: true` header → 释放所有其他 model
- **客户端断开停止**：SSE 断开 → `CancelledError` → `provider.cancel()`

---

## aideo-serv WS → HTTP+SSE 重构

aideo-serv 内部去掉 WebSocket，改用 HTTP+SSE 调用 aideo-runtime。

### 变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/inference_client.py` | 新建 | HTTP+SSE client（POST runtime → SSE → TaskCallbacks） |
| `services/inference_manager.py` | 删除 | WS-based 推理服务管理 |
| `api/tasks.py` | 修改 | `_submit_to_inference()` → `client.run(task_type, payload, callbacks)` |
| `api/generate.py` | 修改 | 复用 tasks.py 的 `_submit_to_inference` |
| `api/ws.py` | 修改 | 删除 `/ws/internal/inference`，transcribe 改用 HTTP call |
| `api/router.py` | 修改 | health 去掉 WS 状态检查 |
| `config.py` | 修改 | `inference_url` → `runtime_url` |
| `dependencies.py` | 修改 | `get_inference_manager` → `get_inference_client` |
| `models/events.py` | 修改 | 删除 InferenceMessage 等 4 个内部协议类型 |
| `services/ai_client.py` | 修改 | 删除 WS 依赖 |
| `tests/test_config.py` | 修改 | `inference_url` → `runtime_url` |

### 测试

161 tests passed, 0 failures.

---

## iPad 契约对齐修复（backend → iPad 同步）

WS→HTTP+SSE 重构属 **serv↔runtime 内部协议**，客户端 REST/WS 契约未变，故重构本身无需改 iPad。但对齐验证中发现 iPad 与后端**客户端契约**存在既有偏差，导致 iPad 实际无法解码后端响应，本次修复。

### 修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `Services/APIClient.swift` | 修改 | +`makeDecoder()`/`parseBackendDate()`，配置 ISO8601 日期解码策略 |
| `Models/APIv2Models.swift` | 修改 | WS 事件 payload 中后端不保证的字段改为可选 |

### 变更要点

- **日期解码（阻塞级）**：`JSONDecoder` 默认 `.deferredToDate` 期望数字时间戳，而后端 `TaskModel.created_at/updated_at` 为 ISO8601 字符串（生产带微秒 + `+00:00`）。此前任何含 `TaskModel` 的响应（`/generate`、项目任务列表）均解码失败。新增 `.custom` 策略，依次尝试 带小数秒 → 不带小数秒 → 裸时间（UTC）。仅 `TaskModel` 用 `Date`（`Project`/`Asset` 用 `String`，`CanvasProject` 为本地 SwiftData），影响面可控。
- **`task.preview` 丢帧**：后端 `_broadcast` 只下发 `frame_url`，不含 `frame_index`，而 iPad `TaskPreviewPayload.frame_index` 为非可选 `Int` → 预览事件静默丢弃。改为 `Int?`；`CanvasViewModel` 本就不消费该字段。
- **容忍未文档化字段**：API.md 未约定 `timestamp`（后端仅经 `WSEvent.model_dump()` 附带下发），7 个 payload 的 `timestamp` 一并改为可选，遵循"宽容读取"，防止后端 `WSEvent` 再次重构时二次破坏。
- **`edit-image`/`upscale`**：iPad 调用 `/canvas/edit-image`、`/canvas/upscale`，后端尚未实现（协议前置声明，commit `ddab53d`），保持现状，客户端遇 404 优雅报错。
- **验证**：`xcodebuild -scheme Aideo -destination 'generic/platform=iOS Simulator'` 构建通过（EXIT 0，仅遗留 `SpeechRecognizer.swift` 无关告警）。

---

## 涉及文件总览

```
aideo/
├── docs/
│   ├── API.md                              # v2.0 API 协议（17 REST + 2 WS）
│   └── changes/
│       └── changed-2026-07-10-aideo-v2.md  # 本文件
├── specs/feat-ipad-app/
│   ├── API.md                              # 同步副本
│   └── todo.md                             # 任务清单 + 变更日志
├── packages/
│   ├── aideo-serv/                         # 后端 — 161 tests
│   │   ├── api/tasks.py, generate.py, ws.py, router.py
│   │   ├── models/events.py (清理)
│   │   ├── services/inference_client.py (新), inference_manager.py (删)
│   │   └── config.py, dependencies.py
│   ├── aideo-runtime/                      # 推理运行时
│   │   ├── provider.py, server.py (重写)
│   │   ├── speech/faster_whisper.py, provider.py
│   │   ├── */__init__.py (PROVIDERS 注册表)
│   │   ├── README.md (新)
│   │   └── pyproject.toml (+sse-starlette)
│   └── aideo-ipad/                         # iPad 客户端
│       ├── Models/APIv2Models.swift, AnyCodable.swift (新)
│       ├── Models/Task.swift, AssistModels.swift, GenerationParams.swift
│       ├── Services/SpeechRecognizer.swift, TranscriptPostProcessor.swift (新)
│       ├── Services/APIClient.swift, WebSocketClient.swift
│       ├── ViewModels/CanvasViewModel.swift, TaskDetailViewModel.swift
│       ├── Views/Sidebar/HealthSheetView.swift (新)
│       ├── Views/Canvas/CardEditorView.swift, AIEnhanceNodeView.swift
│       ├── Views/Tasks/TaskDetailView.swift
│       └── Services/PromptSerializer.swift, Models/WSEvent.swift (删除)
