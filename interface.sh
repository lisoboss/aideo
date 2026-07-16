#!/bin/bash
set -euo pipefail

# ---- aideo-runtime — aggregated local inference service -------------------
RUNTIME_HOST="${AIDEO_RUNTIME_HOST:-0.0.0.0}"
RUNTIME_PORT="${AIDEO_RUNTIME_PORT:-9090}"
RUNTIME_PROVIDERS="${AIDEO_RUNTIME_PROVIDERS:-demo,faster_whisper2,ltx2}"
MODELS_DIR="${AIDEO_RUNTIME_MODELS_DIR:-./models}"
INPUT_DIR="${AIDEO_RUNTIME_INPUT_DIR:-./data/input}"
OUTPUT_DIR="${AIDEO_RUNTIME_OUTPUT_DIR:-./data/output}"

# ---- provider: faster-whisper2 --------------------------------------------
WHISPER_MODEL="${WHISPER_MODEL:-large-v3}"
WHISPER_DEVICE="${WHISPER_DEVICE:-cuda}"
WHISPER_COMPUTE_TYPE="${WHISPER_COMPUTE_TYPE:-float16}"

# ---- provider: ltx2 -------------------------------------------------------
LTX2_DISTILLED_CHECKPOINT="${LTX2_DISTILLED_CHECKPOINT:-LTX-2.3/ltx-2.3-22b-distilled-1.1.safetensors}"
LTX2_GEMMA_ROOT="${LTX2_GEMMA_ROOT:-gemma-3-12b-it-qat-q4_0-unquantized}"
LTX2_SPATIAL_UPSAMPLER="${LTX2_SPATIAL_UPSAMPLER:-LTX-2.3/ltx-2.3-spatial-upscaler-x1.5-1.0.safetensors}"
LTX2_DEVICE="${LTX2_DEVICE:-cuda}"
LTX2_QUANTIZATION="${LTX2_QUANTIZATION:-fp8-cast}"
LTX2_OFFLOAD_MODE="${LTX2_OFFLOAD_MODE:-none}"

# ---- preflight checks -----------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

die() { echo -e "${RED}ERROR:${NC} $*" >&2; exit 1; }

# ---- startup --------------------------------------------------------------
echo -e "${CYAN}aideo-runtime starting …${NC}"
echo "  host:        $RUNTIME_HOST:$RUNTIME_PORT"
echo "  providers:   $RUNTIME_PROVIDERS"
echo "  models_dir:  $MODELS_DIR"
echo "  input_dir:   $INPUT_DIR"
echo "  output_dir:  $OUTPUT_DIR"
echo ""
echo "  whisper:"
echo "    model=$WHISPER_MODEL  device=$WHISPER_DEVICE  compute=$WHISPER_COMPUTE_TYPE"
echo "  ltx2:"
echo "    checkpoint=$LTX2_DISTILLED_CHECKPOINT"
echo "    gemma_root=$LTX2_GEMMA_ROOT"
echo "    upsampler=$LTX2_SPATIAL_UPSAMPLER"
echo "    device=$LTX2_DEVICE  quantization=$LTX2_QUANTIZATION  offload=$LTX2_OFFLOAD_MODE"
echo ""

exec env \
  AIDEO_RUNTIME_HOST="$RUNTIME_HOST" \
  AIDEO_RUNTIME_PORT="$RUNTIME_PORT" \
  AIDEO_RUNTIME_PROVIDERS="$RUNTIME_PROVIDERS" \
  AIDEO_RUNTIME_MODELS_DIR="$MODELS_DIR" \
  AIDEO_RUNTIME_INPUT_DIR="$INPUT_DIR" \
  AIDEO_RUNTIME_OUTPUT_DIR="$OUTPUT_DIR" \
  WHISPER_MODEL="$WHISPER_MODEL" \
  WHISPER_DEVICE="$WHISPER_DEVICE" \
  WHISPER_COMPUTE_TYPE="$WHISPER_COMPUTE_TYPE" \
  LTX2_DISTILLED_CHECKPOINT="$LTX2_DISTILLED_CHECKPOINT" \
  LTX2_GEMMA_ROOT="$LTX2_GEMMA_ROOT" \
  LTX2_SPATIAL_UPSAMPLER="$LTX2_SPATIAL_UPSAMPLER" \
  LTX2_DEVICE="$LTX2_DEVICE" \
  LTX2_QUANTIZATION="$LTX2_QUANTIZATION" \
  LTX2_OFFLOAD_MODE="$LTX2_OFFLOAD_MODE" \
  uv run --package aideo-runtime aideo-runtime
