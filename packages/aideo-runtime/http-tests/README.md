# Runtime HTTP Tests

These Hurl tests exercise the Runtime HTTP/SSE contract against a running local service.

## Start the demo Runtime

```bash
export AIDEO_RUNTIME_PROVIDERS=demo
uv run --package aideo-runtime aideo-runtime
```

Copy `.local.env.example` to `.local.env` if the default URL needs changing.

## Run tests

```bash
make                         # all request domains
make health                  # health only
make inference@verbose       # verbose inference requests
make asr                     # local Faster-Whisper2 JSON and SSE requests
ENV=staging make discovery   # reads .staging.env
```

## ASR prerequisites

Set `WHISPER_AUDIO_PATH` in the selected `.<environment>.env` file to a path
relative to `AIDEO_RUNTIME_INPUT_DIR`. The default example expects
`audio/1.mp3` and asserts its known Chinese transcription metadata.
