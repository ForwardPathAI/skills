---
name: plan-context-imager
description: Gather the codebase context a plan depends on, render it into dense PNG pages the way pxpipe does (text-as-image to cut reader tokens), and embed those images plus a per-page index into the plan so the executor reads them instead of re-grepping the codebase on every step. Use when the user says "image the plan context", "pack the context into images", "add context images to this plan", or wants an executor to work from images instead of repeatedly re-reading the codebase.
disable-model-invocation: true
---

# Plan Context Imager

A plan's executor burns tokens re-reading the same files on every step. This skill gathers the context once, renders it into compact PNG pages using [pxpipe](https://github.com/teamchong/pxpipe)'s renderer, and rewrites the plan to point at those images — dense code costs ~3x fewer tokens as an image than as text, so the executor orients from a picture instead of re-grepping.

The technique is lossy on exact strings, so it is a companion to the real files, never a replacement for reading them before an edit.

## How pxpipe's channel works (grounding)

- `pxpipe-proxy` exports `renderTextToImages(text, opts?)` → `{ pages: [{ png: Uint8Array, width, height }], droppedChars, pixels }`. Pure-JS, no proxy needed.
- Dense code/JSON/logs pack ~3.1 chars per image-token vs ~1 char per text-token — roughly a 3x cut. Sparse prose does not win and must stay text.
- **Lossy on byte-exact strings**: 12-char hex recall is ~13/15 on a strong vision reader (Fable 5 class) and ~0/15 on weaker readers, and misses are *silent confabulations*, not errors. Exact identifiers (hashes, IDs, tokens, exact config values) must stay as text.
- Only two executors are proven to read these dense pages accurately: **Anthropic Fable-5** and **GPT-5.6** (pxpipe's allowlist). Opus and GPT-5.5 degrade on imaged content. So the plan must tell the executor to prefer images over grepping *only* when it is Fable-5 or GPT-5.6, and to fall back to the real files on any other model.

## Prerequisites

- The plan file path (ask if not given).
- Node 18+ and the renderer installed once: from the skill directory run `npm install` (installs the pinned `pxpipe-proxy` from `package.json`).

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Load the plan
- [ ] Step 2: Gather the context
- [ ] Step 3: Assemble the bundle
- [ ] Step 4: Render to images
- [ ] Step 5: Embed in the plan
- [ ] Step 6: Report
```

### Step 1: Load the plan

Read the plan file. Extract every file, symbol, and path it cites.

### Step 2: Gather the context

Pull what the executor will actually need, not just the cited lines: callers/callees of touched functions, the tests covering them, relevant config, and the type/interface definitions those files depend on. For each item, record its `path` and line range. Skip files the plan only mentions in passing.

### Step 3: Assemble the bundle

Write one text file. Precede each snippet with a self-describing header so pages stay navigable when read as an image:

```
=== src/auth/session.ts (lines 10-88) ===
<code>

=== src/auth/session.test.ts (lines 1-40) ===
<code>
```

Two hard exclusion rules:

- **Byte-exact values** the executor must reproduce verbatim (hashes, IDs, tokens, exact config strings) stay OUT of the bundle — put them in the plan as text.
- **Sparse prose** (docs, READMEs, comments-only files) stays out; image only token-dense code/JSON/logs.

### Step 4: Render to images

Run the renderer against the bundle. Output goes to a sibling of the plan file named `<plan-basename>.context/` so relative image links survive the plan moving:

```bash
node scripts/render-context.mjs <bundle.txt> <plan-basename>.context
```

Add `--reflow` only for token-densest packing where line structure doesn't matter; for code, keep the default (one line per row) so the executor can read line numbers off the page. The script prints one summary line per page plus `droppedChars` and total pixels.

### Step 5: Embed in the plan

Add (or regenerate in place) a `## Codebase context (imaged)` section in the plan file containing:

- one image embed per page: `![Context page 1](<plan-basename>.context/page-01.png)`
- a **per-page index** mapping page number to the files and line ranges it holds
- **executor instructions**, verbatim (the model gate is the first sentence and must survive into the plan):
  > Prefer these pages over grepping the codebase **only if you are Anthropic Fable-5 or GPT-5.6** — the readers proven to read dense renders accurately. If you are any other model (Opus, GPT-5.5, or unknown), ignore the images and read or grep the real files directly. When you do use the pages, they are for orientation, not byte-exact copying: re-read the actual file immediately before editing it, and treat any exact identifier (hash, ID, number, config value) read off an image as unverified until confirmed in the real file.

### Step 6: Report

Summarize: chars bundled, pages produced, estimated token cost imaged (chars ÷ 3.1) vs as text (chars ÷ 1), `droppedChars`, and what was deliberately kept as text.

## Decision table

| Situation | Action |
|---|---|
| Bundle under ~6k chars | Don't image; paste the context into the plan as text — below the profitability threshold. |
| Executor is not Fable-5 or GPT-5.6 | Warn the user and offer text fallback; don't image silently — a weak reader will confabulate off the pages. |
| A bundled file changes after imaging | Regenerate the affected page and the index; a stale page is worse than none. |
| Plan already has a context-image section | Regenerate it in place; never append a second one. |
| `droppedChars` is nonzero | The bundle has glyphs outside the atlas (often CJK/symbols); note it and keep those files as text. |

## Anti-patterns

- Putting secrets, hashes, or exact IDs only in images — pxpipe's documented silent-confabulation failure mode.
- Imaging sparse prose where text is already cheaper.
- Absolute image paths that break when the plan moves — always use the `<plan-basename>.context/` relative path.
- Embedding pages without the per-page file index (unnavigable).
- Telling the executor to edit from the image instead of re-reading the file first.

## Additional resources

- The renderer and its lossiness receipts: [pxpipe](https://github.com/teamchong/pxpipe)
- Hardening the plan before imaging its context: [plan-refiner/SKILL.md](../plan-refiner/SKILL.md)
