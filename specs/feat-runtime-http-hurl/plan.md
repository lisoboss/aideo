# Technical Plan: feat-runtime-http-hurl

## 目录结构

```text
packages/aideo-runtime/
├── pyproject.toml                              # [修改] 增加 FastAPI 与 Uvicorn
├── README.md                                   # [修改] 补充启动、环境变量和 Hurl 用法
├── src/aideo_runtime/
│   ├── __init__.py                             # [修改] 导出 app/config 公共 API
│   ├── app.py                                  # [新增] FastAPI app 工厂与生命周期
│   ├── config.py                               # [新增] 环境变量解析与模型配置
│   ├── api/
│   │   ├── __init__.py                         # [新增] API 公共导出
│   │   └── routes.py                           # [新增] health、发现和 SSE 推理路由
│   ├── backend/
│   │   ├── demo.py                             # [删除] 演示实现迁移至 impl/
│   │   ├── loader.py                           # [新增] 根据实现名动态导入 Backend
│   │   ├── providers/
│   │   │   ├── __init__.py                     # [新增] Provider 模块契约
│   │   │   └── demo.py                         # [新增] 确定性本地演示 Backend
│   │   └── manager.py                          # [修改] 支持服务状态查询
│   ├── models/
│   │   ├── parameters.py                       # [新增] 请求级通用推理参数
│   │   └── response.py                         # [修改] 将输出序列化为 API JSON
│   ├── registry/
│   │   └── registry.py                         # [修改] 按 ID/Capability 查询模型
│   └── server.py                               # [新增] `aideo-runtime` Uvicorn 入口
├── tests/
│   ├── test_app.py                             # [新增] HTTP、环境变量与 SSE 单元/集成测试
│   └── ...existing tests
└── http-tests/
    ├── README.md                               # [新增] 启动服务与 Hurl 运行说明
    ├── Makefile                                # [新增] Hurl 全量、目录与 verbose 入口
    ├── .local.env.example                      # [新增] Hurl 本地变量模板
    ├── health/
    │   └── check.hurl                          # [新增] 健康检查
    ├── discovery/
    │   ├── models.hurl                         # [新增] 全量模型发现
    │   └── capability-models.hurl              # [新增] 按能力发现
    └── inference/
        ├── invoke-chat.hurl                    # [新增] 成功 SSE 推理
        ├── unknown-model.hurl                  # [新增] 未注册模型错误
        └── capability-mismatch.hurl            # [新增] 路径/请求体能力不匹配错误

specs/feat-runtime-http-hurl/
├── spec.md                                     # ✅ 已确认
├── plan.md                                     # ✅ 当前文件
└── tasks.md                                    # [下一阶段]
```

## 核心数据模型

```python
@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    host: str
    port: int
    models: list[ModelInfo]

# AIDEO_RUNTIME_PROVIDERS：
demo,xxx
```

Runtime 依次导入 `aideo_runtime.backend.providers.demo`、`aideo_runtime.backend.providers.xxx`。每个模块导出 `create_backend() -> Backend` 和 `models() -> list[ModelInfo]`；Provider 模块是模型元数据、Provider 绑定和连接配置的唯一所有者。

## 接口定义

### 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `AIDEO_RUNTIME_HOST` | `127.0.0.1` | Uvicorn 监听主机 |
| `AIDEO_RUNTIME_PORT` | `9090` | Uvicorn 监听端口 |
| `AIDEO_RUNTIME_PROVIDERS` | `demo` | 逗号分隔的 Provider 名；自动加载 `backend/providers/{name}.py` |
| `AIDEO_RUNTIME_MODELS` | 未设置 | 预留的逗号分隔模型白名单；MVP 不启用 |

### HTTP API

| 方法 | 路径 | 响应 |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok","models":1}` |
| `GET` | `/api/v1` | `{"models":[...],"capabilities":[...]}` |
| `GET` | `/api/v1/{capability}` | `{"capability":"chat","models":[...]}` |
| `POST` | `/api/v1/{capability}/{model}` | `text/event-stream` |

`POST` 请求体必须为 `BackendRequest` JSON。路径 capability/model 与请求体非空值不一致时返回 `422`；未注册模型返回 `404`；模型 capability 与路径不一致返回 `409`；非流式请求返回标准 `BackendResponse` JSON。

### 请求参数与上下文校验

```python
@dataclass(frozen=True, slots=True)
class InferenceParameters:
    max_output_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stop: list[str] | None = None
    seed: int | None = None
    reasoning_effort: str | None = None
    truncation: Literal["auto", "disabled"] = "disabled"
```

- `ModelInfo.context_length` 是 Provider 声明的固定能力，不接受请求覆盖。
- 路由在调用 Backend 前校验 `max_output_tokens` 不超过模型 `max_tokens`；若模型没有上限则不作该项限制。
- Provider/Adapter 负责精确计算输入 token。无法精确计算时，Runtime 只执行确定性参数范围校验；Provider 在实际调用时执行上下文溢出处理。
- Provider 支持 `truncation=auto` 时可以裁剪最早输入；否则返回标准 `422`。不支持的参数不得静默忽略，必须通过 Provider/Adapter 转换或明确报错。

### SSE 事件编码

每个标准事件编码为一条 SSE frame，`event` 是事件类别，`data` 是 JSON：

```text
event: delta
data: {"delta":"demo response"}

event: done
data: {"metadata":{"model":"demo-chat"}}
```

事件映射为 `delta`、`progress`、`log`、`done`、`error`。`DemoBackend` 为 chat 请求依次发出 delta 和 done，不依赖网络或模型权重。

## 实施阶段

### Phase 1 — 服务与配置基础

- 目标：使用环境变量发现后端实现、构建模型注册表，并以 CLI 启动可探测的 FastAPI Runtime。
- 产出文件：`config.py`、`backend/loader.py`、`backend/providers/__init__.py`、`backend/providers/demo.py`、`app.py`、`server.py`、`api/__init__.py`、`api/routes.py`。

### Phase 2 — 统一调用与 SSE

- 目标：将 Registry/Backend/Event 模型连接到 HTTP 调用路径，提供 DemoBackend 与稳定错误响应。
- 产出文件：`backend/demo.py`、`backend/manager.py`、`registry/registry.py`、`models/response.py`、`api/routes.py`、`tests/test_app.py`。

### Phase 3 — Hurl 契约测试与文档

- 目标：提供可对已启动 Runtime 执行的路由覆盖与操作说明。
- 产出文件：`http-tests/Makefile`、`http-tests/.local.env.example`、`http-tests/*/*.hurl`、`http-tests/README.md`、`README.md`、变更日志。

### Hurl Makefile 约定

```makefile
ENV ?= local
ENV_FILE := .$(ENV).env
DIRS := $(patsubst %/,%,$(wildcard */))
VERBOSE_MODE := $(addsuffix @verbose,$(DIRS))

all: $(DIRS)
$(DIRS):
	hurl --variables-file $(ENV_FILE) ./$@/*.hurl --test
$(VERBOSE_MODE): %@verbose:
	hurl --variables-file $(ENV_FILE) ./$*/*.hurl -v
```

测试目录一一对应 API 域：`health`、`discovery`、`inference`。`.local.env.example` 只提供 `RUNTIME_URL=http://localhost:9090`；使用者复制为 `.local.env` 后，可用 `ENV=staging` 改选 `.staging.env`。
