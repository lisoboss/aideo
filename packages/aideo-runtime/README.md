# aideo-runtime

Local inference runtime for Aideo. HTTP + SSE. Runs on Windows 11 / Linux with NVIDIA GPU.

## Architecture

```
POST /api/v1/{category}/{name}   ──→  ProviderManager  ──→  Provider.run()  ──→  SSE stream
                                          │
                                    ┌─────┴─────┐
                                    │  load()    │  ← first request
                                    │  unload()  │  ← 5 min idle / preempt
                                    │  cancel()  │  ← client disconnect
                                    └───────────┘
```

**Design principles:**

1. **One model, one provider.** Each `BaseProvider` subclass wraps exactly one ML model. State is explicit: loaded / unloaded / running.

2. **Load on demand, release on idle.** Models load into GPU memory on the first request and unload after 5 minutes of inactivity. No preloading at startup — memory is expensive.

3. **Request-scoped execution.** `run()` is called once per HTTP request. The SSE connection is the request boundary. Client disconnect → `cancel()` → provider stops inference.

4. **Memory preemption.** A request with `X-Memory-Preempt: true` header unloads ALL other models before loading its own. Fails if any provider is currently running. This lets heavy models (e.g. LTX-2 22B) take exclusive GPU memory when needed.

5. **Category-based routing.** Endpoints follow `/api/v1/{category}/{name}`. Categories: `speech`, `video`, `chat`, `vision`, `image`. Each category has its own `PROVIDERS` registry and optional typed ABC subclass.

6. **SSE for streaming.** Every inference run streams progress via Server-Sent Events. Yields `ProgressStatus` (progress %, message, optional result_data). Final result has `result_data` populated. No polling.

7. **Provider self-registration.** Each provider module calls `register_provider(MyProvider)` at import time. The `ProviderManager` discovers it via `importlib` + each category's `PROVIDERS` dict. No central registry to update.

8. **macOS for dev, Linux/Win for run.** This repo is developed on macOS where CUDA dependencies can't install. Tests execute on the target machine. Only code correctness (syntax) is verified locally.

## Coding Rules

### Provider Implementation

```python
from aideo_runtime.provider import BaseProvider, ProgressStatus
from aideo_runtime.xxx.provider import XxxProvider, register_provider

class MyProvider(XxxProvider):
    provider_name = "my-provider@xxx"   # unique, scoped to category

    def __init__(self, ...) -> None:
        super().__init__()              # REQUIRED: sets up _cancel_event
        self._loaded = False

    async def load(self) -> None:       # idempotent
        if self._loaded: return
        # ... load model ...
        self._loaded = True

    async def unload(self) -> None:     # idempotent
        # ... free model ...
        self._loaded = False

    async def run(self, **kwargs) -> AsyncGenerator[ProgressStatus, None]:
        # 1. Validate inputs, yield error if invalid
        # 2. Auto-load if needed
        # 3. Periodically check self.is_cancelled during long ops
        # 4. Yield ProgressStatus for progress
        # 5. Final yield MUST have result_data populated

register_provider(MyProvider)
```

### Rules

1. **Always call `super().__init__()`** in provider `__init__`. This sets up the cancel event.

2. **`load()` must be idempotent.** Check `self._loaded` first.

3. **Check `self.is_cancelled`** during long operations (especially thread-pool work). Client disconnects are normal — don't waste GPU cycles.

4. **Yield `ProgressStatus`, not dict.** The base class defines the type. Older code used raw dicts — migrated away.

5. **`result_data` marks completion.** The SSE dispatcher and downstream clients use its presence to distinguish progress from final results.

6. **Thread-pool work must run via `loop.run_in_executor`.** Blocking the async event loop kills responsiveness. Wrap model inference in `run_in_executor`.

7. **Don't import torch at module level.** Video/LLM providers should lazy-import heavy dependencies. Speech already has faster-whisper which imports torch — this is acceptable for always-loaded providers but video does it lazily.

8. **Environment variables for config.** Model paths, device selection, and runtime settings come from `os.environ`. Never hardcode paths. Standard vars: `WHISPER_MODEL`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE`, `AIDEO_IDLE_TIMEOUT`, `AIDEO_RUNTIME_HOST`, `AIDEO_RUNTIME_PORT`.

9. **`register_provider()` at module bottom.** The class decorator/register pattern ensures the provider is discoverable as soon as the module is imported.

10. **One file, one provider.** Don't put multiple provider classes in the same module. The `register_provider()` call at module level assumes one provider per file.

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/{category}/{name}` | Run inference, stream SSE |
| `GET` | `/api/v1/{category}` | List providers in category |
| `GET` | `/api/v1` | List all categories |
| `GET` | `/health` | Health check |

### Headers

| Header | Value | Effect |
|--------|-------|--------|
| `X-Memory-Preempt` | `true` / `1` / `yes` | Unload all other models before running |
| `Content-Type` | `application/json` | Standard JSON body |

### SSE Events

```
event: progress
data: {"progress":45.5,"message":"Transcribing... (7s)","result_data":null}

event: progress
data: {"progress":100.0,"message":"Transcription complete","result_data":{"full_text":"...","segments":[...]}}

event: error
data: {"progress":100.0,"message":"preempt_failed","result_data":{"error":"preempt_failed","detail":"..."}}
```

## Directory Layout

```
packages/aideo-runtime/src/aideo_runtime/
├── provider.py          # BaseProvider ABC + ProgressStatus
├── server.py            # FastAPI + ProviderManager + SSE routes
├── speech/
│   ├── __init__.py      # PROVIDERS export
│   ├── provider.py      # SpeechProvider ABC
│   └── faster_whisper.py
├── video/
│   ├── __init__.py      # PROVIDERS export (lazy)
│   ├── provider.py      # VideoProvider ABC
│   └── ltx2.py
├── chat/
│   ├── __init__.py
│   ├── provider.py      # ChatProvider ABC
│   └── stub.py
├── vision/
│   ├── __init__.py
│   ├── provider.py      # VisionProvider ABC
│   └── stub.py
└── image/
    ├── __init__.py
    ├── provider.py      # ImageProvider ABC (edit / upscale)
    └── stub.py
```

## Run

```bash
uv run --package aideo-runtime aideo-runtime

# or directly
python -m aideo_runtime.server
```

Env vars:
- `AIDEO_RUNTIME_HOST` / `AIDEO_RUNTIME_PORT` — listen address (default `0.0.0.0:9090`)
- `AIDEO_IDLE_TIMEOUT` — seconds before auto-unload (default `300`)
- `WHISPER_MODEL` — model size/path (default `large-v3`)
- `WHISPER_DEVICE` — `cuda` or `cpu` (default `cuda`)
- `WHISPER_COMPUTE_TYPE` — `float16` / `int8` (default `float16`)
