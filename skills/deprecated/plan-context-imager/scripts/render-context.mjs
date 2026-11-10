#!/usr/bin/env node
// Render a text context bundle into dense PNG pages via pxpipe's renderTextToImages.
// Usage: node render-context.mjs <bundle.txt> <outdir> [--reflow] [--cols N] [--max-chars N]
// Requires: npm install pxpipe-proxy   (Node 18+)

import { readFile, mkdir, writeFile } from "node:fs/promises";
import { basename } from "node:path";

const args = process.argv.slice(2);
const positional = args.filter((a) => !a.startsWith("--"));
const [bundlePath, outDir] = positional;

if (!bundlePath || !outDir) {
  console.error(
    "Usage: node render-context.mjs <bundle.txt> <outdir> [--reflow] [--cols N] [--max-chars N]",
  );
  process.exit(1);
}

function flagValue(name) {
  const i = args.indexOf(name);
  return i !== -1 && args[i + 1] ? args[i + 1] : undefined;
}

const opts = {};
if (args.includes("--reflow")) opts.reflow = true;
const cols = flagValue("--cols");
if (cols) opts.cols = Number(cols);
const maxChars = flagValue("--max-chars");
if (maxChars) opts.maxCharsPerImage = Number(maxChars);

let renderTextToImages;
try {
  ({ renderTextToImages } = await import("pxpipe-proxy"));
} catch {
  console.error(
    "Cannot load 'pxpipe-proxy'. Install it first from the skill directory:\n  npm install",
  );
  process.exit(1);
}

const text = await readFile(bundlePath, "utf8");
if (!text.trim()) {
  console.error(`Bundle is empty: ${bundlePath}`);
  process.exit(1);
}

const { pages, droppedChars, pixels } = await renderTextToImages(text, opts);

if (!pages.length) {
  console.error("Renderer produced no pages (bundle too small?).");
  process.exit(1);
}

await mkdir(outDir, { recursive: true });

const written = [];
for (let i = 0; i < pages.length; i++) {
  const name = `page-${String(i + 1).padStart(2, "0")}.png`;
  await writeFile(`${outDir}/${name}`, pages[i].png);
  written.push({ name, ...pages[i] });
}

console.log(`Rendered ${basename(bundlePath)} -> ${outDir}`);
for (const p of written) {
  console.log(`  ${p.name}  ${p.width}x${p.height}px  ${p.png.length} bytes`);
}
console.log(
  `Total: ${pages.length} page(s), ${text.length} chars, droppedChars=${droppedChars}, pixels=${pixels}`,
);
console.log(
  `Est. reader tokens: ~${Math.round(text.length / 3.1)} imaged vs ~${text.length} as text`,
);
