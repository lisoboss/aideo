# Architecture

## aideo-serv (`packages/aideo-serv/src/aideo_serv/`)

- **api/** — REST + WebSocket endpoints
  - `router.py` — main `/api/v1` router, health check
  - `tasks.py` — task CRUD: `POST/GET/DELETE /tasks`
  - `ws.py` — WebSocket `/ws/tasks/{id}` (queue-based per-connection broadcast)
  - `results.py` — file download/preview: `GET /results/{id}/download`
- **services/** — business logic
  - `task_service.py` — task lifecycle state machine
  - `storage.py` — local file storage (`data/{prefix}/{task_id}/`)
  - `inference.py` — LTX-2 inference service HTTP client
  - `connection_manager.py` — per-connection `asyncio.Queue` for WS broadcast (thread-safe)
- **models/** — Pydantic models
  - `task.py` — `Task`, `TaskCreate`, `TaskStatus` (StrEnum, 6 states), `TaskListResponse`
  - `events.py` — `WSEvent` (WebSocket push protocol)
- **middleware/auth.py** — JWT skeleton (MVP returns `AnonymousUser`)
- `config.py` — pydantic-settings (`AIDEO_` env prefix)
- `app.py` — FastAPI factory (`create_app()`), CORS, lifespan
- `dependencies.py` — DI singletons (`get_task_service`, `get_connection_manager`)
- `main.py` — uvicorn entry point

## aideo-cli (`packages/aideo-cli/src/aideo_cli/`)

- `client.py` — `AideoClient`: async HTTP + WebSocket wrapper for aideo-serv API
- `commands.py` — 6 typer subcommands: `submit`, `list`, `status`, `cancel`, `download`, `ws`
- `main.py` — typer app definition
- `__init__.py` — exports `main` (console_script entry point)

## aideo-inference (`packages/aideo-inference/src/ltx2_service/`)

- `server.py` — FastAPI server: `POST /generate`, `GET /health`
- `model.py` — `LTX2Model` stub (simulated 10-step progress, placeholder bytes)
- `progress.py` — `send_progress()` HTTP callback to aideo-serv

## Task Lifecycle State Machine

```
queued ──→ running ──→ generating ──→ completed
  │           │            │
  └───────────┴────────────┴──→ failed
  │
  └──→ cancelled
```

## Key Design Decisions

- **ConnectionManager**: `asyncio.Queue` per-connection, `put_nowait()` for thread-safe broadcast. Each WS client gets its own queue; `TaskService._broadcast` pushes synchronously to all queues.
- **WebSocket handlers** call `get_task_service()` / `get_connection_manager()` directly (no `Depends`). Tests inject via `set_task_service()` / `set_connection_manager()`.
- **Storage**: `data/{task_id[:2]}/{task_id}/video.mp4` + `preview/0000.jpg` — ready for S3 migration.
- **Inference**: separate process, communicates via HTTP callbacks (not direct import).
