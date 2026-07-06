---
name: mobile-ui-implement
description: Turn mobile UI mockups (PNG screens or a PDF deck) into per-screen implementation blueprints, then build them in an Expo Go-compatible React Native app. Decomposes each screen into layers, components, states, and animations, maps every capability to an Expo Go-bundled module, and emits blueprints strict enough for a weaker model to implement one screen at a time. Use when the user asks to implement mockups, break a screen into components/layers, turn designs into code, plan an Expo UI build, or build the UI from mockups/a design PDF.
---

# Mobile UI → Expo Implementation

Two modes that close the loop from design to code. The companion [`mobile-ui`](../mobile-ui/SKILL.md) skill produces the mockups; this skill turns them into buildable plans and then builds them.

- **Mode A — Analyze** (run by a capable model): read the mockups (and any spec), decompose every screen, and emit `ui-blueprints/` — a foundation doc, a build-order index, and one strict blueprint per screen.
- **Mode B — Implement** (run by any model, including a weaker one): build **exactly one screen per run** by following its blueprint literally.

```
Mockups (PNG or PDF) + optional spec  ──Mode A──▶  ui-blueprints/  ──Mode B──▶  Expo app code
```

## Which mode am I in?
- No `ui-blueprints/` folder yet, or the user says "analyze / plan / break down the mockups" → **Mode A**.
- `ui-blueprints/` exists and the user says "implement / build screen X" → **Mode B**.
- If ambiguous, ask.

## Hard rules (both modes)
- **Expo Go only.** Use exclusively modules bundled in the Expo SDK / Expo Go. Anything needing a development build — `react-native-vision-camera`, `react-native-mmkv`, `react-native-msal`, or any custom native code — is **flagged and stubbed with mock data**, never assumed to run. See the capability map in [`../mobile-ui/EXPO_SDK_54.md`](../mobile-ui/EXPO_SDK_54.md) and the Expo Go safe list in [`PATTERNS.md`](PATTERNS.md).
- **Mockup = layout truth; spec = behavior truth.** The image is authoritative for what is on screen and where. A spec doc (if provided) is authoritative for tokens, copy, states, and behavior. When they conflict, note it and follow the spec.
- **No raw hex in screens.** Every color, size, radius, and spacing value references a token from `theme/tokens.ts`. Blueprints reference tokens by name; screens import them.
- **One screen per Mode B run.** Never batch-build screens. Never restyle a screen you were not asked to build.
- **No invented features.** Depict and build only what the mockup or spec shows. Tag anything you inferred as `inferred-default`.

---

## Mode A — Analyze mockups into blueprints

Copy this checklist and track it:
```
- [ ] 1. Ingest inputs (mockups + optional spec)
- [ ] 2. Extract the design foundation → 00-foundation.md
- [ ] 3. Decompose each screen into layers + components
- [ ] 4. Specify states, interactions, animations (tag spec vs inferred-default)
- [ ] 5. Map every capability to an Expo Go module; flag/stub dev-build needs
- [ ] 6. Emit INDEX.md build order + one NN-screen.md blueprint per screen
```

**1. Ingest inputs.** Accept any of:
- a folder of mockup PNGs (`mockups/NN-*.png`),
- a **PDF deck** — burst it into per-page PNGs first (see Setup), then Read each page image,
- an optional screens spec / SOW markdown (e.g. `MOBILE_APP_SCREENS_SPEC.md`).

Read **every** mockup image with the Read tool before planning — you cannot decompose a screen you have not looked at. If a spec exists, read it and treat it as authoritative for tokens/copy/behavior.

**2. Extract the design foundation.** Write `ui-blueprints/00-foundation.md` (see [`BLUEPRINT_TEMPLATE.md`](BLUEPRINT_TEMPLATE.md) → Foundation section). It must contain:
- a ready-to-paste `theme/tokens.ts` (colors, type scale, spacing, radii, elevation, light/dark),
- the **navigation skeleton** (tabs + stacks) as an `expo-router` file layout,
- the **shared component inventory** — every component used on 2+ screens (Button, Card, Chip, StatBadge, SectionHeader, Skeleton, SyncChip, ...), each with a TypeScript props interface and the token references it uses.

**3. Decompose each screen into layers.** For every screen, describe it as a stack of layers in this fixed order (see the template):
1. **Background** — solid / gradient / image.
2. **Chrome** — safe-area, status bar, header, tab bar.
3. **Content** — scrollable sections, top → bottom, as a component tree with the **exact label text transcribed from the mockup**.
4. **Overlays** — absolutely-positioned FABs, sync chips, toasts, floating CTAs.
5. **Modals / sheets** — bottom sheets, dialogs.

