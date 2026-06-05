#!/usr/bin/env python3
"""
ForwardPath Mobile UI — mockup generator (self-contained).

Generates, analyzes, and modifies high-fidelity MOBILE APP UI mockups using
Google Gemini native image generation. Forces PORTRAIT phone framing so screens
render upright, and persists the Gemini API key on this machine so it is asked
for only once.

No external skill dependencies. Requires: google-genai, Pillow.

Commands:
  setup        Store the Gemini API key (and optional model overrides)
  check        Report whether an API key is configured (never prints the key)
  generate     Generate a new portrait mobile mockup from a prompt
  analyze      Analyze a mockup image into a JSON design spec
  modify-json  Apply natural-language changes to a JSON design spec
  regenerate   Re-render a mockup from a (modified) JSON spec
"""

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "mobile-ui" / "config.json"
ENV_KEYS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")

DEFAULTS = {
    "generation_model": "gemini-3-pro-image-preview",
    "analysis_model": "gemini-2.5-flash",
    "aspect_ratio": "9:16",
    "image_size": "2K",
}

MIME_MAP = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp",
}

FRAME_INSTRUCTIONS = {
    "iphone": (
        "A single upright modern iPhone (Dynamic Island, accurate iOS status bar) held "
        "vertically, centered, filling ~94% of the frame height, resting on a very light "
        "neutral studio background (#F2F2F2) with a soft realistic shadow. "
        "Do NOT rotate the phone to landscape."
    ),
    "android": (
        "A single upright modern Android phone (Pixel-style, accurate Android status bar) "
        "held vertically, centered, filling ~94% of the frame height, resting on a very "
        "light neutral studio background (#F2F2F2) with a soft realistic shadow. "
        "Do NOT rotate the phone to landscape."
    ),
    "none": (
        "A full-bleed mobile app screen with NO device frame: edge-to-edge portrait UI "
        "that looks like a real screenshot, including a realistic mobile status bar."
    ),
}


# ── Config / client ───────────────────────────────────────────────────────────
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


def find_api_key():
    cfg = load_config()
    if cfg.get("api_key"):
        return cfg["api_key"]
    for k in ENV_KEYS:
        if os.environ.get(k):
            return os.environ[k]
    return None


def get_client():
    try:
        from google import genai
    except ImportError:
        print("ERROR: google-genai not installed. Run: pip install google-genai Pillow",
              file=sys.stderr)
        sys.exit(2)
    api_key = find_api_key()
    if not api_key:
        # Stable, greppable sentinel so the calling agent knows to ask the user.
        print("NO_API_KEY: No Gemini API key configured. Ask the user for a key "
              "(https://aistudio.google.com/apikey), then store it by piping it via "
              "stdin: printf '%s' THE_KEY | python mockup_gen.py setup "
              "(or set GEMINI_API_KEY).", file=sys.stderr)
        sys.exit(3)
    return genai.Client(api_key=api_key)


def resolve(args_value, config_key):
    if args_value:
        return args_value
    return load_config().get(config_key, DEFAULTS[config_key])


def load_image_part(image_path):
    from google.genai import types
    path = Path(image_path)
    if not path.exists():
        print(f"ERROR: reference image not found: {image_path}", file=sys.stderr)
        sys.exit(2)
    mime = MIME_MAP.get(path.suffix.lower(), "image/png")
    return types.Part.from_bytes(data=path.read_bytes(), mime_type=mime)


def image_gen_config(types, temperature, aspect, size):
    """Build a GenerateContentConfig that forces aspect ratio + size when the
    installed google-genai supports it, falling back gracefully otherwise."""
    base = dict(response_modalities=["TEXT", "IMAGE"], temperature=temperature)
    try:
        return types.GenerateContentConfig(
            image_config=types.ImageConfig(aspect_ratio=aspect, image_size=size),
            **base,
        )
    except Exception:
        return types.GenerateContentConfig(**base)


def aspect_is_portrait(aspect):
    """True when a "W:H" aspect ratio is portrait (taller than wide). Unknown or
    unparseable values default to portrait, the skill's intended orientation."""
    try:
        w, h = (float(x) for x in aspect.split(":"))
        return h >= w
    except (ValueError, AttributeError):
        return True


