# Technical Plan: feat-aideo-platform

## 目录结构

```
aideo/
├── aideo-serv/                          # API 网关（现有）
│   ├── pyproject.toml                   # [修改] 添加 FastAPI, httpx, websockets 等依赖
│   └── src/aideo_serv/
│       ├── __init__.py                  # [修改] 导出 app 工厂
│       ├── main.py                      # [新增] uvicorn 启动入口
│       ├── config.py                    # [新增] Settings (pydantic-settings)
│       ├── app.py                       # [新增] FastAPI 应用实例, CORS, 中间件, 生命周期
│       ├── api/
│       │   ├── __init__.py
│       │   ├── router.py               # [新增] 主路由聚合
│       │   ├── tasks.py                # [新增] /api/v1/tasks CRUD
│       │   ├── ws.py                   # [新增] /api/v1/ws/tasks/{id} WebSocket
│       │   └── results.py              # [新增] /api/v1/results/{id}/download
│       ├── models/
│       │   ├── __init__.py
│       │   ├── task.py                 # [新增] Task, TaskStatus, TaskCreate, TaskResponse
│       │   └── events.py              # [新增] WebSocket 事件协议
│       ├── services/
│       │   ├── __init__.py
│       │   ├── task_service.py         # [新增] 任务编排 & 状态机
│       │   ├── inference.py            # [新增] 推理服务 HTTP 客户端
│       │   └── storage.py              # [新增] 文件存储抽象（本地实现）
│       ├── middleware/
│       │   ├── __init__.py
│       │   └── auth.py                 # [新增] JWT 中间件骨架（预留，不强制）
│       └── tests/                      # [新增] 测试目录
│           ├── __init__.py
│           ├── conftest.py             # [新增] FastAPI TestClient fixtures
│           ├── test_tasks.py           # [新增] 任务 API 测试
│           ├── test_ws.py              # [新增] WebSocket 测试
│           └── test_results.py         # [新增] 结果下载测试
│
├── aideo-cli/                           # CLI 客户端（现有空目录）
│   ├── pyproject.toml                   # [新增] 包元数据 + typer, httpx, websockets 依赖
│   └── src/aideo_cli/
│       ├── __init__.py                  # [新增]
│       ├── main.py                      # [新增] CLI 入口 (typer)
│       ├── client.py                    # [新增] aideo-serv API 客户端 (httpx + ws)
│       └── commands.py                  # [新增] submit, list, status, download, cancel, ws 命令
│
├── inference/                           # [新增] 推理服务
│   ├── pyproject.toml                   # [新增] 包元数据 + LTX-2 依赖
│   └── src/ltx2_service/
│       ├── __init__.py
│       ├── server.py                    # [新增] 推理服务入口（轻量 HTTP）
│       ├── model.py                     # [新增] LTX-2 模型加载 & 推理封装
│       └── progress.py                  # [新增] 进度回调 → aideo-serv
│
└── specs/feat-aideo-platform/
    ├── spec.md                          # ✅ Phase 1 产出
    └── plan.md                          # ✅ 当前文件
```

---

## 核心数据模型

### Task 生命周期状态机

```
queued ──→ running ──→ generating ──→ completed
  │           │            │
  └───────────┴────────────┴──→ failed
  │
  └──→ cancelled
```

### Pydantic Models (`aideo_serv/models/task.py`)

```python
from enum import StrEnum
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskCreate(BaseModel):
    prompt: str = Field(min_length=1, max_length=4096)
    params: dict | None = None  # 开放式参数: {resolution, duration, fps, seed, ...}

class Task(TaskCreate):
    id: UUID
    status: TaskStatus = TaskStatus.QUEUED
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    created_at: datetime
    updated_at: datetime
    result_path: str | None = None
    result_url: str | None = None
    previews: list[str] = []       # 中间结果缩略图 URL 列表
    error_message: str | None = None

class TaskListResponse(BaseModel):
    tasks: list[Task]
    total: int
    offset: int
    limit: int
```

### WebSocket 事件协议 (`aideo_serv/models/events.py`)

```python
from datetime import datetime
from pydantic import BaseModel

class WSEvent(BaseModel):
    """推送到客户端的 WebSocket 事件"""
    type: str                          # "status_change" | "progress" | "preview" | "error" | "completed"
    task_id: str
    data: dict                         # 事件负载，随 type 变化
    timestamp: datetime

# 事件负载示例:
# status_change → {"status": "running", "message": "推理服务已接收"}
# progress      → {"progress": 45.2, "step": "denoising", "step_current": 15, "step_total": 30}
# preview       → {"url": "/results/{id}/preview/0001.jpg", "frame": 1}
# completed     → {"result_url": "/results/{id}/download", "duration_ms": 45230}
# error         → {"code": "INFERENCE_TIMEOUT", "message": "推理超时"}
```

