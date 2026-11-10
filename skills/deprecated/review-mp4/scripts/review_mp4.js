#!/usr/bin/env node
/*
 * review-mp4 (Node fallback) — extract in-focus, representative frames from an mp4.
 *
 * Mirrors review_mp4.py's CLI and manifest exactly so the skill can use whichever
 * runtime is available. The blur metric is the variance of the Laplacian, computed
 * with `sharp` (greyscale -> 3x3 Laplacian convolution -> variance), as described in
 * https://www.linkedin.com/pulse/pinpointing-blurry-images-simple-nodejs-way-pablo-schaffner-bofill/
 *
 * Absolute sharpness values are NOT comparable to the Python backend (sharp convolves
 * clamped 8-bit bytes). Selection is relative (sharpest-in-window); --threshold is an
 * optional absolute gate with a node-specific default.
 *
 * Commands:
 *   process <input>   extract + score + select frames, write a manifest
 *   clean             remove stale review-mp4-* temp dirs older than --ttl
 *
 * Requires: ffmpeg + ffprobe on PATH, and the `sharp` npm package (npm install in
 * this scripts dir installs it).
 */

"use strict";

const { spawnSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const TMP_PREFIX = "review-mp4-";
const MARKER = ".review-mp4-created";
const IMAGE_EXT = ".jpg";
const DEFAULT_THRESHOLD_NODE = 4.0; // sharp/clamped-byte Laplacian variance floor

// Segmentation similarity presets. The agent picks --profile per video (see SKILL.md).
const PROFILES = {
  screencast: { hash_dist: 6, diff_thresh: 0.06, block_grid: 8, min_blocks: 2 },
  video: { hash_dist: 8, diff_thresh: 0.12, block_grid: 4, min_blocks: 1 },
};
const DEFAULT_PROFILE = "screencast";
const THUMB_SIZE = 64; // grayscale thumbnail edge for the tiled block-diff

// --------------------------------------------------------------------------- //
// utilities
// --------------------------------------------------------------------------- //
function eprint(...a) {
  process.stderr.write(a.join(" ") + "\n");
}
function fail(msg, code = 1) {
  eprint(`review-mp4: ${msg}`);
  process.exit(code);
}
function have(cmd) {
  const r = spawnSync(process.platform === "win32" ? "where" : "which", [cmd]);
  return r.status === 0;
}
function run(cmd, args) {
  return spawnSync(cmd, args, { encoding: "utf8", maxBuffer: 1 << 26 });
}
function baseTmpdir() {
  return process.env.TMPDIR || os.tmpdir() || "/tmp";
}
function isUrl(s) {
  return /^https?:\/\//i.test(String(s));
}

function parseDuration(s) {
  if (s == null) return null;
  s = String(s).trim();
  if (/^\d+(\.\d+)?$/.test(s)) return parseFloat(s);
  let total = 0;
  let any = false;
  const re = /(\d+(?:\.\d+)?)\s*([smhd])/gi;
  let m;
  const mult = { s: 1, m: 60, h: 3600, d: 86400 };
  while ((m = re.exec(s)) !== null) {
    any = true;
    total += parseFloat(m[1]) * mult[m[2].toLowerCase()];
  }
  if (!any) fail(`could not parse duration: ${s}`);
  return total;
}

function clockToSeconds(s) {
  s = String(s).trim();
  if (s.includes(":")) {
    let sec = 0;
    for (const p of s.split(":")) {
      const v = parseFloat(p);
      if (Number.isNaN(v)) fail(`bad timestamp: ${s}`);
      sec = sec * 60 + v;
    }
    return sec;
  }
  const v = parseFloat(s);
  if (Number.isNaN(v)) fail(`bad timestamp: ${s}`);
  return v;
}

// Resolve a time token to absolute seconds. Supports seconds, HH:MM:SS / MM:SS,
// 'start'/'begin', 'end'/'eof', and end-relative 'end-10' / 'end+5'.
// Returns null only for 'end' when duration is unknown (meaning "to EOF").
function resolveTime(token, duration) {
  if (token == null) return null;
  const t = String(token).trim().toLowerCase();
  if (t === "start" || t === "begin" || t === "beginning" || t === "") return 0.0;
  if (t === "end" || t === "eof") return duration; // null -> EOF
  if (t.startsWith("end-") || t.startsWith("end+")) {
    if (duration == null) fail(`end-relative timestamp '${token}' used but video duration is unknown`);
    const sign = t[3] === "-" ? -1 : 1;
    return Math.max(0.0, duration + sign * clockToSeconds(t.slice(4)));
  }
  return clockToSeconds(t);
}

// Build a sorted list of [startSec, endSec] ranges from --range / --start/--end.
function parseRanges(rangeArgs, start, end, duration) {
  const raw = [];
  for (const r of rangeArgs || []) {
    const sep = r.includes("..") ? ".." : r.includes(",") ? "," : null;
    if (!sep) fail(`range must be LO..HI (got ${r})`);
    const idx = r.indexOf(sep);
    raw.push([r.slice(0, idx).trim() || "start", r.slice(idx + sep.length).trim() || "end"]);
  }
  if (start != null || end != null) raw.push([start != null ? start : "start", end != null ? end : "end"]);
  if (raw.length === 0) raw.push(["start", "end"]);

  const resolved = [];
  for (const [lo, hi] of raw) {
    const s = resolveTime(lo, duration);
    const e = resolveTime(hi, duration);
    if (s != null && e != null && e <= s) fail(`range end (${hi}) must be after start (${lo})`);
    resolved.push([s, e]);
  }
  resolved.sort((a, b) => (a[0] == null ? 0 : a[0]) - (b[0] == null ? 0 : b[0]));
  return resolved;
}

// minimal arg parser: flags with values, boolean flags, repeatable flags, one positional
function parseArgs(argv, spec) {
  const out = { _: [] };
  const multi = spec.multi || [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      if (spec.bools.includes(key)) {
        out[key] = true;
      } else if (multi.includes(key)) {
        (out[key] = out[key] || []).push(argv[++i]);
      } else {
        out[key] = argv[++i];
      }
    } else {
      out._.push(a);
    }
  }
  return out;
}

