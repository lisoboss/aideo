# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aideo — AI Video Generator Studio. Monorepo with two packages:

- **aideo-serv** — Python backend/service (Python 3.12+, `aideo_serv` package)
- **aideo-cli** — CLI client (not yet implemented)

## Development Environment

The Python project (`aideo-serv/`) uses `uv` for dependency management. A `.venv` is already created.

```bash
# Activate the virtual environment
cd aideo-serv

# Install dependencies (including dev)
uv sync

# Run the CLI entry point
uv run aideo-serv

# Add a dependency
uv add <package>
# Add a dev dependency
uv add --dev <package>
```

## Build, Test, Lint

All commands run from `aideo-serv/`.

```bash
# Run all pre-commit checks
pre-commit run --all-files
```

## Architecture

### aideo-serv (`aideo-serv/src/aideo_serv/`)

- **`__init__.py`** — Contains the `main()` entry point, registered as the `aideo-serv` console script. Currently a placeholder.
- Tests live in `aideo-serv/tests/` (directory not yet created).
- Version is derived from git tags via `hatch-vcs`.

### Toolchain

- **Build**: hatchling + hatch-vcs (PEP 621 pyproject.toml)
- **Formatter**: black (line length 88)
- **Import sorter**: isort (black profile)
- **Linter**: flake8 + flake8-docstrings (E203 ignored for black compatibility)
- **Type checker**: mypy
- **Security**: bandit (B101/assert skipped)
- **Tests**: pytest with asyncio_mode=auto, pytest-asyncio

### Pre-commit Hooks

Configured in `.pre-commit-config.yaml`: trailing-whitespace, end-of-file-fixer, check-yaml/toml/json, check-merge-conflict, check-added-large-files, debug-statements, check-docstring-first, black, isort, flake8, mypy, bandit, and pytest (runs full suite on commit).
