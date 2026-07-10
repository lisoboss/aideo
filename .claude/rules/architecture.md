# Architecture

## aideo-serv (`packages/aideo-serv/src/aideo_serv/`)

- **api/** — REST + WebSocket endpoints
  - `router.py` — main `/api/v1` router, health check, `/internal/callback` (HTTP fallback)
  - `tasks.py` — task CRUD: `POST/GET/DELETE /tasks`, `CallbackPayload` model
  - `ws.py` — three WebSocket endpoints:
    - `/ws/tasks/{id}` — per-task progress stream for clients
    - `/ws/internal/inference` — inference service registration + message channel
    - `/ws/transcribe` — streaming speech-to-text (binary audio in, JSON events out)
  - `results.py` — file download/preview: `GET /results/{id}/download`, `GET /results/{id}/preview/{frame}`
- **services/** — business logic
  - `task_service.py` — task lifecycle state machine (6 states, validated transitions)
  - `storage.py` — local file storage (`data/{prefix}/{task_id}/`)
  - `connection_manager.py` — per-connection `asyncio.Queue` for WS broadcast (thread-safe)
  - `inference.py` — `InferenceClient`: HTTP client for remote inference services
  - `inference_manager.py` — `InferenceServiceManager`: WebSocket-based connection manager for local inference services. Handles registration, capability discovery, and message routing between aideo-serv and connected inference runtimes
- **models/** — Pydantic models
  - `task.py` — `Task`, `TaskCreate`, `TaskStatus` (StrEnum, 6 states), `TaskListResponse`. Tasks carry `task_type` for routing (`video_generation`, `speech_to_text`, etc.)
  - `events.py` — `WSEvent` (client-facing push protocol), `InferenceRegistration` (service handshake), `InferenceMessage` (internal inference protocol envelope with `ServiceType`, `TaskType`, `MessageType` literals)
- **middleware/auth.py** — JWT skeleton (MVP returns `AnonymousUser`)
- `config.py` — pydantic-settings (`AIDEO_` env prefix), includes `model_root`/`output_root`/`input_root` passed to inference services
- `app.py` — FastAPI factory (`create_app()`), CORS, lifespan
- `dependencies.py` — DI singletons (`get_task_service`, `get_inference_client`, `get_inference_manager`, `get_connection_manager`)
- `main.py` — uvicorn entry point

## aideo-runtime (`packages/aideo-runtime/src/aideo_runtime/`)

Aggregated local inference service. Connects to aideo-serv via WebSocket, registers capabilities, and routes incoming `task_submit` messages to the correct provider.

- `server.py` — FastAPI app + `AideoWSClient`: connects to aideo-serv's `/ws/internal/inference`, sends `register` with capabilities, loops on messages
- `provider.py` — `BaseProvider` ABC: `load()`, `run(**kwargs) → AsyncGenerator`, `provider_name`, `is_loaded`
- **video/** — text-to-video generation
  - `provider.py` — `VideoProvider(BaseProvider)` ABC
  - `ltx2.py` — `LTX2VideoProvider`: LTX-2.3 distilled model via ltx-pipelines, lazy-loaded on first video task (avoids torch import at startup)
- **speech/** — speech-to-text transcription
  - `provider.py` — `SpeechProvider(BaseProvider)` ABC
  - `faster_whisper.py` — `FasterWhisperProvider`: supports `model_size_or_path` for local model paths, auto-detects CUDA availability
- **chat/** — text conversation (stub)
  - `provider.py` — chat ABC
  - `stub.py` — placeholder
- **vision/** — image-to-text (stub)
  - `provider.py` — vision ABC
  - `stub.py` — placeholder

## aideo-cli (`packages/aideo-cli/src/aideo_cli/`)

- `client.py` — `AideoClient`: async HTTP + WebSocket wrapper for aideo-serv API. Supports `submit()`, `transcribe()`, `list_tasks()`, `get_task()`, `cancel_task()`, `download_result()`, `connect_ws()`, `stream_transcribe()`
- `commands.py` — typer subcommands: `submit`, `list`, `status`, `cancel`, `download`, `ws`, `transcribe`
- `main.py` — typer app definition
- `__init__.py` — exports `main` (console_script entry point)

## Inference Protocol

Two paths for inference communication:

### Primary: WebSocket (local runtime)
```
aideo-runtime ──WS──→ aideo-serv:/ws/internal/inference
  1. runtime sends: {"type": "register", "service_type": "aideo-runtime", "capabilities": [...], "version": "0.1.0"}
  2. serv replies:   {"type": "registered", "data": {"service_type": "aideo-runtime"}}
  3. serv → runtime: {"type": "task_submit", "task_id": "...", "task_type": "video_generation", "data": {...}}
  4. runtime → serv: {"type": "progress"|"completed"|"error"|"cancelled", "task_id": "...", "data": {...}}
```

### Fallback: HTTP callback (remote/cloud inference)
```
POST /api/v1/internal/callback  ←  inference service posts progress/completion/error
```

## Task Lifecycle State Machine

```
queued ──→ running ──→ generating ──→ completed
  │           │            │
  └───────────┴────────────┴──→ failed
  │
  └──→ cancelled
```

Valid transitions are enforced in `TaskService._transition()`.

## Key Design Decisions

- **ConnectionManager**: `asyncio.Queue` per-connection, `put_nowait()` for thread-safe broadcast. Each WS client gets its own queue; `TaskService._broadcast` pushes synchronously to all queues.
- **InferenceServiceManager**: WebSocket-based, one connection per `service_type`. Superseded connections are closed with code 4001. Task submit/cancel messages are routed by `service_type`.
- **WebSocket handlers** call `get_task_service()` / `get_connection_manager()` / `get_inference_manager()` directly (no `Depends`). Tests inject via `set_*()` functions.
- **Storage**: `data/{task_id[:2]}/{task_id}/video.mp4` + `preview/0000.jpg` — ready for S3 migration. Supports inline `result_data` for non-file results (e.g. transcription JSON).
- **Lazy loading**: LTX-2 video provider imports torch only on first `video_generation` task, keeping startup fast for other task types.
- **Provider registry**: `task_type` → provider instance mapping, extensible via `ProviderRegistry.register()`.
