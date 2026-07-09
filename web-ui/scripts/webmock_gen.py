#!/usr/bin/env python3
"""
ForwardPath Web UI — mockup generator (self-contained).

Generates, analyzes, and modifies high-fidelity WEB APP UI mockups using a
Gemini image model, via one of three interchangeable backends:

  - gemini      Google Gemini API directly (google-genai SDK)
  - openrouter  OpenRouter's OpenAI-compatible API (stdlib HTTP, no extra deps)
  - local       On-device fallback (no key, Apple Silicon) — reference-capable
                FLUX.2 Klein Edit / Qwen-Image-Edit via the image-gen skill's
                mflux CLIs. Used only when no cloud key exists and the user has
                consented; see local_backend.py. analyze/modify-json in local
                mode are agent-native by default (the agent writes the JSON),
                with an opt-in offline VLM via --vlm.

All prompt construction, landscape enforcement, and JSON handling are shared
across backends — only the transport differs. Forces LANDSCAPE desktop framing
so screens render wide, and persists API keys per provider on this machine so
they are asked for only once.

Three kinds of image (--kind), generated in this order for consistency:
  style-board  a brand design-system tile (swatches, type, components) — first
  shell        the persistent app chrome (nav/sidebar) with an empty canvas
  screen       a real screen that reuses the same shell (the default)

Requires: Pillow (always). google-genai only for the gemini backend. The local
backend shells out to the separately-installed image-gen skill (mflux).

Commands:
  setup        Store the API key for a provider (and optional model overrides)
  check        Report whether an API key is configured (never prints the key)
  generate     Generate a new landscape web mockup from a prompt
  analyze      Analyze a mockup image into a JSON design spec
  modify-json  Apply natural-language changes to a JSON design spec
  regenerate   Re-render a mockup from a (modified) JSON spec

Select the backend with --provider (gemini|openrouter|local), the WEB_UI_PROVIDER
env var, or the stored default. Default: gemini. The local provider never
engages implicitly — the agent must pass --provider local after confirming Apple
Silicon + user consent (see SKILL.md).
"""

import argparse
import base64
import getpass
import io
import json
import os
import sys
from pathlib import Path

import local_backend

CONFIG_PATH = Path.home() / ".config" / "web-ui" / "config.json"
DEFAULT_PROVIDER = "gemini"

# Per-provider metadata: env vars, default models, where to get a key.
PROVIDERS = {
    "gemini": {
        "env_keys": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "generation_model": "gemini-3-pro-image-preview",
        "analysis_model": "gemini-2.5-flash",
        "key_url": "https://aistudio.google.com/apikey",
    },
    "openrouter": {
        "env_keys": ("OPENROUTER_API_KEY",),
        "generation_model": "google/gemini-3.1-flash-image-preview",
        "analysis_model": "google/gemini-2.5-flash",
        "key_url": "https://openrouter.ai/keys",
    },
}

# Provider-independent render defaults.
RENDER_DEFAULTS = {"aspect_ratio": "16:9", "image_size": "2K"}

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MIME_MAP = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
}

FRAME_INSTRUCTIONS = {
    "browser": (
        "Render inside a clean, modern desktop browser window (subtle top chrome with "
        "traffic-light buttons and a single URL bar), centered on a very light neutral "
        "studio background (#F2F2F2) with a soft realistic shadow. "
        "Do NOT rotate to portrait."
    ),
    "macbook": (
        "Render on the screen of a single modern silver laptop, centered, filling ~92% of "
        "the frame width, on a very light neutral studio background (#F2F2F2) with a soft "
        "realistic shadow. Do NOT rotate to portrait."
    ),
    "none": (
        "A full-bleed web app screen with NO browser or device frame: edge-to-edge "
        "landscape UI that looks like a real desktop screenshot."
    ),
}

