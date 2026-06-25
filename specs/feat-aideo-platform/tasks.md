# Tasks: feat-aideo-platform

> 生成时间：2026-06-26
> 基于：spec.md + plan.md

## 进度
- [ ] 0 / 37 任务完成

---

## Phase 1 — 基础骨架（aideo-serv 数据模型 + 配置 + 存储 + REST API）

> 目标：FastAPI 可启动，任务 CRUD + 内存存储 + 测试全覆盖

---

### Task 1: 创建 `tests/conftest.py` — 测试夹具

- **文件**：`aideo-serv/tests/conftest.py`
- **类型**：测试
- **依赖**：无
- **描述**：提供 FastAPI `TestClient` 和 `TaskService` fixtures。TestClient 指向一个最小 FastAPI app（先用占位，后续 Task 逐步替换为真实 app）。
- **验收**：`uv run pytest tests/conftest.py -v` 能加载 fixtures 不报错

---

### Task 2: 创建 `tests/test_task_models.py` — 数据模型测试

- **文件**：`aideo-serv/tests/test_task_models.py`
- **类型**：测试
- **依赖**：无
- **描述**：为 TaskCreate、Task、TaskStatus、WSEvent 编写 Pydantic 模型校验测试：
  - TaskCreate：prompt 非空、max_length=4096、params 可选、非法类型拒绝
  - TaskStatus：六态枚举值正确
  - Task：id 自动生成(UUID)、status 默认 queued、progress 范围 0-100
  - WSEvent：type 枚举、data dict 非空、timestamp 自动生成
- **验收**：`uv run pytest tests/test_task_models.py -v` → 全部红灯（模型尚不存在）

---

### Task 3: 实现 `models/task.py` — Task 数据模型

- **文件**：`aideo-serv/src/aideo_serv/models/task.py`
- **类型**：实现
- **依赖**：Task 2
- **描述**：实现 TaskStatus(StrEnum)、TaskCreate(BaseModel)、Task(BaseModel)、TaskListResponse(BaseModel)。使用 UUID、datetime、pydantic Field validators。
- **验收**：`uv run pytest tests/test_task_models.py -v` → Task 相关测试全部绿灯

---

### Task 4: 实现 `models/events.py` — WebSocket 事件模型

- **文件**：`aideo-serv/src/aideo_serv/models/events.py`
- **类型**：实现
- **依赖**：Task 2
- **描述**：实现 WSEvent(BaseModel)：type(str)、task_id(str)、data(dict)、timestamp(datetime)。
- **验收**：`uv run pytest tests/test_task_models.py -v` → WSEvent 测试也绿灯

---

### Task 5: 创建 `tests/test_config.py` — 配置测试

- **文件**：`aideo-serv/tests/test_config.py`
- **类型**：测试
- **依赖**：无
- **描述**：测试 Settings(pydantic-settings)：
  - 默认值：host="0.0.0.0", port=8000, inference_url, storage_base_dir
  - 环境变量覆盖（mock_env fixture）
  - 必填项缺失时报错
- **验收**：`uv run pytest tests/test_config.py -v` → 红灯

---

### Task 6: 实现 `config.py` — 应用配置

- **文件**：`aideo-serv/src/aideo_serv/config.py`
- **类型**：实现
- **依赖**：Task 5
- **描述**：实现 `Settings(BaseSettings)`：server_host, server_port, inference_url, storage_base_dir, cors_origins。使用 pydantic-settings，env prefix = `AIDEO_`。
- **验收**：`uv run pytest tests/test_config.py -v` → 绿灯

---

### Task 7: 创建 `tests/test_storage.py` — 存储测试

- **文件**：`aideo-serv/tests/test_storage.py`
- **类型**：测试
- **依赖**：无
- **描述**：测试 StorageService 本地文件存储：
  - 目录结构 `{base_dir}/{task_id[:2]}/{task_id}/`
  - save_video() 写入文件并返回 Path
  - save_preview() 写入到 preview/ 子目录
  - get_path() / get_result_url() / get_preview_url() 返回正确路径/URL
  - 并发写入不冲突
  - 目录自动创建
- **验收**：`uv run pytest tests/test_storage.py -v` → 红灯

---

### Task 8: 实现 `services/storage.py` — 文件存储服务

