#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CUDA_ENV_RUN="$SCRIPT_DIR/scripts/cuda-env-run.sh"

# ---- aideo-runtime — aggregated local inference service -------------------
RUNTIME_HOST="${AIDEO_RUNTIME_HOST:-0.0.0.0}"
RUNTIME_PORT="${AIDEO_RUNTIME_PORT:-9090}"
RUNTIME_PROVIDERS="${AIDEO_RUNTIME_PROVIDERS:-demo,faster_whisper2,ltx2}"
RUNTIME_DEBUG="${AIDEO_RUNTIME_DEBUG:-true}"
MODELS_DIR="${AIDEO_RUNTIME_MODELS_DIR:-${AIDEO_MODEL_ROOT:-./models}}"
INPUT_DIR="${AIDEO_RUNTIME_INPUT_DIR:-./data/input}"
OUTPUT_DIR="${AIDEO_RUNTIME_OUTPUT_DIR:-./data/output}"

# ---- provider: faster-whisper2 --------------------------------------------
WHISPER_MODEL="${WHISPER_MODEL:-faster-whisper-large-v3}"
WHISPER_DEVICE="${WHISPER_DEVICE:-cuda}"
WHISPER_COMPUTE_TYPE="${WHISPER_COMPUTE_TYPE:-float16}"

# ---- provider: ltx2 -------------------------------------------------------
LTX2_DISTILLED_CHECKPOINT="${LTX2_DISTILLED_CHECKPOINT:-LTX-2.3/ltx-2.3-22b-distilled-1.1.safetensors}"
LTX2_GEMMA_ROOT="${LTX2_GEMMA_ROOT:-gemma-3-12b-it-qat-q4_0-unquantized}"
LTX2_SPATIAL_UPSAMPLER="${LTX2_SPATIAL_UPSAMPLER:-LTX-2.3/ltx-2.3-spatial-upscaler-x2-1.1.safetensors}"
LTX2_DEVICE="${LTX2_DEVICE:-cuda}"
LTX2_QUANTIZATION="${LTX2_QUANTIZATION:-fp8-cast}"
LTX2_OFFLOAD_MODE="${LTX2_OFFLOAD_MODE:-none}"

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

provider_enabled() {
  local provider="$1"
  local normalized=",${RUNTIME_PROVIDERS//[[:space:]]/},"
  [[ "$normalized" == *",$provider,"* ]]
}

require_model_path() {
  local variable_name="$1"
  local relative_path="$2"
  [[ "$relative_path" != /* ]] || die "$variable_name must be relative to AIDEO_RUNTIME_MODELS_DIR"
  [[ -e "$MODELS_DIR/$relative_path" ]] || die "$variable_name not found: $MODELS_DIR/$relative_path"
}

command -v uv >/dev/null 2>&1 || die "uv is required; install it from https://docs.astral.sh/uv/"
[[ -f "$CUDA_ENV_RUN" ]] || die "CUDA environment launcher not found: $CUDA_ENV_RUN"
mkdir -p "$MODELS_DIR" "$INPUT_DIR" "$OUTPUT_DIR"

if provider_enabled "ltx2"; then
  require_model_path "LTX2_DISTILLED_CHECKPOINT" "$LTX2_DISTILLED_CHECKPOINT"
  require_model_path "LTX2_GEMMA_ROOT" "$LTX2_GEMMA_ROOT"
  require_model_path "LTX2_SPATIAL_UPSAMPLER" "$LTX2_SPATIAL_UPSAMPLER"
fi
if provider_enabled "faster_whisper2"; then
  require_model_path "WHISPER_MODEL" "$WHISPER_MODEL"
  [[ -d "$MODELS_DIR/$WHISPER_MODEL" ]] || die "WHISPER_MODEL must be a local model directory"
fi

# ---- startup --------------------------------------------------------------
info "aideo-runtime starting …"
echo "  host:        $RUNTIME_HOST:$RUNTIME_PORT"
echo "  providers:   $RUNTIME_PROVIDERS"
echo "  debug:       $RUNTIME_DEBUG"
echo "  models_dir:  $MODELS_DIR"
echo "  input_dir:   $INPUT_DIR"
echo "  output_dir:  $OUTPUT_DIR"
echo ""

if provider_enabled "faster_whisper2"; then
  echo "  whisper:"
  echo "    model=$WHISPER_MODEL  device=$WHISPER_DEVICE  compute=$WHISPER_COMPUTE_TYPE"
fi
if provider_enabled "ltx2"; then
  echo "  ltx2:"
  echo "    checkpoint=$LTX2_DISTILLED_CHECKPOINT"
  echo "    gemma_root=$LTX2_GEMMA_ROOT"
  echo "    upsampler=$LTX2_SPATIAL_UPSAMPLER"
  echo "    device=$LTX2_DEVICE  quantization=$LTX2_QUANTIZATION  offload=$LTX2_OFFLOAD_MODE"
fi
success "Runtime preflight passed."

exec env \
  AIDEO_RUNTIME_HOST="$RUNTIME_HOST" \
  AIDEO_RUNTIME_PORT="$RUNTIME_PORT" \
  AIDEO_RUNTIME_PROVIDERS="$RUNTIME_PROVIDERS" \
  AIDEO_RUNTIME_DEBUG="$RUNTIME_DEBUG" \
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
  bash "$CUDA_ENV_RUN" uv run --package aideo-runtime aideo-runtime