# Base scaffolds per --kind: (opening line, strict line with an optional {frame} slot).
GENERATE_SCAFFOLDS = {
    "screen": (
        "Generate ONE high-fidelity WEB APP UI mockup image (a single real screen).",
        "STRICT: LANDSCAPE desktop orientation, wider than tall. {frame} "
        "Crisp legible text, pixel-accurate alignment, realistic web components "
        "(buttons, inputs, tables, cards, menus), real concise labels (NO lorem ipsum).",
    ),
    "shell": (
        "Generate ONE high-fidelity WEB APP SHELL mockup — the persistent navigation "
        "chrome (top nav and/or left sidebar, logo, user menu) with an EMPTY content "
        "area. This is the reusable frame every screen sits inside, NOT a full screen.",
        "STRICT: LANDSCAPE desktop orientation, wider than tall. {frame} "
        "Crisp legible navigation labels (NO lorem ipsum). Leave the main content "
        "region visibly empty/blank.",
    ),
    "style-board": (
        "Generate ONE brand STYLE BOARD image: a design-system tile showing the visual "
        "language — labeled color swatches, typography specimens, and core component "
        "states (primary/secondary/ghost buttons, input, select, card, badge, table "
        "row, tabs) plus the logo lockup, radius and shadow samples.",
        "STRICT: LANDSCAPE orientation, wider than tall. A neat flat design board on a "
        "light neutral canvas — NO browser window, NO device frame, NO app navigation. "
        "Crisp legible labels on every swatch and specimen (NO lorem ipsum).",
    ),
}

KIND_NOUN = {"screen": "Screen", "shell": "Shell", "style-board": "Style board"}


# ── Config / provider resolution ───────────────────────────────────────────────
def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def resolve_provider(args):
    # --provider is argparse-validated; env var and stored config are not, so
    # validate here to fail with a clear message instead of a later KeyError.
    if getattr(args, "provider", None):
        return args.provider
    provider = os.environ.get("WEB_UI_PROVIDER") or load_config().get("provider")
    if provider is None:
        return DEFAULT_PROVIDER
    if provider not in PROVIDERS and provider != "local":
        valid = ", ".join(list(PROVIDERS) + ["local"])
        print(f"ERROR: unknown provider {provider!r} (from WEB_UI_PROVIDER or stored "
              f"config). Valid providers: {valid}.", file=sys.stderr)
        sys.exit(2)
    return provider


def provider_config(provider):
    """Per-provider settings block, tolerating the legacy flat config schema
    (top-level api_key/models) which only ever stored gemini credentials."""
    cfg = load_config()
    pc = dict((cfg.get("providers") or {}).get(provider, {}))
    if provider == "gemini" and not pc.get("api_key") and cfg.get("api_key"):
        pc.setdefault("api_key", cfg["api_key"])
        for k in ("generation_model", "analysis_model"):
            if cfg.get(k):
                pc.setdefault(k, cfg[k])
    return pc


def find_api_key(provider):
    pc = provider_config(provider)
    if pc.get("api_key"):
        return pc["api_key"]
    for k in PROVIDERS[provider]["env_keys"]:
        if os.environ.get(k):
            return os.environ[k]
    return None


def resolve_model(args_model, provider, kind):
    if args_model:
        return args_model
    if provider == "local":
        # One image engine covers both kinds; analyze/modify-json bypass this.
        return load_config().get("local_model") or local_backend.resolve_default_local_model()
    return provider_config(provider).get(kind) or PROVIDERS[provider][kind]


def resolve_setting(args_value, key):
    if args_value:
        return args_value
    return load_config().get(key, RENDER_DEFAULTS[key])


def check_paths(paths):
    for p in paths:
        if not Path(p).exists():
            print(f"ERROR: image not found: {p}", file=sys.stderr)
            sys.exit(2)


# ── Shared image helpers ────────────────────────────────────────────────────────
def aspect_is_landscape(aspect):
    """True when a "W:H" aspect ratio is landscape (wider than tall). Unknown or
    unparseable values default to landscape, the skill's intended orientation."""
    try:
        w, h = (float(x) for x in aspect.split(":"))
        return w >= h
    except (ValueError, AttributeError):
        return True


