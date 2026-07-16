# CLAUDE.md

Aideo — AI Video Generator Studio. uv workspace monorepo.

## Packages

- **packages/aideo-serv** — FastAPI backend (Python 3.12+)
- **packages/aideo-cli** — Typer CLI client
- **packages/aideo-runtime** — aggregated local inference runtime (T2V, STT, LLM, vision)
- **packages/aideo-ipad** — iPad client (excluded from workspace, not Python)

## Quick Commands

```bash
uv sync --all-packages                     # sync workspace
uv run pytest                              # all tests (108)
uv run --package aideo-serv pytest -v      # serv tests only
uv run --package aideo-serv aideo-serv     # start API server
uv run --package aideo-runtime aideo-runtime  # start inference runtime
uv run --package aideo-cli aideo submit "prompt"  # CLI
uv run --package aideo-cli aideo transcribe audio.wav  # speech-to-text
uv add --package aideo-serv <pkg>          # add dep
uv add --dev <pkg>                         # add shared dev dep
```

## Rules

`CLAUDE.md` is kept simple and `.claude/rules/` is split by modules.

See `.claude/rules/` for conventions and per-module architecture:

| File | Module |
|------|--------|
| [architecture.md](.claude/rules/architecture.md) | Overview + shared concepts |
| [architecture-serv.md](.claude/rules/architecture-serv.md) | aideo-serv backend |
| [architecture-runtime.md](.claude/rules/architecture-runtime.md) | aideo-runtime + CLI |
| [architecture-ipad.md](.claude/rules/architecture-ipad.md) | aideo-ipad client |
| [conventions.md](.claude/rules/conventions.md) | Code conventions |