// --------------------------------------------------------------------------- //
// input + probe
// --------------------------------------------------------------------------- //
function resolveInput(inp, workdir) {
  if (isUrl(inp)) {
    const dest = path.join(workdir, "input.mp4");
    if (have("curl")) {
      const r = run("curl", ["-fsSL", "--retry", "2", "-o", dest, inp]);
      if (r.status !== 0 || !fs.existsSync(dest) || fs.statSync(dest).size === 0) {
        eprint((r.stderr || "").trim());
        fail(`failed to download ${inp}`);
      }
    } else {
      const r = run("ffmpeg", ["-y", "-i", inp, "-c", "copy", dest]);
      if (r.status !== 0 || !fs.existsSync(dest)) {
        eprint((r.stderr || "").slice(-2000));
        fail(`failed to fetch ${inp}`);
      }
    }
    return dest;
  }
  let p = inp;
  if (inp === "~") p = os.homedir();
  else if (inp.startsWith("~/")) p = path.join(os.homedir(), inp.slice(2));
  if (!fs.existsSync(p)) fail(`input not found: ${inp}`);
  return p;
}

function ffprobeInfo(video) {
  const info = { duration: null, fps: null };
  const r = run("ffprobe", [
    "-v", "error", "-select_streams", "v:0",
    "-show_entries", "stream=avg_frame_rate,r_frame_rate:format=duration",
    "-of", "json", video,
  ]);
  if (r.status !== 0) return info;
  let data;
  try {
    data = JSON.parse(r.stdout);
  } catch (e) {
    return info;
  }
  if (data.format && data.format.duration) {
    const d = parseFloat(data.format.duration);
    if (!Number.isNaN(d)) info.duration = d;
  }
  const st = (data.streams || [])[0];
  if (st) {
    const rate = st.avg_frame_rate || st.r_frame_rate;
    if (rate && rate.includes("/")) {
      const [num, den] = rate.split("/").map(Number);
      if (den) info.fps = num / den;
    }
  }
  return info;
}

