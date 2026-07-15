# feat-aideo-models-extraction

## 背景与目标

将本地推理模型的跨平台依赖与加载实现从 `aideo-runtime` 提取为独立
`aideo-models` 库，使 Runtime 保留能力路由、HTTP/SSE API、模型注册和全局
路径编排。这样 Linux CUDA 生产环境与 macOS 开发环境可使用同一 Runtime
接口，而重型本地模型依赖由库层按平台处理。

同时将 `sse-starlette` 升级到当前兼容的较新稳定版本。

## 用户故事

- 作为 Runtime 使用者，我希望在 macOS 上安装并运行 demo、HTTP API 与单元测试，
  而不下载 Linux CUDA 模型依赖。
- 作为 Linux GPU 部署者，我希望安装 `aideo-models` 后直接启用 LTX2 和
  Faster-Whisper2 Provider，继续使用现有的共享 models/input/output 路径配置。
- 作为库维护者，我希望未来新增本地模型时只扩展 `aideo-models`，不污染
  Runtime 的服务层依赖与平台判断。

## 功能列表

### MVP（必须有）

- [ ] 创建 `packages/aideo-models`，采用标准 `src` layout、Python 3.12+、
  uv workspace 兼容配置。
- [ ] 将 LTX2 与 Faster-Whisper2 的惰性加载、本地模型执行与 Linux CUDA 依赖
  移入该库。
- [ ] 为本地模型库定义小型稳定接口，供 Runtime Provider 适配；不让模型库依赖
  FastAPI、Runtime HTTP API、Runtime 的数据模型或 Runtime 路径配置。
- [ ] 将 `aideo-runtime` 的 `ltx2` 和 `faster_whisper2` Provider 降为薄适配层，
  保留现有 Provider 名称、模型 ID、请求字段、SSE 事件和输出 URI 行为。
- [ ] 模型库与 Runtime 均可在 macOS 无 GPU 依赖下导入、发现 Provider 并通过测试。
- [ ] `PathSettings`、安全相对路径解析与 `runtime://output/...` URI 始终保留在
  `aideo-runtime`；Runtime 在调用本地模型库前解析路径，并只向库传递已验证的
  `pathlib.Path`。
- [ ] 保留 Linux 的 PyTorch CUDA 13 index、LTX Git sources、Faster-Whisper2 Git
  source 与 NVIDIA 依赖，但只归属 `aideo-models`。
- [ ] 将 `sse-starlette` 升级到当前可用的较新稳定版本，并更新锁文件与兼容性测试。
- [ ] 更新 README、环境变量示例、变更记录和测试。

### 后续迭代（可以有）

- [ ] 将更多本地模型（LLM、Vision、Diffusers）加入 `aideo-models`。
- [ ] 增加模型能力发现、显存需求和安装诊断 API。
- [ ] 为 Linux CUDA 实机提供独立的集成测试矩阵。

## 技术方案概述

- 平台/运行环境：Python 3.12+、uv workspace；macOS 开发与 Linux CUDA 13 部署。
- 核心技术栈：`aideo-models` 负责惰性导入与本地推理实现；`aideo-runtime`
  负责 `Backend`、全局路径、请求/事件转换、Registry 与 HTTP/SSE。
- 关键约束：保持公开 Runtime HTTP 契约与 `AIDEO_RUNTIME_*` 全局路径配置不变；
  不在导入时加载模型或 GPU 库；不保留 Provider 私有模型/input/output 根目录。

## 非功能需求

- 兼容性：无 Linux-only 轮子的平台可完成 `uv sync --all-packages`、Provider 发现与
  单元测试。
- 可维护性：每个本地模型的第三方依赖只在 `aideo-models` 声明；Runtime 不声明
  torch、LTX、Whisper 或 NVIDIA 包。
- 质量：新增/迁移单元测试；`ruff`、`mypy`、`pre-commit` 通过。

## 待定问题

- 无。MVP 默认仅迁移已实现的 LTX2 和 Faster-Whisper2。
