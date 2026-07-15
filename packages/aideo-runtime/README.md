# aideo-runtime

`aideo-runtime` provides a provider-neutral inference boundary for Aideo agents.
Agents invoke capabilities such as chat, image, video, ASR, TTS, embedding,
vision, and rerank through registered models. Protocol adapters isolate provider
wire formats from HTTP backends and transports.

The package includes provider adapters for OpenAI Responses, local ComfyUI
workflows, and LTX asynchronous video jobs. Each adapter owns its provider
request, response, and progress models while the Runtime core remains neutral.

## Provider Protocols

- **OpenAI**: Responses API request/response and SSE text events for chat and vision.
- **ComfyUI**: local API-format workflow submission, history outputs, and WebSocket JSON progress.
- **LTX**: v2 text-to-video submission and asynchronous job-status polling.

Provider authentication, file uploads, ComfyUI binary preview frames, and LTX
image/audio video modes remain outside the current adapter scope.

## HTTP Runtime

The HTTP Runtime exposes health, model discovery, JSON invocation, and SSE streaming.
Its MVP uses environment configuration and a deterministic `demo` provider:

```bash
cp .env.example .env
set -a && source .env && set +a
uv run --package aideo-runtime aideo-runtime
```

Run contract tests with `make -C http-tests`; see [http-tests/README.md](http-tests/README.md).

Provider modules declare fixed `context_length` and `max_tokens` capabilities.
Requests set generation controls through `parameters`, including
`max_output_tokens`, `temperature`, `top_p`, `stop`, `seed`, and `truncation`.
The Runtime rejects `max_output_tokens` values above the model limit.
