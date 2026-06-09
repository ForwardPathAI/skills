#!/usr/bin/env python3
"""
review-mp4 — extract in-focus, representative frames from an mp4 for an LLM to read.

Pipeline (see REFERENCE.md):
  1. resolve input (local path, or download a URL into the temp dir)
  2. ffprobe for duration / fps / rotation
  3. ffmpeg-extract candidate frames oversampled above the target rate
  4. score each candidate's sharpness = variance of the Laplacian
  5. per time window, select the sharpest candidate (the "check neighbors" behavior)
  6. dedup near-identical selected frames, cap to --max-frames
  7. write selected frames + manifest.json into the temp dir

The agent then reads the selected frames (manifest.json -> selected[]) with its
own vision to answer the user's request. No frame/video is ever uploaded anywhere.

Backends for the blur metric:
  - opencv  cv2.Laplacian(gray, CV_64F).var()      (used if OpenCV is importable)
  - numpy   discrete Laplacian via array slicing    (default; Pillow + numpy)
Absolute sharpness values are NOT comparable across backends; selection is
relative (sharpest-in-window). --threshold is an optional absolute gate.

Commands:
  process <input>   extract + score + select frames, write a manifest
  clean             remove stale review-mp4-* temp dirs older than --ttl
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TMP_PREFIX = "review-mp4-"
MARKER = ".review-mp4-created"

# Backend-specific absolute blur floors (a window's best below this is "blurry").
# These are starting points; tune per-source. See REFERENCE.md.
DEFAULT_THRESHOLD = {"opencv": 100.0, "numpy": 8.0}

IMAGE_EXT = ".jpg"


# --------------------------------------------------------------------------- #
# small utilities
# --------------------------------------------------------------------------- #
def eprint(*args):
    print(*args, file=sys.stderr)


def fail(msg, code=1):
    eprint(f"review-mp4: {msg}")
    sys.exit(code)


def have(cmd):
    return shutil.which(cmd) is not None


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def parse_duration(s):
    """Parse '24h', '90m', '3600', '1h30m' -> seconds (int)."""
    if s is None:
        return None
    s = str(s).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*([smhd])", s, re.I)
    if not matches:
        fail(f"could not parse duration: {s!r}")
    total = 0.0
    for num, unit in matches:
        total += float(num) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit.lower()]
    return total


def parse_timestamp(s):
    """Parse a seek timestamp: seconds or HH:MM:SS(.ms). Return a string ffmpeg accepts."""
    if s is None:
        return None
    return str(s)


def is_url(s):
    return bool(re.match(r"^https?://", str(s), re.I))


# --------------------------------------------------------------------------- #
# input resolution
# --------------------------------------------------------------------------- #
def resolve_input(inp, workdir):
    """Return a local path to the video. Download URLs into workdir."""
    if is_url(inp):
        dest = workdir / "input.mp4"
        if have("curl"):
            r = run(["curl", "-fsSL", "--retry", "2", "-o", str(dest), inp])
            if r.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
                eprint(r.stderr.strip())
                fail(f"failed to download {inp}")
        else:
            # ffmpeg can read the URL directly; copy the stream without re-encode.
            r = run(["ffmpeg", "-y", "-i", inp, "-c", "copy", str(dest)])
            if r.returncode != 0 or not dest.exists():
                eprint(r.stderr.strip()[-2000:])
                fail(f"failed to fetch {inp}")
        return dest
    p = Path(inp).expanduser()
    if not p.exists():
        fail(f"input not found: {inp}")
    return p


def ffprobe_info(path):
    info = {"duration": None, "fps": None, "rotation": 0}
    r = run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=avg_frame_rate,r_frame_rate:format=duration",
        "-of", "json", str(path),
    ])
    if r.returncode != 0:
        eprint(r.stderr.strip())
        return info
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return info
    fmt = data.get("format", {})
    if fmt.get("duration"):
        try:
            info["duration"] = float(fmt["duration"])
        except ValueError:
            pass
    streams = data.get("streams", [])
    if streams:
        rate = streams[0].get("avg_frame_rate") or streams[0].get("r_frame_rate")
        if rate and "/" in rate:
            num, den = rate.split("/")
            try:
                den_f = float(den)
                info["fps"] = float(num) / den_f if den_f else None
            except ValueError:
                pass
    return info


# --------------------------------------------------------------------------- #
# frame extraction
# --------------------------------------------------------------------------- #
def extract_frames(video, outdir, oversample, start, end, scene):
    """Extract candidate frames at `oversample` fps into outdir/cand-%05d.jpg.

    Also emits ffprobe-style timestamps so each candidate maps back to a video time.
    Returns a list of (path, t_seconds) sorted by time.
    """
    pattern = str(outdir / f"cand-%05d{IMAGE_EXT}")
    cmd = ["ffmpeg", "-y"]
    if start is not None:
        cmd += ["-ss", str(start)]
    if end is not None:
        cmd += ["-to", str(end)]
    cmd += ["-i", str(video)]
    # vfr fps filter gives evenly spaced frames; -frame_pts keeps ordering stable.
    vf = f"fps={oversample}"
    cmd += ["-vf", vf, "-q:v", "3", pattern]
    r = run(cmd)
    if r.returncode != 0:
        eprint(r.stderr.strip()[-2000:])
        fail("ffmpeg frame extraction failed")

    frames = sorted(outdir.glob(f"cand-*{IMAGE_EXT}"))
    if not frames:
        fail("no frames were extracted (empty or unreadable video)")

    base = parse_duration(start) if start is not None else 0.0
    step = 1.0 / oversample
    out = []
    for i, fp in enumerate(frames):
        t = (base or 0.0) + i * step
        out.append((fp, t))
    return out


# --------------------------------------------------------------------------- #
# sharpness backends
# --------------------------------------------------------------------------- #
def load_backend(requested):
    """Return (name, score_fn). score_fn(path) -> float variance-of-Laplacian."""
    want = requested or "auto"
    if want in ("auto", "opencv"):
        try:
            import cv2

            def score_cv(path):
                img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    return 0.0
                return float(cv2.Laplacian(img, cv2.CV_64F).var())

            return "opencv", score_cv
        except Exception:
            if want == "opencv":
                fail("opencv backend requested but cv2/numpy not available")

    # numpy + Pillow backend
    try:
        import numpy as np
        from PIL import Image
    except Exception:
        fail("need Pillow + numpy (pip install pillow numpy) or OpenCV")

    def score_np(path):
        try:
            with Image.open(path) as im:
                g = np.asarray(im.convert("L"), dtype=np.float64)
        except Exception:
            return 0.0
        if g.ndim != 2 or g.shape[0] < 3 or g.shape[1] < 3:
            return 0.0
        # discrete Laplacian: -4*c + up + down + left + right (interior pixels)
        c = g[1:-1, 1:-1]
        lap = (-4.0 * c) + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
        return float(lap.var())

    return "numpy", score_np


# --------------------------------------------------------------------------- #
# dedup (average-hash Hamming distance)
# --------------------------------------------------------------------------- #
def ahash(path):
    try:
        import numpy as np
        from PIL import Image
        with Image.open(path) as im:
            g = np.asarray(im.convert("L").resize((8, 8)), dtype=np.float64)
        bits = (g > g.mean()).flatten()
        val = 0
        for b in bits:
            val = (val << 1) | int(b)
        return val
    except Exception:
        return None


def hamming(a, b):
    return bin(a ^ b).count("1") if (a is not None and b is not None) else 64


# --------------------------------------------------------------------------- #
# selection
# --------------------------------------------------------------------------- #
def select_frames(scored, fps, threshold, skip_blurry, max_frames, dedup_dist):
    """scored: list of dicts {index,t,path,sharpness}. Returns the same list with
    selected/blurry/window/reason filled in, and a list of selected dicts."""
    window = 1.0 / fps if fps > 0 else 1.0
    # bucket by window index
    buckets = {}
    for f in scored:
        w = int(f["t"] // window)
        buckets.setdefault(w, []).append(f)

    chosen = []
    for w in sorted(buckets):
        cand = max(buckets[w], key=lambda x: x["sharpness"])
        cand["window"] = w
        cand["blurry"] = cand["sharpness"] < threshold
        if cand["blurry"] and skip_blurry:
            cand["selected"] = False
            cand["reason"] = "below-threshold-skipped"
            continue
        cand["selected"] = True
        cand["reason"] = "sharpest-in-window" + ("-blurry" if cand["blurry"] else "")
        chosen.append(cand)

    # dedup near-identical consecutive selections
    deduped = []
    for f in chosen:
        h = ahash(f["path"])
        f["_hash"] = h
        if deduped and hamming(deduped[-1].get("_hash"), h) <= dedup_dist:
            # keep the sharper of the two
            if f["sharpness"] > deduped[-1]["sharpness"]:
                deduped[-1]["selected"] = False
                deduped[-1]["reason"] = "deduped"
                deduped[-1] = f
            else:
                f["selected"] = False
                f["reason"] = "deduped"
            continue
        deduped.append(f)

    # cap to max_frames, evenly distributed across the timeline
    if len(deduped) > max_frames:
        keep_idx = {round(i * (len(deduped) - 1) / (max_frames - 1)) for i in range(max_frames)}
        capped = []
        for i, f in enumerate(deduped):
            if i in keep_idx:
                capped.append(f)
            else:
                f["selected"] = False
                f["reason"] = "over-max-frames"
        deduped = capped

    for f in scored:
        f.pop("_hash", None)
    selected = [f for f in scored if f.get("selected")]
    return scored, selected


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def cmd_process(args):
    if not have("ffmpeg") or not have("ffprobe"):
        fail("ffmpeg and ffprobe are required (install ffmpeg)")

    sweep_ttl(parse_duration(args.ttl), base_tmpdir())

    if args.outdir:
        workdir = Path(args.outdir).expanduser()
        workdir.mkdir(parents=True, exist_ok=True)
    else:
        workdir = Path(tempfile.mkdtemp(prefix=TMP_PREFIX, dir=base_tmpdir()))
    (workdir / MARKER).write_text(str(time.time()))

    backend_name, score_fn = load_backend(args.backend)
    threshold = args.threshold if args.threshold is not None else DEFAULT_THRESHOLD[backend_name]

    video = resolve_input(args.input, workdir)
    info = ffprobe_info(video)

    frames = extract_frames(video, workdir, args.oversample, args.start, args.end, args.scene)

    scored = []
    for i, (fp, t) in enumerate(frames):
        scored.append({
            "index": i,
            "t": round(t, 3),
            "path": str(fp),
            "sharpness": round(score_fn(fp), 4),
        })

    scored, selected = select_frames(
        scored, args.fps, threshold, args.skip_blurry, args.max_frames, args.dedup_dist
    )

    # rename selected frames to stable, ordered names; remove unselected candidates
    final = []
    for n, f in enumerate(selected):
        newp = workdir / f"frame-{n:03d}-t{f['t']:.2f}{IMAGE_EXT}"
        try:
            os.replace(f["path"], newp)
            f["path"] = str(newp)
        except OSError:
            pass
        final.append(f)
    if not args.keep_candidates:
        for f in scored:
            if not f.get("selected"):
                try:
                    p = Path(f["path"])
                    if p.name.startswith("cand-"):
                        p.unlink(missing_ok=True)
                except OSError:
                    pass

    manifest = {
        "video": str(video),
        "source": args.input,
        "duration": info["duration"],
        "source_fps": info["fps"],
        "fps_target": args.fps,
        "oversample": args.oversample,
        "backend": backend_name,
        "threshold": threshold,
        "outdir": str(workdir),
        "count_candidates": len(scored),
        "count_selected": len(final),
        "created_at": time.time(),
        "selected": [
            {k: f[k] for k in ("index", "t", "path", "sharpness", "blurry", "window", "reason")}
            for f in final
        ],
    }
    if args.keep_candidates:
        manifest["candidates"] = scored

    manifest_path = workdir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    if args.json:
        print(json.dumps({"manifest": str(manifest_path), **{k: manifest[k] for k in (
            "outdir", "backend", "count_selected", "count_candidates", "duration")}}))
    else:
        print(f"outdir: {workdir}")
        print(f"backend: {backend_name}  threshold: {threshold}")
        print(f"selected {len(final)} of {len(scored)} candidates")
        print(f"manifest: {manifest_path}")
        for f in final:
            flag = " (blurry)" if f["blurry"] else ""
            print(f"  t={f['t']:.2f}s  sharp={f['sharpness']:.2f}{flag}  {Path(f['path']).name}")
    return 0


def base_tmpdir():
    return Path(os.environ.get("TMPDIR", "/tmp"))


def sweep_ttl(ttl_seconds, base):
    """Remove stale review-mp4-* dirs older than ttl_seconds."""
    if ttl_seconds is None:
        ttl_seconds = 86400
    now = time.time()
    removed = 0
    try:
        for d in base.glob(f"{TMP_PREFIX}*"):
            if not d.is_dir():
                continue
            marker = d / MARKER
            try:
                created = float(marker.read_text()) if marker.exists() else d.stat().st_mtime
            except (OSError, ValueError):
                created = d.stat().st_mtime
            if now - created > ttl_seconds:
                shutil.rmtree(d, ignore_errors=True)
                removed += 1
    except OSError:
        pass
    return removed


def cmd_clean(args):
    base = Path(args.dir).expanduser() if args.dir else base_tmpdir()
    removed = sweep_ttl(parse_duration(args.ttl), base)
    print(f"removed {removed} stale {TMP_PREFIX}* dir(s) from {base}")
    return 0


# --------------------------------------------------------------------------- #
# argparse
# --------------------------------------------------------------------------- #
def build_parser():
    p = argparse.ArgumentParser(prog="review_mp4", description="Extract in-focus frames from an mp4.")
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("process", help="extract, score, and select frames")
    pr.add_argument("input", help="local mp4 path or http(s) URL")
    pr.add_argument("--fps", type=float, default=1.0, help="target selected frames per second (default 1)")
    pr.add_argument("--oversample", type=int, default=3, help="candidate extraction fps multiplier (default 3)")
    pr.add_argument("--max-frames", type=int, default=24, dest="max_frames", help="max selected frames (default 24)")
    pr.add_argument("--threshold", type=float, default=None, help="absolute blur floor (backend-specific default)")
    pr.add_argument("--skip-blurry", action="store_true", dest="skip_blurry", help="drop windows whose best is below threshold")
    pr.add_argument("--scene", type=float, default=0.3, help="scene-change sensitivity hint (reserved; default 0.3)")
    pr.add_argument("--dedup-dist", type=int, default=4, dest="dedup_dist", help="avg-hash Hamming distance for dedup (default 4)")
    pr.add_argument("--start", default=None, help="start timestamp (s or HH:MM:SS)")
    pr.add_argument("--end", default=None, help="end timestamp (s or HH:MM:SS)")
    pr.add_argument("--outdir", default=None, help="output dir (default: a fresh temp dir)")
    pr.add_argument("--keep-candidates", action="store_true", dest="keep_candidates", help="keep + record all candidate frames")
    pr.add_argument("--ttl", default="24h", help="TTL sweep window for stale temp dirs (default 24h)")
    pr.add_argument("--backend", choices=["auto", "opencv", "numpy"], default="auto", help="sharpness backend (default auto)")
    pr.add_argument("--json", action="store_true", help="print a JSON summary line")
    pr.set_defaults(func=cmd_process)

    cl = sub.add_parser("clean", help="remove stale review-mp4-* temp dirs")
    cl.add_argument("--ttl", default="24h", help="max age before removal (default 24h)")
    cl.add_argument("--dir", default=None, help="base temp dir to sweep (default $TMPDIR or /tmp)")
    cl.set_defaults(func=cmd_clean)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
