# Mockup prompting & project file

## Generating consistent, premium portrait mockups

`scripts/mockup_gen.py generate` already forces portrait phone framing. Your job is a strong, grounded `--prompt` plus consistent brand inputs.

A good `--prompt` describes, in order:
1. **Screen identity** — e.g. "Guided photo capture (hero)".
2. **Theme** — light or dark (pass `--theme` too).
3. **Layout top→bottom** — status bar, header, body sections, tab bar / CTA.
4. **Key components with REAL labels** — never lorem ipsum. Use concrete copy and realistic data from the SOW domain.
5. **The single primary action** — the one obvious button.
6. **What to omit** — keep it to the SOW; do not add maps, bells, charts, retailers, etc. that aren't grounded.

### Consistency rules (critical)
- Generate **one screen per call**, in **usage order**.
- Always pass the **brand color palette** (`--colors`) and **style** (`--style`) on every call — pull both from the project file.
- Always pass **all previously generated screens** (and any logo) via `--refs` so the app looks like one product. As the set grows, prefer the 3–5 most representative prior screens to stay within limits.
- Keep `--description` set to the project brand context.
- Save outputs as `mockups/NN-screen-name.png` (zero-padded, usage order).

### Example
```bash
TOOL="<this skill dir>/scripts/mockup_gen.py"   # scripts/mockup_gen.py inside this skill's own directory
python "$TOOL" generate \
  --prompt "Guided photo capture (hero, dark). Status bar; minimal top chrome with End + aisle label; live viewfinder with a green focus reticle and a check when a price tag is valid; one short 'Hold steady' hint; big shutter with a thin progress ring; last-capture thumbnail bottom-left; a small amber 'queued' sync chip. One job: capture the tag." \
  --theme dark \
  --colors "primary:#00A475, ink:#252525, petrol:#002C39, amber:#FFB100, surface:#FFFFFF, bg:#F8F8F8" \
  --style "ultra-premium native iOS app, editorial serif accents + clean grotesque UI, soft low-contrast shadows, 20px card radius, 56px full-width primary buttons, low cognitive load" \
  --description "Field-rep price-tag audit app for PRS (an Acosta Group company)" \
  --refs mockups/01-sign-in.png mockups/02-today.png logo.png \
  -o mockups/03-guided-capture.png
```

### Tips
- If a result comes back landscape or off-brand, retry once; then lower `--temperature` (e.g. 0.2) or simplify the prompt.
- Use `--frame android` for Android-styled chrome, `--frame none` for full-bleed (no device) screenshots.
- Tablet screens: `--aspect 3:4` (still pass through the same prompt structure).
- After each generation, **show the image** to the user with the Read tool.

## Project file — `.forwardpath-ui-project.json`
Create this at the workspace root to keep generations consistent and track progress.

```json
{
  "app_name": "PRS Price Tag Audit — Mobile App",
  "description": "One-paragraph brand + product context passed as --description.",
  "platforms": "iOS & Android",
  "colors": { "primary": "#00A475", "ink": "#252525", "amber": "#FFB100" },
  "style": "Full --style string (premium aesthetic, components, radii, buttons, motifs).",
  "typography": "Display + UI font direction.",
  "brand_assets": ["logo.png"],
  "render": { "tool": "scripts/mockup_gen.py", "aspect": "9:16", "size": "2K", "frame": "iphone" },
  "screens": [
    { "id": "S02", "name": "sign-in", "path": "mockups/01-sign-in.png", "theme": "dark", "order": 1,
      "description": "What the screen shows (grounded on SOW §ref)." }
  ]
}
```

Update the `screens` array after each successful generation (id, name, path, theme, order, description).