- **文件**：`aideo-serv/src/aideo_serv/services/storage.py`
- **类型**：实现
- **依赖**：Task 6(需要 config)，Task 7
- **描述**：实现 StorageService 类：构造函数接受 base_dir，提供 save_video/save_preview/get_path/get_result_url/get_preview_url 方法。使用 pathlib + aiofiles。
- **验收**：`uv run pytest tests/test_storage.py -v` → 绿灯

---

### Task 9: 创建 `tests/test_task_service.py` — 任务服务测试

- **文件**：`aideo-serv/tests/test_task_service.py`
- **类型**：测试
- **依赖**：Task 1(conftest 夹具)
- **描述**：测试 TaskService 核心逻辑（无需 HTTP，直接实例化）：
  - create() 返回 Task(status=queued)
  - get() 查询已存在的任务
  - list() 分页 + status 过滤
  - cancel() 只能取消 queued/running 状态的任务
  - update_status() 状态机转换合法性（queued→running→generating→completed）
  - 非法状态转换抛异常（如 completed→running）
  - update_progress() 范围校验
  - add_preview() 追加预览 URL
  - complete() 设置 result_path + status=completed
  - fail() 设置 error_message + status=failed
  - 查询不存在的任务抛 LookupError
- **验收**：`uv run pytest tests/test_task_service.py -v` → 红灯

---

### Task 10: 实现 `services/task_service.py` — 任务编排服务

- **文件**：`aideo-serv/src/aideo_serv/services/task_service.py`
- **类型**：实现
- **依赖**：Task 3(models/task.py)，Task 9
- **描述**：实现 TaskService 类：内存 dict 存储，完整状态机校验，_broadcast() 桩方法（Phase 2 填入 WebSocket 广播）。提供 create/get/list/cancel/update_status/update_progress/add_preview/complete/fail 方法。
- **验收**：`uv run pytest tests/test_task_service.py -v` → 绿灯

---

### Task 11: 创建 `tests/test_tasks_api.py` — 任务 REST API 测试

- **文件**：`aideo-serv/tests/test_tasks_api.py`
- **类型**：测试
- **依赖**：Task 1(conftest)
- **描述**：通过 TestClient 测试任务 REST 端点（端点尚不存在，红灯）：
  - POST /api/v1/tasks → 201 + Task JSON
  - POST /api/v1/tasks 空 prompt → 422
  - GET /api/v1/tasks → 200 + 任务列表 + 分页
  - GET /api/v1/tasks?status=queued → 过滤
  - GET /api/v1/tasks/{id} → 200 + 单任务
  - GET /api/v1/tasks/{nonexistent} → 404
  - DELETE /api/v1/tasks/{id} → 200 + status=cancelled
  - GET /api/v1/health → 200 + {"status": "ok"}
- **验收**：`uv run pytest tests/test_tasks_api.py -v` → 红灯（404/路由不存在）

---

### Task 12: 实现 `api/router.py` — 主路由聚合

- **文件**：`aideo-serv/src/aideo_serv/api/router.py`
- **类型**：实现
- **依赖**：Task 3(models)
- **描述**：创建 APIRouter(prefix="/api/v1")，注册 health 端点（GET /health），预留 tasks router 挂载点。
- **验收**：`uv run pytest tests/test_tasks_api.py -v` → health 测试绿灯，其余仍红灯

---

### Task 13: 实现 `app.py` — FastAPI 应用工厂

- **文件**：`aideo-serv/src/aideo_serv/app.py`
- **类型**：实现
- **依赖**：Task 12(router)，Task 6(config)
- **描述**：实现 `create_app() -> FastAPI`：CORS 中间件配置、注册主路由、lifespan（启动/关闭日志）、全局异常处理。返回配置好的 FastAPI 实例。
- **验收**：`from aideo_serv.app import create_app; app = create_app()` 可执行不报错

---

### Task 14: 实现 `api/tasks.py` — 任务 REST 端点

- **文件**：`aideo-serv/src/aideo_serv/api/tasks.py`
- **类型**：实现
- **依赖**：Task 10(task_service)，Task 13(app)
- **描述**：实现任务 CRUD 端点：POST /tasks、GET /tasks、GET /tasks/{id}、DELETE /tasks/{id}。通过 FastAPI Depends 注入 TaskService 单例。
- **验收**：`uv run pytest tests/test_tasks_api.py -v` → 全部绿灯

