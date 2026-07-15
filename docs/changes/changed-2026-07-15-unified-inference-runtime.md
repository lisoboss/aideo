# 2026-07-15 — Unified Inference Runtime

## Runtime Package

### 新增文件

| 文件 | 操作 | 说明 |
| --- | --- | --- |
| `packages/aideo-runtime/` | 新增 | Provider-neutral unified inference runtime package. |
| `packages/aideo-runtime/tests/` | 新增 | Unit and HTTP interaction tests for the runtime. |
| `docs/changes.md` | 修改 | Change-log summary index. |
| `docs/changes/changed-2026-07-15-unified-inference-runtime.md` | 新增 | This change detail. |

### 变更要点

- Defined capability, request, response, output, event, health, and model metadata contracts.
- Added protocol adapters for OpenAI, Ollama, ComfyUI, and LTX as intentionally unimplemented boundaries.
- Added reusable HTTP/SSE transport, HTTP backend, backend manager, registry, and router interface.
- Added deterministic unit tests and in-memory HTTP/SSE tests using `httpx.MockTransport`.
- Added an environment-configured FastAPI Runtime, deterministic demo provider, and Hurl/Makefile HTTP contract suite.
- Added a root `.env.example` for starting the configured demo Runtime locally.
- Simplified configuration to a comma-separated `AIDEO_RUNTIME_PROVIDERS` list with dynamically loaded Provider modules.
- Added normalized request inference parameters and Provider-declared output/context limits.
- Implemented OpenAI Responses, ComfyUI workflow, and LTX async-job protocol models with offline adapter tests.
- Relaxed the Hurl SSE delta assertion so optional event metadata does not make the contract test brittle.
- Added ComfyUI-style shared `models`, `input`, and `output` roots with safe
  relative-path resolution and portable `runtime://output/<path>` result URIs.
- Added lazy `ltx2` and `faster_whisper2` local Backends. LTX resolves all
  checkpoints beneath the shared model root and emits video-stage progress;
  Faster-Whisper2 resolves audio beneath the shared input root and falls back
  from unavailable CUDA to CPU `int8`.
- Added Linux-scoped CUDA 13, PyTorch, LTX, and Faster-Whisper2 dependencies,
  preserving the PyTorch CUDA index and upstream Git sources from the prior
  Runtime configuration. GPU packages remain uninstalled on macOS.

### 验证

- `uv run pytest`：全量测试通过。
- 新增文件的 `pre-commit` hooks：全部通过。
- Hurl/Makefile 目标已展开；本机 Hurl 二进制因缺失 `/opt/local/lib/libxml2.2.dylib` 无法执行，待修复本机依赖后可直接运行。
- `uv run --package aideo-runtime pytest packages/aideo-runtime/tests`：34 项通过。
- `uv run ruff check packages/aideo-runtime`：通过。
- `uv run mypy packages/aideo-runtime/src`：通过。
- LTX/Faster-Whisper2 的真实 GPU 推理依赖 Linux CUDA 与本地模型文件；本次通过 mock Backend 覆盖路径、CPU 回退、统一输出和进度契约。

## 涉及文件总览

```text
aideo/
├── .gitignore
├── docs/
│   ├── changes.md
│   └── changes/
│       └── changed-2026-07-15-unified-inference-runtime.md
├── packages/
    └── aideo-runtime/
        ├── .env.example
        ├── README.md
        ├── pyproject.toml
        ├── http-tests/
        │   ├── .local.env.example
        │   ├── Makefile
        │   ├── README.md
        │   ├── discovery/
        │   │   ├── capability-models.hurl
        │   │   └── models.hurl
        │   ├── health/
        │   │   └── check.hurl
        │   └── inference/
        │       ├── error-cases.hurl
        │       └── invoke-chat.hurl
        ├── src/aideo_runtime/
        │   ├── __init__.py
        │   ├── app.py
        │   ├── config.py
        │   ├── paths.py
        │   ├── server.py
        │   ├── api/ (__init__.py, routes.py)
        │   ├── backend/
        │   │   ├── __init__.py, base.py, http.py, loader.py, manager.py
        │   │   └── providers/ (__init__.py, demo.py, faster_whisper2.py, ltx2.py)
        │   ├── capabilities/ (__init__.py, capability.py)
        │   ├── models/ (__init__.py, events.py, health.py, model_info.py, parameters.py, request.py, response.py)
        │   ├── protocol/ (__init__.py, base.py, comfyui.py, ltx.py, ollama.py, openai.py)
        │   ├── registry/ (__init__.py, registry.py)
        │   ├── router/ (__init__.py, base.py)
        │   └── transport/ (__init__.py, http.py, sse.py)
        └── tests/
            ├── test_app.py
            ├── test_demo_backend.py
            ├── test_faster_whisper2_provider.py
            ├── test_http.py
            ├── test_inference_parameters.py
            ├── test_ltx2_provider.py
            ├── test_models.py
            ├── test_paths.py
            ├── test_registry_manager.py
            └── test_runtime_config.py
├── pyproject.toml
├── specs/feat-runtime-http-hurl/
│   ├── plan.md
│   ├── spec.md
│   └── tasks.md
├── specs/feat-local-ltx-asr-providers/
│   ├── plan.md
│   ├── spec.md
│   └── tasks.md
└── uv.lock
```
