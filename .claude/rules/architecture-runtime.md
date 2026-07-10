# aideo-runtime + CLI

## aideo-runtime (`packages/aideo-runtime/src/aideo_runtime/`)

Aggregated local inference. WS-connects to aideo-serv, registers capabilities, routes `task_submit` to providers.

- `server.py` — FastAPI app + `AideoWSClient`: connects to `/ws/internal/inference`, sends `register`, loops on messages
- `provider.py` — `BaseProvider` ABC: `load()`, `run(**kwargs) → AsyncGenerator`
- **video/** — text-to-video: `VideoProvider` ABC, `LTX2VideoProvider` (ltx-pipelines, lazy torch import)
- **speech/** — speech-to-text: `SpeechProvider` ABC, `FasterWhisperProvider` (auto-detects CUDA)
- **chat/** — text conversation (stub)
- **vision/** — image-to-text (stub)

Key: provider registry maps `task_type` → provider, extensible via `ProviderRegistry.register()`.

## aideo-cli (`packages/aideo-cli/src/aideo_cli/`)

Thin Typer CLI wrapping aideo-serv API.

- `client.py` — `AideoClient`: async HTTP + WebSocket. Supports `submit()`, `transcribe()`, `list_tasks()`, `get_task()`, `cancel_task()`, `download_result()`, `connect_ws()`, `stream_transcribe()`
- `commands.py` — typer subcommands: `submit`, `list`, `status`, `cancel`, `download`, `ws`, `transcribe`
- `main.py` — typer app definition
- `__init__.py` — exports `main` (console_script entry point)
