# Tasks: feat-runtime-http-hurl

> 生成时间：2026-07-15
> 基于：spec.md + plan.md

## 进度

- [x] 30 / 30 任务完成

## 参数契约扩展

### Task 23: 创建 `tests/test_inference_parameters.py`

- **文件**：`packages/aideo-runtime/tests/test_inference_parameters.py`
- **类型**：测试
- **依赖**：无
- **描述**：覆盖通用参数默认值、范围验证、停止词和截断策略。
- **验收**：参数模型不存在时测试为红。

### Task 24: 实现 `models/parameters.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/models/parameters.py`
- **类型**：实现
- **依赖**：Task 23
- **描述**：实现不可变 `InferenceParameters`，支持最大输出、采样、停止词、种子、推理强度和截断策略。
- **验收**：Task 23 通过。

### Task 25: 更新 `tests/test_app.py`

- **文件**：`packages/aideo-runtime/tests/test_app.py`
- **类型**：测试
- **依赖**：Task 24
- **描述**：覆盖 `max_output_tokens` 超出 Provider 模型上限的 `422`，以及有效参数继续完成 JSON/SSE 调用。
- **验收**：新增 API 断言在路由实现前为红。

### Task 26: 更新 `api/routes.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/api/routes.py`
- **类型**：实现
- **依赖**：Task 24、Task 25
- **描述**：解析 `parameters`，校验 `max_output_tokens <= ModelInfo.max_tokens`，并将标准化参数传递给 BackendRequest。
- **验收**：Task 25 通过。

### Task 27: 更新 `backend/providers/demo.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/backend/providers/demo.py`
- **类型**：实现
- **依赖**：Task 26
- **描述**：声明 demo 模型的 `context_length` 与 `max_tokens`，并接受标准化请求参数。
- **验收**：Provider 元数据用于路由上限校验。

### Task 28: 更新 `http-tests/inference/invoke-chat.hurl`

- **文件**：`packages/aideo-runtime/http-tests/inference/invoke-chat.hurl`
- **类型**：测试
- **依赖**：Task 26、Task 27
- **描述**：发送有效的 `max_output_tokens`、`temperature` 和 `truncation` 参数，断言 SSE 契约不变。
- **验收**：对启动的 demo Runtime 通过。

### Task 29: 更新 `http-tests/inference/error-cases.hurl`

- **文件**：`packages/aideo-runtime/http-tests/inference/error-cases.hurl`
- **类型**：测试
- **依赖**：Task 26、Task 27
- **描述**：增加超过 `max_tokens` 的 `422` 请求断言。
- **验收**：对启动的 demo Runtime 通过。

### Task 30: 更新文档与变更记录

- **文件**：`packages/aideo-runtime/README.md`、`docs/changes/changed-2026-07-15-unified-inference-runtime.md`
- **类型**：文档
- **依赖**：Task 24、Task 26、Task 27
- **描述**：说明 Provider 能力与请求参数的边界、验证命令和参数示例。
- **验收**：README 示例与 HTTP 契约一致。

---

## Phase 1 — 配置与可调用 Backend

### Task 1: 扩展 `tests/test_registry_manager.py`

- **文件**：`packages/aideo-runtime/tests/test_registry_manager.py`
- **类型**：测试
- **依赖**：无
- **描述**：新增按模型 ID 查询与按 Capability 过滤模型的失败测试，并覆盖未注册模型的 `KeyError`。
- **验收**：新增断言在 Registry 实现前失败。

### Task 2: 实现 `registry/registry.py` 查询接口

- **文件**：`packages/aideo-runtime/src/aideo_runtime/registry/registry.py`
- **类型**：实现
- **依赖**：Task 1
- **描述**：添加 `get_model()` 与 `list_models(capability: Capability | None = None)`，保持既有注册和注销行为兼容。
- **验收**：`uv run --package aideo-runtime pytest packages/aideo-runtime/tests/test_registry_manager.py` 通过。

### Task 3: 更新 `tests/test_runtime_config.py`