def save_image_bytes(data, output_path, expect_landscape=True):
    from PIL import Image
    try:
        img = Image.open(io.BytesIO(data))
    except Exception as e:  # noqa: BLE001 - surface any decode failure cleanly
        print(f"ERROR: could not decode returned image data: {e}", file=sys.stderr)
        return False
    w, h = img.size
    is_landscape = w >= h
    if expect_landscape and not is_landscape:
        # Landscape was requested but the model returned a portrait asset — fail
        # loudly instead of saving a wrong-orientation mockup that looks like success.
        print(f"ERROR: model returned a PORTRAIT image ({w}x{h}); expected landscape. "
              "Not saving. Retry, or lower --temperature / simplify the prompt.",
              file=sys.stderr)
        return False
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    kb = Path(output_path).stat().st_size / 1024
    orient = "landscape" if is_landscape else "portrait"
    print(f"OK: {output_path} ({w}x{h}, {orient}, {kb:.0f} KB)")
    return True


def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        newline = text.find("\n")
        # Drop the opening fence line (e.g. ```json). If the whole payload is on
        # one line with no newline, just strip the leading backticks instead of
        # indexing a missing "\n".
        text = text[newline + 1:] if newline != -1 else text.lstrip("`")
    if text.endswith("```"):
        text = text[: text.rfind("```")]
    return text.strip()


# ── Backends ────────────────────────────────────────────────────────────────────
class GeminiBackend:
    """Talks to the Google Gemini API via the google-genai SDK."""

    def __init__(self, api_key):
        from google import genai  # raises ImportError if not installed
        self._genai = genai
        self._client = genai.Client(api_key=api_key)

    def _image_part(self, path):
        from google.genai import types
        mime = MIME_MAP.get(Path(path).suffix.lower(), "image/png")
        return types.Part.from_bytes(data=Path(path).read_bytes(), mime_type=mime)

    def _image_config(self, types, temperature, aspect, size):
        base = dict(response_modalities=["TEXT", "IMAGE"], temperature=temperature)
        try:
            return types.GenerateContentConfig(
                image_config=types.ImageConfig(aspect_ratio=aspect, image_size=size),
                **base,
            )
        except Exception:  # noqa: BLE001 - older SDKs lack image_config
            return types.GenerateContentConfig(**base)

    def generate_image(self, model, prompt, image_paths, temperature, aspect, size):
        from google.genai import types
        contents = [self._image_part(p) for p in image_paths]
        contents.append(prompt)
        resp = self._client.models.generate_content(
            model=model, contents=contents,
            config=self._image_config(types, temperature, aspect, size))
        texts = []
        for cand in resp.candidates or []:
            for part in (cand.content.parts if cand.content else []) or []:
                data = getattr(getattr(part, "inline_data", None), "data", None)
                if data:
                    return data, texts
                if getattr(part, "text", None):
                    texts.append(part.text)
        return None, texts

    def generate_text(self, model, prompt, image_paths, temperature):
        from google.genai import types
        contents = [self._image_part(p) for p in (image_paths or [])]
        contents.append(prompt)
        resp = self._client.models.generate_content(
            model=model, contents=contents,
            config=types.GenerateContentConfig(temperature=temperature))
        parts = []
        for cand in getattr(resp, "candidates", None) or []:
            content = getattr(cand, "content", None)
            for part in (getattr(content, "parts", None) or []):
                if getattr(part, "text", None):
                    parts.append(part.text)
        if parts:
            return "".join(parts), None
        try:
            return resp.text, None
        except Exception:  # noqa: BLE001 - no text part (safety block / image only)
            return None, None