def save_image_from_response(response, output_path, expect_portrait=True):
    from PIL import Image
    import io
    texts = []
    for cand in response.candidates or []:
        for part in (cand.content.parts if cand.content else []) or []:
            data = getattr(getattr(part, "inline_data", None), "data", None)
            if data:
                img = Image.open(io.BytesIO(data))
                w, h = img.size
                is_portrait = h >= w
                if expect_portrait and not is_portrait:
                    # Portrait was requested but the model returned a landscape
                    # asset — fail loudly instead of saving a wrong-orientation
                    # mockup that looks like success.
                    print(f"ERROR: model returned a LANDSCAPE image ({w}x{h}); "
                          "expected portrait. Not saving. Retry, or lower "
                          "--temperature / simplify the prompt.", file=sys.stderr)
                    return False
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                img.save(output_path)
                kb = Path(output_path).stat().st_size / 1024
                orient = "portrait" if is_portrait else "landscape"
                print(f"OK: {output_path} ({w}x{h}, {orient}, {kb:.0f} KB)")
                return True
            if getattr(part, "text", None):
                texts.append(part.text)
    print("ERROR: no image in response." + (" Model said:" if texts else ""), file=sys.stderr)
    if texts:
        print("\n".join(texts)[:800], file=sys.stderr)
    return False


def response_text(response):
    """Concatenate any text parts from a Gemini response, or return None.

    Guards against safety blocks / empty candidates / non-text modalities where
    `response.text` raises or is absent, mirroring how image extraction fails soft.
    """
    parts = []
    for cand in getattr(response, "candidates", None) or []:
        content = getattr(cand, "content", None)
        for part in (getattr(content, "parts", None) or []):
            if getattr(part, "text", None):
                parts.append(part.text)
    if parts:
        return "".join(parts)
    try:
        return response.text
    except Exception:
        return None


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


# ── Commands ──────────────────────────────────────────────────────────────────
def read_api_key(args):
    """Resolve the key without exposing it via process args when possible.

    Order: --api-key (legacy) → GEMINI/GOOGLE env → stdin (getpass on a TTY,
    otherwise a piped line). Prefer stdin/env so the secret never lands in
    `ps`/`/proc` or shell history via a visible --api-key argument.
    """
    if args.api_key:
        return args.api_key.strip()
    for k in ENV_KEYS:
        if os.environ.get(k):
            return os.environ[k].strip()
    try:
        if sys.stdin.isatty():
            return getpass.getpass("Gemini API key (input hidden): ").strip()
        return sys.stdin.readline().strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def cmd_setup(args):
    key = read_api_key(args)
    if not key:
        print("ERROR: no API key provided. Pipe it via stdin "
              "(printf '%s' THE_KEY | python mockup_gen.py setup), set "
              "GEMINI_API_KEY, or pass --api-key.", file=sys.stderr)
        sys.exit(2)
    cfg = load_config()
    cfg["api_key"] = key
    if args.generation_model:
        cfg["generation_model"] = args.generation_model
    if args.analysis_model:
        cfg["analysis_model"] = args.analysis_model
    save_config(cfg)
    try:
        CONFIG_PATH.chmod(0o600)
    except OSError:
        pass
    print(f"Saved Gemini API key to {CONFIG_PATH}")
    print(f"  Generation model: {cfg.get('generation_model', DEFAULTS['generation_model'])}")
    print(f"  Analysis model:   {cfg.get('analysis_model', DEFAULTS['analysis_model'])}")


def cmd_check(args):
    cfg = load_config()
    if cfg.get("api_key"):
        print(f"CONFIGURED: key stored at {CONFIG_PATH}")
    elif any(os.environ.get(k) for k in ENV_KEYS):
        present = next(k for k in ENV_KEYS if os.environ.get(k))
        print(f"CONFIGURED: key from environment variable {present}")
    else:
        print("NOT_CONFIGURED: pipe key via stdin (printf '%s' THE_KEY | "
              "python mockup_gen.py setup) or set GEMINI_API_KEY")


