# API 定义 — aideo-ipad

## 现有 API（aideo-serv 已实现）

以下接口 iPad 端直接消费，无需修改后端。

### 1. 健康检查
```
GET /api/v1/health
→ { "status": "ok" }
```

### 2. 提交生成任务
```
POST /api/v1/tasks                        # Status: 201
  Body: {
    "prompt": "一只猫在太空站漂浮",          // string, 1-4096 chars
    "params": {                           // dict | null, 当前无 schema 约束
      "duration": 10,                     // 时长（秒）
      "resolution": "1080p",              // 分辨率
      "style": "cinematic",               // 风格预设
      "seed": 42,                         // 随机种子
      "fps": 24,                          // 帧率
      "cfg_scale": 7.5,                   // CFG scale
      "steps": 50                         // 推理步数
    },
    "task_type": "video_generation",      // string, 默认 "video_generation"
                                          // 可选: "speech_to_text" | "text_conversation" | "image_to_text"
    "input_files": [                      // list[dict] | null, 可选
      {"path": "/tmp/audio.wav", "type": "audio"}
    ]
  }
→ Task {
    "id": "uuid",
    "prompt": "...",
    "params": {...},
    "task_type": "video_generation",
    "input_files": null,
    "status": "queued",
    "progress": 0.0,
    "created_at": "iso8601",
    "updated_at": "iso8601",
    "result_path": null,
    "result_url": null,
    "result_data": null,
    "previews": [],
    "error_message": null,
    "project_id": null
  }
```

> **iPad 注意**: iPad 当前还发送 `reference_images`（base64 data-URL 数组），该字段由 `PromptSerializer` 序列化时嵌入 `prompt` 文本，不在 `TaskCreate` model 中。

### 3. 任务列表
```
GET /api/v1/tasks?status=completed&offset=0&limit=20
→ {
    "tasks": [Task, ...],
    "total": 42,
    "offset": 0,
    "limit": 20
  }
```
- `status` 可选值：`queued` | `running` | `generating` | `completed` | `failed` | `cancelled`
- `limit` 范围：1-100

### 4. 获取单个任务
```
GET /api/v1/tasks/{task_id}
→ Task
```
- 任务不存在返回 404

### 5. 取消任务
```
DELETE /api/v1/tasks/{task_id}
→ Task  (status: "cancelled")
```
- 任务不存在返回 404
- 任务已在终态返回 409
- 若任务处于 `generating`，先向推理服务发送 `task_cancel` 消息再本地标记取消

### 6. WebSocket 实时进度
```
WS /api/v1/ws/tasks/{task_id}
→ 连接后首先推送当前状态，随后实时推送进度事件：

  初始事件:
  { "type": "status_change", "task_id": "uuid", "data": {"status": "queued"}, "timestamp": "iso" }

  后续事件:
  { "type": "status_change", "task_id": "uuid", "data": {"status": "running"}, "timestamp": "iso" }
  { "type": "progress",      "task_id": "uuid", "data": {"progress": 45.5, "message": "..."}, "timestamp": "iso" }
  { "type": "preview",       "task_id": "uuid", "data": {"frame": "0024"}, "timestamp": "iso" }
  { "type": "completed",     "task_id": "uuid", "data": {"result_path": "...", "result_url": "..."}, "timestamp": "iso" }
  { "type": "error",         "task_id": "uuid", "data": {"message": "..."}, "timestamp": "iso" }

  WebSocket 事件类型:
  - status_change : 状态变更 (queued→running→generating→completed/failed/cancelled)
  - progress      : 生成进度 0-100%，可选附带 message
  - preview       : 中间帧预览就绪，frame 为预览帧标识（如 "0000", "0024"）
  - completed     : 任务完成，result_url 可下载视频
  - error         : 任务失败，含错误详情

  连接行为:
  - 任务不存在 → close code 4004
  - 任务已终态 → 发送 completed/error 后立即关闭
  - iPad 端最多重连 5 次，指数退避 1s→2s→4s→8s→16s
```

### 7. 下载视频
```
GET /api/v1/results/{task_id}/download
→ video/mp4 (二进制流, Content-Disposition: attachment; filename="{task_id}.mp4")
  或 JSON (当任务携带 inline result_data 时)
```
- 任务未完成或无结果返回 404

### 8. 获取预览帧
```
GET /api/v1/results/{task_id}/preview/{frame}
→ image/jpeg
```
- `frame` 匹配预览文件名前缀（如 `0000`, `0024`）
- 预览帧不存在返回 404

### 9. WebSocket 流式语音转写
```
WS /api/v1/ws/transcribe

  客户端 → 服务端: 二进制帧 (raw PCM 16kHz 16bit mono 或 WAV)
  服务端 → 客户端: JSON 文本帧

  事件流:
  → {"type": "status_change", "data": {"status": "queued"}}
  → {"type": "progress",      "data": {"progress": 50.0, "message": "..."}}
  → {"type": "result", "task_id": "uuid", "data": {
        "full_text": "转录的完整文本",
        "segments": [{"start": 0.0, "end": 2.5, "text": "..."}],
        "language": "zh"
      }}
  → {"type": "error", "task_id": "uuid", "data": {"message": "..."}}

  处理流程:
  1. 每段二进制音频保存为临时 .wav
  2. 创建 task_type="speech_to_text" 任务
  3. 通过内部 WS 分发给 aideo-runtime
  4. 转录结果流式回客户端，清理临时文件
```

---

## 缺失 API（需在 aideo-serv 新增）

以下接口为 iPad 画布式创作和 AI 辅助功能所需，后端尚未实现。

