#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

FAKE_BIN="$TEMP_DIR/bin"
CAPTURE="$TEMP_DIR/uv.env"
CUDA_LIB_DIR="$TEMP_DIR/cuda/cublas/lib"
mkdir -p "$FAKE_BIN"
mkdir -p "$CUDA_LIB_DIR"

cat > "$FAKE_BIN/uv" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "run" && "${2:-}" == "python" ]]; then
  printf '%s\n' "$CUDA_LIB_DIR"
  exit 0
fi
printf 'debug=%s\nproviders=%s\nld_library_path=%s\n' \
  "${AIDEO_RUNTIME_DEBUG:-}" "${AIDEO_RUNTIME_PROVIDERS:-}" \
  "${LD_LIBRARY_PATH:-}" > "$CAPTURE"
EOF
chmod +x "$FAKE_BIN/uv"

MODELS_DIR="$TEMP_DIR/models"
INPUT_DIR="$TEMP_DIR/input"
OUTPUT_DIR="$TEMP_DIR/output"

PATH="$FAKE_BIN:$PATH" \
CAPTURE="$CAPTURE" \
CUDA_LIB_DIR="$CUDA_LIB_DIR" \
AIDEO_RUNTIME_PROVIDERS="demo" \
AIDEO_RUNTIME_DEBUG="true" \
AIDEO_RUNTIME_MODELS_DIR="$MODELS_DIR" \
AIDEO_RUNTIME_INPUT_DIR="$INPUT_DIR" \
AIDEO_RUNTIME_OUTPUT_DIR="$OUTPUT_DIR" \
bash "$ROOT_DIR/interface.sh" > "$TEMP_DIR/demo.log"

test -d "$MODELS_DIR"
test -d "$INPUT_DIR"
test -d "$OUTPUT_DIR"
grep -qx 'debug=true' "$CAPTURE"
grep -qx 'providers=demo' "$CAPTURE"
grep -qx "ld_library_path=$CUDA_LIB_DIR:" "$CAPTURE"

if PATH="$FAKE_BIN:$PATH" \
  AIDEO_RUNTIME_PROVIDERS="ltx2" \
  AIDEO_RUNTIME_MODELS_DIR="$MODELS_DIR" \
  LTX2_DISTILLED_CHECKPOINT="missing.safetensors" \
  LTX2_GEMMA_ROOT="missing-gemma" \
  LTX2_SPATIAL_UPSAMPLER="missing-upscaler.safetensors" \
  bash "$ROOT_DIR/interface.sh" > "$TEMP_DIR/ltx.log" 2>&1; then
  echo "expected LTX2 preflight to fail" >&2
  exit 1
fi

grep -q 'LTX2_DISTILLED_CHECKPOINT' "$TEMP_DIR/ltx.log"
