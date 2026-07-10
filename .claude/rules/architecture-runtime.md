# aideo-runtime + CLI

## aideo-runtime (`packages/aideo-runtime/src/aideo_runtime/`)

Aggregated local inference. HTTP + SSE service. aideo-serv POSTs to `/api/v1/{category}/{name}`; the runtime streams `ProgressStatus` back via SSE. Auto load/unload with idle sweeper.

- `server.py` — FastAPI app + `ProviderManager`: category-based routing (`POST /api/v1/{category}/{name}` → SSE), auto load on first request, unload after idle timeout, `X-Memory-Preempt` header for exclusive GPU
- `provider.py` — `BaseProvider` ABC: `load()`, `unload()`, `run(**kwargs) → AsyncGenerator[ProgressStatus]`, `cancel()`/`is_cancelled`
- **video/** — text-to-video: `VideoProvider` ABC, `LTX2VideoProvider` (ltx-pipelines, lazy torch import)
- **speech/** — speech-to-text: `SpeechProvider` ABC, `FasterWhisperProvider` (auto-detects CUDA)
- **chat/** — text conversation (stub)
- **vision/** — image-to-text (stub)
- **image/** — image edit / upscale: `ImageProvider` ABC, `StubImageProvider` (`stub@image.provider`, real model TBD)

Key: each category exposes a `PROVIDERS` dict; providers self-register at import via `register_provider()`. aideo-serv's `inference_client.TASK_TO_PROVIDER` maps `task_type` → `(category, name)` (`image_edit`/`image_upscale` → `("image", "stub")`).

## aideo-cli (`packages/aideo-cli/src/aideo_cli/`)

Thin Typer CLI wrapping aideo-serv API.

- `client.py` — `AideoClient`: async HTTP + WebSocket. Supports `submit()`, `transcribe()`, `list_tasks()`, `get_task()`, `cancel_task()`, `download_result()`, `connect_ws()`, `stream_transcribe()`
- `commands.py` — typer subcommands: `submit`, `list`, `status`, `cancel`, `download`, `ws`, `transcribe`
- `main.py` — typer app definition
- `__init__.py` — exports `main` (console_script entry point)
