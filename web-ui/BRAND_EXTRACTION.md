# Brand extraction — grounding on a real Next.js + Tailwind codebase

Goal: fill §1 (Brand Foundation) and §2 (App Shell) of the spec with the app's **real** tokens, fonts, logos, and chrome, so the mockups look like screenshots of the actual product. If no codebase exists, use the SOW fallback at the bottom.

## Where to look (in priority order)

Search with Grep/Glob; read the hits. Prefer real, resolved values over guesses.

### 1. Design tokens
- **Tailwind v4** (CSS-first): `@theme` blocks and CSS custom properties in `app/globals.css` (or `styles/globals.css`). Look for `--color-*`, `--radius`, `--font-*`.
- **Tailwind v3**: `tailwind.config.{ts,js,cjs}` → `theme.extend.colors`, `borderRadius`, `fontFamily`, `boxShadow`.
- **shadcn/ui**: `components.json` (confirms shadcn + base color + CSS-vars mode) and the `:root` / `.dark` HSL variables in `globals.css` (`--background`, `--foreground`, `--primary`, `--border`, `--destructive`, `--muted`, `--accent`, `--ring`). Record light and dark.
- Resolve semantic aliases to concrete values (e.g. `--primary: 240 6% 10%` → note both the token name and the hex).

### 2. Typography
- `next/font` imports in `app/layout.tsx` (e.g. `Geist`, `Inter`, `next/font/google` or `local`), and the CSS variables they define (`--font-sans`, `--font-mono`).
- Heading vs body vs mono roles; default weights used in headings.

### 3. Logos & brand imagery
- `public/*.svg` / `public/*.png` (logo, wordmark, favicon, `icon.svg`, `apple-icon.png`, `opengraph-image`).
- Inline logo components (`components/logo.tsx`, an SVG in the header). Note exact files — pass them to the style board and shell via `--refs`.

### 4. App shell (the persistent chrome)
- Root and group layouts: `app/layout.tsx`, `app/(app)/layout.tsx`, `app/(dashboard)/layout.tsx`.
- Shell components: `components/**/{navbar,header,top-nav,sidebar,side-nav,app-sidebar,shell,nav-main}.tsx` (shadcn's `sidebar.tsx` if present).
- **Transcribe the nav model verbatim:** the array of nav items (label + href + icon), their order, groups/sections, and the active-state logic (`usePathname`, `aria-current`, active classes).
- Right cluster: search box, notifications, help, theme toggle (`next-themes`), user/account menu (avatar + items).
- Breadcrumbs and page-header patterns.

### 5. Component vocabulary & density
- `components/ui/*` (shadcn primitives present → use their names in the spec: Button, Card, Table, Dialog, Tabs, DropdownMenu, ...).
- Data-heavy patterns: TanStack Table, Recharts/visx, forms via React Hook Form + Zod.
- Note density (padding on cards/rows), default radius, and whether dark mode is `class`-based (`next-themes`) or media-based.

## Map findings → spec
Fill [`SPEC_TEMPLATE.md`](SPEC_TEMPLATE.md):
- §1.1 color table — include the real Tailwind/CSS token name beside each value; capture light + dark.
- §1.2 typography — the actual fonts and their roles.
- §1.3 layout — max content width, radius scale, shadow usage, density.
- §1.5 stack — only the libs actually present.
- §2 App Shell — the verbatim nav items/order, sidebar groups, logo placement, right cluster, active-state treatment. This is what keeps every mockup consistent.

Record the source file for each non-obvious value (e.g. `nav items: components/app-sidebar.tsx`) so the spec is auditable.

## If tokens are ambiguous or missing
- Multiple themes/brands in the repo: ask the user which one to mock.
- Tailwind defaults only (no custom theme): note that the brand is minimal/default and lean on logos + any accent color for identity; still fix the shell.

## Fallback — no codebase (SOW entity research)
Same approach as the `mobile-ui` skill:
1. Identify the entities named in the SOW (the client/company, parent group, key partners).
2. Research their public brands with web tools: logo, color palette, typography vibe, naming/wordmark rules.
3. Define a coherent foundation (color tokens, type, layout, motion) and a plausible app shell (nav items derived from the SOW's feature set, in usage order).
4. Mark §1/§2 as *derived from brand research* (not codebase-grounded) so the user knows to confirm.
