#!/usr/bin/env python3
"""
review-mp4 — extract in-focus, representative frames from an mp4 for an LLM to read.

Pipeline (see REFERENCE.md):
  1. resolve input (local path, or download a URL into the temp dir)
  2. ffprobe for duration / fps / rotation
  3. ffmpeg-extract candidate frames oversampled above the target rate
  4. score each candidate's sharpness = variance of the Laplacian
  5. per time window, select the sharpest candidate (the "check neighbors" behavior)
  6. segment: collapse consecutive same-looking frames into one representative that
     covers a time span (dHash prefilter + tiled block-diff confirm), cap to --max-frames
  7. write representative frames + manifest.json (with coverage) into the temp dir

The agent then reads the representative frames (manifest.json -> selected[]) with its
own vision to answer the user's request, telling the model each frame's coverage span.
No frame/video is ever uploaded anywhere.

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

# Segmentation similarity presets. The agent picks --profile per video (see SKILL.md).
# - screencast: sensitive tiled diff so localized UI changes (typing, menus) split.
# - video:      coarser so constant natural motion does not over-segment.
PROFILES = {
    "screencast": {"hash_dist": 6, "diff_thresh": 0.06, "block_grid": 8, "min_blocks": 2},
    "video": {"hash_dist": 8, "diff_thresh": 0.12, "block_grid": 4, "min_blocks": 1},
}
DEFAULT_PROFILE = "screencast"
THUMB_SIZE = 64  # grayscale thumbnail edge used for the tiled block-diff


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
# similarity (dHash prefilter + tiled block-diff confirm)
# --------------------------------------------------------------------------- #
def frame_fingerprint(path):
    """Compute (dhash:int|None, thumb:2D float array 0-1 | None) once per frame.

    dHash: 9x8 grayscale, 64 bits comparing horizontal neighbors (brightness-robust).
    thumb: THUMB_SIZE x THUMB_SIZE grayscale normalized to 0-1 for the tiled diff.
    """
    try:
        import numpy as np
        from PIL import Image
        with Image.open(path) as im:
            gray = im.convert("L")
            dh = np.asarray(gray.resize((9, 8)), dtype=np.int16)
            thumb = np.asarray(
                gray.resize((THUMB_SIZE, THUMB_SIZE)), dtype=np.float64
            ) / 255.0
        diff = dh[:, 1:] > dh[:, :-1]
        val = 0
        for b in diff.flatten():
            val = (val << 1) | int(b)
        return val, thumb
    except Exception:
        return None, None


def hamming(a, b):
    return bin(a ^ b).count("1") if (a is not None and b is not None) else 64


def changed_blocks(thumb_a, thumb_b, grid, diff_thresh):
    """Count NxN grid blocks whose normalized mean-abs-difference exceeds diff_thresh.

    Returns (changed_count, max_block_diff). A localized change saturates a few blocks
    even when the whole-frame average is ~0, so typing/menus register while a static
    page does not. Returns a large count when fingerprints are missing (treat as
    different = safe).
    """
    if thumb_a is None or thumb_b is None:
        return grid * grid, 1.0
    import numpy as np
    step = THUMB_SIZE // grid
    changed = 0
    max_diff = 0.0
    for by in range(grid):
        for bx in range(grid):
            y0, x0 = by * step, bx * step
            a = thumb_a[y0:y0 + step, x0:x0 + step]
            b = thumb_b[y0:y0 + step, x0:x0 + step]
            d = float(np.abs(a - b).mean())
            if d > max_diff:
                max_diff = d
            if d > diff_thresh:
                changed += 1
    return changed, max_diff


# --------------------------------------------------------------------------- #
# selection
# --------------------------------------------------------------------------- #
def select_frames(scored, fps, threshold, skip_blurry, max_frames, seg):
    """Pick the sharpest frame per 1/fps window, then collapse consecutive
    same-looking windows into segments and emit one representative per segment.

    scored: list of dicts {index,t,range,path,sharpness}. `seg` carries the
    segmentation knobs: segment(bool), hash_dist, diff_thresh, block_grid,
    min_blocks, max_segment_seconds, duration(video length or None).

    Returns (scored, selected) where each selected (representative) dict has
    selected/blurry/window/reason plus coverage: segment_start, segment_end,
    duration, represents.
    """
    window = 1.0 / fps if fps > 0 else 1.0
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
        cand["selected"] = False  # decided during segmentation below
        chosen.append(cand)

    segment_enabled = seg["segment"]
    hash_dist = seg["hash_dist"]
    diff_thresh = seg["diff_thresh"]
    grid = max(1, min(THUMB_SIZE, seg["block_grid"]))
    min_blocks = seg["min_blocks"]
    max_seg_s = seg["max_segment_seconds"]
    duration = seg.get("duration")

    for f in chosen:
        f["_fp"] = frame_fingerprint(f["path"])

    # build segments of consecutive same-looking windows (within a range)
    segments = []
    cur = None
    for f in chosen:
        w = f["window"]
        win_start = w * window
        win_end = (w + 1) * window
        fp_hash, fp_thumb = f["_fp"]
        start_new = cur is None or f["range"] != cur["range"]
        if not start_new:
            if not segment_enabled:
                start_new = True
            else:
                anchor_hash, anchor_thumb = cur["anchor_fp"]
                same = hamming(anchor_hash, fp_hash) <= hash_dist
                if same:
                    cb, _ = changed_blocks(anchor_thumb, fp_thumb, grid, diff_thresh)
                    if cb >= min_blocks:
                        same = False
                if not same:
                    start_new = True
                elif max_seg_s and (win_end - cur["start"]) > max_seg_s:
                    start_new = True
        if start_new:
            cur = {
                "range": f["range"],
                "anchor_fp": (fp_hash, fp_thumb),
                "start": win_start,
                "end": win_end,
                "frames": [f],
                "rep": f,
            }
            segments.append(cur)
        else:
            cur["frames"].append(f)
            cur["end"] = win_end
            if f["sharpness"] > cur["rep"]["sharpness"]:
                cur["rep"] = f

    # one representative (the sharpest) per segment, annotated with coverage
    reps = []
    for s in segments:
        rep = s["rep"]
        start = round(s["start"], 3)
        end = round(min(s["end"], duration) if duration else s["end"], 3)
        rep["selected"] = True
        rep["reason"] = "segment-representative"
        rep["segment_start"] = start
        rep["segment_end"] = end
        rep["duration"] = round(max(0.0, end - start), 3)
        rep["represents"] = len(s["frames"])
        for f in s["frames"]:
            if f is not rep:
                f["selected"] = False
                f["reason"] = "merged-into-segment"
        reps.append(rep)

    # cap representatives to max_frames, evenly distributed across the timeline
    if len(reps) > max_frames:
        if max_frames <= 1:
            keep_idx = {0}
        else:
            keep_idx = {round(i * (len(reps) - 1) / (max_frames - 1)) for i in range(max_frames)}
        kept = []
        for i, rep in enumerate(reps):
            if i in keep_idx:
                kept.append(rep)
            else:
                rep["selected"] = False
                rep["reason"] = "over-max-frames"
        reps = kept

    for f in scored:
        f.pop("_fp", None)
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

    # Resolve segmentation knobs from the profile; explicit flags override.
    preset = PROFILES[args.profile]
    hash_dist = args.hash_dist if args.hash_dist is not None else preset["hash_dist"]
    diff_thresh = args.diff_thresh if args.diff_thresh is not None else preset["diff_thresh"]
    block_grid = args.block_grid if args.block_grid is not None else preset["block_grid"]
    min_blocks = args.min_blocks if args.min_blocks is not None else preset["min_blocks"]
    if hash_dist < 0:
        fail("--hash-dist must be >= 0")
    if not (0.0 <= diff_thresh <= 1.0):
        fail("--diff-thresh must be between 0 and 1")
    if block_grid < 1:
        fail("--block-grid must be >= 1")
    if min_blocks < 1:
        fail("--min-blocks must be >= 1")
    if args.max_segment_seconds < 0:
        fail("--max-segment-seconds must be >= 0")

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
        scored, args.fps, threshold, args.skip_blurry, args.max_frames,
        {
            "segment": not args.no_segment,
            "hash_dist": hash_dist,
            "diff_thresh": diff_thresh,
            "block_grid": block_grid,
            "min_blocks": min_blocks,
            "max_segment_seconds": args.max_segment_seconds,
            "duration": info["duration"],
        },
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
        "profile": args.profile,
        "segment": not args.no_segment,
        "hash_dist": hash_dist,
        "diff_thresh": diff_thresh,
        "block_grid": block_grid,
        "min_blocks": min_blocks,
        "max_segment_seconds": args.max_segment_seconds,
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
            {k: f[k] for k in (
                "index", "t", "range", "path", "sharpness", "blurry", "window", "reason",
                "segment_start", "segment_end", "duration", "represents")}
            for f in final
        ],
    }
    if args.keep_candidates:
        manifest["candidates"] = scored

    manifest_path = workdir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    if args.json:
        print(json.dumps({"manifest": str(manifest_path), **{k: manifest[k] for k in (
            "outdir", "backend", "profile", "count_selected", "count_candidates", "duration")}}))
    else:
        print(f"outdir: {workdir}")
        print(f"backend: {backend_name}  threshold: {threshold}  profile: {args.profile}"
              + ("" if not args.no_segment else "  (segmentation off)"))
        rng_desc = ", ".join(
            f"[{m['start']:.1f}s-" + (f"{m['end']:.1f}s]" if m["end"] is not None else "EOF]")
            for m in manifest["ranges"]
        )
        print(f"ranges: {rng_desc}")
        print(f"selected {len(final)} representative(s) of {len(scored)} candidates")
        print(f"manifest: {manifest_path}")
        for f in final:
            flag = " (blurry)" if f["blurry"] else ""
            covers = (f" covers {f['segment_start']:.1f}-{f['segment_end']:.1f}s "
                      f"(~{f['duration']:.0f}s, {f['represents']} frames)")
            print(f"  r{f['range']} t={f['t']:.2f}s  sharp={f['sharpness']:.2f}{flag}{covers}")
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
    # segmentation (collapse consecutive same-looking frames into time spans)
    pr.add_argument("--profile", choices=list(PROFILES), default=DEFAULT_PROFILE,
                    help="similarity preset: screencast (sensitive, default) or video (coarser)")
    pr.add_argument("--hash-dist", type=int, default=None, dest="hash_dist",
                    help="stage-1 dHash Hamming threshold (overrides profile)")
    pr.add_argument("--dedup-dist", type=int, default=None, dest="hash_dist",
                    help="deprecated alias of --hash-dist")
    pr.add_argument("--diff-thresh", type=float, default=None, dest="diff_thresh",
                    help="stage-2 per-block normalized diff threshold 0-1 (overrides profile)")
    pr.add_argument("--block-grid", type=int, default=None, dest="block_grid",
                    help="stage-2 NxN block grid over a 64x64 thumbnail (overrides profile)")
    pr.add_argument("--min-blocks", type=int, default=None, dest="min_blocks",
                    help="changed blocks that count as a real change; cursor-jitter floor (overrides profile)")
    pr.add_argument("--max-segment-seconds", type=float, default=0.0, dest="max_segment_seconds",
                    help="force a fresh representative after this many seconds (default 0 = unbounded)")
    pr.add_argument("--no-segment", action="store_true", dest="no_segment",
                    help="disable segmentation; emit one frame per kept window")
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
