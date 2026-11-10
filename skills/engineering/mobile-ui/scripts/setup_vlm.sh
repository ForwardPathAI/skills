#!/usr/bin/env bash
# Optional setup for the OFFLINE analyze / modify-json path of the mobile-ui and
# web-ui skills (the `--vlm` flag). Creates a shared venv with mlx-vlm (which
# also brings mlx-lm) so both skills reuse one environment and one set of model
# weights.
#
# You do NOT need this for normal use: with --provider local the default
# analyze/modify-json path is agent-native (the agent reads the mockup and writes
# the JSON itself). Install this only if you want a fully-scripted, model-driven
# offline analyze/modify-json (e.g. batch/headless runs).
#
# mlx-vlm runs the model on the Apple GPU via MLX, so this needs an Apple Silicon
# Mac (a Metal GPU). Model weights download from Hugging Face on first run into
# the shared HF cache (~/.cache/huggingface) - never into the repo.
#
# Idempotent: re-running recreates the venv and upgrades mlx-vlm. Prints the venv
# python path on the last stdout line.
#
# Usage:  setup_vlm.sh
# Env:
#   UI_VLM_HOME     data root for the shared venv (default ~/.ui-vlm)
#   UI_VLM_PYTHON   python version for the venv (default 3.11)
set -euo pipefail

VLM_HOME="${UI_VLM_HOME:-$HOME/.ui-vlm}"
VENV="$VLM_HOME/.venv"
PYTHON_VERSION="${UI_VLM_PYTHON:-3.11}"

mkdir -p "$VLM_HOME"

# --- platform check ------------------------------------------------------------
OS="$(uname -s)"; ARCH="$(uname -m)"
if [[ "$OS" != "Darwin" || "$ARCH" != "arm64" ]]; then
  echo "[setup] WARNING: the offline --vlm path uses mlx-vlm (native MLX), which" >&2
  echo "[setup]          requires an Apple Silicon Mac with a Metal GPU. Detected:" >&2
  echo "[setup]          $OS/$ARCH. The local VLM/LLM will not work on this platform." >&2
fi

# --- required tools ------------------------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
  echo "[setup] 'uv' not found on PATH." >&2
  echo "[setup]   install: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  echo "[setup]   (falling back to 'python3 -m venv' + pip)" >&2
fi

# --- create venv + install mlx-vlm --------------------------------------------
echo "[setup] creating venv at $VENV (python $PYTHON_VERSION)" >&2
if command -v uv >/dev/null 2>&1; then
  uv venv --python "$PYTHON_VERSION" "$VENV" >&2
  PY="$VENV/bin/python"
  echo "[setup] installing mlx-vlm (brings mlx-lm, transformers, Pillow; first run" >&2
  echo "[setup] downloads dependencies)" >&2
  uv pip install --python "$PY" --upgrade mlx-vlm >&2
else
  python3 -m venv "$VENV" >&2
  PY="$VENV/bin/python"
  echo "[setup] installing mlx-vlm (brings mlx-lm, transformers, Pillow; first run" >&2
  echo "[setup] downloads dependencies)" >&2
  "$PY" -m pip install --upgrade pip >&2
  "$PY" -m pip install --upgrade mlx-vlm >&2
fi

# --- verify the GPU-backed import actually works ------------------------------
if "$PY" -c "import mlx_vlm; import mlx.core as mx; mx.eval(mx.array([1.0]) + 1); print('ok')" >/dev/null 2>&1; then
  echo "[setup] mlx-vlm + MLX GPU import OK" >&2
else
  echo "[setup] WARNING: mlx-vlm/MLX GPU check did not pass here." >&2
  echo "[setup]          This is expected inside a sandbox or headless session;" >&2
  echo "[setup]          it will work when run from a normal desktop session." >&2
fi

echo "[setup] done." >&2
echo "[setup]   venv home : $VLM_HOME" >&2
echo "[setup]   python    : $PY" >&2
echo "[setup] Default models (download to the HF cache on first --vlm run):" >&2
echo "[setup]   analyze VLM : mlx-community/Qwen2.5-VL-3B-Instruct-4bit (~3 GB, Apache-2.0)" >&2
echo "[setup]   modify  LLM : mlx-community/Qwen2.5-3B-Instruct-4bit" >&2
echo "[setup] Override per run with --vlm-model (alias or HF id; e.g. a Moondream" >&2
echo "[setup] MLX build - note Moondream 3 is BSL-licensed)." >&2
# stdout: the venv python that local_backend.py will drive
echo "$PY"