// --------------------------------------------------------------------------- //
// extraction
// --------------------------------------------------------------------------- //
function extractRanges(video, workdir, candFps, ranges) {
  // candFps is the target rate (--fps * --oversample) so each 1/--fps window holds
  // --oversample candidates. Candidate timestamps are absolute (range_start + i/candFps).
  const step = 1 / candFps;
  const frames = [];
  ranges.forEach(([s, e], ri) => {
    const sub = path.join(workdir, `r${ri}`);
    fs.mkdirSync(sub, { recursive: true });
    const pattern = path.join(sub, `cand-%05d${IMAGE_EXT}`);
    const cmd = ["-y"];
    // -ss before -i = fast seek; pair with -t (duration) so the range is unambiguous.
    if (s != null && s > 0) cmd.push("-ss", s.toFixed(3));
    if (e != null) cmd.push("-t", Math.max(0, e - (s || 0)).toFixed(3));
    cmd.push("-i", video, "-vf", `fps=${candFps}`, "-q:v", "3", pattern);
    const r = run("ffmpeg", cmd);
    if (r.status !== 0) {
      eprint((r.stderr || "").slice(-2000));
      fail("ffmpeg frame extraction failed");
    }
    const base = s || 0;
    fs.readdirSync(sub)
      .filter((f) => f.startsWith("cand-") && f.endsWith(IMAGE_EXT))
      .sort()
      .forEach((f, i) => frames.push({ path: path.join(sub, f), t: base + i * step, range: ri }));
  });
  if (frames.length === 0) fail("no frames were extracted (empty or unreadable video, or empty range)");
  frames.sort((a, b) => a.t - b.t);
  return frames;
}

// --------------------------------------------------------------------------- //
// sharpness (variance of Laplacian) via sharp
// --------------------------------------------------------------------------- //
let sharp;
function loadSharp() {
  if (sharp) return sharp;
  try {
    sharp = require("sharp");
  } catch (e) {
    fail("the 'sharp' package is required (run: npm install in this scripts dir)");
  }
  return sharp;
}

async function scoreSharpness(imgPath) {
  const s = loadSharp();
  const laplacianKernel = { width: 3, height: 3, kernel: [0, 1, 0, 1, -4, 1, 0, 1, 0] };
  let buf;
  try {
    buf = await s(imgPath).greyscale().raw().convolve(laplacianKernel).toBuffer();
  } catch (e) {
    return 0.0;
  }
  let sum = 0;
  for (let i = 0; i < buf.length; i++) sum += buf[i];
  const mean = sum / buf.length;
  let varSum = 0;
  for (let i = 0; i < buf.length; i++) {
    const d = buf[i] - mean;
    varSum += d * d;
  }
  return varSum / buf.length;
}

// Compute { hash:{hi,lo}|null, thumb:Float64Array|null } once per frame.
// dHash: 9x8 grayscale, 64 bits comparing horizontal neighbors (brightness-robust).
// thumb: THUMB_SIZE x THUMB_SIZE grayscale normalized 0-1 for the tiled diff.
async function frameFingerprint(imgPath) {
  const s = loadSharp();
  let dh;
  let tb;
  try {
    dh = await s(imgPath).greyscale().resize(9, 8, { fit: "fill" }).raw().toBuffer();
    tb = await s(imgPath).greyscale().resize(THUMB_SIZE, THUMB_SIZE, { fit: "fill" }).raw().toBuffer();
  } catch (e) {
    return { hash: null, thumb: null };
  }
  let hi = 0n;
  let lo = 0n;
  let bit = 0;
  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const idx = row * 9 + col;
      const b = dh[idx + 1] > dh[idx] ? 1n : 0n;
      if (bit < 32) hi = (hi << 1n) | b;
      else lo = (lo << 1n) | b;
      bit++;
    }
  }
  const thumb = new Float64Array(THUMB_SIZE * THUMB_SIZE);
  for (let i = 0; i < thumb.length; i++) thumb[i] = tb[i] / 255.0;
  return { hash: { hi, lo }, thumb };
}

function hamming(a, b) {
  if (!a || !b) return 64;
  const popc = (x) => {
    let c = 0;
    while (x) {
      x &= x - 1n;
      c++;
    }
    return c;
  };
  return popc(a.hi ^ b.hi) + popc(a.lo ^ b.lo);
}

// Count NxN grid blocks whose normalized mean-abs-difference exceeds diffThresh.
// A localized change saturates a few blocks even when the whole-frame average is ~0.
function changedBlocks(thumbA, thumbB, grid, diffThresh) {
  if (!thumbA || !thumbB) return grid * grid;
  const step = Math.max(1, Math.floor(THUMB_SIZE / grid));
  let changed = 0;
  for (let by = 0; by < grid; by++) {
    for (let bx = 0; bx < grid; bx++) {
      let sum = 0;
      let n = 0;
      for (let y = by * step; y < by * step + step && y < THUMB_SIZE; y++) {
        for (let x = bx * step; x < bx * step + step && x < THUMB_SIZE; x++) {
          const idx = y * THUMB_SIZE + x;
          sum += Math.abs(thumbA[idx] - thumbB[idx]);
          n++;
        }
      }
      if (n > 0 && sum / n > diffThresh) changed++;
    }
  }
  return changed;
}

