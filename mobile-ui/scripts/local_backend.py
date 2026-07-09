#!/usr/bin/env python3
"""On-device (local) fallback backend for the ForwardPath UI mockup generators.

Used only when no cloud key (Gemini / OpenRouter) is available, on an Apple
Silicon Mac, and only after the calling agent has asked the user for consent
(the generator never silently falls back — local runs solely via
`--provider local`).

Two capabilities, both fully offline:

  1. Image generation — shells out to the `mflux` CLIs installed in the
     `image-gen` skill's venv. It is REFERENCE-CAPABLE: when reference images are
     supplied they are passed via `--image-paths` to a FLUX.2 Klein Edit (default)
     or Qwen-Image-Edit model, so brand/chrome consistency across screens is
     preserved (unlike a pure text-to-image fallback). With no references it uses
     the plain text-to-image CLI (first screen / style board).

  2. analyze / modify-json (only when the caller passes `--vlm`) — runs a local
     VLM (image -> JSON) or LLM (text -> JSON) from a separate `~/.ui-vlm` venv
     created by `scripts/setup_vlm.sh`. The default, recommended path is
     agent-native (the agent reads the image and writes/edits the JSON itself),
     handled by the generator, not here.

This module imports only the Python stdlib so importing it is cheap even on the
cloud path.
"""

import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ── Local image engines (mflux, via the image-gen venv) ─────────────────────────
DEFAULT_LOCAL_MODEL = "flux2-klein-4b"

# Each engine maps to its plain text-to-image CLI + its reference/edit CLI, the
# substrings that identify its weights in the HF hub cache, and an approx free-GB
# bar for a first-time weight download.
LOCAL_MODELS = {
    "flux2-klein-4b": {
        "t2i_cli": "mflux-generate-flux2",
        "edit_cli": "mflux-generate-flux2-edit",
        "mflux_model": "flux2-klein-4b",  # passed via --model
        "repo_match": ["FLUX.2-klein", "FLUX2-klein", "flux2-klein"],
        "min_free_gb": 12.0,
    },
    "qwen-image-edit": {
        "t2i_cli": "mflux-generate-qwen",
        "edit_cli": "mflux-generate-qwen-edit",
        "mflux_model": None,  # the qwen CLIs pick their own default model
        "repo_match": ["Qwen-Image-Edit", "Qwen-Image"],
        "min_free_gb": 20.0,
    },
}

# Aspect ratio -> base (w, h) near ~1 MP; scaled by resolution then snapped to /16.
# Orientation is inherent to the ratio (9:16 -> portrait, 16:9 -> landscape), so
# the generator's save_image_bytes orientation check passes by construction.
AR_BASE = {
    "1:1": (1024, 1024), "3:2": (1216, 832), "2:3": (832, 1216),
    "16:9": (1280, 720), "9:16": (720, 1280), "4:3": (1152, 896),
    "3:4": (896, 1152), "4:5": (896, 1120), "5:4": (1120, 896), "21:9": (1536, 640),
}
RES_SCALE = {"1K": 1.0, "2K": 1.5, "4K": 2.0}

# Light quality cue appended to the prompt for the local (diffusion) path.
LOCAL_UI_BOOST = (
    "clean high-fidelity product UI design, a realistic app screenshot, crisp legible text, "
    "sharp pixel-aligned elements, flat vector interface, high detail, no photograph"
)

# ── Optional offline VLM/LLM (mlx-vlm, via the ~/.ui-vlm venv) ───────────────────
DEFAULT_VLM_MODEL = "mlx-community/Qwen2.5-VL-3B-Instruct-4bit"
DEFAULT_LLM_MODEL = "mlx-community/Qwen2.5-3B-Instruct-4bit"
VLM_ALIASES = {
    "qwen2.5-vl-3b": "mlx-community/Qwen2.5-VL-3B-Instruct-4bit",
    "qwen2.5-vl-7b": "mlx-community/Qwen2.5-VL-7B-Instruct-4bit",
    "moondream": "mlx-community/moondream2",
    "moondream2": "mlx-community/moondream2",
}
LLM_ALIASES = {
    "qwen2.5-3b": "mlx-community/Qwen2.5-3B-Instruct-4bit",
    "qwen2.5-7b": "mlx-community/Qwen2.5-7B-Instruct-4bit",
}


def is_apple_silicon():
    return platform.system() == "Darwin" and platform.machine() == "arm64"


# ── image-gen venv / mflux discovery ────────────────────────────────────────────
def image_gen_home():
    return Path(os.environ.get("IMAGE_GEN_HOME", str(Path.home() / ".image-gen")))