- **文件**：`packages/aideo-runtime/tests/test_runtime_config.py`
- **类型**：测试
- **依赖**：无
- **描述**：覆盖 `AIDEO_RUNTIME_HOST`、`AIDEO_RUNTIME_PORT`、`AIDEO_RUNTIME_PROVIDERS` 的默认、逗号分隔解析、空值和未知 Provider；验证 `AIDEO_RUNTIME_MODELS` 在 MVP 不影响加载结果。
- **验收**：旧 JSON 配置断言移除；新 Provider 配置断言在实现前为红。

### Task 4: 实现 `config.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/config.py`
- **类型**：实现
- **依赖**：Task 3
- **描述**：使用标准库环境变量解析 Provider 名列表，定义不可变 `RuntimeSettings`；不再在配置层解析模型元数据。
- **验收**：Task 3 全部通过。

### Task 5: 更新 `tests/test_demo_backend.py`

- **文件**：`packages/aideo-runtime/tests/test_demo_backend.py`
- **类型**：测试
- **依赖**：无
- **描述**：覆盖 Demo Provider 的模型声明、Backend 工厂、chat 非流式响应、流式 `DeltaEvent`/`DoneEvent`、健康状态及模型目录。
- **验收**：模块不存在时测试为红。

### Task 6: 实现 `backend/providers/demo.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/backend/providers/demo.py`
- **类型**：实现
- **依赖**：Task 5
- **描述**：实现无网络、确定性的 Demo Provider，导出模型目录与 Backend 工厂，并从 chat 输入产生稳定文本与标准流式事件。
- **验收**：Task 5 全部通过。

### Task 7: 创建 `backend/loader.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/backend/loader.py`
- **类型**：实现
- **依赖**：Task 6
- **描述**：通过 `importlib` 按 Provider 名加载 `backend.providers.{name}`，验证模块契约并返回 Provider 的模型和 Backend。
- **验收**：`demo` 可成功加载；缺失模块或缺少契约时返回清晰配置错误。

### Task 8: 更新 `backend/providers/__init__.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/backend/providers/__init__.py`
- **类型**：实现
- **依赖**：Task 6
- **描述**：定义 Provider 模块可复用的类型别名与公开导出，不从主包直接导入具体 Provider。
- **验收**：Loader 与 Demo Provider 使用同一加载契约。

---

## Phase 2 — HTTP/SSE 服务

### Task 9: 创建 `tests/test_app.py`

- **文件**：`packages/aideo-runtime/tests/test_app.py`
- **类型**：测试
- **依赖**：Task 2、Task 4、Task 6、Task 7、Task 8
- **描述**：通过 FastAPI TestClient 覆盖健康检查、所有模型发现、能力筛选、非流式调用、SSE 调用、未知模型 `404`、能力冲突 `409` 与路径/请求体不匹配 `422`。
- **验收**：路由未实现时测试为红。

### Task 10: 创建 `api/routes.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/api/routes.py`
- **类型**：实现
- **依赖**：Task 2、Task 6、Task 7、Task 9
- **描述**：定义 `/health`、`/api/v1`、`/api/v1/{capability}` 与 `/api/v1/{capability}/{model}`，实现统一响应序列化、HTTP 错误和 `text/event-stream` 编码。
- **验收**：路由层直接测试可通过；应用装配相关用例仍由后续任务完成。

### Task 11: 创建 `api/__init__.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/api/__init__.py`
- **类型**：实现
- **依赖**：Task 10
- **描述**：导出 Runtime API router 或 router factory，不暴露内部依赖。
- **验收**：公共 API 可被 `app.py` 导入。

### Task 12: 创建 `app.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/app.py`
- **类型**：实现
- **依赖**：Task 4、Task 7、Task 8、Task 10、Task 11
- **描述**：实现 `create_app(settings: RuntimeSettings | None = None) -> FastAPI`，从环境配置动态加载 Provider、构造 Registry，并挂载 API router。
- **验收**：Task 9 全部通过。

### Task 13: 创建 `tests/test_server.py`

- **文件**：`packages/aideo-runtime/tests/test_server.py`
- **类型**：测试
- **依赖**：Task 12
- **描述**：验证命令行入口将配置的 host、port 与 app 传给 Uvicorn，不实际监听端口。
- **验收**：服务器入口不存在时测试为红。

