# Aideo API v2.0 — iPad Canvas First

Base URL: `/api/v1` | 所有 datetime 为 ISO 8601 UTC | IDs 为 UUID 小写带连字符

## 认证

当前为 anonymous。JWT 槽位已预留：

```
Authorization: Bearer <token>
```

`auto_error=False`，未认证请求按匿名处理。未来迁移：`auto_error=True` + `requires_auth` 依赖。

## 分页

所有列表接口统一 offset/limit：

| 参数 | 类型 | 默认 | 最大 | 说明 |
|---|---|---|---|---|
| `offset` | int | 0 | — | 跳过条数 |
| `limit` | int | 20 | 100 | 每页条数 |

响应：`{ "items": [...], "total": 42, "offset": 0, "limit": 20 }`

## 错误格式

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "可读描述",
    "details": []
  }
}
```

| HTTP | Code | 场景 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Schema 校验失败 |
| 401 | `UNAUTHENTICATED` | 缺 token（未来） |
| 403 | `FORBIDDEN` | 无权限 |
| 404 | `RESOURCE_NOT_FOUND` | 资源不存在 |
| 409 | `CONFLICT` | 状态冲突（如取消终态任务） |
| 422 | `VALIDATION_ERROR` | Pydantic 校验失败 |
| 500 | `INTERNAL_ERROR` | 服务端异常 |

---

## 数据模型

### PromptBlock（画布卡片）

```json
{
  "id": "uuid",
  "type": "scene",
  "content": "A dark forest at twilight",
  "scene_tag": 0,
  "params": {}
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | UUID | 是 | 客户端分配 |
| `type` | enum | 是 | `scene` \| `character` \| `action` \| `style` \| `camera` \| `mood` \| `custom` |
| `content` | string | 是 | 提示词内容 |
| `scene_tag` | int \| null | 否 | 分镜场景组（0-based），null = 未分配 |
| `params` | object | 否 | 每卡片参数覆盖（见 GenerationParams） |

### GenerationParams

```json
{
  "duration": 5,
  "resolution": "1080p",
  "style": "cinematic",
  "seed": 42,
  "fps": 24,
  "cfg_scale": 7.5,
  "steps": 50
}
```

所有字段可选。客户端只发送覆盖值。

| 字段 | 类型 | 可选值 |
|---|---|---|
| `duration` | int | 5, 10 |
| `resolution` | string | `720p`, `1080p` |
| `style` | string | `cinematic`, `anime`, `realistic`, `oil-painting`, `3d-render`, `cyberpunk` |
| `seed` | int | 任意 |
| `fps` | int | 24, 30 |
| `cfg_scale` | float | ~7.5 |
| `steps` | int | ~50 |

### BlockConnection

```json
{ "source_id": "uuid", "target_id": "uuid" }
```

有向边。无额外元数据。

### GenerationTask

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID | 任务 ID |
| `project_id` | UUID \| null | 所属项目 |
| `output_node_id` | UUID \| null | 触发的画布输出节点 |
| `prompt` | string | 序列化后的 prompt |
| `prompt_structured` | object \| null | 结构化提交快照（调试/重新生成） |
| `params` | object \| null | 生成参数 |
| `task_type` | string | `video_generation` \| `speech_to_text` \| ... |
| `status` | enum | `queued` → `running` → `generating` → `completed` / `failed` / `cancelled` |
| `progress` | float | 0.0 – 100.0 |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `result_path` | string \| null | 服务端文件路径 |
| `result_url` | string \| null | 下载 URL |
| `result_data` | object \| null | 内联结果（如转录 JSON） |
| `previews` | string[] | 预览帧 URL 列表 |
| `error_message` | string \| null | 失败原因 |
| `input_files` | array \| null | 输入文件引用 |

### Project

```json
{
  "id": "uuid",
  "name": "My Animation",
  "canvas_data": {
    "prompt_blocks": [...],
    "media_outputs": [...],
    "reference_nodes": [...],
    "ai_enhance_nodes": [...],
    "connections": [...],
    "viewport": { "center_x": 1500, "center_y": 1000, "scale": 1.0 }
  },
  "metadata": {},
  "task_count": 3,
  "created_at": "2026-07-10T12:00:00Z",
  "updated_at": "2026-07-10T12:00:00Z"
}
```

`canvas_data` 的四个节点数组 1:1 对应 iPad SwiftData model，客户端可无损 round-trip。

### Asset

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "filename": "ref_01.jpg",
  "content_type": "image/jpeg",
  "size": 2048576,
  "media_type": "image",
  "uploaded_at": "2026-07-10T12:00:00Z",
  "url": "/api/v1/assets/uuid/download",
  "metadata": { "original_name": "IMG_001.jpg", "width": 1920, "height": 1080 }
}
```

### AssistBlock

Assist 端点返回，可直接落画布：

```json
{ "type": "scene", "content": "...", "params": {} }
```

---

## REST 端点

### 系统

```
GET /health
→ { "status": "ok", "version": "2.0.0", "services": { "inference": "connected", "storage": "ok" } }
```

---

### 项目

```
POST   /projects                        创建项目
GET    /projects                        列表（offset/limit）
GET    /projects/{id}                   详情 + canvas_data
PATCH  /projects/{id}                   局部更新（name | canvas_data | metadata）
DELETE /projects/{id}                   删项目 + 关联 tasks + assets → 204
GET    /projects/{id}/tasks             项目下任务列表（offset/limit + status filter）
GET    /projects/{id}/assets            项目素材列表（offset/limit + media_type filter）
```

**PATCH body**（全部可选）：`{ "name": "新名", "canvas_data": {...}, "metadata": {...} }`

---

### 素材

```
POST   /assets                          上传 → 201。multipart/form-data
GET    /assets/{id}                     元数据
GET    /assets/{id}/download            文件二进制
DELETE /assets/{id}                     删除文件 → 204
```

**上传请求**：`file` (binary, 必填)、`project_id` (UUID, 可选)、`media_type` (可选，自动检测)

限制：50 MB/文件（`AIDEO_MAX_ASSET_SIZE`）

---

### 生成 — 结构化画布提交

```
POST /generate
```

客户端的 `collectInputs()` BFS 收集子图 + PromptBlock + 连线 → 发结构给后端。后端负责序列化为模型 prompt。

**Request**：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `project_id` | UUID | 否 | 所属项目 |
| `output_node_id` | UUID | 是 | 目标输出节点 |
| `output_content_type` | string | 是 | `video` \| `image` \| `text` |
| `blocks` | PromptBlock[] | 是 | 上游所有 prompt 卡片 |
| `connections` | BlockConnection[] | 是 | 子图连线 |
| `reference_assets` | ReferenceAsset[] | 否 | 已上传素材引用 |
| `upstream_context` | UpstreamResult[] | 否 | 上游输出节点的文本/图片/视频 |
| `ai_enhance_context` | string[] | 否 | AIEnhanceNode 的输出文本 |
| `output_params` | GenerationParams | 否 | 此次生成参数 |

**ReferenceAsset**：`{ "asset_id": "uuid", "usage": "style_reference" }` — usage 可选值：`style_reference` \| `character_reference` \| `background` \| `motion_reference`

**UpstreamResult**：`{ "node_id": "uuid", "content_type": "...", "text": "...", "asset_id": "uuid" }`

**示例**：
```json
{
  "project_id": "proj-1234",
  "output_node_id": "out-5678",
  "output_content_type": "video",
  "blocks": [
    {"id": "b1", "type": "scene", "content": "Neon-lit cyberpunk alley at midnight", "scene_tag": 0},
    {"id": "b2", "type": "character", "content": "Samurai with cybernetic arm, glowing blue tattoos", "scene_tag": 0},
    {"id": "b3", "type": "action", "content": "Walking through rain, hand on katana", "scene_tag": 0},
    {"id": "b4", "type": "style", "content": "Cinematic noir, Blade Runner aesthetic", "params": {"style": "cinematic"}}
  ],
  "connections": [
    {"source_id": "b1", "target_id": "out-5678"},
    {"source_id": "b2", "target_id": "out-5678"},
    {"source_id": "b3", "target_id": "out-5678"},
    {"source_id": "b4", "target_id": "out-5678"}
  ],
  "reference_assets": [{"asset_id": "asset-aaaa", "usage": "style_reference"}],
  "output_params": {"duration": 5, "resolution": "1080p", "fps": 24}
}
```

**Response 201**：`{ "task_id": "uuid", "task": {...} }`

**后端行为**：
1. 按 `scene_tag` 分组 → 多场景提示词结构
2. 用 block type 做分区头
3. `asset_id` → 文件路径
4. task 上写 `prompt_structured`（调试/重新生成用）
5. 设置 `project_id` 和 `output_node_id`
6. 创建任务 → 提交推理 → 返回 task_id 供 WS 订阅

---

### Canvas Assist

三个端点都返回结构化 `PromptBlock`，iPad 建好卡片直接落画布。

#### `POST /canvas/structure` — 自由文本 → 类型化 PromptBlock

```json
// Request
{ "description": "A samurai in a cyberpunk city at night, walking through rain" }