def find_image_gen_venv_bin():
    """The mflux console scripts live in the image-gen venv's bin. That venv is
    created by image-gen's setup_env.sh at IMAGE_GEN_HOME regardless of where the
    skill dir was installed, so that is the authoritative location."""
    bin_dir = image_gen_home() / ".venv" / "bin"
    if (bin_dir / "python").exists():
        return bin_dir
    return None


def mflux_bin(name):
    bin_dir = find_image_gen_venv_bin()
    if not bin_dir:
        return None
    p = bin_dir / name
    return p if p.exists() else None


# ── HF cache / weight detection ─────────────────────────────────────────────────
def hf_hub_dir():
    cache = os.environ.get("HF_HUB_CACHE")
    if cache:
        return Path(cache)
    home = os.environ.get("HF_HOME")
    base = Path(home) if home else (Path.home() / ".cache" / "huggingface")
    return base / "hub"


def weights_present(model):
    info = LOCAL_MODELS.get(model)
    if not info:
        return False
    d = hf_hub_dir()
    if not d.is_dir():
        return False
    try:
        for entry in d.iterdir():
            if not entry.is_dir():
                continue
            name = entry.name.lower()
            if any(m.lower() in name for m in info["repo_match"]):
                if any(entry.rglob("*.safetensors")):
                    return True
    except Exception:
        pass
    return False


def resolve_default_local_model():
    """Auto-pick: prefer the heavier Qwen-Image-Edit only when its weights are
    already cached, otherwise the lighter FLUX.2 Klein Edit (whose family the
    image-gen skill has most likely already downloaded)."""
    if weights_present("qwen-image-edit"):
        return "qwen-image-edit"
    return DEFAULT_LOCAL_MODEL


def free_gb(path):
    try:
        p = Path(path)
        while not p.exists() and p != p.parent:
            p = p.parent
        return shutil.disk_usage(str(p)).free / (1024 ** 3)
    except Exception:
        return 0.0


def local_installed():
    """image-gen venv present with the mflux flux2-edit CLI, on Apple Silicon."""
    return is_apple_silicon() and mflux_bin("mflux-generate-flux2-edit") is not None


def local_status():
    bin_dir = find_image_gen_venv_bin()
    model = resolve_default_local_model()
    return {
        "apple_silicon": is_apple_silicon(),
        "image_gen_venv_bin": str(bin_dir) if bin_dir else None,
        "flux2_edit_cli": str(mflux_bin("mflux-generate-flux2-edit") or ""),
        "default_model": model,
        "weights_present": weights_present(model),
        "free_gb": round(free_gb(hf_hub_dir()), 1),
        "installed": local_installed(),
    }


def unavailable_reason():
    """Human-readable reason the local image path can't run (or None if it can)."""
    if not is_apple_silicon():
        return "not an Apple Silicon Mac"
    if find_image_gen_venv_bin() is None:
        return "image-gen skill not set up (run its scripts/setup_env.sh)"
    if mflux_bin("mflux-generate-flux2-edit") is None:
        return "mflux flux2-edit CLI missing (update image-gen: setup_env.sh --update)"
    return None


# ── sizing ──────────────────────────────────────────────────────────────────────
def _snap16(v):
    return max(16, int(round(v / 16.0)) * 16)


def aspect_to_wh(aspect, size):
    w, h = AR_BASE.get(aspect or "1:1", (1024, 1024))
    scale = RES_SCALE.get((size or "1K").upper(), 1.0)
    return _snap16(w * scale), _snap16(h * scale)


# ── optional VLM/LLM venv discovery ─────────────────────────────────────────────
def ui_vlm_home():
    return Path(os.environ.get("UI_VLM_HOME", str(Path.home() / ".ui-vlm")))


def find_vlm_python():
    py = ui_vlm_home() / ".venv" / "bin" / "python"
    return py if py.exists() else None


def vlm_installed():
    return is_apple_silicon() and find_vlm_python() is not None


def _resolve_vlm_model(name):
    if not name:
        return DEFAULT_VLM_MODEL
    if "/" in name:
        return name
    return VLM_ALIASES.get(name.lower(), name)


def _resolve_llm_model(name):
    if not name:
        return DEFAULT_LLM_MODEL
    if "/" in name:
        return name
    return LLM_ALIASES.get(name.lower(), name)


def _extract_generation(stdout):
    """mlx-vlm / mlx-lm bracket the generated text between '=====' rules and print
    stats afterwards; return just the generated block."""
    if not stdout:
        return ""
    parts = stdout.split("==========")
    if len(parts) >= 3:
        return parts[1].strip()
    return stdout.strip()


