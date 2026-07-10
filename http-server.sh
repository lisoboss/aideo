#!/bin/bash
set -euo pipefail

# ---- server settings ----------------------------------------------------
HOST="${AIDEO_SERVER_HOST:-0.0.0.0}"
PORT="${AIDEO_SERVER_PORT:-8000}"
INFERENCE_URL="${AIDEO_INFERENCE_URL:-http://localhost:9090}"
STORAGE_DIR="${AIDEO_STORAGE_BASE_DIR:-./data}"
MODEL_ROOT="${AIDEO_MODEL_ROOT:-/mnt/g/AI/models}"
OUTPUT_ROOT="${AIDEO_OUTPUT_ROOT:-./data/output}"
INPUT_ROOT="${AIDEO_INPUT_ROOT:-./data/input}"

# ---- preflight checks ---------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

die() { echo -e "${RED}ERROR:${NC} $*" >&2; exit 1; }

# ---- startup ------------------------------------------------------------
echo -e "${CYAN}aideo-serv starting …${NC}"
echo "  host:        $HOST"
echo "  port:        $PORT"
echo "  inference:   $INFERENCE_URL"
echo "  storage:     $STORAGE_DIR"
echo "  model_root:  $MODEL_ROOT"
echo "  output_root: $OUTPUT_ROOT"
echo "  input_root:  $INPUT_ROOT"
echo ""

exec env \
  AIDEO_SERVER_HOST="$HOST" \
  AIDEO_SERVER_PORT="$PORT" \
  AIDEO_INFERENCE_URL="$INFERENCE_URL" \
  AIDEO_STORAGE_BASE_DIR="$STORAGE_DIR" \
  AIDEO_MODEL_ROOT="$MODEL_ROOT" \
  AIDEO_OUTPUT_ROOT="$OUTPUT_ROOT" \
  AIDEO_INPUT_ROOT="$INPUT_ROOT" \
  uv run --package aideo-serv aideo-serv
