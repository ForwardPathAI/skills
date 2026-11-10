#!/usr/bin/env bash
# One-time setup for the on-device image fallback of the mobile-ui and web-ui
# skills (`--provider local`). Creates a venv with mflux, which provides the
# FLUX.2 Klein and Qwen-Image CLIs that local_backend.py drives
# (mflux-generate-flux2, mflux-generate-flux2-edit, mflux-generate-qwen,
# mflux-generate-qwen-edit).
#
# You do NOT need this when a Gemini or OpenRouter key is available: cloud is
# the preferred path. Install this only for offline mockups on an Apple Silicon
# Mac, after the user has agreed to the local fallback.
#
# mflux runs on the Apple GPU via MLX, so this needs an Apple Silicon Mac.
# Model weights download from Hugging Face on first generate into the shared HF
# cache (~/.cache/huggingface) - never into the repo. Expect ~12 GB free for
# FLUX.2 Klein, ~20 GB for Qwen-Image-Edit.
#
# Both skills share one venv. The default location matches what local_backend.py
# looks for, so an existing venv there is reused and upgraded.
#
# Idempotent: re-running recreates the venv and upgrades mflux. Prints the venv
# bin path on the last stdout line.
#
# Usage:  setup_local.sh
# Env:
#   IMAGE_GEN_HOME    data root for the shared venv (default ~/.image-gen)
#   IMAGE_GEN_PYTHON  python version for the venv (default 3.11; mflux needs >=3.11)
set -euo pipefail

HOME_DIR="${IMAGE_GEN_HOME:-$HOME/.image-gen}"
VENV="$HOME_DIR/.venv"
PYTHON_VERSION="${IMAGE_GEN_PYTHON:-3.11}"
MFLUX_SPEC="mflux>=0.24"

mkdir -p "$HOME_DIR"

# --- platform check ------------------------------------------------------------
OS="$(uname -s)"; ARCH="$(uname -m)"
if [[ "$OS" != "Darwin" || "$ARCH" != "arm64" ]]; then
  echo "[setup] ERROR: the local fallback uses mflux (native MLX), which requires" >&2
  echo "[setup]        an Apple Silicon Mac. Detected: $OS/$ARCH." >&2
  echo "[setup]        Use a Gemini or OpenRouter key instead." >&2
  exit 1
fi

# --- required tools ------------------------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
  echo "[setup] 'uv' not found on PATH." >&2
  echo "[setup]   install: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  echo "[setup]   (falling back to 'python3 -m venv' + pip)" >&2
fi

# --- create venv + install mflux ----------------------------------------------
echo "[setup] creating venv at $VENV (python $PYTHON_VERSION)" >&2
if command -v uv >/dev/null 2>&1; then
  uv venv --clear --python "$PYTHON_VERSION" "$VENV" >&2
  PY="$VENV/bin/python"
  echo "[setup] installing $MFLUX_SPEC (first run downloads dependencies)" >&2
  uv pip install --python "$PY" --upgrade "$MFLUX_SPEC" >&2
else
  python3 -m venv --clear "$VENV" >&2
  PY="$VENV/bin/python"
  echo "[setup] installing $MFLUX_SPEC (first run downloads dependencies)" >&2
  "$PY" -m pip install --upgrade pip >&2
  "$PY" -m pip install --upgrade "$MFLUX_SPEC" >&2
fi

# --- verify the CLIs local_backend.py needs -----------------------------------
missing=0
for cli in mflux-generate-flux2 mflux-generate-flux2-edit mflux-generate-qwen mflux-generate-qwen-edit; do
  if [[ ! -x "$VENV/bin/$cli" ]]; then
    echo "[setup] ERROR: $cli missing from $VENV/bin" >&2
    missing=1
  fi
done
if [[ "$missing" -ne 0 ]]; then
  echo "[setup] mflux installed without the expected CLIs; check its version." >&2
  exit 1
fi

echo "[setup] done." >&2
echo "[setup]   venv home : $HOME_DIR" >&2
echo "[setup]   CLIs      : $VENV/bin/mflux-generate-*" >&2
echo "[setup] Weights download to the HF cache on the first --provider local run." >&2
# stdout: the venv bin dir local_backend.py reads
echo "$VENV/bin"
