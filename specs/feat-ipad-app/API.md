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
    }
  }
→ Task {
    "id": "uuid",
    "prompt": "...",
    "params": {...},
    "status": "queued",
    "progress": 0.0,
    "created_at": "iso8601",
    "updated_at": "iso8601",
    "result_path": null,
    "result_url": null,
    "previews": [],
    "error_message": null
  }
```

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
- 任务已完成/已取消返回 409

### 6. WebSocket 实时进度
```
WS /api/v1/ws/tasks/{task_id}
→ 连接后首先推送当前状态，随后实时推送进度事件：

  初始事件:
  { "type": "status_change", "task_id": "uuid", "data": {"status": "queued"}, "timestamp": "iso" }

  后续事件:
  { "type": "progress",    "task_id": "uuid", "data": {"progress": 45.5}, "timestamp": "iso" }
  { "type": "preview",     "task_id": "uuid", "data": {"frame": "0024.jpg"}, "timestamp": "iso" }
  { "type": "completed",   "task_id": "uuid", "data": {"result_path": "..."}, "timestamp": "iso" }
  { "type": "error",       "task_id": "uuid", "data": {"message": "..."}, "timestamp": "iso" }

  WebSocket 事件类型:
  - status_change : 状态变更 (queued→running→generating→completed/failed/cancelled)
  - progress      : 生成进度 0-100%
  - preview       : 中间帧预览就绪
  - completed     : 任务完成，视频可下载
  - error         : 任务失败，含错误详情
```

### 7. 下载视频
```
GET /api/v1/results/{task_id}/download
→ video/mp4 (二进制流, Content-Disposition: attachment; filename="{task_id}.mp4")
```
- 任务未完成或无结果返回 404

### 8. 获取预览帧
```
GET /api/v1/results/{task_id}/preview/{frame}
→ image/jpeg
```
- `frame` 匹配预览文件名前缀（如 `0000`, `0024`）
- 预览帧不存在返回 404

---

## 缺失 API（需在 aideo-serv 新增）

以下接口为 iPad 画布式创作和 AI 辅助功能所需，后端尚未实现。

### 9. AI 提示词补全
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

### 10. AI 自动结构化
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

### 11. AI 灵感探索
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

## API 总结

```
现有（7个端点 + 1个WS）                  新增（3个端点）
─────────────────────────               ──────────────────────────
GET    /health                          POST /assist/complete
POST   /tasks                           POST /assist/structure
GET    /tasks                           POST /assist/inspire
GET    /tasks/{id}
DELETE /tasks/{id}
WS     /ws/tasks/{id}     ← 实时进度
GET    /results/{id}/download
GET    /results/{id}/preview/{frame}
```