### Task 14: 创建 `server.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/server.py`
- **类型**：实现
- **依赖**：Task 4、Task 12、Task 13
- **描述**：实现 `main()`，读取 `RuntimeSettings`、构造 app 并调用 `uvicorn.run()`。
- **验收**：Task 13 通过；设置 demo 模型环境变量后可启动服务。

### Task 15: 更新包级 `__init__.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/__init__.py`
- **类型**：实现
- **依赖**：Task 12、Task 14
- **描述**：将 CLI `main()` 委托给 `server.main`，并导出 `create_app` 与 `RuntimeSettings`。
- **验收**：`uv run --package aideo-runtime aideo-runtime --help` 可启动命令入口，公共导入成功。

---

## Phase 3 — Hurl 契约测试与文档

### Task 16: 创建 `.local.env.example`

- **文件**：`packages/aideo-runtime/http-tests/.local.env.example`
- **类型**：配置
- **依赖**：Task 15
- **描述**：提供 `RUNTIME_URL=http://localhost:9090`，不包含密钥或本地绝对路径。
- **验收**：复制为 `.local.env` 后可被 Hurl variables file 读取。

### Task 17: 创建 `health/check.hurl`

- **文件**：`packages/aideo-runtime/http-tests/health/check.hurl`
- **类型**：测试
- **依赖**：Task 15、Task 16
- **描述**：断言 `GET /health` 的 `200`、JSON Content-Type、`status=ok` 与模型计数。
- **验收**：对已启动 demo Runtime 执行 Hurl 通过。

### Task 18: 创建 `discovery/models.hurl`

- **文件**：`packages/aideo-runtime/http-tests/discovery/models.hurl`
- **类型**：测试
- **依赖**：Task 15、Task 16
- **描述**：断言全量发现返回 demo-chat 模型及 chat capability。
- **验收**：`hurl --variables-file .local.env discovery/models.hurl --test` 通过。

### Task 19: 创建 `discovery/capability-models.hurl`

- **文件**：`packages/aideo-runtime/http-tests/discovery/capability-models.hurl`
- **类型**：测试
- **依赖**：Task 15、Task 16
- **描述**：覆盖已注册 chat 能力与无模型能力的列表响应。
- **验收**：对应 Hurl 文件通过。

### Task 20: 创建 `inference/invoke-chat.hurl`

- **文件**：`packages/aideo-runtime/http-tests/inference/invoke-chat.hurl`
- **类型**：测试
- **依赖**：Task 15、Task 16
- **描述**：提交 chat stream 请求，断言 `text/event-stream`、delta frame 与 done frame。
- **验收**：对应 Hurl 文件通过。

### Task 21: 创建 `inference/error-cases.hurl`

- **文件**：`packages/aideo-runtime/http-tests/inference/error-cases.hurl`
- **类型**：测试
- **依赖**：Task 15、Task 16
- **描述**：覆盖未注册模型 `404`、能力冲突 `409` 和路径/请求体不匹配 `422`。
- **验收**：对应 Hurl 文件通过。

### Task 22: 创建 `http-tests/Makefile`

- **文件**：`packages/aideo-runtime/http-tests/Makefile`
- **类型**：实现
- **依赖**：Task 17、Task 18、Task 19、Task 20、Task 21
- **描述**：按参考 Makefile 实现 `ENV`、动态一级目录、`all`、目录目标及 `<目录>@verbose` 目标；`hurl --test` 用于普通测试，verbose 保留请求详情。
- **验收**：`make`、`make health`、`make inference@verbose` 均调用正确的 Hurl 文件与变量文件。

---

## 收尾（随最后实现任务一并完成）

- 更新 `packages/aideo-runtime/http-tests/README.md`、包 README 和 2026-07-15 变更详情，说明服务启动、模型环境变量、`make` 使用和验证结果。
- 运行 `uv sync --all-packages`、`uv run --package aideo-runtime pytest`、`pre-commit run --files ...`；在已启动 demo Runtime 后运行 `make -C packages/aideo-runtime/http-tests`。
