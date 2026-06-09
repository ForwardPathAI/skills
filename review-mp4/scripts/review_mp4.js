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
  const p = inp.startsWith("~") ? path.join(os.homedir(), inp.slice(1)) : inp;
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
function extractRanges(video, workdir, oversample, ranges) {
  const step = 1 / oversample;
  const frames = [];
  ranges.forEach(([s, e], ri) => {
    const sub = path.join(workdir, `r${ri}`);
    fs.mkdirSync(sub, { recursive: true });
    const pattern = path.join(sub, `cand-%05d${IMAGE_EXT}`);
    const cmd = ["-y"];
    // -ss before -i = fast seek; pair with -t (duration) so the range is unambiguous.
    if (s != null && s > 0) cmd.push("-ss", s.toFixed(3));
    if (e != null) cmd.push("-t", Math.max(0, e - (s || 0)).toFixed(3));
    cmd.push("-i", video, "-vf", `fps=${oversample}`, "-q:v", "3", pattern);
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

async function ahash(imgPath) {
  const s = loadSharp();
  let buf;
  try {
    buf = await s(imgPath).greyscale().resize(8, 8, { fit: "fill" }).raw().toBuffer();
  } catch (e) {
    return null;
  }
  let sum = 0;
  for (let i = 0; i < buf.length; i++) sum += buf[i];
  const mean = sum / buf.length;
  let hi = 0n;
  let lo = 0n;
  for (let i = 0; i < 64; i++) {
    const bit = buf[i] > mean ? 1n : 0n;
    if (i < 32) hi = (hi << 1n) | bit;
    else lo = (lo << 1n) | bit;
  }
  return { hi, lo };
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

// --------------------------------------------------------------------------- //
// selection (mirrors review_mp4.py)
// --------------------------------------------------------------------------- //
async function selectFrames(scored, fps, threshold, skipBlurry, maxFrames, dedupDist) {
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
    cand.selected = true;
    cand.reason = "sharpest-in-window" + (cand.blurry ? "-blurry" : "");
    chosen.push(cand);
  }

  const deduped = [];
  for (const f of chosen) {
    f._hash = await ahash(f.path);
    if (deduped.length && hamming(deduped[deduped.length - 1]._hash, f._hash) <= dedupDist) {
      const prev = deduped[deduped.length - 1];
      if (f.sharpness > prev.sharpness) {
        prev.selected = false;
        prev.reason = "deduped";
        deduped[deduped.length - 1] = f;
      } else {
        f.selected = false;
        f.reason = "deduped";
      }
      continue;
    }
    deduped.push(f);
  }

  if (deduped.length > maxFrames) {
    const keep = new Set();
    for (let i = 0; i < maxFrames; i++) {
      keep.add(Math.round((i * (deduped.length - 1)) / (maxFrames - 1)));
    }
    deduped.forEach((f, i) => {
      if (!keep.has(i)) {
        f.selected = false;
        f.reason = "over-max-frames";
      }
    });
  }

  for (const f of scored) delete f._hash;
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
    bools: ["skip-blurry", "keep-candidates", "json"],
    multi: ["range"],
  });
  if (a._.length < 1) fail("process requires an input path or URL");
  if (!have("ffmpeg") || !have("ffprobe")) fail("ffmpeg and ffprobe are required (install ffmpeg)");

  const input = a._[0];
  const fps = a.fps != null ? parseFloat(a.fps) : 1.0;
  const oversample = a.oversample != null ? parseInt(a.oversample, 10) : 3;
  const maxFrames = a["max-frames"] != null ? parseInt(a["max-frames"], 10) : 24;
  const threshold = a.threshold != null ? parseFloat(a.threshold) : DEFAULT_THRESHOLD_NODE;
  const skipBlurry = !!a["skip-blurry"];
  const dedupDist = a["dedup-dist"] != null ? parseInt(a["dedup-dist"], 10) : 4;
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
  const frames = extractRanges(video, workdir, oversample, ranges);

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

  const selected = await selectFrames(scored, fps, threshold, skipBlurry, maxFrames, dedupDist);

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
        count_selected: final.length,
        count_candidates: scored.length,
        duration: info.duration,
      }) + "\n"
    );
  } else {
    console.log(`outdir: ${workdir}`);
    console.log(`backend: sharp  threshold: ${threshold}`);
    const rngDesc = manifest.ranges
      .map((m) => `[${m.start.toFixed(1)}s-${m.end != null ? m.end.toFixed(1) + "s]" : "EOF]"}`)
      .join(", ");
    console.log(`ranges: ${rngDesc}`);
    console.log(`selected ${final.length} of ${scored.length} candidates`);
    console.log(`manifest: ${manifestPath}`);
    for (const f of final) {
      const flag = f.blurry ? " (blurry)" : "";
      console.log(`  r${f.range} t=${f.t.toFixed(2)}s  sharp=${f.sharpness.toFixed(2)}${flag}  ${path.basename(f.path)}`);
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
