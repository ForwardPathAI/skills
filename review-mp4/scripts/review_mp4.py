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


def clock_to_seconds(s):
    """Parse seconds ('12', '1.5') or clock ('HH:MM:SS(.ms)', 'MM:SS') -> float seconds."""
    s = str(s).strip()
    if ":" in s:
        try:
            parts = [float(p) for p in s.split(":")]
        except ValueError:
            fail(f"bad timestamp: {s!r}")
        sec = 0.0
        for p in parts:
            sec = sec * 60 + p
        return sec
    try:
        return float(s)
    except ValueError:
        fail(f"bad timestamp: {s!r}")


def resolve_time(token, duration):
    """Resolve a time token to absolute seconds.

    Accepts: seconds, HH:MM:SS / MM:SS, 'start'/'begin', 'end'/'eof', and
    end-relative 'end-10' / 'end+5' (the offset itself may be seconds or clock).
    Returns None only for 'end' when duration is unknown (meaning "to EOF").
    """
    if token is None:
        return None
    t = str(token).strip().lower()
    if t in ("start", "begin", "beginning", ""):
        return 0.0
    if t in ("end", "eof"):
        return duration  # None -> caller treats as EOF (no -t/-to)
    if t.startswith("end-") or t.startswith("end+"):
        if duration is None:
            fail(f"end-relative timestamp {token!r} used but video duration is unknown")
        sign = -1.0 if t[3] == "-" else 1.0
        return max(0.0, duration + sign * clock_to_seconds(t[4:]))
    return clock_to_seconds(t)


def parse_ranges(range_args, start, end, duration):
    """Build a sorted list of (start_sec, end_sec) ranges from --range / --start/--end.

    --range accepts LO..HI (or LO,HI); each bound goes through resolve_time. A missing
    bound defaults to start/end. With no ranges at all, returns the whole video.
    """
    raw = []
    for r in range_args or []:
        sep = ".." if ".." in r else ("," if "," in r else None)
        if not sep:
            fail(f"range must be LO..HI (got {r!r})")
        lo, hi = r.split(sep, 1)
        raw.append((lo.strip() or "start", hi.strip() or "end"))
    if start is not None or end is not None:
        raw.append((start if start is not None else "start",
                    end if end is not None else "end"))
    if not raw:
        raw.append(("start", "end"))

    resolved = []
    for lo, hi in raw:
        s = resolve_time(lo, duration)
        e = resolve_time(hi, duration)
        if s is not None and e is not None and e <= s:
            fail(f"range end ({hi}) must be after start ({lo})")
        resolved.append((s, e))
    resolved.sort(key=lambda x: (x[0] if x[0] is not None else 0.0))
    return resolved


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
def extract_ranges(video, outdir, cand_fps, ranges):
    """Extract candidate frames at `cand_fps` frames/sec for each (start_sec, end_sec) range.

    `cand_fps` is the target rate (`--fps * --oversample`) so each `1/--fps` window holds
    `--oversample` candidates. Each range gets its own subdir (r0, r1, ...). Candidate
    timestamps are absolute (range_start + i/cand_fps). Returns dicts {path, t, range}.
    """
    step = 1.0 / cand_fps
    frames = []
    for ri, (s, e) in enumerate(ranges):
        sub = outdir / f"r{ri}"
        sub.mkdir(parents=True, exist_ok=True)
        pattern = str(sub / f"cand-%05d{IMAGE_EXT}")
        cmd = ["ffmpeg", "-y"]
        # -ss before -i = fast seek; pair with -t (duration) so -to is unambiguous.
        if s is not None and s > 0:
            cmd += ["-ss", f"{s:.3f}"]
        if e is not None:
            cmd += ["-t", f"{max(0.0, e - (s or 0.0)):.3f}"]
        cmd += ["-i", str(video), "-vf", f"fps={cand_fps:g}", "-q:v", "3", pattern]
        r = run(cmd)
        if r.returncode != 0:
            eprint(r.stderr.strip()[-2000:])
            fail("ffmpeg frame extraction failed")
        base = s or 0.0
        for i, fp in enumerate(sorted(sub.glob(f"cand-*{IMAGE_EXT}"))):
            frames.append({"path": fp, "t": base + i * step, "range": ri})

    if not frames:
        fail("no frames were extracted (empty or unreadable video, or empty range)")
    frames.sort(key=lambda f: f["t"])
    return frames


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
        if max_frames <= 1:
            keep_idx = {0}
        else:
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
    if args.fps <= 0:
        fail("--fps must be > 0")
    if args.oversample < 1:
        fail("--oversample must be >= 1")
    if args.max_frames < 1:
        fail("--max-frames must be >= 1")

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

    ranges = parse_ranges(args.ranges_arg, args.start, args.end, info["duration"])
    frames = extract_ranges(video, workdir, args.fps * args.oversample, ranges)

    scored = []
    for i, fr in enumerate(frames):
        scored.append({
            "index": i,
            "t": round(fr["t"], 3),
            "range": fr["range"],
            "path": str(fr["path"]),
            "sharpness": round(score_fn(fr["path"]), 4),
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
    # drop now-empty per-range subdirs
    for sub in workdir.glob("r*"):
        if sub.is_dir():
            try:
                sub.rmdir()
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
        "ranges": [
            {"index": i,
             "start": round(s, 3) if s is not None else 0.0,
             "end": round(e, 3) if e is not None else info["duration"]}
            for i, (s, e) in enumerate(ranges)
        ],
        "count_candidates": len(scored),
        "count_selected": len(final),
        "created_at": time.time(),
        "selected": [
            {k: f[k] for k in ("index", "t", "range", "path", "sharpness", "blurry", "window", "reason")}
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
        rng_desc = ", ".join(
            f"[{m['start']:.1f}s-" + (f"{m['end']:.1f}s]" if m["end"] is not None else "EOF]")
            for m in manifest["ranges"]
        )
        print(f"ranges: {rng_desc}")
        print(f"selected {len(final)} of {len(scored)} candidates")
        print(f"manifest: {manifest_path}")
        for f in final:
            flag = " (blurry)" if f["blurry"] else ""
            print(f"  r{f['range']} t={f['t']:.2f}s  sharp={f['sharpness']:.2f}{flag}  {Path(f['path']).name}")
    return 0


def base_tmpdir():
    return Path(os.environ.get("TMPDIR") or tempfile.gettempdir())


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
    pr.add_argument("--range", action="append", dest="ranges_arg", metavar="LO..HI",
                    help="time range LO..HI (repeatable). Bounds accept seconds, HH:MM:SS, "
                         "start, end, or end-relative like end-10. E.g. --range 0..10 --range end-10..end")
    pr.add_argument("--start", default=None, help="single-range start (seconds, HH:MM:SS, or end-N)")
    pr.add_argument("--end", default=None, help="single-range end (seconds, HH:MM:SS, end, or end-N)")
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