class OpenRouterBackend:
    """Talks to OpenRouter's OpenAI-compatible chat/completions API over stdlib
    HTTP (no third-party client needed)."""

    def __init__(self, api_key):
        self._api_key = api_key

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://forwardpath.ai",
            "X-Title": "ForwardPath Web UI",
        }

    def _image_content(self, path):
        mime = MIME_MAP.get(Path(path).suffix.lower(), "image/png")
        b64 = base64.b64encode(Path(path).read_bytes()).decode("ascii")
        return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}

    def _message(self, prompt, image_paths):
        content = [self._image_content(p) for p in (image_paths or [])]
        content.append({"type": "text", "text": prompt})
        return {"role": "user", "content": content}

    def _post(self, body):
        import urllib.error
        import urllib.request
        req = urllib.request.Request(
            OPENROUTER_URL, data=json.dumps(body).encode("utf-8"),
            headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                body = r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:800]
            return None, f"HTTP {e.code} from OpenRouter: {detail}"
        except urllib.error.URLError as e:
            return None, f"network error reaching OpenRouter: {e.reason}"
        try:
            return json.loads(body), None
        except json.JSONDecodeError:
            return None, f"non-JSON response from OpenRouter: {body[:800] or '(empty body)'}"

    def generate_image(self, model, prompt, image_paths, temperature, aspect, size):
        body = {
            "model": model,
            "modalities": ["image", "text"],
            "messages": [self._message(prompt, image_paths)],
            "temperature": temperature,
            "image_config": {"aspect_ratio": aspect, "image_size": size},
        }
        payload, err = self._post(body)
        if err:
            return None, [err]
        texts = []
        for choice in payload.get("choices", []) or []:
            msg = choice.get("message") or {}
            for img in msg.get("images") or []:
                url = (img.get("image_url") or {}).get("url", "")
                if url.startswith("data:") and "," in url:
                    return base64.b64decode(url.split(",", 1)[1]), texts
            content = msg.get("content")
            if isinstance(content, str) and content:
                texts.append(content)
        return None, texts

    def generate_text(self, model, prompt, image_paths, temperature):
        body = {
            "model": model,
            "messages": [self._message(prompt, image_paths)],
            "temperature": temperature,
        }
        payload, err = self._post(body)
        if err:
            return None, err
        parts = []
        for choice in payload.get("choices", []) or []:
            content = (choice.get("message") or {}).get("content")
            if isinstance(content, str) and content:
                parts.append(content)
            elif isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text" and c.get("text"):
                        parts.append(c["text"])
        return ("".join(parts) if parts else None), None


def get_backend(provider):
    if provider == "local":
        reason = local_backend.unavailable_reason()
        if reason:
            print(f"ERROR: --provider local unavailable: {reason}. The on-device fallback "
                  "needs an Apple Silicon Mac with the image-gen skill set up "
                  "(bash <image-gen>/scripts/setup_env.sh).", file=sys.stderr)
            sys.exit(2)
        return local_backend.LocalBackend()
    api_key = find_api_key(provider)
    if not api_key:
        meta = PROVIDERS[provider]
        keys = " / ".join(meta["env_keys"])
        # If this machine can run the on-device fallback, tell the agent so it can
        # offer local generation (after user consent) instead of blocking on a key.
        extra = ""
        if local_backend.local_installed():
            extra = (" Alternatively this Apple Silicon Mac can generate on-device with no "
                     "key — ask the user to confirm, then re-run with --provider local.")
        # Stable, greppable sentinel so the calling agent knows to ask the user.
        print(f"NO_API_KEY: No {provider} API key configured. Ask the user for a key "
              f"({meta['key_url']}), then store it by piping it via stdin: "
              f"printf '%s' THE_KEY | python webmock_gen.py setup --provider {provider} "
              f"(or set {keys}).{extra}", file=sys.stderr)
        sys.exit(3)
    if provider == "gemini":
        try:
            return GeminiBackend(api_key)
        except ImportError:
            print("ERROR: google-genai not installed (needed for --provider gemini). "
                  "Run: pip install google-genai Pillow — or use --provider openrouter.",
                  file=sys.stderr)
            sys.exit(2)
    return OpenRouterBackend(api_key)


# ── Prompt builders (shared across backends) ────────────────────────────────────
def build_generate_prompt(args, frame):
    kind = getattr(args, "kind", "screen") or "screen"
    head, strict = GENERATE_SCAFFOLDS.get(kind, GENERATE_SCAFFOLDS["screen"])
    # style-board has no {frame} slot; .format ignores the unused kwarg.
    lines = [head, strict.format(frame=frame)]
    if args.description:
        lines.append(f"\nProject / brand context: {args.description}")
    lines.append(f"\n{KIND_NOUN.get(kind, 'Screen')} to generate: {args.prompt}")
    if args.theme:
        lines.append(f"\nTheme: {args.theme} mode.")
    if args.colors:
        lines.append(f"\nColor palette (use exactly): {args.colors}")
    if args.style:
        lines.append(f"\nVisual style: {args.style}")
    if args.refs:
        if kind == "style-board":
            lines.append(
                "\nUse the attached image(s) (e.g. the logo) as brand assets to feature "
                "on the board — match their exact colors and marks.")
        else:
            lines.append(
                "\nUse the attached reference image(s) for one-product consistency: match "
                "the same color palette, typography, component style, corner radii and "
                "iconography, AND reproduce the SAME app chrome — identical navigation "
                "items, order, logo and active state as the shell reference. This is a "
                "DIFFERENT screen of the SAME app.")
    return "\n".join(lines)