---

### Task 15: 实现 `main.py` — 服务启动入口

- **文件**：`aideo-serv/src/aideo_serv/main.py`
- **类型**：实现
- **依赖**：Task 14(完整 API)
- **描述**：`python -m aideo_serv.main` 或 `uvicorn aideo_serv.main:app` 启动服务。读取 Settings，调用 create_app()，uvicorn.run()。
- **验收**：`uv run python -m aideo_serv.main` 启动，`curl localhost:8000/api/v1/health` 返回 `{"status":"ok"}`

---

### Task 16: 更新 `__init__.py` — 包导出

- **文件**：`aideo-serv/src/aideo_serv/__init__.py`
- **类型**：实现
- **依赖**：Task 13(app)，Task 15(main)
- **描述**：保留旧 `main()` 兼容（打印 hello），新增 `create_app`、`Settings` 的公开导出。`__all__` 列表。
- **验收**：`from aideo_serv import create_app, Settings` 可用，`uv run aideo-serv` 仍可执行

---

### Task 17: 更新 `pyproject.toml` — 添加依赖

- **文件**：`aideo-serv/pyproject.toml`
- **类型**：配置
- **依赖**：Task 16（代码就绪后统一加依赖）
- **描述**：添加运行时依赖：fastapi, uvicorn[standard], pydantic-settings, aiofiles, websockets。dev 依赖已有 pytest/pytest-asyncio。
- **验收**：`uv sync` 无错误，`uv run pytest` 全量测试通过

---

## Phase 2 — 实时通信 + 推理调度

> 目标：WebSocket 进度推送 + 推理服务 Mock + 结果下载

---

### Task 18: 创建 `tests/test_ws.py` — WebSocket 测试

- **文件**：`aideo-serv/tests/test_ws.py`
- **类型**：测试
- **依赖**：Task 1(conftest)，Task 14(API 就绪)
- **描述**：使用 `TestClient.websocket_connect` 测试：
  - 连接 WS /api/v1/ws/tasks/{id} 成功
  - 任务状态变更时收到 WSEvent JSON
  - 进度更新时收到 progress 事件
  - 任务完成时收到 completed 事件 + 连接关闭
  - 连接不存在的任务 → 立即关闭 + 错误事件
  - 多客户端同时连接同一任务 → 都收到事件
- **验收**：`uv run pytest tests/test_ws.py -v` → 红灯（WS 端点不存在）

---

### Task 19: 实现 `api/ws.py` — WebSocket 端点

- **文件**：`aideo-serv/src/aideo_serv/api/ws.py`
- **类型**：实现
- **依赖**：Task 10(task_service 的 broadcast 桩)，Task 18
- **描述**：实现 WS 端点：连接管理（dict[task_id, set[WebSocket]]），接收连接、注册到 TaskService 的广播列表、断线清理。任务终态后发送最后事件并关闭连接。
- **验收**：`uv run pytest tests/test_ws.py -v` → 绿灯

---

### Task 20: 更新 `task_service.py` — 接入 WebSocket 广播

- **文件**：`aideo-serv/src/aideo_serv/services/task_service.py`
- **类型**：实现（修改已有文件）
- **依赖**：Task 19
- **描述**：将 TaskService 的 `_broadcast()` 从桩实现改为真实 WebSocket 广播：构造 WSEvent 并发送到该 task_id 的所有已连接客户端。在所有状态变更/进度更新/完成/失败时触发 _broadcast()。
- **验收**：`uv run pytest tests/test_ws.py tests/test_task_service.py -v` → 全部绿灯

---

### Task 21: 创建 `tests/test_inference.py` — 推理客户端测试

- **文件**：`aideo-serv/tests/test_inference.py`
- **类型**：测试
- **依赖**：Task 1(conftest)
- **描述**：测试 InferenceClient：
  - submit() 发送正确 payload 到推理服务
  - 推理服务不可达时 fail 任务
  - health_check() 返回 bool
  - 回调接收：推理服务 POST 回调 → TaskService 正确更新
- **验收**：`uv run pytest tests/test_inference.py -v` → 红灯

---

### Task 22: 实现 `services/inference.py` — 推理服务客户端

