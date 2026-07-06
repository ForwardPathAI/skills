# {{APP_NAME}} — Web App Screen Spec

> Scope: **web app screens only** (desktop-first, {{BROWSERS}}). Native mobile apps are out of scope for this document.
>
> **Purpose:** define each screen precisely enough to generate consistent, credible desktop UI mockups and guide implementation. Tech target is **Next.js (App Router) + Tailwind**{{SHADCN}} — used to keep the UI web-feasible (see [`NEXT_TAILWIND.md`](NEXT_TAILWIND.md)).
>
> **Brand source:** {{BRAND_SOURCE}} (a real codebase at `{{REPO_PATH}}`, or SOW-named entity research).
>
> **⚠️ Grounding rule:** screens depict **only SOW-documented capabilities** and reuse the **same app shell** on every view. Do **not** invent features or restyle the chrome per screen. Anything not in the SOW is listed under *Inferred (not in SOW)* and excluded from mockups unless the client confirms it.

---

## 1. Brand Foundation ({{extracted from codebase | extracted from ENTITIES}})

The app is **{{APP_NAME}}**, used by **{{PRIMARY_ENTITY}}**{{PARENT_RELATION}}.

> **Brand naming / wordmark:** {{WORDMARK_RULE}}

### 1.1 Color tokens
> When codebase-derived, list the real token name (Tailwind class / CSS var) beside each value.

| Token | Value | Tailwind / CSS name | Role |
|---|---|---|---|
| `background` | `#______` | `bg-background` / `--background` | Page background |
| `foreground` | `#______` | `text-foreground` / `--foreground` | Primary text |
| `muted` | `#______` | `--muted` | Secondary surfaces |
| `muted-foreground` | `#______` | `--muted-foreground` | Secondary text |
| `primary` | `#______` | `--primary` | **Primary action**, brand |
| `primary-foreground` | `#______` | `--primary-foreground` | Text on primary |
| `accent` | `#______` | `--accent` | Secondary accent |
| `border` | `#______` | `--border` | Dividers, input borders |
| `success` | `#______` | — | Positive / go |
| `warning` | `#______` | — | Attention |
| `destructive` | `#______` | `--destructive` | Errors / danger |

**Dark mode:** {{DARK_MODE_NOTE}} (which screens/default; `class` strategy vs `media`).
Use color sparingly and semantically: primary = action, warning = check this, destructive = danger.

### 1.2 Typography
- **Display / headings:** {{HEADING_FONT}} ({{next/font import if codebase}}).
- **UI / body:** {{BODY_FONT}}.
- **Mono (code/data):** {{MONO_FONT}} (if used).

| Style | Size / Line | Weight |
|---|---|---|
| Display | 48 / 52 | Semibold |
| H1 | 32 / 40 | Semibold |
| H2 | 24 / 32 | Semibold |
| H3 | 18 / 28 | Medium |
| Body | 14 / 22 | Regular |
| Small / caption | 12 / 16 | Regular/Medium |

### 1.3 Layout, shape & elevation
- **Grid:** 12-column, max content width {{MAX_W}} (e.g. 1280-1440), gutters {{GUTTER}}.
- **Spacing scale:** Tailwind default (4px base): 1 / 2 / 3 / 4 / 6 / 8 / 12 / 16.
- **Radii:** {{RADIUS}} (e.g. `rounded-lg` cards, `rounded-md` controls, `rounded-full` avatars/pills).
- **Elevation:** {{SHADOW}} (prefer `border` + subtle `shadow-sm`; heavier shadow only for popovers/modals).
- **Density:** {{DENSITY}} (comfortable vs compact tables/forms).

### 1.4 Motion & feedback
- Transitions 150-200ms ease-out; hover/focus states on all interactive elements.
- Skeletons (not spinners) for data regions; toasts for async results; optimistic UI where sensible.

### 1.5 Next.js + Tailwind reference stack (feasibility)
List only what's actually needed, mapped from [`NEXT_TAILWIND.md`](NEXT_TAILWIND.md). Example:
App Router (`app/`) · Server Components + `"use client"` islands · Tailwind {{TW_VERSION}} · shadcn/ui ({{COMPONENTS}}) · TanStack Table (data grids) · Recharts/visx (charts) · React Hook Form + Zod (forms) · TanStack Query (client data) · next/font · lucide-react (icons).

---

## 2. App Shell (persistent chrome — identical on every screen)

> This is the credibility anchor. Transcribe **exact** labels and order. The `00-shell` mockup renders this with an empty content canvas; every screen mockup restates it verbatim.

### 2.1 Top navigation
- **Logo / wordmark:** {{LOGO}} placement (e.g. top-left, 32px).
- **Primary nav items (in order):** {{NAV_ITEMS}} (e.g. `Dashboard`, `Audits`, `Reports`, `Settings`).
- **Active state:** {{ACTIVE_TREATMENT}} (e.g. primary underline + bold).
- **Right cluster:** {{RIGHT_CLUSTER}} (global search, notifications, help, user/account menu with avatar).

### 2.2 Sidebar (if present)
- **Groups + items (in order):** {{SIDEBAR_GROUPS}}.
- **Behavior:** collapsible? default width? icon-only collapsed state?
- **Active / hover states:** {{SIDEBAR_STATES}}.

### 2.3 Content frame
- **Breadcrumbs:** {{BREADCRUMBS}} (pattern + when shown).
- **Page header pattern:** title + subtitle + primary action (top-right), then content region.
- **Footer:** {{FOOTER}} (or none).

### 2.4 Empty states / global patterns
- Loading skeletons, empty-state illustration + CTA, error banner, toast position.

---

## 3. Information Architecture & Navigation
```
{{FLOW_DIAGRAM}}
```
Describe route structure (App Router segments), which screens are in the shell vs full-bleed (e.g. auth), and any modal/drawer routes.

---

## 4. Screen Inventory
| # | Screen | Flow | Route | In shell? | SOW basis |
|---|---|---|---|---|---|
| S01 | {{...}} | {{...}} | `/{{...}}` | yes/no | §{{...}} |

> Mark each row with a real SOW section reference, `implied`, or `inferred`.

---

## 5. Screen Definitions

For **every** screen, use this block:

### S{{NN}} · {{Screen name}}
- **Route / flow:** `/{{route}}` · {{flow}}
- **In shell:** yes (nav `{{active item}}` active) / no (full-bleed, e.g. auth)
- **SOW basis:** §{{ref}} (or `implied` / `inferred`)
- **Purpose:** one sentence — the single job of this screen.
- **Layout (content region, by area):** describe the 12-col regions — e.g. left filters rail, main table, right detail drawer; or hero + card grid. Left→right, top→bottom.
- **Key components:** list with real labels (shadcn/ui component names where they apply — Table, Card, Dialog, Tabs, etc.).
- **States:** default / loading (skeleton) / empty / error / no-permission as relevant.
- **Primary action:** the one obvious next step (usually a top-right button).
- **Next.js/Tailwind mapping:** server vs client, key libs, any feasibility caveat.

Repeat for all screens, ordered by usage.

---

## Appendix · Grounding decisions
- **Inferred (not in SOW), excluded from mockups:** {{list}}.
- **Out of scope (native mobile / back-office not in SOW):** {{list}}.
- **Open questions for the client:** {{list}}.