// --------------------------------------------------------------------------- //
// selection (mirrors review_mp4.py)
// --------------------------------------------------------------------------- //
async function selectFrames(scored, fps, threshold, skipBlurry, maxFrames, seg) {
  const window = fps > 0 ? 1 / fps : 1;
  const buckets = new Map();
  for (const f of scored) {
    const w = Math.floor(f.t / window);
    if (!buckets.has(w)) buckets.set(w, []);
    buckets.get(w).push(f);
  }

  const chosen = [];
  for (const w of [...buckets.keys()].sort((a, b) => a - b)) {
    const cand = buckets.get(w).reduce((a, b) => (b.sharpness > a.sharpness ? b : a));
    cand.window = w;
    cand.blurry = cand.sharpness < threshold;
    if (cand.blurry && skipBlurry) {
      cand.selected = false;
      cand.reason = "below-threshold-skipped";
      continue;
    }
    cand.selected = false; // decided during segmentation below
    chosen.push(cand);
  }

  const grid = Math.max(1, Math.min(THUMB_SIZE, seg.block_grid));
  for (const f of chosen) f._fp = await frameFingerprint(f.path);

  // build segments of consecutive same-looking windows (within a range)
  const segments = [];
  let cur = null;
  for (const f of chosen) {
    const winStart = f.window * window;
    const winEnd = (f.window + 1) * window;
    let startNew = cur === null || f.range !== cur.range;
    if (!startNew) {
      if (!seg.segment) {
        startNew = true;
      } else {
        let same = hamming(cur.anchor.hash, f._fp.hash) <= seg.hash_dist;
        if (same && changedBlocks(cur.anchor.thumb, f._fp.thumb, grid, seg.diff_thresh) >= seg.min_blocks) {
          same = false;
        }
        if (!same) startNew = true;
        else if (seg.max_segment_seconds && winEnd - cur.start > seg.max_segment_seconds) startNew = true;
      }
    }
    if (startNew) {
      cur = { range: f.range, anchor: f._fp, start: winStart, end: winEnd, frames: [f], rep: f };
      segments.push(cur);
    } else {
      cur.frames.push(f);
      cur.end = winEnd;
      if (f.sharpness > cur.rep.sharpness) cur.rep = f;
    }
  }

  // one representative (sharpest) per segment, annotated with coverage
  let reps = [];
  for (const s of segments) {
    const rep = s.rep;
    const start = Math.round(s.start * 1000) / 1000;
    const end = Math.round((seg.duration != null ? Math.min(s.end, seg.duration) : s.end) * 1000) / 1000;
    rep.selected = true;
    rep.reason = "segment-representative";
    rep.segment_start = start;
    rep.segment_end = end;
    rep.duration = Math.round(Math.max(0, end - start) * 1000) / 1000;
    rep.represents = s.frames.length;
    for (const f of s.frames) {
      if (f !== rep) {
        f.selected = false;
        f.reason = "merged-into-segment";
      }
    }
    reps.push(rep);
  }

  if (reps.length > maxFrames) {
    const keep = new Set();
    if (maxFrames <= 1) {
      keep.add(0);
    } else {
      for (let i = 0; i < maxFrames; i++) {
        keep.add(Math.round((i * (reps.length - 1)) / (maxFrames - 1)));
      }
    }
    reps.forEach((rep, i) => {
      if (!keep.has(i)) {
        rep.selected = false;
        rep.reason = "over-max-frames";
      }
    });
  }

  for (const f of scored) delete f._fp;
  return scored.filter((f) => f.selected);
}

// --------------------------------------------------------------------------- //
// TTL sweep
// --------------------------------------------------------------------------- //
function sweepTtl(ttlSeconds, base) {
  if (ttlSeconds == null) ttlSeconds = 86400;
  const now = Date.now() / 1000;
  let removed = 0;
  let entries;
  try {
    entries = fs.readdirSync(base);
  } catch (e) {
    return 0;
  }
  for (const name of entries) {
    if (!name.startsWith(TMP_PREFIX)) continue;
    const d = path.join(base, name);
    let created;
    try {
      if (!fs.statSync(d).isDirectory()) continue;
      const marker = path.join(d, MARKER);
      created = fs.existsSync(marker)
        ? parseFloat(fs.readFileSync(marker, "utf8"))
        : fs.statSync(d).mtimeMs / 1000;
    } catch (e) {
      continue;
    }
    if (Number.isNaN(created)) created = 0;
    if (now - created > ttlSeconds) {
      fs.rmSync(d, { recursive: true, force: true });
      removed++;
    }
  }
  return removed;
}