// Response
{
  "blocks": [
    {"type": "scene", "content": "Cyberpunk city at night, neon-lit streets, rain falling"},
    {"type": "character", "content": "Skilled samurai with cybernetic arm, glowing blue tattoos, dark cloak"},
    {"type": "action", "content": "Walking slowly through rain, hand on katana"},
    {"type": "style", "content": "Cyberpunk noir, cinematic lighting, volumetric rain"},
    {"type": "camera", "content": "Low angle wide shot, depth of field"},
    {"type": "mood", "content": "Melancholic, tense, atmospheric"}
  ]
}
```

#### `POST /canvas/complete` — 上下文 + 模式 → 补全建议

mode = `"completion"`（补缺类型）或 `"suggestion"`（提供替代）

```json
// Request
{
  "context": "A warrior princess in an ancient temple",
  "existing_blocks": [{"id": "x", "type": "scene", "content": "Ancient temple ruins at sunset"}],
  "mode": "completion"
}

// Response
{
  "suggestions": [
    {
      "title": "Add character details",
      "blocks": [
        {"type": "character", "content": "Warrior princess, long braided hair, leather armor"},
        {"type": "action", "content": "Standing at temple entrance, surveying ruins"}
      ]
    }
  ]
}
```

#### `POST /canvas/inspire` — 主题 → 灵感模板

```json
// Request
{ "theme": "underwater civilization" }