**4. Specify behavior.** Per screen list: states (`default / loading / empty / error / offline` as relevant), the interaction for each tappable element, and an **animation table** (trigger → effect → package → recipe link into [`PATTERNS.md`](PATTERNS.md)). Tag every behavior `spec` (documented in the spec) or `inferred-default` (a premium default you chose — e.g. spring-scale on CTA press, success haptic on confirm, skeletons on load).

**5. Map to packages, flag infeasibility.** Every capability maps to an Expo Go-bundled module. For anything dev-build-only, write an explicit stub instruction in the blueprint (e.g. *"live-frame CV is not in Expo Go → render a static reticle that turns green on a 1.5s timer; leave a `// TODO(dev-build): vision-camera frame processor` marker"*).

**6. Emit the build order.** Write `ui-blueprints/INDEX.md`: foundation → shared components → screens ordered by dependency (screens using only shared components first). Then write one `ui-blueprints/NN-screen-name.md` per screen from [`BLUEPRINT_TEMPLATE.md`](BLUEPRINT_TEMPLATE.md).

Show the user the foundation doc and the index, and confirm before they hand off to Mode B.

---

## Mode B — Implement one screen from its blueprint

Deliberately low-freedom. Follow the blueprint literally; do not improvise.

Copy this checklist and track it:
```
- [ ] 1. Read 00-foundation.md fully
- [ ] 2. Ensure tokens + navigation + shared components exist (build missing ones first)
- [ ] 3. Read the target screen blueprint end to end
- [ ] 4. Build the screen top → bottom, layer by layer
- [ ] 5. Wire it into navigation with the blueprint's mock data
- [ ] 6. Verify: tsc + lint pass, then walk the acceptance checklist vs the mockup
```

1. **Read `00-foundation.md`.** Confirm `theme/tokens.ts`, the navigation skeleton, and the shared components the blueprint lists under "Depends on" already exist in the codebase. **Build any missing ones first**, exactly as specified in the foundation doc.
2. **Read the whole screen blueprint** before writing code. Open its mockup image with the Read tool.
3. **Build layer by layer** in the template's order (background → chrome → content → overlays → modals). Use **only**: tokens from `theme/tokens.ts`, the shared components, and recipes from [`PATTERNS.md`](PATTERNS.md). Add no dependencies the blueprint does not name.
4. **Use the blueprint's mock data** for anything not yet wired to a backend, and honor the stub instructions for dev-build-only capabilities.
5. **Wire it into navigation** at the route the foundation doc assigns.
6. **Verify.** Run `npx tsc --noEmit` and the project's linter; fix what you introduced. Then walk the blueprint's **acceptance checklist** against the mockup image before marking the screen done.

**Do NOT:** restyle other screens · add features not in the blueprint · inline hex colors or magic numbers · swap in a dev-build-only library · build more than one screen.

---

## Setup

Blueprint generation needs no dependencies. Bursting a **PDF** deck into page PNGs (Mode A step 1) needs PyMuPDF:
```bash
pip install PyMuPDF
```

Set `TOOL` to the absolute path of `scripts/pdf_extract.py` inside this skill's own directory (wherever it was installed), then burst the deck:
```bash
TOOL="<this skill dir>/scripts/pdf_extract.py"
python "$TOOL" "path/to/deck.pdf" -o mockups/ --dpi 200
```
Each page is written as `mockups/page-NN.png`. Read them, discard non-screen pages (covers, section dividers), and rename kept screens to `mockups/NN-screen-name.png`.

---

## Resources
- [`BLUEPRINT_TEMPLATE.md`](BLUEPRINT_TEMPLATE.md) — the foundation doc format and the fixed per-screen blueprint format.
- [`PATTERNS.md`](PATTERNS.md) — Expo Go safe-list, `tokens.ts` pattern, layer/stacking recipes, and Reanimated/haptics animation recipes referenced by blueprints.
- [`EXAMPLE.md`](EXAMPLE.md) — a worked Mode A output (foundation excerpt + full Guided Capture blueprint) from the PRS deck.
- [`../mobile-ui/EXPO_SDK_54.md`](../mobile-ui/EXPO_SDK_54.md) — capability → package map and grounding constraints (shared with the `mobile-ui` skill).