def cmd_generate(args):
    from google.genai import types
    client = get_client()
    model = resolve(args.model, "generation_model")
    aspect = resolve(args.aspect, "aspect_ratio")
    size = resolve(args.size, "image_size")
    frame = FRAME_INSTRUCTIONS.get(args.frame, FRAME_INSTRUCTIONS["iphone"])

    contents = [load_image_part(p) for p in (args.refs or [])]
    lines = [
        "Generate ONE high-fidelity MOBILE APP UI mockup image.",
        f"STRICT: PORTRAIT orientation, taller than wide. {frame} "
        "Crisp legible text, pixel-accurate alignment, realistic native mobile "
        "components, real concise labels (NO lorem ipsum).",
    ]
    if args.description:
        lines.append(f"\nProject / brand context: {args.description}")
    lines.append(f"\nScreen to generate: {args.prompt}")
    if args.theme:
        lines.append(f"\nTheme: {args.theme} mode.")
    if args.colors:
        lines.append(f"\nColor palette (use exactly): {args.colors}")
    if args.style:
        lines.append(f"\nVisual style: {args.style}")
    if args.refs:
        lines.append(
            "\nUse the attached reference image(s) ONLY for brand consistency — match the "
            "same color palette, typography, component style, corner radii, iconography and "
            "overall premium aesthetic. This is a DIFFERENT screen of the SAME app.")
    contents.append("\n".join(lines))

    print(f"Generating {args.output} ({aspect}, {size}) with {model}...")
    resp = client.models.generate_content(
        model=model, contents=contents,
        config=image_gen_config(types, args.temperature, aspect, size))
    if not save_image_from_response(resp, args.output, aspect_is_portrait(aspect)):
        sys.exit(1)


def cmd_analyze(args):
    from google.genai import types
    client = get_client()
    model = resolve(args.model, "analysis_model")
    contents = [
        load_image_part(args.image),
        ("Analyze this MOBILE APP UI screenshot in extreme detail. Return ONE JSON "
         "object describing: screen_name, theme (light/dark), layout (status bar, header, "
         "body sections top→bottom, tab bar), colors (with hex), typography, every visible "
         "component (type, text, position, style), spacing, visual_effects, and the single "
         "primary action. Return ONLY valid JSON, no commentary."),
    ]
    print(f"Analyzing with {model}...")
    resp = client.models.generate_content(
        model=model, contents=contents,
        config=types.GenerateContentConfig(temperature=0.1))
    raw = response_text(resp)
    if not raw:
        print("ERROR: model returned no text (possible safety block or empty "
              "response). Try again or adjust the image.", file=sys.stderr)
        sys.exit(1)
    out_text = extract_json(raw)
    try:
        out_text = json.dumps(json.loads(out_text), indent=2)
    except json.JSONDecodeError:
        print("ERROR: model response was not valid JSON; not writing output.",
              file=sys.stderr)
        print(out_text[:800], file=sys.stderr)
        sys.exit(1)
    output = args.output or (Path(args.image).stem + "_analysis.json")
    Path(output).write_text(out_text)
    print(f"Saved {output}")


def cmd_modify_json(args):
    from google.genai import types
    client = get_client()
    model = resolve(args.model, "analysis_model")
    spec = Path(args.json_file).read_text()
    prompt = (f"Here is a JSON spec of a mobile app screen:\n\n{spec}\n\n"
              f"Apply these modifications: {args.changes}\n\n"
              "Return the COMPLETE modified JSON, keeping all unmentioned fields exactly. "
              "Return ONLY valid JSON.")
    print(f"Modifying JSON with {model}...")
    resp = client.models.generate_content(
        model=model, contents=[prompt],
        config=types.GenerateContentConfig(temperature=0.1))
    raw = response_text(resp)
    if not raw:
        print("ERROR: model returned no text (possible safety block or empty "
              "response). Try again or simplify the changes.", file=sys.stderr)
        sys.exit(1)
    out_text = extract_json(raw)
    try:
        out_text = json.dumps(json.loads(out_text), indent=2)
    except json.JSONDecodeError:
        print("ERROR: model response was not valid JSON; not writing output.",
              file=sys.stderr)
        print(out_text[:800], file=sys.stderr)
        sys.exit(1)
    output = args.output or (Path(args.json_file).stem + "_modified.json")
    Path(output).write_text(out_text)
    print(f"Saved {output}")


