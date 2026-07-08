# DOCX Guide

How to produce the **shareable DOCX report** companion to the architecture canvas. The canvas is the interactive source of truth; the DOCX is the artifact you hand to non-technical stakeholders (customer sponsors, execs) who just want to open a clean document — no Cursor, no toolchain.

This guide is self-contained. Pair it with [CANVAS_GUIDE.md](CANVAS_GUIDE.md); the two deliverables share the same content, gathered in Steps 1–4.

## When to produce it

Produce the DOCX **after** the canvas passes ([CANVAS_GUIDE.md](CANVAS_GUIDE.md)), when the user wants a document to circulate. The canvas remains authoritative; the DOCX mirrors it. If you change the design later, regenerate both.

## The one hard rule: rendered diagrams, no literal source

The DOCX is a **reading** deliverable. It must **not** contain literal Bicep or Mermaid source text.

| Content | Canvas | DOCX |
|---------|--------|------|
| Architecture diagram | mermaid `CodeBlock` and/or inline SVG | **rendered PNG** (Figure 1) |
| Cost chart | `BarChart` / mermaid | **rendered PNG** (Figure) |
| Bicep skeleton | code block (section 6) | **omitted** — reference the next-step skills instead |
| Mermaid source | code block | **omitted** — only the rendered image appears |

The bundled generator [assets/build_docx.py](assets/build_docx.py) ships **no code-block helper** on purpose, so it is structurally hard to violate this rule. If a stakeholder needs the Bicep/mermaid source, point them at the canvas or the repo `.mmd` / `azure-infra-setup` output — not the DOCX.

## Prerequisites

