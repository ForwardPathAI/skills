---
name: mobile-ui
description: Turn a Statement of Work (SOW) into a grounded mobile app screen spec and premium UI mockups for an Expo SDK 54 + React Native app. Extracts a brand foundation from the entities named in the SOW, writes a per-screen Markdown spec grounded strictly on the SOW and Expo SDK 54 capabilities, then generates consistent portrait phone mockups with Google Gemini. Use when the user references this skill by name, or asks to design mobile app screens / screen specs / UI mockups from a SOW or scope document for an Expo/React Native project.
---

# ForwardPath Mobile UI

Two deliverables from one SOW, for an **Expo SDK 54 + React Native** mobile app:

1. **A grounded screen spec** (`MOBILE_APP_SCREENS_SPEC.md`) — brand foundation + every required screen, grounded **only** on the SOW and on Expo SDK 54 capabilities.
2. **Premium UI mockups** — one consistent, portrait phone image per screen, via Google Gemini.

This skill is self-contained: it does not depend on any other skill. PDF/report generation is out of scope.

## Hard rules
- **Ground on the SOW.** Depict and spec only SOW-documented mobile capabilities. Never invent features. List anything inferred under an Appendix and exclude it from mockups unless the user confirms.
- **Mobile only.** Web admin, client portals, dashboards and back-office are out of scope.
- **Expo SDK 54 feasible.** Every feature must map to a real Expo SDK 54 capability — see [`EXPO_SDK_54.md`](EXPO_SDK_54.md). Flag anything needing a development build or that isn't feasible.
- **Show your work.** After each mockup, display it with the Read tool.

## Setup (once per machine)

Dependencies:
```bash
pip install google-genai Pillow
```

Set `TOOL` to the absolute path of `scripts/mockup_gen.py` **inside this skill's own directory** (the folder this `SKILL.md` lives in — wherever the skill was installed, e.g. `.cursor/skills/`, `.claude/skills/`, or `.agents/skills/`). Reuse this `$TOOL` for every command below.

API key — check, and if missing, **ask the user** (they get one at https://aistudio.google.com/apikey), then store it:
```bash
TOOL="<this skill dir>/scripts/mockup_gen.py"
python "$TOOL" check
# If NOT_CONFIGURED, ask the user for their Gemini API key, then:
python "$TOOL" setup --api-key "USER_KEY_HERE"
```
The key persists at `~/.config/mobile-ui/config.json` (also honors `GEMINI_API_KEY` / `GOOGLE_API_KEY`). If any generate call prints `NO_API_KEY`, ask the user for a key and run `setup`, then retry. Never hardcode a key.

---

## Phase 1 — SOW → grounded screen spec

Copy this checklist and track it:
```
- [ ] 1. Ingest the SOW
- [ ] 2. Extract brand entities + brand foundation
- [ ] 3. Map required mobile features to Expo SDK 54
- [ ] 4. Enumerate required screens (grounded)
- [ ] 5. Write MOBILE_APP_SCREENS_SPEC.md from the template
```

**1. Ingest the SOW.** Accept a URL or a file. For a URL, fetch it; if it's JavaScript-rendered (e.g. Notion) and comes back empty, use a browser tool to navigate and read the rendered text. Capture objectives, scope, roles, features, data, integrations, constraints, and phasing.

**2. Extract brand entities + brand foundation.** Identify the entities named in the SOW (the client/company the app is for, its parent group, key partners/retailers). Research those entities' brands (logo, colors, typography vibe, naming conventions) using web tools, and define a brand foundation: color tokens, typography, layout/shape, motion. Capture naming/wordmark rules (e.g. preferred shorthand). This becomes §1 of the spec.

**3. Map features to Expo SDK 54.** For each mobile capability in the SOW (auth/SSO, camera/capture, OCR/CV, offline storage, background sync, connectivity, notifications, etc.), pick the Expo SDK 54 path from [`EXPO_SDK_54.md`](EXPO_SDK_54.md). Note dev-build needs and anything not feasible.

**4. Enumerate required screens.** Derive the minimal set of mobile screens needed to deliver the SOW, in **usage order** (first-run → core loop → results → account). Each screen must trace to a SOW section (or be marked `implied`/`inferred`).

**5. Write the spec.** Create `MOBILE_APP_SCREENS_SPEC.md` using [`SPEC_TEMPLATE.md`](SPEC_TEMPLATE.md): brand foundation, information architecture, screen inventory table, and a definition block per screen (purpose, layout, components, states, primary action, low-cognitive-load notes, Expo SDK 54 mapping, SOW basis). Include the grounding rule and an Appendix of inferred/out-of-scope items.

Confirm the spec with the user before generating mockups.

---

## Phase 2 — generate the UI mockups

Tool: the `$TOOL` set in Setup (`scripts/mockup_gen.py` in this skill's directory). Prompting and the project-file format are in [`MOCKUP_PROMPTING.md`](MOCKUP_PROMPTING.md).

```
- [ ] 1. Create .forwardpath-ui-project.json (brand, colors, style, render)
- [ ] 2. Generate screens one at a time, in usage order, into mockups/
- [ ] 3. Pass brand palette + style + ALL prior screens as refs each time
- [ ] 4. Show each result; record it in the project file
- [ ] 5. Audit the full set against the SOW
```

**1. Project file.** Write `.forwardpath-ui-project.json` at the workspace root (format in [`MOCKUP_PROMPTING.md`](MOCKUP_PROMPTING.md)) so every generation reuses the same brand inputs.

**2–4. Generate consistently.** One screen per call, in usage order, saved as `mockups/NN-screen-name.png`:
```bash
python "$TOOL" generate \
  --prompt "<screen identity, theme, layout top→bottom, real labels, primary action, what to omit>" \
  --theme dark \
  --colors "<palette from project file>" \
  --style "<style from project file>" \
  --description "<brand context from project file>" \
  --refs mockups/01-*.png mockups/02-*.png logo.png \
  -o mockups/03-<name>.png
```
Always pass `--colors`, `--style`, `--description`, and previously generated screens via `--refs` for one-product consistency. Defaults are portrait `9:16`, `2K`, `iphone` frame (override with `--frame android|none`, `--aspect`, `--size`). Show each image with the Read tool and append it to the project file's `screens` array.

**5. Audit.** Re-check every mockup against the SOW (no invented features) and Expo SDK 54 feasibility. Regenerate any drift (retry once; if needed lower `--temperature` or simplify).

### Editing an existing mockup (optional)
Use the 3-step flow: `analyze` → `modify-json` → `regenerate` (keeps layout, applies only requested changes). See script `--help`.

---

## Command reference
```bash
python "$TOOL" check
python "$TOOL" setup --api-key KEY [--generation-model M] [--analysis-model M]
python "$TOOL" generate --prompt "..." -o out.png [--refs ...] [--colors ...] [--style ...] [--description ...] [--theme light|dark] [--frame iphone|android|none] [--aspect 9:16] [--size 1K|2K|4K] [--temperature 0.35]
python "$TOOL" analyze image.png [-o spec.json]
python "$TOOL" modify-json --json-file spec.json --changes "..." [-o spec2.json]
python "$TOOL" regenerate --json-spec spec2.json [--original image.png] [--refs ...] -o out.png
```

## Resources
- [`EXPO_SDK_54.md`](EXPO_SDK_54.md) — capability → package map + grounding constraints.
- [`SPEC_TEMPLATE.md`](SPEC_TEMPLATE.md) — the screen-spec Markdown template.
- [`MOCKUP_PROMPTING.md`](MOCKUP_PROMPTING.md) — prompt construction + `.forwardpath-ui-project.json` format.
