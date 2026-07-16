#!/usr/bin/env bash

set -euo pipefail

# 查找当前 Python 环境中所有 NVIDIA CUDA 库目录。不能只匹配 cu*/lib：
# cuBLAS 与 cuDNN 分别位于 nvidia/cublas/lib、nvidia/cudnn/lib。
CUDA_LIBS="$(
uv run python - <<'PY'
import site
from pathlib import Path

dirs = set()
for root in map(Path, site.getsitepackages()):
    nvidia = root / "nvidia"
    if not nvidia.exists():
        continue
    for p in nvidia.glob("*/lib"):
        if p.is_dir():
            dirs.add(str(p))
print(":".join(sorted(dirs)))
PY
)"

if [[ -z "$CUDA_LIBS" ]]; then
    echo "No NVIDIA CUDA libraries found." >&2
    exit 1
fi

echo "CUDA library paths configured: $CUDA_LIBS" >&2
LD_LIBRARY_PATH="${CUDA_LIBS}:${LD_LIBRARY_PATH:-}" exec "$@"