---

## 接口定义

### REST API（`aideo_serv/api/`）

| Method | Path | 说明 | 请求体 | 响应 |
|--------|------|------|--------|------|
| `POST` | `/api/v1/tasks` | 创建任务 | `TaskCreate` | `Task` (201) |
| `GET` | `/api/v1/tasks` | 任务列表 | query: `?status=&offset=0&limit=20` | `TaskListResponse` |
| `GET` | `/api/v1/tasks/{id}` | 任务详情 | — | `Task` |
| `DELETE` | `/api/v1/tasks/{id}` | 取消任务 | — | `Task` (status=cancelled) |
| `GET` | `/api/v1/results/{id}/download` | 下载视频 | — | `application/octet-stream` |
| `GET` | `/api/v1/results/{id}/preview/{frame}` | 预览图 | — | `image/jpeg` |
| `GET` | `/api/v1/health` | 健康检查 | — | `{"status": "ok", "inference": "connected"}` |

### WebSocket（`aideo_serv/api/ws.py`）

```
WS /api/v1/ws/tasks/{id}
```

- 客户端连接后，服务端持续推送 `WSEvent` JSON 消息
- 支持多客户端同时监听同一任务
- 任务终态（completed/failed/cancelled）后服务端发送最后一条事件，然后关闭连接

### 推理服务内部协议（`aideo_serv/services/inference.py` → `inference/src/ltx2_service/server.py`）

```
POST /generate
  Body: { "task_id": "uuid", "prompt": "...", "params": {...}, "callback_url": "http://aideo-serv/internal/callback" }
  Response: 202 Accepted

POST {callback_url}  (推理服务回调 aideo-serv)
  Body: WSEvent
```

### CLI 命令（`aideo_cli/commands.py`）

```
aideo submit <prompt> [--param key=value]...
aideo list [--status queued|running] [--limit 20]
aideo status <task_id>
aideo cancel <task_id>
aideo download <task_id> [--output ./output.mp4]
aideo ws <task_id>             # 实时跟踪进度（WebSocket）
```

CLI 全局选项：
- `--server http://localhost:8000` — aideo-serv 地址
- `--format table|json` — 输出格式

---

## 服务层设计

### TaskService（`task_service.py`）

```
class TaskService:
    """任务编排核心"""
    - create(prompt, params) → Task          # 创建任务，状态=queued
    - get(task_id) → Task                     # 查询单个任务
    - list(status, offset, limit) → list[Task] # 任务列表
    - cancel(task_id) → Task                  # 取消任务
    - update_status(task_id, status) → Task   # 更新状态（内部）
    - update_progress(task_id, pct) → Task    # 更新进度（内部）
    - add_preview(task_id, path) → Task       # 添加预览（内部）
    - complete(task_id, result_path) → Task   # 标记完成（内部）
    - fail(task_id, error) → Task             # 标记失败（内部）
    - _broadcast(task_id, event: WSEvent)      # 向所有 WS 连接广播事件
```

初期使用 **内存 dict** 存储（单进程），后续可替换为 Redis/PostgreSQL。存储接口预留为可注入的抽象。

### InferenceClient（`inference.py`）

```python
class InferenceClient:
    """推理服务客户端"""
    async def submit(task: Task, callback_url: str) -> None
        # POST /generate 到推理服务
        # 失败时调用 TaskService.fail()

    async def health_check() -> bool
        # GET /health 到推理服务
```

### StorageService（`storage.py`）

```python
class StorageService:
    """文件存储抽象"""
    def __init__(base_dir: Path = Path("./data"))
        # 目录结构: data/{task_id[:2]}/{task_id}/

    async def save_video(task_id, file_bytes) -> Path
    async def save_preview(task_id, frame_no, image_bytes) -> Path
    def get_path(task_id) -> Path
    def get_result_url(task_id) -> str
    def get_preview_url(task_id, frame) -> str
```

---

## 实施阶段

### Phase 1 — 基础骨架（aideo-serv 核心）

**目标**：FastAPI 应用可启动，数据模型定义完毕，内存存储 + 任务 CRUD 可用。

