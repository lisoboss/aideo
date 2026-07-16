#!/usr/bin/env bash

set -euo pipefail

# ---- ai provider settings -------------------------------------------------
AIDEO_AI_PROVIDER="${AIDEO_AI_PROVIDER:-deepseek}"
AIDEO_AI_BASE_URL="${AIDEO_AI_BASE_URL:-https://api.deepseek.com}"
AIDEO_AI_API_KEY="${AIDEO_AI_API_KEY:-}"
AIDEO_AI_MODEL="${AIDEO_AI_MODEL:-deepseek-v4-flash}"
AIDEO_AI_PROVIDERS="${AIDEO_AI_PROVIDERS:-}"
AIDEO_MAX_ASSET_SIZE="${AIDEO_MAX_ASSET_SIZE:-52428800}"
AIDEO_ASSET_BASE_DIR="${AIDEO_ASSET_BASE_DIR:-./data/assets}"

# ---- server settings ------------------------------------------------------
HOST="${AIDEO_SERVER_HOST:-0.0.0.0}"
PORT="${AIDEO_SERVER_PORT:-8000}"
INFERENCE_URL="${AIDEO_INFERENCE_URL:-http://localhost:9090}"
STORAGE_DIR="${AIDEO_STORAGE_BASE_DIR:-./data}"
MODEL_ROOT="${AIDEO_MODEL_ROOT:-/mnt/g/AI/models}"
OUTPUT_ROOT="${AIDEO_OUTPUT_ROOT:-./data/output}"
INPUT_ROOT="${AIDEO_INPUT_ROOT:-./data/input}"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

die() {
  echo -e "${RED}ERROR:${NC} $*" >&2
  exit 1
}

info() {
  echo -e "${CYAN}$*${NC}"
}

success() {
  echo -e "${GREEN}$*${NC}"
}

command -v uv >/dev/null 2>&1 || die "uv is required; install it from https://docs.astral.sh/uv/"
command -v curl >/dev/null 2>&1 || die "curl is required for Runtime health checks"
mkdir -p "$STORAGE_DIR" "$AIDEO_ASSET_BASE_DIR" "$INPUT_ROOT" "$OUTPUT_ROOT"

RUNTIME_HEALTH_URL="${INFERENCE_URL%/}/health"
if ! runtime_health="$(curl -fsS --connect-timeout 2 --max-time 5 "$RUNTIME_HEALTH_URL")"; then
  die "Runtime health check failed at $RUNTIME_HEALTH_URL; start aideo-runtime or set AIDEO_INFERENCE_URL"
fi

# ---- startup --------------------------------------------------------------
info "aideo-serv starting …"
echo "  host:          $HOST:$PORT"
echo "  inference:     $INFERENCE_URL"
echo "  runtime:       $runtime_health"
echo "  storage:       $STORAGE_DIR"
echo "  model_root:    $MODEL_ROOT"
echo "  output_root:   $OUTPUT_ROOT"
echo "  input_root:    $INPUT_ROOT"
echo "  ai_provider:   $AIDEO_AI_PROVIDER"
echo "  ai_base_url:   $AIDEO_AI_BASE_URL"
echo "  ai_model:      $AIDEO_AI_MODEL"
echo "  ai_api_key:    $( [ -n "$AIDEO_AI_API_KEY" ] && echo '***set***' || echo '(empty)' )"
echo "  asset_dir:     $AIDEO_ASSET_BASE_DIR"
success "Runtime preflight passed."

exec env \
  AIDEO_SERVER_HOST="$HOST" \
  AIDEO_SERVER_PORT="$PORT" \
  AIDEO_INFERENCE_URL="$INFERENCE_URL" \
  AIDEO_STORAGE_BASE_DIR="$STORAGE_DIR" \
  AIDEO_MODEL_ROOT="$MODEL_ROOT" \
  AIDEO_OUTPUT_ROOT="$OUTPUT_ROOT" \
  AIDEO_INPUT_ROOT="$INPUT_ROOT" \
  AIDEO_AI_PROVIDER="$AIDEO_AI_PROVIDER" \
  AIDEO_AI_BASE_URL="$AIDEO_AI_BASE_URL" \
  AIDEO_AI_API_KEY="$AIDEO_AI_API_KEY" \
  AIDEO_AI_MODEL="$AIDEO_AI_MODEL" \
  AIDEO_AI_PROVIDERS="$AIDEO_AI_PROVIDERS" \
  AIDEO_MAX_ASSET_SIZE="$AIDEO_MAX_ASSET_SIZE" \
  AIDEO_ASSET_BASE_DIR="$AIDEO_ASSET_BASE_DIR" \
  uv run --package aideo-serv aideo-serv
