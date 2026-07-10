# Code Conventions

## Top-level imports only
All `import` statements must be at the top of the file. Never use inline imports inside functions or methods. If a circular import arises, restructure the modules — extract shared dependencies into a separate module.

## No `__init__.py` in test directories
`tests/` is NOT a Python module. pytest discovers tests via the filesystem. Never create `tests/__init__.py` in any package. Applies to all `packages/*/tests/` directories.

## Dependency management: `uv add` / `uv remove` only
Never edit `pyproject.toml` directly. Always use `uv add --package <pkg> <dep>` or `uv remove --package <pkg> <dep>`.

## Use `uv run` for all Python commands
Always go through `uv run` or `uv run --package <pkg>`. Never use `.venv/bin/python` or `.venv/bin/pytest` directly.

## Static versions
All packages use static `version = "0.1.0"` (not dynamic/vcs). The shared `uv.lock` at the workspace root is the single source of truth for pinned dependency versions.

## pyproject.toml consistency
All sub-project `pyproject.toml` files must have the same structure: `[project]` with name/version/description/readme/authors/requires-python/dependencies/scripts, plus `[build-system]` with `uv_build`.