| 文件 | 动作 | 关键内容 |
|------|------|----------|
| `aideo-serv/pyproject.toml` | 修改 | 添加 fastapi, uvicorn[standard], pydantic-settings, websockets 依赖 |
| `aideo_serv/config.py` | 新增 | `Settings` 类：server host/port, inference URL, storage base_dir |
| `aideo_serv/models/task.py` | 新增 | `TaskStatus`, `TaskCreate`, `Task` — 完整 Pydantic 模型 |
| `aideo_serv/models/events.py` | 新增 | `WSEvent` — WebSocket 事件协议 |
| `aideo_serv/services/storage.py` | 新增 | `StorageService` — 本地文件存储（目录结构 `data/{prefix}/{task_id}/`） |
| `aideo_serv/services/task_service.py` | 新增 | `TaskService` — 内存 dict 存储 + 任务 CRUD + 状态机 |
| `aideo_serv/app.py` | 新增 | `create_app()` 工厂：FastAPI 实例、CORS、路由注册、lifespan |
| `aideo_serv/api/router.py` | 新增 | 主路由 `/api/v1` 聚合 |
| `aideo_serv/api/tasks.py` | 新增 | `POST/GET/DELETE /tasks` 端点，注入 TaskService |
| `aideo_serv/main.py` | 新增 | `uvicorn.run()` 启动入口 |
| `aideo_serv/__init__.py` | 修改 | 保留旧 `main()` 兼容，新增 `create_app` 导出 |
| `aideo_serv/tests/conftest.py` | 新增 | `TestClient` + `TaskService` fixtures |
| `aideo_serv/tests/test_tasks.py` | 新增 | 创建/查询/取消任务的集成测试 |

### Phase 2 — 实时通信 + 推理调度

**目标**：WebSocket 进度推送可用，推理服务客户端完成（可对接真实 LTX-2 或 Mock）。

| 文件 | 动作 | 关键内容 |
|------|------|----------|
| `aideo_serv/api/ws.py` | 新增 | WebSocket 端点：连接管理、事件广播、断线清理 |
| `aideo_serv/services/inference.py` | 新增 | `InferenceClient`：提交任务到推理服务 + 回调接收 |
| `aideo_serv/api/results.py` | 新增 | 视频下载 + 预览图端点 |
| `aideo_serv/middleware/auth.py` | 新增 | JWT 中间件骨架：解析 Bearer Token、注入 request.user（不强制验证） |
| `inference/pyproject.toml` | 新增 | 推理服务包元数据 |
| `inference/src/ltx2_service/server.py` | 新增 | Mock 推理服务：接收 /generate、模拟进度、回调 aideo-serv |
| `inference/src/ltx2_service/model.py` | 新增 | LTX-2 模型加载桩（Phase 3 填入真实实现） |
| `inference/src/ltx2_service/progress.py` | 新增 | 进度回调发送器 |
| `aideo_serv/tests/test_ws.py` | 新增 | WebSocket 集成测试 |
| `aideo_serv/tests/test_results.py` | 新增 | 结果下载测试 |

### Phase 3 — CLI 客户端

**目标**：`aideo-cli` 全功能可用，能通过命令行完成完整工作流。

| 文件 | 动作 | 关键内容 |
|------|------|----------|
| `aideo-cli/pyproject.toml` | 新增 | typer, httpx, websockets, rich 依赖 + `aideo` console_script |
| `aideo_cli/__init__.py` | 新增 | 版本号 |
| `aideo_cli/client.py` | 新增 | `AideoClient`：httpx REST 客户端 + websockets WS 客户端 |
| `aideo_cli/commands.py` | 新增 | 6 个子命令：submit/list/status/cancel/download/ws，rich 美化输出 |
| `aideo_cli/main.py` | 新增 | typer app 入口，全局 --server / --format 选项 |

### Phase 4 — LTX-2 真实集成

**目标**：对接真实 LTX-2 模型，端到端视频生成可用。

| 文件 | 动作 | 关键内容 |
|------|------|----------|
| `inference/src/ltx2_service/model.py` | 修改 | 填入真实 LTX-2 模型加载、推理、进度回调逻辑 |
| `inference/src/ltx2_service/server.py` | 修改 | 接入 GPU、资源管理、并发限制 |
| `aideo_serv/config.py` | 修改 | 添加视频参数配置（由模型能力驱动） |
| 文档 | 新增 | 部署指南、模型下载、GPU 环境配置 |

---

## 关键技术决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| Web 框架 | FastAPI | 异步原生、WebSocket 原生支持、自动 OpenAPI/Swagger 文档、Pydantic 深度集成 |
| 任务存储（MVP） | 内存 dict | 单进程够用，通过 TaskService 抽象接口预留切换到 Redis/DB 的能力 |
| WebSocket 连接管理 | 内存 dict[task_id, set[WebSocket]] | 简单直接，单进程内广播 |
| 推理通信 | HTTP 回调 | 简单可靠，无需额外中间件。后续可升级为 gRPC streaming |
| CLI 框架 | Typer + Rich | Click 的现代替代，类型提示驱动，Rich 提供彩色表格/进度条 |
| 文件存储 | 本地文件系统 | MVP 够用。`StorageService` 抽象接口，目录结构 `data/{2char_prefix}/{task_id}/` 为 S3 迁移预留 |
| 认证 | FastAPI Dependency 注入 | `Depends(get_current_user)` 骨架就位，MVP 返回 AnonymousUser，后续接入 JWT 验证 |