def build_regenerate_prompt(args, frame, spec):
    kind = getattr(args, "kind", "screen") or "screen"
    head, strict = GENERATE_SCAFFOLDS.get(kind, GENERATE_SCAFFOLDS["screen"])
    lines = [
        head + " It must PRECISELY match this design specification and look like a real "
        "screenshot.",
        strict.format(frame=frame),
        f"\nDesign specification:\n{spec}",
    ]
    if args.original:
        lines.append("\nThe first attached image is the original. Keep its layout and "
                     "aesthetic; change only what the spec modifies.")
    if args.refs:
        lines.append("\nUse the other attached image(s) for brand + chrome consistency "
                     "(same app: identical nav items, order, logo, active state).")
    if args.extra_instructions:
        lines.append(f"\nAdditional instructions: {args.extra_instructions}")
    return "\n".join(lines)


ANALYZE_PROMPT = (
    "Analyze this WEB APP UI screenshot in extreme detail. Return ONE JSON "
    "object describing: screen_name, theme (light/dark), app_shell (top nav items in "
    "order, sidebar groups/items, logo, user menu, active nav item), layout (content "
    "regions left→right / top→bottom), colors (with hex), typography, every visible "
    "component (type, text, position, style), spacing, visual_effects, and the single "
    "primary action. Return ONLY valid JSON, no commentary.")


# ── Commands ──────────────────────────────────────────────────────────────────
def read_api_key(args, provider):
    """Resolve the key without exposing it via process args when possible.

    Order: --api-key (legacy) → provider env vars → stdin (getpass on a TTY,
    otherwise a piped line). Prefer stdin/env so the secret never lands in
    `ps`/`/proc` or shell history via a visible --api-key argument.
    """
    if args.api_key:
        return args.api_key.strip()
    for k in PROVIDERS[provider]["env_keys"]:
        if os.environ.get(k):
            return os.environ[k].strip()
    try:
        if sys.stdin.isatty():
            return getpass.getpass(f"{provider} API key (input hidden): ").strip()
        return sys.stdin.readline().strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def cmd_setup(args):
    provider = resolve_provider(args)
    if provider == "local":
        cfg = load_config()
        cfg["provider"] = "local"
        if getattr(args, "local_model", None):
            cfg["local_model"] = args.local_model
        save_config(cfg)
        print(f"Saved local as the default provider at {CONFIG_PATH} (no key needed).")
        print(f"  Local engine: {resolve_model(None, 'local', 'generation_model')} "
              "(auto: Qwen-Image-Edit if cached, else FLUX.2 Klein Edit)")
        return
    key = read_api_key(args, provider)
    if not key:
        keys = " / ".join(PROVIDERS[provider]["env_keys"])
        print(f"ERROR: no API key provided. Pipe it via stdin (printf '%s' THE_KEY | "
              f"python webmock_gen.py setup --provider {provider}), set {keys}, or pass "
              "--api-key.", file=sys.stderr)
        sys.exit(2)
    cfg = load_config()
    cfg["provider"] = provider
    pc = cfg.setdefault("providers", {}).setdefault(provider, {})
    pc["api_key"] = key
    if args.generation_model:
        pc["generation_model"] = args.generation_model
    if args.analysis_model:
        pc["analysis_model"] = args.analysis_model
    save_config(cfg)
    try:
        CONFIG_PATH.chmod(0o600)
    except OSError:
        pass
    print(f"Saved {provider} API key to {CONFIG_PATH}")
    print(f"  Default provider: {provider}")
    print(f"  Generation model: {resolve_model(None, provider, 'generation_model')}")
    print(f"  Analysis model:   {resolve_model(None, provider, 'analysis_model')}")


