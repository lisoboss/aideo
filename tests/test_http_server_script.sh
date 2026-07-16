#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

FAKE_BIN="$TEMP_DIR/bin"
CURL_CAPTURE="$TEMP_DIR/curl.args"
UV_CAPTURE="$TEMP_DIR/uv.env"
mkdir -p "$FAKE_BIN"

cat > "$FAKE_BIN/curl" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" > "$CURL_CAPTURE"
if [[ "${CURL_FAIL:-false}" == "true" ]]; then
  exit 22
fi
printf '{"status":"ok"}'
EOF
chmod +x "$FAKE_BIN/curl"

cat > "$FAKE_BIN/uv" <<'EOF'
#!/usr/bin/env bash
printf 'inference=%s\nstorage=%s\n' \
  "${AIDEO_INFERENCE_URL:-}" "${AIDEO_STORAGE_BASE_DIR:-}" > "$UV_CAPTURE"
EOF
chmod +x "$FAKE_BIN/uv"

STORAGE_DIR="$TEMP_DIR/storage"
ASSET_DIR="$TEMP_DIR/assets"
INPUT_DIR="$TEMP_DIR/input"
OUTPUT_DIR="$TEMP_DIR/output"

PATH="$FAKE_BIN:$PATH" \
CURL_CAPTURE="$CURL_CAPTURE" \
UV_CAPTURE="$UV_CAPTURE" \
AIDEO_INFERENCE_URL="http://runtime.example:9090" \
AIDEO_STORAGE_BASE_DIR="$STORAGE_DIR" \
AIDEO_ASSET_BASE_DIR="$ASSET_DIR" \
AIDEO_INPUT_ROOT="$INPUT_DIR" \
AIDEO_OUTPUT_ROOT="$OUTPUT_DIR" \
AIDEO_AI_API_KEY="must-not-leak" \
bash "$ROOT_DIR/http-server.sh" > "$TEMP_DIR/success.log"

test -d "$STORAGE_DIR"
test -d "$ASSET_DIR"
test -d "$INPUT_DIR"
test -d "$OUTPUT_DIR"
grep -q 'http://runtime.example:9090/health' "$CURL_CAPTURE"
grep -qx 'inference=http://runtime.example:9090' "$UV_CAPTURE"
if grep -q 'must-not-leak' "$TEMP_DIR/success.log"; then
  echo "API key leaked into startup logs" >&2
  exit 1
fi

if PATH="$FAKE_BIN:$PATH" \
  CURL_FAIL="true" \
  CURL_CAPTURE="$CURL_CAPTURE" \
  UV_CAPTURE="$UV_CAPTURE" \
  AIDEO_INFERENCE_URL="http://runtime.example:9090" \
  AIDEO_STORAGE_BASE_DIR="$TEMP_DIR/failure-storage" \
  AIDEO_ASSET_BASE_DIR="$TEMP_DIR/failure-assets" \
  AIDEO_INPUT_ROOT="$TEMP_DIR/failure-input" \
  AIDEO_OUTPUT_ROOT="$TEMP_DIR/failure-output" \
  bash "$ROOT_DIR/http-server.sh" > "$TEMP_DIR/failure.log" 2>&1; then
  echo "expected Runtime health preflight to fail" >&2
  exit 1
fi

grep -q 'Runtime health check failed' "$TEMP_DIR/failure.log"
