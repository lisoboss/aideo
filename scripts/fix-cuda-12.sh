#!/usr/bin/env bash
set -euo pipefail

# 查找当前 Python 环境中的 NVIDIA CUDA 库目录
CUDA_LIB="$(
uv run python - <<'PY'
import site
from pathlib import Path
def find():
    for root in map(Path, site.getsitepackages()):
        nvidia = root / "nvidia"
        if not nvidia.exists():
            continue
        if any([p.is_file() for p in nvidia.glob("**/libcublas.so.12")]):
            return "-" # CUDA 12
        for p in nvidia.glob("**/libcublas.so.1*"):
            if p.is_file():
                return str(p)
    return ""

print(find())
PY
)"

if [[ -z "$CUDA_LIB" ]]; then
    echo "No NVIDIA CUDA libraries libcublas.so.1* found." >&2
    exit 1
fi

if [[ "$CUDA_LIB" == "-" ]]; then
    echo "CUDA 12 detected, no fix needed."
    exit 0
fi

ln -sf "$CUDA_LIB" "$(dirname "$CUDA_LIB")/libcublas.so.12"

echo "Symlink created: $(dirname "$CUDA_LIB")/libcublas.so.12 -> $CUDA_LIB"