def _print_local_fallback_status():
    st = local_backend.local_status()
    if st["installed"]:
        weights = "weights cached" if st["weights_present"] else "weights download on first run"
        print(f"LOCAL_FALLBACK_AVAILABLE: on-device generation ready (engine "
              f"{st['default_model']}, {weights}, {st['free_gb']} GB free).")
    else:
        print(f"LOCAL_FALLBACK_UNAVAILABLE ({local_backend.unavailable_reason()}).")
    vlm = "AVAILABLE" if local_backend.vlm_installed() else "UNAVAILABLE"
    tail = "ready" if local_backend.vlm_installed() else "needs scripts/setup_vlm.sh"
    print(f"LOCAL_VLM_{vlm}: offline analyze/modify-json --vlm {tail} "
          "(default path is agent-native, no setup).")


def cmd_check(args):
    provider = resolve_provider(args)
    if provider == "local":
        _print_local_fallback_status()
        return
    meta = PROVIDERS[provider]
    if provider_config(provider).get("api_key"):
        print(f"CONFIGURED: {provider} key stored at {CONFIG_PATH}")
    else:
        env_present = next((k for k in meta["env_keys"] if os.environ.get(k)), None)
        if env_present:
            print(f"CONFIGURED: {provider} key from environment variable {env_present}")
        else:
            keys = " or ".join(meta["env_keys"])
            print(f"NOT_CONFIGURED ({provider}): pipe key via stdin (printf '%s' THE_KEY | "
                  f"python webmock_gen.py setup --provider {provider}) or set {keys}")
    _print_local_fallback_status()


def cmd_generate(args):
    provider = resolve_provider(args)
    check_paths(args.refs or [])
    backend = get_backend(provider)
    model = resolve_model(args.model, provider, "generation_model")
    aspect = resolve_setting(args.aspect, "aspect_ratio")
    size = resolve_setting(args.size, "image_size")
    frame = FRAME_INSTRUCTIONS.get(args.frame, FRAME_INSTRUCTIONS["browser"])
    prompt = build_generate_prompt(args, frame)

    print(f"Generating {args.output} [{args.kind}] ({aspect}, {size}) with {model} "
          f"[{provider}]...")
    data, texts = backend.generate_image(
        model, prompt, args.refs or [], args.temperature, aspect, size)
    if data is None:
        print("ERROR: no image in response." + (" Model said:" if texts else ""),
              file=sys.stderr)
        if texts:
            print("\n".join(texts)[:800], file=sys.stderr)
        sys.exit(1)
    if not save_image_bytes(data, args.output, aspect_is_landscape(aspect)):
        sys.exit(1)


def _write_json_or_exit(raw, err, output_path, retry_hint):
    if not raw:
        detail = f": {err}" if err else " (possible safety block or empty response)"
        print(f"ERROR: model returned no text{detail}. {retry_hint}", file=sys.stderr)
        sys.exit(1)
    out_text = extract_json(raw)
    try:
        out_text = json.dumps(json.loads(out_text), indent=2)
    except json.JSONDecodeError:
        print("ERROR: model response was not valid JSON; not writing output.",
              file=sys.stderr)
        print(out_text[:800], file=sys.stderr)
        sys.exit(1)
    Path(output_path).write_text(out_text)
    print(f"Saved {output_path}")


def _emit_agent_native_analyze(image, output):
    """Local default: no model call — the agent (itself a strong VLM) reads the
    mockup and writes the JSON spec. Print a greppable directive it can act on."""
    print("LOCAL_ANALYZE_AGENT_NATIVE: running on-device with no cloud key. The agent "
          f"should READ the image '{image}', produce the JSON design spec described "
          f"below, and WRITE it to '{output}'. (Or re-run with --vlm to use the offline "
          "Qwen2.5-VL model instead.)")
    print("\n--- analyze instruction / schema ---")
    print(ANALYZE_PROMPT)


