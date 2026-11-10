# Mockup prompting & project file (web)

`scripts/webmock_gen.py generate` forces landscape desktop framing and swaps its base scaffold on `--kind`. Your job is a strong, grounded `--prompt` plus consistent brand inputs, generated in the right order so consistency compounds: **style board → shell → screens**.

## The three kinds

### `--kind style-board` — the master anchor (generate first)
One image, not a screen: a brand **style tile** that pins the visual language every screen inherits. Prompt should request, laid out as a neat board:
- the color palette as labeled swatches (use the exact hex/token values),
- typography specimens (display / heading / body / mono with sizes),
- core components in their real states (primary + secondary + ghost buttons, input, select, card, badge/pill, table row, tab bar),
- the logo lockup,
- radius + shadow samples.

Pass real logo files via `--refs` if extracted from `public/`. Iterate with the user until approved — **do not generate screens against an unapproved board.**

```bash
python "$TOOL" generate --kind style-board \
  --prompt "Brand style board for <app>. Labeled color swatches: <token:hex list>. Type specimens: <fonts + sizes>. Component states: primary/secondary/ghost buttons, text input, select, card, badge, table row, tabs. Logo lockup top-left. Radius and shadow samples. Neat grid on a light canvas — a design system tile, NOT an app screen." \
  --colors "<palette>" --style "<style>" --description "<brand context>" \
  --refs logo.svg -o mockups/00-style-board.png
```

### `--kind shell` — the persistent chrome (generate second)
The app shell with an **empty content canvas**: top nav (logo + items in exact order + active state), sidebar (groups + items), right cluster (search, notifications, user menu). No page content — just the frame every screen sits inside. Refs: the approved style board (+ logo).

```bash
python "$TOOL" generate --kind shell \
  --prompt "App shell only, empty content area. Top nav: logo left; items in order: Dashboard | Audits | Reports | Settings (Dashboard active, primary underline). Right: search field, notifications bell, help, user avatar menu 'Casey R.'. Left sidebar groups: <groups+items>. Main content area empty with a faint 'content' placeholder. This chrome is reused on every screen." \
  --colors "<palette>" --style "<style>" --description "<brand context>" \
  --refs mockups/00-style-board.png logo.svg -o mockups/00-shell.png
```

### `--kind screen` — a real screen (generate the rest)
A full screen that **restates the shell verbatim**, then fills the content region.

## A good `--kind screen --prompt`, in order
1. **Screen identity** — e.g. "Audits list (data table)".
2. **Shell, restated verbatim** — the SAME nav items/order/active item, logo, sidebar, right cluster copy as the shell mockup. Do not paraphrase.
3. **Content region layout** — describe the 12-col regions left→right, top→bottom (e.g. "page header with title + 'New audit' button top-right; filter bar; then a data table with columns …; right detail drawer").
4. **Real labels & data** — concrete column names, row values, button text from the SOW domain. Never lorem ipsum.
5. **The single primary action** — the one obvious button (usually top-right).
6. **What to omit** — anything not in the SOW; don't add nav items or features not in the shell/spec.

### Example
```bash
python "$TOOL" generate --kind screen \
  --prompt "Audits list. SHELL (identical to 00-shell): logo left; nav Dashboard | Audits | Reports | Settings with 'Audits' active; right search + bell + avatar 'Casey R.'; left sidebar groups <...>. CONTENT: page header 'Audits' + subtitle, 'New audit' primary button top-right; filter bar (Status, Store, Date range, search); data table columns Store | Status | Tags | Discrepancies | Updated | (row menu), 8 realistic rows with status pills; pagination footer. Primary action: New audit. Omit: any nav item not in the shell, charts, maps." \
  --theme light \
  --colors "<palette from project file>" \
  --style "<style from project file>" \
  --description "<brand context from project file>" \
  --refs mockups/00-style-board.png mockups/00-shell.png mockups/01-dashboard.png logo.svg \
  -o mockups/02-audits-list.png
```

## Consistency rules (critical)
- Generate **one image per call**, in order: style board, then shell, then screens in **usage order**.
- On **every** screen call, pass `--refs mockups/00-style-board.png mockups/00-shell.png` plus the 2-3 most representative prior screens (and the logo). As the set grows, keep the board + shell + a few key screens rather than all of them.
- Always pass `--colors`, `--style`, `--description` from the project file.
- **Restate the shell copy verbatim** in each screen prompt — refs keep the look; the text keeps nav items/order/active-state from drifting.
- Save outputs as `mockups/NN-screen-name.png` (zero-padded, usage order; `00-` reserved for board + shell).

## Tips
- If a result comes back portrait or off-brand, retry once; then lower `--temperature` (e.g. 0.2) or simplify the prompt.
- Frames: `--frame browser` (default, clean browser window + URL bar), `--frame none` (full-bleed app screenshot), `--frame macbook` (laptop hero shot for a title/cover image).
- After each generation, **show the image** with the Read tool.

## Project file — `.forwardpath-webui-project.json`
Create at the workspace root to keep generations consistent and track progress.

```json
{
  "app_name": "Acme Ops Console — Web App",
  "description": "One-paragraph brand + product context passed as --description.",
  "brand_source": "codebase: /path/to/repo | entity research",
  "browsers": "desktop-first, modern evergreen browsers",
  "colors": { "primary": "#4F46E5", "foreground": "#0A0A0A", "destructive": "#DC2626" },
  "style": "Full --style string (clean SaaS aesthetic, shadcn/ui components, radii, shadows, density, motifs).",
  "typography": "Heading + body + mono font direction.",
  "brand_assets": ["public/logo.svg"],
  "chrome": {
    "nav_items": ["Dashboard", "Audits", "Reports", "Settings"],
    "active_treatment": "primary underline + medium weight",
    "logo": "top-left, 32px",
    "sidebar_groups": [{ "label": "Workspace", "items": ["Overview", "Stores"] }],
    "right_cluster": ["search", "notifications", "help", "user menu: Casey R."]
  },
  "render": { "tool": "scripts/webmock_gen.py", "aspect": "16:9", "size": "2K", "frame": "browser" },
  "style_board": "mockups/00-style-board.png",
  "shell": "mockups/00-shell.png",
  "screens": [
    { "id": "S01", "name": "dashboard", "path": "mockups/01-dashboard.png", "theme": "light", "order": 1,
      "description": "What the screen shows (grounded on SOW §ref)." }
  ]
}
```

Update `style_board`, `shell`, and the `screens` array after each successful generation.
