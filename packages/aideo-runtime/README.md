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
It uses environment configuration and a deterministic `demo` provider by default:

```bash
cp .env.example .env
set -a && source .env && set +a
uv run --package aideo-runtime aideo-runtime
```

Run contract tests with `make -C http-tests`; see [http-tests/README.md](http-tests/README.md).

## Development debug errors

Set `AIDEO_RUNTIME_DEBUG=true` only during local development to include a full
Python traceback in HTTP 500 JSON responses and in SSE `error.details.traceback`.
This option can disclose local paths and configuration details, so leave it
disabled for untrusted networks and production deployments.

## Local GPU providers

On Linux, add `ltx2` and/or `faster_whisper2` to `AIDEO_RUNTIME_PROVIDERS`.
Their heavyweight implementation and CUDA dependencies live in the workspace
package `aideo-models`; Runtime Providers remain thin capability and SSE
adapters. The model packages are Linux-only and loaded only when their Backend
handles its first request, so model discovery and the demo HTTP service remain
usable on development machines without CUDA.

All local providers use the same ComfyUI-style path roots:

| Environment variable | Purpose |
| --- | --- |
| `AIDEO_RUNTIME_MODELS_DIR` | Model checkpoints and downloaded Whisper models |
| `AIDEO_RUNTIME_INPUT_DIR` | Request input files, such as `audio_path` for ASR |
| `AIDEO_RUNTIME_OUTPUT_DIR` | Generated files; returned as `runtime://output/<path>` |

The Runtime accepts only relative paths below those roots. For example, place an
audio file at `data/input/recordings/sample.wav`, then submit
`{"input": {"audio_path": "recordings/sample.wav"}}` to the
`faster-whisper2` ASR model. Configure `WHISPER_MODEL=whisper/large-v3` to
load the local directory `models/whisper/large-v3`; the setting must be a
relative path below `AIDEO_RUNTIME_MODELS_DIR`. LTX returns an output URI such as
`runtime://output/videos/dog.mp4` for a relative request filename of
`videos/dog.mp4`.

For heavyweight local models, send `X-Memory-Preempt: true` to release other
loaded local Backends before the request starts. This is useful when switching
from Whisper to LTX2 on a constrained GPU.

The complete relative model-path configuration for LTX and the Whisper device
configuration are documented in [.env.example](.env.example). Do not configure
provider-specific model, input, or output roots.

Provider modules declare fixed `context_length` and `max_tokens` capabilities.
Requests set generation controls through `parameters`, including
`max_output_tokens`, `temperature`, `top_p`, `stop`, `seed`, and `truncation`.
The Runtime rejects `max_output_tokens` values above the model limit.
