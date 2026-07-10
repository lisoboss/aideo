#!/bin/bash
set -euo pipefail

# ---- aideo-runtime — aggregated local inference service -------------------
MODEL_ROOT="${AIDEO_MODEL_ROOT:-/mnt/g/AI/models}"
OUTPUT_ROOT="${AIDEO_OUTPUT_ROOT:-./data/output}"
INPUT_ROOT="${AIDEO_INPUT_ROOT:-./data/input}"
DEVICE="${AIDEO_DEVICE:-cuda}"

# ---- aideo-serv WebSocket connection --------------------------------------
AIDEO_HOST="${AIDEO_SERVER_HOST:-localhost}"
AIDEO_PORT="${AIDEO_SERVER_PORT:-8000}"

# ---- optional overrides ---------------------------------------------------
QUANTIZATION="${LTX2_QUANTIZATION:-fp8-cast}"
OFFLOAD_MODE="${LTX2_OFFLOAD_MODE:-none}"
WHISPER_MODEL="${WHISPER_MODEL:-large-v3}"
WHISPER_DEVICE="${WHISPER_DEVICE:-cuda}"
WHISPER_COMPUTE_TYPE="${WHISPER_COMPUTE_TYPE:-float16}"

# ---- preflight checks -----------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

die() { echo -e "${RED}ERROR:${NC} $*" >&2; exit 1; }

# ---- startup --------------------------------------------------------------
echo -e "${CYAN}aideo-runtime starting …${NC}"
echo "  model_root:  $MODEL_ROOT"
echo "  output_root: $OUTPUT_ROOT"
echo "  input_root:  $INPUT_ROOT"
echo "  device:      $DEVICE"
echo "  aideo-serv:  ws://$AIDEO_HOST:$AIDEO_PORT"
echo ""
echo "  capabilities:"
echo "    video_generation  (LTX-2, quantization=$QUANTIZATION, offload=$OFFLOAD_MODE)"
echo "    speech_to_text    (faster-whisper, model=$WHISPER_MODEL, device=$WHISPER_DEVICE)"
echo "    text_conversation  (stub)"
echo "    image_to_text      (stub)"
echo ""

exec env \
  AIDEO_MODEL_ROOT="$MODEL_ROOT" \
  AIDEO_OUTPUT_ROOT="$OUTPUT_ROOT" \
  AIDEO_INPUT_ROOT="$INPUT_ROOT" \
  AIDEO_DEVICE="$DEVICE" \
  AIDEO_SERVER_HOST="$AIDEO_HOST" \
  AIDEO_SERVER_PORT="$AIDEO_PORT" \
  LTX2_QUANTIZATION="$QUANTIZATION" \
  LTX2_OFFLOAD_MODE="$OFFLOAD_MODE" \
  WHISPER_MODEL="$WHISPER_MODEL" \
  WHISPER_DEVICE="$WHISPER_DEVICE" \
  WHISPER_COMPUTE_TYPE="$WHISPER_COMPUTE_TYPE" \
  uv run --package aideo-runtime aideo-runtime
