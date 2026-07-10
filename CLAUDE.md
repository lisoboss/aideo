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

See `.claude/rules/` for detailed conventions and architecture.