- **文件**：`aideo-serv/src/aideo_serv/services/inference.py`
- **类型**：实现
- **依赖**：Task 6(config)，Task 10(task_service)，Task 21
- **描述**：实现 InferenceClient(httpx.AsyncClient)：submit(task, callback_url) 异步发送，失败异常处理，health_check()。callback_url 由 aideo-serv 自身地址 + 内部回调路径构成。
- **验收**：`uv run pytest tests/test_inference.py -v` → 绿灯

---

### Task 23: 创建 `tests/test_results.py` — 结果下载测试

- **文件**：`aideo-serv/tests/test_results.py`
- **类型**：测试
- **依赖**：Task 1(conftest)，Task 8(storage)
- **描述**：测试结果端点：
  - GET /api/v1/results/{id}/download → 200 + 文件流 + Content-Disposition
  - GET /api/v1/results/{id}/preview/{frame} → 200 + image/jpeg
  - 不存在的任务结果 → 404
  - 未完成的任务下载 → 404
- **验收**：`uv run pytest tests/test_results.py -v` → 红灯

---

### Task 24: 实现 `api/results.py` — 结果下载端点

- **文件**：`aideo-serv/src/aideo_serv/api/results.py`
- **类型**：实现
- **依赖**：Task 8(storage)，Task 10(task_service)，Task 23
- **描述**：实现下载端点和预览图端点。使用 FastAPI FileResponse / StreamingResponse，从 StorageService 读取文件。
- **验收**：`uv run pytest tests/test_results.py -v` → 绿灯

---

### Task 25: 更新 `api/router.py` — 注册新路由

- **文件**：`aideo-serv/src/aideo_serv/api/router.py`
- **类型**：实现（修改已有文件）
- **依赖**：Task 19(ws)，Task 24(results)
- **描述**：在主路由中注册 ws_router 和 results_router。
- **验收**：`uv run pytest -v` → Phase 1 + 2 所有测试绿灯

---

### Task 26: 实现 `middleware/auth.py` — JWT 中间件骨架

- **文件**：`aideo-serv/src/aideo_serv/middleware/auth.py`
- **类型**：实现
- **依赖**：Task 13(app)
- **描述**：实现 JWT 中间件骨架：`get_current_user()` FastAPI Dependency，解析 Authorization: Bearer <token>。MVP 阶段不验证签名，始终返回 AnonymousUser。预留真实验证逻辑的接口。
- **验收**：注入到任意端点，`request.user` 可访问，`uv run pytest` 全量不退化

---

## Phase 3 — CLI 客户端

> 目标：aideo-cli 包可用，6 个子命令跑通完整工作流

---

### Task 27: 创建 `aideo-cli/pyproject.toml` — CLI 包元数据

- **文件**：`aideo-cli/pyproject.toml`
- **类型**：配置
- **依赖**：无
- **描述**：新建 CLI 包：name="aideo-cli", requires-python>=3.12, 依赖 typer, httpx, websockets, rich。console_script: `aideo = "aideo_cli.main:app"`。
- **验收**：`cd aideo-cli && uv sync` 成功

---

### Task 28: 创建测试 `aideo-cli/tests/test_client.py` — API 客户端测试

- **文件**：`aideo-cli/tests/test_client.py`
- **类型**：测试
- **依赖**：Task 27(包就绪)，Task 14(aideo-serv API 可用)
- **描述**：测试 AideoClient（HTTP + WS 封装）：
  - submit_task(prompt, params) → Task
  - list_tasks(status, limit) → list[Task]
  - get_task(id) → Task
  - cancel_task(id) → Task
  - download_result(id, output_path) → 文件写入
  - connect_ws(id) → async iterator of WSEvent
  - 连接失败 / 超时 → 合理报错
- **验收**：需要 aideo-serv 运行，`uv run pytest tests/test_client.py -v` → 红灯

---

### Task 29: 实现 `aideo_cli/client.py` — API 客户端

- **文件**：`aideo-cli/src/aideo_cli/client.py`
- **类型**：实现
- **依赖**：Task 28
- **描述**：实现 AideoClient 类：封装 httpx.AsyncClient（REST）和 websockets.connect（WS）。提供 submit/list/get/cancel/download/connect_ws 方法。支持 `--server` base URL 配置。
- **验收**：`uv run pytest tests/test_client.py -v` → 绿灯

