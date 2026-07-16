#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

FAKE_BIN="$TEMP_DIR/bin"
CAPTURE="$TEMP_DIR/uv.env"
mkdir -p "$FAKE_BIN"

cat > "$FAKE_BIN/uv" <<'EOF'
#!/usr/bin/env bash
printf 'debug=%s\nproviders=%s\n' \
  "${AIDEO_RUNTIME_DEBUG:-}" "${AIDEO_RUNTIME_PROVIDERS:-}" > "$CAPTURE"
EOF
chmod +x "$FAKE_BIN/uv"

MODELS_DIR="$TEMP_DIR/models"
INPUT_DIR="$TEMP_DIR/input"
OUTPUT_DIR="$TEMP_DIR/output"

PATH="$FAKE_BIN:$PATH" \
CAPTURE="$CAPTURE" \
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