- **Python 3** with **`python-docx`** — `pip install python-docx` (or `python3 -m pip install --user python-docx`).
- **mermaid-cli** via `npx -y @mermaid-js/mermaid-cli` — renders `.mmd` → `.png`. It needs a Chromium; if none is cached it will download one, or reuse a local Puppeteer cache.
- If any tool is unavailable and cannot be installed, fall back (see [Fallback](#fallback)).

## Pipeline

Work inside `docs/architecture/` in the POC repo, alongside the canvas.

### 1. Author the diagram sources (`.mmd`)

Write mermaid sources whose content matches the canvas diagrams:

- `<app>-architecture.mmd` — the target topology (**required**). Use a `flowchart LR` with a `subgraph` for the Container Apps environment and a shared theme init block. Color by plane: compute / data / external / client.
- `<app>-cost.mmd` — the monthly run-rate chart (**recommended**). Use `xychart-beta` with a `bar` series — **not** matplotlib (avoids numpy/version breakage). Compare the design's run-rate against the SOW's budget signal.
- `<app>-<name>.mmd` — any extra diagram the design needs (e.g. `-tenancy` for a multi-tenant model).

Keep edge labels short and ASCII — some fonts render "SSO" oddly at small sizes; verify the rendered PNG reads correctly.

### 2. Render each to PNG

```bash
npx -y @mermaid-js/mermaid-cli -i <app>-architecture.mmd -o <app>-architecture.png -s 3 -b white
npx -y @mermaid-js/mermaid-cli -i <app>-cost.mmd -o <app>-cost.png -s 3 -b white
```

`-s 3` renders at 3× for crisp embedding; `-b white` gives an opaque background. If the renderer **segfaults in a sandbox**, pass a Puppeteer config and re-run with the needed permissions:

```bash
printf '{"args":["--no-sandbox","--disable-setuid-sandbox"]}' > /tmp/pptr.json
npx -y @mermaid-js/mermaid-cli -i <app>-architecture.mmd -o <app>-architecture.png -s 3 -b white -p /tmp/pptr.json
```

Always open the PNG and confirm labels/edges are legible before embedding.

### 3. Generate the DOCX

Copy [assets/build_docx.py](assets/build_docx.py) to `docs/architecture/build_docx.py`, edit the `CONFIG` block and the `build()` content region to mirror the canvas, then:

```bash
python3 build_docx.py     # writes <App-Title>-Production-Architecture.docx
```

`add_image()` skips gracefully with an inline "[missing diagram]" note if a PNG is absent, so the doc still builds while you iterate — but the final deliverable must have every figure present.

## Section mapping (canvas → DOCX)

Same order as [CANVAS_GUIDE.md](CANVAS_GUIDE.md). Section 6 (Bicep skeleton) becomes a pointer to next-step skills; diagrams become images.

| # | Canvas section | DOCX rendering |
|---|----------------|----------------|
| — | Cover | Title + subtitle + one-paragraph summary + **stat cards** + "design intent vs. SOW" callout |
| 1 | Executive overview | Intro paragraph (grounded in the SOW, cited) + stat cards |
| 4 | Architecture layers | **Figure 1 (rendered topology PNG)** + layers table + deviations callout |
| 2 | SOW traceability | Tone-colored table (green covered / amber partial / blue new), one row per requirement |
| 3 | POC gap audit | Tone-colored table (red demo-grade / amber missing / green reusable) with citations; omit if no POC |
| 5 | Azure resource map | Table: resource, SKU/tier, region, purpose |
| 6 | Bicep skeleton | **Omitted** — covered by the next-step skills line at the end |
| 7 | Security & reliability | Two bulleted lists of **decisions** |
| 8 | Cost estimate | Grouped/subtotal/total table + **rendered cost chart PNG** |
| 9 | Phased migration | Table: phase, built/migrated, POC items replaced |
| 10 | Risks & open questions | Tone-colored table: risk, severity, mitigation |

Optional extra sections (e.g. multi-tenancy) slot in where they belong, each with their own rendered diagram if useful.

## Quality bar

The DOCX must look like a designed report, not a Word default:

- **Page setup:** US Letter, 0.7" margins, Calibri body at 10.5pt, a centered footer citing the SOW version/date for provenance.
- **Headings:** section headings in brand blue with a thin bottom rule; sub-headings in ink.
- **Tables:** fixed layout, navy header row with white text, thin borders, vertical-centered cells, and **semantic row tinting** so status/severity/tag columns read at a glance (reuse the `success` / `warning` / `info` / `danger` tones from the canvas).
- **Stat cards:** a 4-up band of headline numbers (run-rate, users, timeline, residency/region) under the intro.
- **Figures:** centered, with an italic caption that explains the legend (what solid vs. dashed edges and each color mean).
- **Callouts:** boxed "design intent" (info) and "deviations" (warning) blocks, matching the canvas callouts.

All of this is already implemented in [assets/build_docx.py](assets/build_docx.py) — you mostly edit content lists, not styling.

## Output and dual location

- Write `build_docx.py`, the `.mmd` sources, the rendered `.png` files, and the generated `.docx` to `docs/architecture/` in the POC repo (same folder as the canvas).
- The DOCX is **generated**, but committing it (and the PNGs) lets stakeholders open it without the toolchain — recommended for this read-oriented deliverable. Note it in the Step 5 report and let the user decide whether to track the binaries.
- Do **not** write the DOCX to the IDE managed canvases directory — that folder is for the canvas only.

## Verification

Before reporting done:

1. `python3 build_docx.py` runs clean and writes the `.docx`.
2. Every figure is present (no "[missing diagram]" placeholder in the output).
3. Confirm the DOCX contains **no** literal Bicep or Mermaid source — only rendered diagrams. A quick text scan of the built doc should find the diagram captions but not `resource ` / `flowchart ` / `param ` code.
4. Numbers, statuses, and section content match the canvas (they must not drift apart).

## Fallback

- **No `python-docx` and cannot install:** deliver the same sections as `docs/architecture/ARCHITECTURE.md` (per [CANVAS_GUIDE.md](CANVAS_GUIDE.md) fallback) and tell the user the DOCX needs `python-docx`.
- **No mermaid renderer:** still generate the DOCX, but flag the missing figures in the report and provide the `.mmd` sources so they can render later. Do **not** paste raw mermaid text into the DOCX as a substitute.