---

### Task 30: 创建测试 `aideo-cli/tests/test_commands.py` — CLI 命令测试

- **文件**：`aideo-cli/tests/test_commands.py`
- **类型**：测试
- **依赖**：Task 29(client 实现)
- **描述**：通过 typer.testing.CliRunner 测试 6 个子命令：
  - `aideo submit "prompt"` → JSON 输出
  - `aideo list` → 表格输出
  - `aideo status <id>` → JSON
  - `aideo cancel <id>` → JSON
  - `aideo download <id> -o path` → 文件写入确认
  - `aideo ws <id>` → 事件逐行输出
  - --format json/table 切换
- **验收**：`uv run pytest tests/test_commands.py -v` → 红灯

---

### Task 31: 实现 `aideo_cli/commands.py` — CLI 命令

- **文件**：`aideo-cli/src/aideo_cli/commands.py`
- **类型**：实现
- **依赖**：Task 29(client)，Task 30
- **描述**：实现 6 个 typer 子命令，每个命令调用 AideoClient 对应方法，使用 rich 美化输出（table 命令用 Rich Table，json 命令直接 print）。ws 命令用 asyncio 循环接收事件并用 rich Progress 显示进度条。
- **验收**：`uv run pytest tests/test_commands.py -v` → 绿灯

---

### Task 32: 实现 `aideo_cli/main.py` — CLI 入口

- **文件**：`aideo-cli/src/aideo_cli/main.py`
- **类型**：实现
- **依赖**：Task 31(commands)
- **描述**：创建 typer.Typer app，注册 6 个子命令，添加全局 --server 和 --format 选项。
- **验收**：`uv run aideo --help` 显示 6 个子命令

---

### Task 33: 实现 `aideo_cli/__init__.py` — 包初始化

- **文件**：`aideo-cli/src/aideo_cli/__init__.py`
- **类型**：实现
- **依赖**：Task 32
- **描述**：版本号定义，公开导出 AideoClient。
- **验收**：`from aideo_cli import AideoClient` 可用

---

## Phase 4 — 推理服务 + 集成

> 目标：LTX-2 推理服务可运行（先 Mock），端到端流程打通

---

### Task 34: 创建 `inference/pyproject.toml` — 推理服务包

- **文件**：`inference/pyproject.toml`
- **类型**：配置
- **依赖**：无
- **描述**：新建推理服务包：name="ltx2-service"，依赖 fastapi, uvicorn, httpx（进度回调用）。console_script: `ltx2-server`。
- **验收**：`cd inference && uv sync` 成功

---

### Task 35: 实现 `inference/src/ltx2_service/model.py` — 模型加载桩

- **文件**：`inference/src/ltx2_service/model.py`
- **类型**：实现
- **依赖**：Task 34
- **描述**：实现 LTX2Model 类（先 Mock）：generate(prompt, params, progress_callback) async generator。Mock 实现用 asyncio.sleep 模拟进度（0→100%，每 5% 回调一次），最终返回占位视频 bytes。
- **验收**：单元测试：调用 generate() → 看到进度回调触发 → 返回假视频数据

---

### Task 36: 实现 `inference/src/ltx2_service/progress.py` — 进度回调

- **文件**：`inference/src/ltx2_service/progress.py`
- **类型**：实现
- **依赖**：Task 34
- **描述**：实现 progress callback 函数：接收 callback_url、task_id、WSEvent 数据，用 httpx 异步 POST 到 aideo-serv 的内部回调端点。
- **验收**：与 Task 35 一起验证：进度回调 → aideo-serv 收到事件 → WS 推送到客户端

---

### Task 37: 实现 `inference/src/ltx2_service/server.py` — 推理服务入口

- **文件**：`inference/src/ltx2_service/server.py`
- **类型**：实现
- **依赖**：Task 35(model)，Task 36(progress)
- **描述**：FastAPI 推理服务：
  - POST /generate：接收 task_id, prompt, params, callback_url
  - 启动异步 generate()，进度回调中 POST 到 callback_url
  - 生成完成后 POST completed 事件到 callback_url
  - 失败时 POST error 事件
  - GET /health：返回推理服务健康状态
- **验收**：启动推理服务 + aideo-serv → CLI submit → CLI ws 看到进度 → CLI download 拿到假视频
