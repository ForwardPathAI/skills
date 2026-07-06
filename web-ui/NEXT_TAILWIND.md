# Next.js + Tailwind — capability & feasibility map (grounding reference)

Use this to keep every screen and feature in the spec **feasible as a Next.js (App Router) + Tailwind web app**. If a SOW feature has no clean web path, flag it in the spec instead of drawing it. This mirrors the role [`../mobile-ui/EXPO_SDK_54.md`](../mobile-ui/EXPO_SDK_54.md) plays for the mobile skill. For the full Forward Path stack and conventions, see the [`product-foundation`](../product-foundation/SKILL.md) skill.

## Platform baseline
- **Next.js App Router** (`app/`), React Server Components by default; `"use client"` only for interactive islands.
- **Tailwind** (v3 config-based or v4 CSS-first `@theme`) + **shadcn/ui** (Radix primitives, CSS variables, `class`-based dark mode via `next-themes`).
- **Desktop-first**, responsive down; icons via **lucide-react**; fonts via **next/font**.
- Data: **TanStack Query** (client) over **Hono RPC** / route handlers + server actions; forms via **React Hook Form + Zod**.

## Layout conventions to reflect in mockups
- **Shell = a layout.** The nav/sidebar live in `app/(app)/layout.tsx` and wrap every child route — which is exactly why every mockup must reuse the same shell. Auth/marketing routes use a different (or no) shell → those screens are full-bleed.
- **Page = `page.tsx`** rendering a header (title + subtitle + primary action) then the content region.
- **Modals/drawers** map to Dialog/Sheet (often intercepting routes) — fine to depict as overlays.
- **Route segments** → breadcrumbs and active nav state.

## Capability → web pattern
| Need | Use | Notes |
|---|---|---|
| App chrome (nav + sidebar) | shadcn `sidebar`, custom `navbar`, in a route-group `layout.tsx` | The persistent shell; identical on every in-app screen. |
| Auth / SSO | Better Auth + Microsoft SSO (route handlers) | Sign-in is a full-bleed screen (no shell). |
| Data tables / grids | **TanStack Table** + shadcn `Table` | Sorting, filters, pagination, row actions, sticky header. |
| Forms | **React Hook Form + Zod** + shadcn `Form`, `Input`, `Select`, `Checkbox` | Inline validation, sections, sticky save bar. |
| Charts / analytics | **Recharts** or **visx** | Cards with KPI + trend; keep to what the SOW reports. |
| Dialogs / drawers / menus | shadcn `Dialog`, `Sheet`, `DropdownMenu`, `Popover`, `Command` (⌘K) | Radix-backed. |
| Tabs / segmented views | shadcn `Tabs` | For detail screens. |
| Notifications / async feedback | shadcn `Toast`/`Sonner`, `Skeleton` for loading | Skeletons, not spinners. |
| File upload | route handler / server action + dropzone | Show drag-drop + progress; heavy processing is server-side. |
| Real-time | polling via TanStack Query, or WebSocket/SSE island | Depict live badges/counters modestly. |
| Rich text / editor | Tiptap (client island) | Only if the SOW needs authoring. |
| Maps | react-map-gl / Leaflet (client island) | Only if the SOW documents geographic data. |
| Dark mode | `next-themes`, `class` strategy | Spec which screens/default; shadcn tokens already dual. |
| Tables → export, print, PDF | server-generated (out of visual scope) | A button in the UI is fine; the artifact is backend. |

## Common pitfalls to ground against
- **Native-mobile widgets** (iOS switches, bottom tab bars, pull-to-refresh): not web patterns — use web equivalents (toggle, top nav, refresh button).
- **Inconsistent chrome:** the fastest way to look fake. Nav items, order, logo, and active-state must match the shell on every screen — restate them verbatim in each prompt.
- **Inventing nav items or features** not in the SOW/shell: omit them.
- **Over-dense dashboards:** keep to the metrics the SOW actually reports; one clear primary action per screen.
- **Mobile-only flows on desktop:** if the SOW is truly mobile, this is the wrong skill — use `mobile-ui`.

> When unsure whether a pattern fits, prefer the shadcn/ui component vocabulary the codebase already uses (from [`BRAND_EXTRACTION.md`](BRAND_EXTRACTION.md)) so mockups match what will actually be built.
