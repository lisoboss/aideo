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
- 将语音模型的惰性导入目标修正为 `faster_whisper2`，与已配置的 Faster-Whisper2 分发包模块名一致。
- 将 `tools/novel-dump` 加入根 pytest 导入路径，使提交 hook 可以收集并执行该独立工具的测试。
- Runtime 通过 `uvicorn.error` 记录推理开始、完成、SSE 后端错误和完整异常 traceback，便于直接在服务端终端诊断模型执行失败。
- Faster-Whisper2 仅加载 `AIDEO_RUNTIME_MODELS_DIR` 内的本地相对模型目录，默认 `whisper/large-v3`；兼容旧 `AIDEO_MODEL_ROOT` 作为模型根目录回退。
- `interface.sh` 通过 `scripts/cuda-env-run.sh` 启动 Runtime；该脚本将虚拟环境内全部 NVIDIA 动态库目录（包括 cuBLAS 与 cuDNN）加入 `LD_LIBRARY_PATH`。
- 新增 `http-tests/asr/transcribe-whisper.hurl`，覆盖 Faster-Whisper2 本地模型的 JSON 与 SSE 转写请求。
- 恢复 `X-Memory-Preempt: true`：在加载目标本地模型前释放其他已加载的本地 Backend，缓解 Whisper 与 LTX2 之间的 GPU 显存竞争；LTX2 默认资源路径对齐备份分支的 x2 Upscaler。
- 将 Runtime Provider 改为薄适配层，保持模型 ID、HTTP 请求、SSE 事件和输出 URI 契约。
- 添加 `AIDEO_RUNTIME_DEBUG`。启用时，HTTP 500 返回结构化 Python traceback，
  SSE 在流开始后发生异常时返回带 traceback 的 `error` 事件。

## Runtime 依赖

- Runtime 新增 workspace 依赖 `aideo-models`，移除本地模型和 GPU 依赖。
- `sse-starlette` 最低版本升级到 `3.4.5`；`websockets` 保持属于 Runtime 传输层。

## Linux 启动脚本

- `interface.sh` 现在检查 `uv`、创建 Runtime models/input/output 根目录、转发 debug
  配置，并在启用 LTX2 时校验所需模型资源。
- `http-server.sh` 现在检查 `uv` 与 `curl`、创建服务数据目录，并在启动前确认
  `AIDEO_INFERENCE_URL/health` 可访问。
- 两个脚本统一输出启动信息；AI API Key 始终只显示是否已设置。

## 验证

- `uv sync --all-packages`：通过。
- `uv run ruff check packages/aideo-models packages/aideo-runtime`：通过。
- `uv run mypy packages/aideo-models/src packages/aideo-runtime/src`：通过。
- `uv run pytest packages/aideo-models/tests packages/aideo-runtime/tests`：37 项通过。
- Runtime debug 配置、JSON traceback 与 SSE error traceback 测试：通过。
- `bash -n interface.sh http-server.sh` 与两项隔离 shell 启动脚本测试：通过。
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
├── interface.sh
├── http-server.sh
├── tests/
│   ├── test_http_server_script.sh
│   └── test_interface_script.sh
├── specs/feat-startup-script-hardening/
│   ├── plan.md
│   ├── spec.md
│   └── tasks.md
├── specs/feat-aideo-models-extraction/
│   ├── plan.md
│   ├── spec.md
│   └── tasks.md
└── uv.lock
```
