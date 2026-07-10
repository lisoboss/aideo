# aideo-serv (`packages/aideo-serv/src/aideo_serv/`)

## api/

- `router.py` — main `/api/v1` router, health check, `/internal/callback` (HTTP fallback)
- `tasks.py` — task CRUD: `POST/GET/DELETE /tasks`, `CallbackPayload` model
- `ws.py` — three WebSocket endpoints:
  - `/ws/tasks/{id}` — per-task progress stream for clients
  - `/ws/internal/inference` — inference service registration + message channel
  - `/ws/transcribe` — streaming speech-to-text (binary audio in, JSON events out)
- `results.py` — file download/preview: `GET /results/{id}/download`, `GET /results/{id}/preview/{frame}`

## services/

- `task_service.py` — task lifecycle state machine (6 states, validated transitions)
- `storage.py` — local file storage (`data/{prefix}/{task_id}/`)
- `connection_manager.py` — per-connection `asyncio.Queue` for WS broadcast (thread-safe)
- `inference.py` — `InferenceClient`: HTTP client for remote inference services
- `inference_manager.py` — `InferenceServiceManager`: WebSocket-based connection manager for local inference services

## models/

- `task.py` — `Task`, `TaskCreate`, `TaskStatus` (StrEnum, 6 states), `TaskListResponse`. Tasks carry `task_type` for routing (`video_generation`, `speech_to_text`, etc.)
- `events.py` — `WSEvent` (client-facing), `InferenceRegistration` (handshake), `InferenceMessage` (internal protocol with `ServiceType`, `TaskType`, `MessageType`)

## middleware/auth.py

JWT skeleton (MVP returns `AnonymousUser`).

## Config

- `config.py` — pydantic-settings (`AIDEO_` env prefix), includes `model_root`/`output_root`/`input_root`
- `app.py` — FastAPI factory (`create_app()`), CORS, lifespan
- `dependencies.py` — DI singletons
- `main.py` — uvicorn entry point