def _emit_agent_native_modify(json_file, changes, output):
    print("LOCAL_MODIFY_AGENT_NATIVE: running on-device with no cloud key. The agent "
          f"should READ the JSON spec '{json_file}', apply the changes below, and WRITE "
          f"the COMPLETE modified JSON (all unmentioned fields kept exactly) to "
          f"'{output}'. (Or re-run with --vlm to use the offline LLM instead.)")
    print(f"\n--- requested changes ---\n{changes}")


def cmd_analyze(args):
    provider = resolve_provider(args)
    check_paths([args.image])
    output = args.output or (Path(args.image).stem + "_analysis.json")
    if provider == "local":
        if not getattr(args, "vlm", False):
            _emit_agent_native_analyze(args.image, output)
            return
        backend = local_backend.LocalBackend()
        print("Analyzing with the on-device VLM [local --vlm]...")
        raw, err = backend.generate_text(None, ANALYZE_PROMPT, [args.image], 0.1,
                                         vlm_model=args.vlm_model)
        _write_json_or_exit(raw, err, output,
                            "Try again, or drop --vlm to analyze agent-native.")
        return
    backend = get_backend(provider)
    model = resolve_model(args.model, provider, "analysis_model")
    print(f"Analyzing with {model} [{provider}]...")
    raw, err = backend.generate_text(model, ANALYZE_PROMPT, [args.image], 0.1)
    _write_json_or_exit(raw, err, output, "Try again or adjust the image.")


def cmd_modify_json(args):
    provider = resolve_provider(args)
    spec = Path(args.json_file).read_text()
    output = args.output or (Path(args.json_file).stem + "_modified.json")
    prompt = (f"Here is a JSON spec of a web app screen:\n\n{spec}\n\n"
              f"Apply these modifications: {args.changes}\n\n"
              "Return the COMPLETE modified JSON, keeping all unmentioned fields exactly. "
              "Return ONLY valid JSON.")
    if provider == "local":
        if not getattr(args, "vlm", False):
            _emit_agent_native_modify(args.json_file, args.changes, output)
            return
        backend = local_backend.LocalBackend()
        print("Modifying JSON with the on-device LLM [local --vlm]...")
        raw, err = backend.generate_text(None, prompt, None, 0.1, vlm_model=args.vlm_model)
        _write_json_or_exit(raw, err, output,
                            "Try again, or drop --vlm to modify agent-native.")
        return
    backend = get_backend(provider)
    model = resolve_model(args.model, provider, "analysis_model")
    print(f"Modifying JSON with {model} [{provider}]...")
    raw, err = backend.generate_text(model, prompt, None, 0.1)
    _write_json_or_exit(raw, err, output, "Try again or simplify the changes.")


def cmd_regenerate(args):
    provider = resolve_provider(args)
    image_paths = ([args.original] if args.original else []) + list(args.refs or [])
    check_paths(image_paths)
    backend = get_backend(provider)
    model = resolve_model(args.model, provider, "generation_model")
    aspect = resolve_setting(args.aspect, "aspect_ratio")
    size = resolve_setting(args.size, "image_size")
    frame = FRAME_INSTRUCTIONS.get(args.frame, FRAME_INSTRUCTIONS["browser"])
    spec = Path(args.json_spec).read_text()
    prompt = build_regenerate_prompt(args, frame, spec)

    print(f"Regenerating {args.output} [{args.kind}] ({aspect}, {size}) with {model} "
          f"[{provider}]...")
    data, texts = backend.generate_image(
        model, prompt, image_paths, args.temperature, aspect, size)
    if data is None:
        print("ERROR: no image in response." + (" Model said:" if texts else ""),
              file=sys.stderr)
        if texts:
            print("\n".join(texts)[:800], file=sys.stderr)
        sys.exit(1)
    if not save_image_bytes(data, args.output, aspect_is_landscape(aspect)):
        sys.exit(1)


# ── CLI ───────────────────────────────────────────────────────────────────────
def add_provider_arg(sp):
    sp.add_argument(
        "--provider", choices=list(PROVIDERS) + ["local"],
        help="Backend to use (default: WEB_UI_PROVIDER env, stored default, "
             "then gemini). 'local' = on-device fallback (Apple Silicon, no key, "
             "user consent required)")