def cmd_regenerate(args):
    from google.genai import types
    client = get_client()
    model = resolve(args.model, "generation_model")
    aspect = resolve(args.aspect, "aspect_ratio")
    size = resolve(args.size, "image_size")
    frame = FRAME_INSTRUCTIONS.get(args.frame, FRAME_INSTRUCTIONS["iphone"])
    spec = Path(args.json_spec).read_text()

    contents = []
    if args.original:
        contents.append(load_image_part(args.original))
    contents += [load_image_part(p) for p in (args.refs or [])]
    lines = [
        "Generate ONE high-fidelity MOBILE APP UI mockup image that PRECISELY matches this "
        "design specification and looks like a real screenshot.",
        f"STRICT: PORTRAIT orientation, taller than wide. {frame}",
        f"\nDesign specification:\n{spec}",
    ]
    if args.original:
        lines.append("\nThe first attached image is the original. Keep its layout and "
                     "aesthetic; change only what the spec modifies.")
    if args.refs:
        lines.append("\nUse the other attached image(s) for brand consistency (same app).")
    if args.extra_instructions:
        lines.append(f"\nAdditional instructions: {args.extra_instructions}")
    contents.append("\n".join(lines))

    print(f"Regenerating {args.output} ({aspect}, {size}) with {model}...")
    resp = client.models.generate_content(
        model=model, contents=contents,
        config=image_gen_config(types, args.temperature, aspect, size))
    if not save_image_from_response(resp, args.output, aspect_is_portrait(aspect)):
        sys.exit(1)


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="ForwardPath Mobile UI — mockup generator")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser(
        "setup",
        help="Store the Gemini API key on this machine. Prefer piping the key via "
             "stdin or GEMINI_API_KEY over --api-key (which is visible in ps/proc).")
    sp.add_argument("--api-key", help="Legacy: visible in process args; prefer stdin/env")
    sp.add_argument("--generation-model")
    sp.add_argument("--analysis-model")

    sub.add_parser("check", help="Report whether an API key is configured")

    sp = sub.add_parser("generate", help="Generate a new portrait mobile mockup")
    sp.add_argument("--prompt", required=True)
    sp.add_argument("--refs", nargs="*", default=[])
    sp.add_argument("--colors", default="")
    sp.add_argument("--style", default="")
    sp.add_argument("--description", default="")
    sp.add_argument("--theme", default="", help="light | dark (optional)")
    sp.add_argument("--frame", default="iphone", choices=list(FRAME_INSTRUCTIONS))
    sp.add_argument("-o", "--output", required=True)
    sp.add_argument("--aspect", default="", help="default 9:16")
    sp.add_argument("--size", default="", help="1K | 2K | 4K (default 2K)")
    sp.add_argument("--temperature", type=float, default=0.35)
    sp.add_argument("--model")

    sp = sub.add_parser("analyze", help="Analyze a mockup into a JSON spec")
    sp.add_argument("image")
    sp.add_argument("-o", "--output")
    sp.add_argument("--model")

    sp = sub.add_parser("modify-json", help="Apply changes to a JSON spec")
    sp.add_argument("--json-file", required=True)
    sp.add_argument("--changes", required=True)
    sp.add_argument("-o", "--output")
    sp.add_argument("--model")

    sp = sub.add_parser("regenerate", help="Re-render a mockup from a JSON spec")
    sp.add_argument("--json-spec", required=True)
    sp.add_argument("--original")
    sp.add_argument("--refs", nargs="*", default=[])
    sp.add_argument("--extra-instructions", default="")
    sp.add_argument("--frame", default="iphone", choices=list(FRAME_INSTRUCTIONS))
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