# ── the backend ─────────────────────────────────────────────────────────────────
class LocalBackend:
    """Mirrors the GeminiBackend / OpenRouterBackend interface used by the
    generators: generate_image(...) and generate_text(...)."""

    def __init__(self, model=None):
        self.model = model or resolve_default_local_model()

    # -- image generation (mflux) ------------------------------------------------
    def generate_image(self, model, prompt, image_paths, temperature, aspect, size):
        model = model if model in LOCAL_MODELS else self.model
        info = LOCAL_MODELS[model]
        w, h = aspect_to_wh(aspect, size)
        full_prompt = f"{prompt.rstrip('. ')}. {LOCAL_UI_BOOST}"

        refs = [str(p) for p in (image_paths or []) if Path(p).exists()]
        use_edit = bool(refs)
        texts = []

        cli_name = info["edit_cli"] if use_edit else info["t2i_cli"]
        cli = mflux_bin(cli_name)
        if use_edit and cli is None:
            msg = (f"WARN: {cli_name} not found in the image-gen venv; falling back to "
                   f"text-to-image (references dropped). Update image-gen: "
                   f"bash <image-gen>/scripts/setup_env.sh --update")
            print(msg, file=sys.stderr)
            texts.append(msg)
            use_edit = False
            cli_name = info["t2i_cli"]
            cli = mflux_bin(cli_name)
        if cli is None:
            return None, texts + [f"ERROR: {cli_name} not available (is image-gen set up "
                                  "on this Apple Silicon Mac?)."]

        tmpdir = Path(tempfile.mkdtemp(prefix="uilocal_"))
        out_path = tmpdir / "gen.png"
        cmd = [str(cli), "--prompt", full_prompt,
               "--width", str(w), "--height", str(h),
               "--output", str(out_path)]
        if info.get("mflux_model"):
            cmd += ["--model", info["mflux_model"]]
        if use_edit:
            cmd += ["--image-paths", *refs]

        kind = f"edit with {len(refs)} ref(s)" if use_edit else "text-to-image"
        print(f"Local render: {cli_name} ({model}) at {w}x{h} [{kind}]; "
              "first run downloads weights...", file=sys.stderr)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
        except Exception as e:  # noqa: BLE001
            return None, texts + [f"ERROR launching {cli_name}: {e}"]

        if proc.stderr:
            tail = "\n".join(proc.stderr.strip().splitlines()[-8:])
            print(tail, file=sys.stderr)
        if proc.returncode != 0:
            return None, texts + [f"ERROR: {cli_name} exited {proc.returncode}."]

        produced = out_path if out_path.exists() else None
        if produced is None:
            pngs = sorted(tmpdir.glob("*.png"))
            produced = pngs[0] if pngs else None
        if produced is None:
            return None, texts + ["ERROR: the local generator produced no output image."]
        return Path(produced).read_bytes(), texts

    # -- analyze / modify-json (offline VLM/LLM; only used with --vlm) ------------
    def generate_text(self, model, prompt, image_paths, temperature, vlm_model=None):
        py = find_vlm_python()
        if py is None:
            return None, ("LOCAL_VLM_NOT_SETUP: the offline --vlm path needs the ~/.ui-vlm "
                          "venv. Set it up once: bash <this skill>/scripts/setup_vlm.sh "
                          "(or drop --vlm to do it agent-native).")
        imgs = [str(p) for p in (image_paths or []) if Path(p).exists()]
        if imgs:
            mdl = _resolve_vlm_model(vlm_model)
            cmd = [str(py), "-m", "mlx_vlm.generate", "--model", mdl,
                   "--max-tokens", "4096", "--temperature", str(temperature or 0.1),
                   "--prompt", prompt, "--image", *imgs]
        else:
            mdl = _resolve_llm_model(vlm_model)
            # Greedy default (temp 0) is best for JSON; don't pass a temp flag
            # (its name varies across mlx-lm versions).
            cmd = [str(py), "-m", "mlx_lm.generate", "--model", mdl,
                   "--max-tokens", "4096", "--prompt", prompt]

        print(f"Local {'VLM' if imgs else 'LLM'}: {mdl} (first run downloads weights)...",
              file=sys.stderr)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
        except Exception as e:  # noqa: BLE001
            return None, f"ERROR launching the local VLM/LLM: {e}"
        if proc.returncode != 0:
            tail = "\n".join((proc.stderr or "").strip().splitlines()[-8:])
            return None, f"local VLM/LLM exited {proc.returncode}: {tail}"
        return _extract_generation(proc.stdout), None