// Response
{
  "themes": [
    {
      "title": "Atlantean Palace",
      "prompt": "A grand underwater palace built from coral and crystal...",
      "style_hint": "Submerged lighting, bioluminescent accents, deep blue palette",
      "tags": ["underwater", "fantasy", "palace"],
      "blocks": [
        {"type": "scene", "content": "Grand underwater hall with coral pillars"},
        {"type": "character", "content": "Atlantean queen, pearl crown, iridescent robes"},
        {"type": "style", "content": "Fantasy realism, ethereal glow", "params": {"style": "cinematic"}}
      ]
    }
  ]
}
```

---

### 结果

```
GET /results/{task_id}/download      → video/mp4 或 JSON
GET /results/{task_id}/preview/{frame} → image/jpeg
```

---

## WebSocket 端点

### `WS /ws/projects/{project_id}` — 项目级多路复用

单连接承载项目内所有任务事件。

**连接行为**：
1. 接受连接
2. 发送 `connected` 事件 + 所有非终态任务快照（断线重放）
3. 流式推送所有任务事件，每个事件带 `task_id` + `output_node_id`
4. 全部任务终态后连接保持，等待新任务

**类型化事件**（`event` 字段区分，无泛型 `data` dict）：

| 事件 | `event` 值 | 关键字段 |
|---|---|---|
| 初始快照 | `connected` | `snapshot.active_tasks[]` — task_id, status, progress, previews |
| 状态变更 | `task.status` | `status`: queued/running/generating/completed/failed/cancelled |
| 进度 | `task.progress` | `progress`, `message` |
| 帧预览 | `task.preview` | `frame_url`, `frame_index` |
| 完成 | `task.completed` | `result_url`, `result_data`, `previews[]` |
| 失败 | `task.failed` | `error_message` |
| 取消 | `task.cancelled` | — |
| 协议错误 | `error` | `code`, `message`（后关闭连接） |

Close codes：4004=项目不存在, 4005=未授权（未来）

### `WS /ws/transcribe` — 流式语音转写

流式语音转写。二进制音频入，JSON 事件出。

---

## 内部端点（参考，不对外暴露）

```
POST /internal/callback            推理服务 HTTP 回调（遗留 LTX-2）
WS   /ws/internal/inference        推理服务注册 + 消息路由
```

---

## API 总结

```
REST (17)                                WebSocket (2)
──────────                               ────────────
GET    /health                           WS  /ws/projects/{id}
POST   /projects                         WS  /ws/transcribe
GET    /projects
GET    /projects/{id}                    内部
PATCH  /projects/{id}                    ────
DELETE /projects/{id}                    POST /internal/callback
GET    /projects/{id}/tasks              WS  /ws/internal/inference
GET    /projects/{id}/assets
POST   /assets
GET    /assets/{id}
GET    /assets/{id}/download
DELETE /assets/{id}
POST   /generate
POST   /canvas/structure
POST   /canvas/complete
POST   /canvas/inspire
GET    /results/{id}/download
GET    /results/{id}/preview/{frame}
```

## 状态机

```
queued ──→ running ──→ generating ──→ completed
  │           │            │
  └───────────┴────────────┴──→ failed
  │
  └──→ cancelled
```

终态：`completed`、`failed`、`cancelled`。
