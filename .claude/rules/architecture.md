# Architecture Overview

Aideo — AI Video Generator Studio. uv workspace + iPad client.

## Packages

| Package | Lang | Purpose |
|---------|------|---------|
| aideo-serv | Python | FastAPI backend: REST + WebSocket |
| aideo-runtime | Python | Local inference: LTX-2 T2V, Whisper STT, LLM, vision |
| aideo-cli | Python | Typer CLI client for aideo-serv |
| aideo-ipad | Swift | iPad client (excluded from uv workspace) |

## Task Lifecycle

```
queued ──→ running ──→ generating ──→ completed
  │           │            │
  └───────────┴────────────┴──→ failed
  │
  └──→ cancelled
```

Valid transitions enforced in `TaskService._transition()`.

## Inference Protocol

**Primary: WebSocket** (aideo-runtime → aideo-serv)
```
1. runtime → /ws/internal/inference: {"type": "register", "capabilities": [...]}
2. serv → runtime: {"type": "registered"}
3. serv → runtime: {"type": "task_submit", "task_id": "...", "data": {...}}
4. runtime → serv: {"type": "progress"|"completed"|"error", "data": {...}}
```

**Fallback: HTTP callback** (remote/cloud)
```
POST /api/v1/internal/callback  ←  inference service posts progress
```

## Shared Design Decisions

- **ConnectionManager**: `asyncio.Queue` per-connection, `put_nowait()` for thread-safe broadcast
- **WebSocket handlers**: call service singletons directly (no `Depends`); tests inject via `set_*()`
- **Storage**: `data/{task_id[:2]}/{task_id}/video.mp4` + `preview/0000.jpg`, S3-ready. Supports inline `result_data`
- **Lazy loading**: LTX-2 imports torch only on first `video_generation` task

## Per-Module Architecture

- [aideo-serv](architecture-serv.md)
- [aideo-runtime + CLI](architecture-runtime.md)
- [aideo-ipad](architecture-ipad.md)
