# CLAUDE.md

Aideo — AI Video Generator Studio. uv workspace monorepo.

## Packages

- **packages/aideo-serv** — FastAPI backend (Python 3.12+)
- **packages/aideo-cli** — Typer CLI client
- **packages/aideo-inference** — LTX-2 inference service (`ltx2-service`)
- **packages/aideo-ipad** — iPad client (excluded from workspace, not Python)

## Quick Commands

```bash
uv sync --all-packages                   # sync workspace
uv run pytest                            # all tests (103)
uv run --package aideo-serv pytest -v    # serv tests only
uv run --package aideo-serv aideo-serv   # start API server
uv run --package ltx2-service ltx2-server # start inference
uv run --package aideo-cli aideo submit "prompt"  # CLI
uv add --package aideo-serv <pkg>        # add dep
uv add --dev <pkg>                       # add shared dev dep
```

## Rules

See `.claude/rules/` for detailed conventions and architecture.
