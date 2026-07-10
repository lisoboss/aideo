#!/usr/bin/env bash

# 查找当前 Python 环境中的 NVIDIA CUDA 库目录
CUDA_LIBS="$(
uv run python - <<'PY'
import site
from pathlib import Path
dirs = set()
for root in map(Path, site.getsitepackages()):
    nvidia = root / "nvidia"
    if not nvidia.exists():
        continue
    for p in nvidia.glob("cu*/lib"):
        if p.is_dir():
            dirs.add(str(p))
print(":".join(sorted(dirs)))
PY
)"

if [[ -z "$CUDA_LIBS" ]]; then
    echo "No NVIDIA CUDA libraries found." >&2
    exit 1
fi

LD_LIBRARY_PATH="${CUDA_LIBS}:${LD_LIBRARY_PATH:-}" exec "$@"