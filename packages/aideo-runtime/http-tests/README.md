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
ENV=staging make discovery   # reads .staging.env
```