def main():
    p = argparse.ArgumentParser(description="ForwardPath Web UI — mockup generator")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser(
        "setup",
        help="Store a provider's API key on this machine. Prefer piping the key via "
             "stdin or an env var over --api-key (which is visible in ps/proc).")
    add_provider_arg(sp)
    sp.add_argument("--api-key", help="Legacy: visible in process args; prefer stdin/env")
    sp.add_argument("--generation-model")
    sp.add_argument("--analysis-model")
    sp.add_argument("--local-model", choices=list(local_backend.LOCAL_MODELS),
                    help="With --provider local: pin the on-device engine "
                         "(default auto-picks Qwen-Image-Edit if cached, else FLUX.2)")

    sp = sub.add_parser("check", help="Report whether an API key is configured")
    add_provider_arg(sp)

    sp = sub.add_parser("generate", help="Generate a new landscape web mockup")
    add_provider_arg(sp)
    sp.add_argument("--kind", default="screen", choices=list(GENERATE_SCAFFOLDS),
                    help="style-board | shell | screen (default: screen)")
    sp.add_argument("--prompt", required=True)
    sp.add_argument("--refs", nargs="*", default=[])
    sp.add_argument("--colors", default="")
    sp.add_argument("--style", default="")
    sp.add_argument("--description", default="")
    sp.add_argument("--theme", default="", help="light | dark (optional)")
    sp.add_argument("--frame", default="browser", choices=list(FRAME_INSTRUCTIONS))
    sp.add_argument("-o", "--output", required=True)
    sp.add_argument("--aspect", default="", help="default 16:9")
    sp.add_argument("--size", default="", help="1K | 2K | 4K (default 2K)")
    sp.add_argument("--temperature", type=float, default=0.35)
    sp.add_argument("--model")

    sp = sub.add_parser("analyze", help="Analyze a mockup into a JSON spec")
    add_provider_arg(sp)
    sp.add_argument("image")
    sp.add_argument("-o", "--output")
    sp.add_argument("--model")
    sp.add_argument("--vlm", action="store_true",
                    help="With --provider local: use the offline VLM instead of the "
                         "agent-native default (needs scripts/setup_vlm.sh)")
    sp.add_argument("--vlm-model",
                    help="Override the offline VLM (alias or HF id; "
                         "default mlx-community/Qwen2.5-VL-3B-Instruct-4bit)")

    sp = sub.add_parser("modify-json", help="Apply changes to a JSON spec")
    add_provider_arg(sp)
    sp.add_argument("--json-file", required=True)
    sp.add_argument("--changes", required=True)
    sp.add_argument("-o", "--output")
    sp.add_argument("--model")
    sp.add_argument("--vlm", action="store_true",
                    help="With --provider local: use the offline LLM instead of the "
                         "agent-native default (needs scripts/setup_vlm.sh)")
    sp.add_argument("--vlm-model",
                    help="Override the offline LLM (alias or HF id; "
                         "default mlx-community/Qwen2.5-3B-Instruct-4bit)")

    sp = sub.add_parser("regenerate", help="Re-render a mockup from a JSON spec")
    add_provider_arg(sp)
    sp.add_argument("--kind", default="screen", choices=list(GENERATE_SCAFFOLDS),
                    help="style-board | shell | screen (default: screen)")
    sp.add_argument("--json-spec", required=True)
    sp.add_argument("--original")
    sp.add_argument("--refs", nargs="*", default=[])
    sp.add_argument("--extra-instructions", default="")
    sp.add_argument("--frame", default="browser", choices=list(FRAME_INSTRUCTIONS))
    sp.add_argument("-o", "--output", required=True)
    sp.add_argument("--aspect", default="")
    sp.add_argument("--size", default="")
    sp.add_argument("--temperature", type=float, default=0.2)
    sp.add_argument("--model")

    args = p.parse_args()
    {
        "setup": cmd_setup, "check": cmd_check, "generate": cmd_generate,
        "analyze": cmd_analyze, "modify-json": cmd_modify_json, "regenerate": cmd_regenerate,
    }[args.command](args)


if __name__ == "__main__":
    main()
