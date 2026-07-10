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

## Change Logging
每次有意义的代码变更（新功能、重构、协议变更）必须记录到以下两个文件：

### 1. `docs/changes.md` — 变更索引

每条记录一行，格式：
```markdown
- [changed-YYYY-MM-DD-title.md](changes/changed-YYYY-MM-DD-title.md) — one-line summary
```

内容：日期、标题、涉及文件、关键指标。

### 2. `docs/changes/changed-{年}-{月}-{日}-{title}.md` — 变更详情

命名规则：`changed-{YYYY}-{MM}-{DD}-{kebab-case-title}.md`

内容结构：
```markdown
# YYYY-MM-DD — Title

## Section 1
### 新增/删除/修改文件
| 文件 | 操作 | 说明 |
### 变更要点

## Section 2
...

## 涉及文件总览
```
aideo/
├── packages/
│   ├── aideo-serv/ ...
│   └── aideo-ipad/ ...
```

**规则**：
- 同一天的变更合并到一个文件
- 涉及文件总览必须用 tree 格式列出所有变更文件的路径
- 同一文件跨多个 section 时只在 tree 中列出一次
- 每条记录独立成行，不跨天合并
