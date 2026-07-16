# 2026-07-16 — Extract Aideo Local Models

## 本地模型库

### 新增文件

| 文件 | 操作 | 说明 |
| --- | --- | --- |
| `packages/aideo-models/` | 新增 | 跨平台本地模型加载与执行库。 |

### 变更要点

- 新增 `aideo-models`，提供 Runtime 无关的 LTX2 与 Faster-Whisper2 请求、结果和惰性执行实现。
- 保留 Runtime 的 `PathSettings`、相对路径安全校验和 `runtime://output/` URI；模型库只接收已验证的 `Path`。
- 将 Linux CUDA 13、PyTorch、NVIDIA、LTX 和 Faster-Whisper2 依赖与 Git sources 迁移至 `aideo-models`。
- 将 Runtime Provider 改为薄适配层，保持模型 ID、HTTP 请求、SSE 事件和输出 URI 契约。
- 添加 `AIDEO_RUNTIME_DEBUG`。启用时，HTTP 500 返回结构化 Python traceback，
  SSE 在流开始后发生异常时返回带 traceback 的 `error` 事件。

## Runtime 依赖

- Runtime 新增 workspace 依赖 `aideo-models`，移除本地模型和 GPU 依赖。
- `sse-starlette` 最低版本升级到 `3.4.5`；`websockets` 保持属于 Runtime 传输层。

## 验证

- `uv sync --all-packages`：通过。
- `uv run ruff check packages/aideo-models packages/aideo-runtime`：通过。
- `uv run mypy packages/aideo-models/src packages/aideo-runtime/src`：通过。
- `uv run pytest packages/aideo-models/tests packages/aideo-runtime/tests`：37 项通过。
- Runtime debug 配置、JSON traceback 与 SSE error traceback 测试：通过。
- LTX2 与 Faster-Whisper2 的实际推理仍需 Linux CUDA 与本地模型文件；mock 测试覆盖跨平台导入、路径边界、CPU 回退、适配与输出契约。

## 涉及文件总览

```text
aideo/
├── docs/
│   ├── changes.md
│   └── changes/
│       └── changed-2026-07-16-aideo-models-extraction.md
├── packages/
│   ├── aideo-models/
│   │   ├── README.md
│   │   ├── pyproject.toml
│   │   ├── src/aideo_models/
│   │   │   ├── __init__.py
│   │   │   ├── ltx2.py
│   │   │   ├── models.py
│   │   │   ├── py.typed
│   │   │   └── whisper.py
│   │   └── tests/
│   │       ├── test_local_model_contracts.py
│   │       ├── test_ltx2.py
│   │       ├── test_public_api.py
│   │       └── test_whisper.py
│   └── aideo-runtime/
│       ├── .env.example
│       ├── README.md
│       ├── pyproject.toml
│       ├── src/aideo_runtime/
│       │   ├── api/routes.py
│       │   ├── app.py
│       │   ├── config.py
│       │   ├── models/events.py
│       │   └── backend/providers/
│       │       ├── faster_whisper2.py
│       │       └── ltx2.py
│       └── tests/
│           ├── test_app.py
│           ├── test_faster_whisper2_provider.py
│           ├── test_ltx2_provider.py
│           └── test_runtime_config.py
├── specs/feat-aideo-models-extraction/
│   ├── plan.md
│   ├── spec.md
│   └── tasks.md
└── uv.lock
```