// --------------------------------------------------------------------------- //
// commands
// --------------------------------------------------------------------------- //
async function cmdProcess(argv) {
  const a = parseArgs(argv, {
    bools: ["skip-blurry", "keep-candidates", "json", "no-segment"],
    multi: ["range"],
  });
  if (a._.length < 1) fail("process requires an input path or URL");
  if (!have("ffmpeg") || !have("ffprobe")) fail("ffmpeg and ffprobe are required (install ffmpeg)");

  const input = a._[0];
  const fps = a.fps != null ? parseFloat(a.fps) : 1.0;
  const oversample = a.oversample != null ? parseInt(a.oversample, 10) : 3;
  const maxFrames = a["max-frames"] != null ? parseInt(a["max-frames"], 10) : 24;
  if (!(fps > 0)) fail("--fps must be > 0");
  if (!(oversample >= 1)) fail("--oversample must be >= 1");
  if (!(maxFrames >= 1)) fail("--max-frames must be >= 1");

  // Resolve segmentation knobs from the profile; explicit flags override.
  const profile = a.profile != null ? a.profile : DEFAULT_PROFILE;
  if (!PROFILES[profile]) fail(`--profile must be one of: ${Object.keys(PROFILES).join(", ")}`);
  const preset = PROFILES[profile];
  const hashArg = a["hash-dist"] != null ? a["hash-dist"] : a["dedup-dist"];
  const hashDist = hashArg != null ? parseInt(hashArg, 10) : preset.hash_dist;
  const diffThresh = a["diff-thresh"] != null ? parseFloat(a["diff-thresh"]) : preset.diff_thresh;
  const blockGrid = a["block-grid"] != null ? parseInt(a["block-grid"], 10) : preset.block_grid;
  const minBlocks = a["min-blocks"] != null ? parseInt(a["min-blocks"], 10) : preset.min_blocks;
  const maxSegmentSeconds = a["max-segment-seconds"] != null ? parseFloat(a["max-segment-seconds"]) : 0.0;
  if (!(hashDist >= 0)) fail("--hash-dist must be >= 0");
  if (!(diffThresh >= 0 && diffThresh <= 1)) fail("--diff-thresh must be between 0 and 1");
  if (!(blockGrid >= 1)) fail("--block-grid must be >= 1");
  if (!(minBlocks >= 1)) fail("--min-blocks must be >= 1");
  if (!(maxSegmentSeconds >= 0)) fail("--max-segment-seconds must be >= 0");
  const noSegment = !!a["no-segment"];

  const threshold = a.threshold != null ? parseFloat(a.threshold) : DEFAULT_THRESHOLD_NODE;
  const skipBlurry = !!a["skip-blurry"];
  const start = a.start != null ? a.start : null;
  const end = a.end != null ? a.end : null;
  const ttl = a.ttl != null ? a.ttl : "24h";

  sweepTtl(parseDuration(ttl), baseTmpdir());

  let workdir;
  if (a.outdir) {
    workdir = a.outdir;
    fs.mkdirSync(workdir, { recursive: true });
  } else {
    workdir = fs.mkdtempSync(path.join(baseTmpdir(), TMP_PREFIX));
  }
  fs.writeFileSync(path.join(workdir, MARKER), String(Date.now() / 1000));

  loadSharp();
  const video = resolveInput(input, workdir);
  const info = ffprobeInfo(video);
  const ranges = parseRanges(a.range, start, end, info.duration);
  const frames = extractRanges(video, workdir, fps * oversample, ranges);

  const scored = [];
  for (let i = 0; i < frames.length; i++) {
    const sharpness = await scoreSharpness(frames[i].path);
    scored.push({
      index: i,
      t: Math.round(frames[i].t * 1000) / 1000,
      range: frames[i].range,
      path: frames[i].path,
      sharpness: Math.round(sharpness * 10000) / 10000,
    });
  }

  const selected = await selectFrames(scored, fps, threshold, skipBlurry, maxFrames, {
    segment: !noSegment,
    hash_dist: hashDist,
    diff_thresh: diffThresh,
    block_grid: blockGrid,
    min_blocks: minBlocks,
    max_segment_seconds: maxSegmentSeconds,
    duration: info.duration,
  });

  const final = [];
  selected.forEach((f, n) => {
    const newp = path.join(workdir, `frame-${String(n).padStart(3, "0")}-t${f.t.toFixed(2)}${IMAGE_EXT}`);
    try {
      fs.renameSync(f.path, newp);
      f.path = newp;
    } catch (e) {
      /* keep original path */
    }
    final.push(f);
  });
  if (!a["keep-candidates"]) {
    for (const f of scored) {
      if (!f.selected && path.basename(f.path).startsWith("cand-")) {
        try {
          fs.unlinkSync(f.path);
        } catch (e) {
          /* ignore */
        }
      }
    }
  }
  // drop now-empty per-range subdirs
  for (let ri = 0; ri < ranges.length; ri++) {
    try {
      fs.rmdirSync(path.join(workdir, `r${ri}`));
    } catch (e) {
      /* not empty or missing */
    }
  }

  const manifest = {
    video,
    source: input,
    duration: info.duration,
    source_fps: info.fps,
    fps_target: fps,
    oversample,
    backend: "sharp",
    threshold,
    outdir: workdir,
    profile,
    segment: !noSegment,
    hash_dist: hashDist,
    diff_thresh: diffThresh,
    block_grid: blockGrid,
    min_blocks: minBlocks,
    max_segment_seconds: maxSegmentSeconds,
    ranges: ranges.map(([s, e], i) => ({
      index: i,
      start: s != null ? Math.round(s * 1000) / 1000 : 0.0,
      end: e != null ? Math.round(e * 1000) / 1000 : info.duration,
    })),
    count_candidates: scored.length,
    count_selected: final.length,
    created_at: Date.now() / 1000,
    selected: final.map((f) => ({
      index: f.index,
      t: f.t,
      range: f.range,
      path: f.path,
      sharpness: f.sharpness,
      blurry: f.blurry,
      window: f.window,
      reason: f.reason,
      segment_start: f.segment_start,
      segment_end: f.segment_end,
      duration: f.duration,
      represents: f.represents,
    })),
  };
  if (a["keep-candidates"]) manifest.candidates = scored;

  const manifestPath = path.join(workdir, "manifest.json");
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

  if (a.json) {
    process.stdout.write(
      JSON.stringify({
        manifest: manifestPath,
        outdir: workdir,
        backend: "sharp",
        profile,
        count_selected: final.length,
        count_candidates: scored.length,
        duration: info.duration,
      }) + "\n"
    );
  } else {
    console.log(`outdir: ${workdir}`);
    console.log(`backend: sharp  threshold: ${threshold}  profile: ${profile}${noSegment ? "  (segmentation off)" : ""}`);
    const rngDesc = manifest.ranges
      .map((m) => `[${m.start.toFixed(1)}s-${m.end != null ? m.end.toFixed(1) + "s]" : "EOF]"}`)
      .join(", ");
    console.log(`ranges: ${rngDesc}`);
    console.log(`selected ${final.length} representative(s) of ${scored.length} candidates`);
    console.log(`manifest: ${manifestPath}`);
    for (const f of final) {
      const flag = f.blurry ? " (blurry)" : "";
      const covers = ` covers ${f.segment_start.toFixed(1)}-${f.segment_end.toFixed(1)}s (~${Math.round(f.duration)}s, ${f.represents} frames)`;
      console.log(`  r${f.range} t=${f.t.toFixed(2)}s  sharp=${f.sharpness.toFixed(2)}${flag}${covers}`);
    }
  }
}

function cmdClean(argv) {
  const a = parseArgs(argv, { bools: [] });
  const base = a.dir || baseTmpdir();
  const removed = sweepTtl(parseDuration(a.ttl || "24h"), base);
  console.log(`removed ${removed} stale ${TMP_PREFIX}* dir(s) from ${base}`);
}

function usage() {
  eprint("usage: review_mp4.js <process|clean> [options]   (see SKILL.md / REFERENCE.md)");
  process.exit(2);
}

async function main() {
  const [, , command, ...rest] = process.argv;
  if (command === "process") await cmdProcess(rest);
  else if (command === "clean") cmdClean(rest);
  else usage();
}

main().catch((e) => fail(e && e.stack ? e.stack : String(e)));