### 10. AI 提示词补全
```
POST /api/v1/assist/complete
  Body: {
    "context": "一只猫在",                  // 用户当前输入的上下文
    "mode": "suggestion"                  // "suggestion" | "completion"
  }
→ {
    "suggestions": [                      // 建议列表，按相关度排序
      "一只猫在太空站漂浮，背景是浩瀚星空",
      "一只猫在花园里追逐蝴蝶，阳光透过树叶",
      "一只猫在屋顶上眺望城市夜景"
    ]
  }
```
**用途**：用户在画布卡片中输入时，实时获取提示词补全建议。

### 11. AI 自动结构化
```
POST /api/v1/assist/structure
  Body: {
    "description": "夕阳下的海滩，一个冲浪者正在准备下海，慢镜头"   // 自由文本描述
  }
→ {
    "blocks": [
      {"type": "scene",   "content": "夕阳下的海滩，金色光线，海浪拍打沙滩"},
      {"type": "character","content": "冲浪者，手持冲浪板，走向大海"},
      {"type": "action",  "content": "慢镜头，准备下海的动作"},
      {"type": "style",   "content": "cinematic, warm tone, slow motion"}
    ]
  }
```
**用途**：用户输入一段自由描述，AI 自动拆成画布卡片块。block type 枚举：`scene` | `character` | `action` | `style` | `camera` | `mood`。

### 12. AI 灵感探索
```
POST /api/v1/assist/inspire
  Body: {
    "theme": "赛博朋克"                    // 可选，不传则随机
  }
→ {
    "themes": [
      {
        "title": "霓虹雨夜的东京小巷",
        "prompt": "雨夜的东京小巷，霓虹灯倒映在水洼中，一个cyborg在街头漫步...",
        "style_hint": "cyberpunk, neon, rain",
        "tags": ["赛博朋克", "雨夜", "城市"]
      },
      ...共 3-5 个
    ]
  }
```
**用途**：用户需要创意灵感时，AI 推荐主题和对应的提示词。

---

## 参数定义约定

`POST /api/v1/tasks` 的 `params` 字段当前为自由 dict。iPad 端统一使用以下 key（与 CLI 对齐）：

| Key | 类型 | 说明 | 示例值 |
|-----|------|------|--------|
| `duration` | int | 视频时长（秒） | `5`, `10` |
| `resolution` | string | 输出分辨率 | `720p`, `1080p` |
| `style` | string | 风格预设 | `cinematic`, `anime`, `realistic` |
| `seed` | int | 随机种子 | `42` |
| `fps` | int | 帧率 | `24`, `30` |
| `cfg_scale` | float | CFG scale | `7.5` |
| `steps` | int | 推理步数 | `50` |

---

## Task 模型完整字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `id` | UUID | — | 唯一任务标识 |
| `prompt` | string | — | 生成提示词 |
| `params` | dict \| null | `null` | 生成参数 |
| `task_type` | string | `"video_generation"` | 任务类型 |
| `input_files` | list[dict] \| null | `null` | 输入文件（如音频） |
| `status` | TaskStatus | `"queued"` | 生命周期状态 |
| `progress` | float | `0.0` | 0.0–100.0 |
| `created_at` | datetime | now | 创建时间 (UTC) |
| `updated_at` | datetime | now | 更新时间 (UTC) |
| `result_path` | string \| null | `null` | 服务端结果文件路径 |
| `result_url` | string \| null | `null` | 结果下载 URL |
| `result_data` | dict \| null | `null` | 内联结果数据（替代文件） |
| `previews` | list[string] | `[]` | 预览帧标识列表 |
| `error_message` | string \| null | `null` | 失败原因 |
| `project_id` | UUID \| null | `null` | 关联项目（预留） |

## 任务状态机

```
queued ──→ running ──→ generating ──→ completed
  │           │            │
  └───────────┴────────────┴──→ failed
  │
  └──→ cancelled
```

终态：`completed`, `failed`, `cancelled`。状态转换由 `TaskService._transition()` 校验。

---

## 内部端点（参考，不对外暴露）

### HTTP 回调（遗留 LTX-2 模式）
```
POST /api/v1/internal/callback
  Body: {
    "type": "progress | completed | error",
    "task_id": "uuid",
    "data": { ... }
  }
```
推理服务通过 HTTP 回传进度，作为 WebSocket 的降级方案。

### 推理服务 WebSocket
```
WS /api/v1/ws/internal/inference
```
aideo-serv ↔ aideo-runtime 之间的内部通道。

1. **注册握手**（推理→serv，30s 超时）：
```json
{"type": "register", "service_type": "aideo-runtime", "capabilities": ["video_generation", "speech_to_text"], "version": "0.1.0"}
```

2. **确认**（serv→推理）：`{"type": "registered", "data": {"service_type": "aideo-runtime"}}`

3. **任务分发**（serv→推理）：`task_submit`（含 prompt/params/model_root/output_root/input_root/input_files）、`task_cancel`

4. **状态回传**（推理→serv，转发至 TaskService）：`progress`、`completed`、`error`、`cancelled`

每种 `service_type` 只允许一个连接，新连接挤掉旧连接（close code 4001）。

---

## API 总结

```
现有（8个端点 + 2个WS）                   新增（3个端点）
─────────────────────────               ──────────────────────────
GET    /health                          POST /assist/complete
POST   /tasks                           POST /assist/structure
GET    /tasks                           POST /assist/inspire
GET    /tasks/{id}
DELETE /tasks/{id}
WS     /ws/tasks/{id}         ← 任务实时进度
WS     /ws/transcribe         ← 流式语音转写
GET    /results/{id}/download
GET    /results/{id}/preview/{frame}
```
