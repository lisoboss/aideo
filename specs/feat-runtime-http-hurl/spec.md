# feat-runtime-http-hurl

## 背景与目标

> 为 Aideo 服务端和运维人员提供可通过环境变量配置、可由 Hurl 端到端验证的统一推理 Runtime HTTP/SSE 服务。

## 用户故事

- 作为 `aideo-serv`，我希望通过统一 HTTP API 发现 Runtime 中已注册的模型与能力，以便不依赖任何具体 Provider。
- 作为 `aideo-serv`，我希望向已注册模型提交请求并接收标准化 SSE 事件，以便持续更新任务状态。
- 作为运维人员，我希望仅通过环境变量配置服务监听地址与模型注册信息，以便在本地、容器和线上环境中部署。
- 作为开发者，我希望通过 Hurl 覆盖每个 HTTP 路由及其成功、错误和 SSE 场景，以便验证真实运行的 Runtime 契约。

## 功能列表

### MVP（必须有）

- [ ] FastAPI Runtime 服务及命令行入口。
- [ ] `GET /health`：返回 Runtime 健康状态。
- [ ] `GET /api/v1`：列出全部已注册模型与能力。
- [ ] `GET /api/v1/{capability}`：列出指定能力的模型。
- [ ] `POST /api/v1/{capability}/{model}`：验证模型能力匹配、调用 Backend，并以 SSE 返回统一事件。
- [ ] 使用 `AIDEO_RUNTIME_*` 环境变量配置主机、端口及 Provider 列表。
- [ ] 请求未注册模型、能力不匹配、非流式调用失败和 Backend 异常时返回稳定 HTTP 错误响应。
- [ ] 支持 Provider 声明的 `context_length` 硬上限，并在请求层校验 `max_output_tokens`。
- [ ] 支持统一请求参数：`max_output_tokens`、`temperature`、`top_p`、`stop`、`seed`、`reasoning_effort` 与 `truncation`。
- [ ] 在 `packages/aideo-runtime/http-tests/` 提供 Hurl 文件：健康检查、全量发现、按能力发现、推理 SSE、未知模型、能力不匹配。
- [ ] 在 `packages/aideo-runtime/http-tests/Makefile` 提供 Hurl 测试入口，采用参考项目相同的目录目标与 `@verbose` 目标约定。
- [ ] 在 `packages/aideo-runtime/http-tests/.local.env.example` 提供可复制的 Hurl 变量示例；本地实际配置放在未提交的 `.local.env` 中。
- [ ] 提供可供本地 Hurl 验证的内置演示 Provider；它只产生确定性模拟输出，不连接真实模型服务。

### 后续迭代（可以有）

- [ ] OpenAI、Ollama、ComfyUI、LTX 等真实 Provider 的环境变量配置与协议实现。
- [ ] gRPC、WebSocket、FFI 和本地进程 Transport。
- [ ] 动态模型发现、权重路由和负载均衡。

## API 契约

| 方法 | 路径 | 成功响应 |
| --- | --- | --- |
| `GET` | `/health` | JSON 健康状态与已注册模型数 |
| `GET` | `/api/v1` | JSON 模型列表，按 capability 分组 |
| `GET` | `/api/v1/{capability}` | JSON 指定 capability 的模型列表 |
| `POST` | `/api/v1/{capability}/{model}` | `text/event-stream`，发送 `delta`、`progress`、`log`、`done` 或 `error` 事件 |

请求体沿用 `BackendRequest`：`capability`、`model`、`input`、`parameters`、`stream`。路径中的 capability 和 model 是权威路由信息；若请求体提供的值不匹配，服务返回 `422`。

`context_length` 是 Provider 模型目录声明的只读能力，客户端不能覆盖。请求使用 `parameters.max_output_tokens` 限制生成上限；当可估算的输入 token 与最大输出之和超过模型上下文上限时，`truncation=auto` 允许 Provider/Adapter 截断最早输入，其他值返回 `422`。

## 技术方案概述

- 平台/运行环境：Python 3.12+、uv workspace、FastAPI、httpx。
- 核心技术栈：现有 Capability / Registry / Backend / Event 领域模型；FastAPI 适配层；SSE 响应。
- 配置：以 `AIDEO_RUNTIME_HOST`、`AIDEO_RUNTIME_PORT` 和逗号分隔的 `AIDEO_RUNTIME_PROVIDERS` 环境变量为主，例如 `AIDEO_RUNTIME_PROVIDERS=demo,xxx`。Runtime 自动导入 `aideo_runtime.backend.providers.demo` 与 `aideo_runtime.backend.providers.xxx`；每个 Provider 模块自行声明模型元数据与 Backend 工厂。MVP 提供 `demo` Provider。`AIDEO_RUNTIME_MODELS` 保留给后续按模型过滤 Provider 模型目录的能力。
- Hurl：测试目标由 `RUNTIME_URL` 变量提供，默认 `http://localhost:9090`；运行前由使用者启动 Runtime 并设置模型环境变量。`Makefile` 以 `ENV=local` 选择 `.local.env`，自动发现一级测试目录；`make` 运行全部目录，`make <目录>` 只运行该目录，`make <目录>@verbose` 输出请求详情。

## 非功能需求

- 性能：SSE 首个事件不应等待完整推理结果；服务可复用 HTTP Backend 的连接池。
- 安全：不得在响应或 Hurl 文件中记录 Provider 密钥；环境变量中的密钥仅留给后续 Provider 实现。
- 兼容性：Hurl 用例使用标准 HTTP/SSE；所有 API 返回 JSON 或 `text/event-stream`。
- 可测试性：内置 `backend/providers/demo.py` 确保 Hurl 测试无需外部模型或网络访问。

## 待定问题

- 无。MVP 以确定性演示 Backend 建立端到端契约；真实 Provider 在后续迭代接入。
