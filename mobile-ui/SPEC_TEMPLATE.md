# {{APP_NAME}} — Mobile App Screen Spec

> Companion to the SOW reference. Scope: **mobile app screens only** ({{PLATFORMS}}). Web admin / client dashboards / back-office are **out of scope** for this document.
>
> **Purpose:** define each screen precisely enough to generate premium UI mockups and guide implementation. Tech target is **Expo SDK 54 + React Native** — used to keep the UI native-feasible (see [`EXPO_SDK_54.md`](EXPO_SDK_54.md)).
>
> **North-star UX:** *{{NORTH_STAR}}* (e.g. one job per screen, one obvious next action, near-zero reading).
>
> **⚠️ Grounding rule:** screens must depict **only SOW-documented capabilities** for the mobile app. Do **not** invent features. Anything not in the SOW is listed under *Inferred (not in SOW)* and excluded from mockups unless the client confirms it.

---

## 1. Brand Foundation (extracted from {{ENTITIES}})

The app is **{{APP_NAME}}**, used by **{{PRIMARY_ENTITY}}**{{PARENT_RELATION}}. Brand is anchored to {{BRAND_ANCHOR}}.

> **Brand naming / wordmark:** {{WORDMARK_RULE}}

### 1.1 Color tokens
| Token | Hex | Role |
|---|---|---|
| `ink` | `#______` | Primary text |
| `ink-60` | `#______` | Secondary text |
| `ink-30` | `#______` | Disabled / placeholder |
| `primary` | `#______` | **Primary brand action**, success |
| `primary-pressed` | `#______` | Pressed/active |
| `primary-tint` | `#______` | Success surfaces, selected chips |
| `accent` | `#______` | Secondary brand accent |
| `warning` | `#______` | Attention / soft warning |
| `critical` | `#______` | Errors / critical state |
| `surface` | `#FFFFFF` | Cards, sheets |
| `background` | `#______` | App background |
| `hairline` | `#______` | Dividers, borders |

**Dark mode:** {{DARK_MODE_NOTE}} (state which screens default to dark vs light).
Use color sparingly and semantically: primary = good/go, warning = check this, critical = problem.

### 1.2 Typography
- **Display / accents:** {{DISPLAY_FONT}} (used sparingly for headings / large numerals).
- **UI / body:** {{UI_FONT}} (clean, legible).
- **Signature move:** {{BRAND_MOTIF}}.

| Style | Size / Line | Weight |
|---|---|---|
| Display | 34 / 40 | Light |
| H1 | 28 / 34 | Semibold |
| H2 | 22 / 28 | Semibold |
| Body | 16 / 24 | Regular |
| Caption | 13 / 18 | Regular/Medium |
| Overline | 11 / 14 | Medium, tracked, UPPERCASE |

### 1.3 Layout, shape & elevation
- **Spacing scale:** 4 / 8 / 12 / 16 / 20 / 24 / 32. Screen side padding `20`.
- **Radii:** controls `12`, cards `20`, sheets `28`, pills `999`.
- **Touch targets:** min `48×48`; primary CTA `56` tall, full-width.
- **Elevation:** soft, low-contrast shadows; prefer hairlines + tint over heavy shadows.

### 1.4 Motion & feedback
- Transitions 200–280 ms ease-out; meaningful shared-element transitions.
- Success → spring + success haptic (`expo-haptics`); error → error haptic + subtle shake.
- Skeleton loaders (not spinners); branded pull-to-refresh.

### 1.5 Expo SDK 54 reference stack (feasibility)
List only modules actually needed, mapped from [`EXPO_SDK_54.md`](EXPO_SDK_54.md). Example:
`expo-camera` · `expo-router`/`react-navigation` · `expo-auth-session` (SSO) · `expo-secure-store` · `expo-sqlite` (+ `expo-sqlite/kv-store`) · `expo-file-system` + `expo-task-manager`/`expo-background-task` · `expo-network` · `@shopify/flash-list` · `react-native-reanimated` + `gesture-handler` · `expo-haptics` · `expo-image` · `react-native-svg`.

---

## 2. Information Architecture & Navigation
**Bottom tabs ({{TAB_COUNT}}):** {{TABS}}.
Describe contextual (non-tab) flows, persistent chrome, and the connectivity/sync indicator.

```
{{FLOW_DIAGRAM}}
```

---

## 3. Screen Inventory
| # | Screen | Flow | Theme | SOW basis |
|---|---|---|---|---|
| S01 | {{...}} | {{...}} | light/dark | §{{...}} |

> Mark each row with a real SOW section reference, `implied`, or `inferred`.

---

## 4. Screen Definitions

For **every** screen, use this block:

### S{{NN}} · {{Screen name}}
- **Flow / theme:** {{flow}} · {{light|dark}}
- **SOW basis:** §{{ref}} (or `implied` / `inferred`)
- **Purpose:** one sentence — the single job of this screen.
- **Layout (top → bottom):** status bar → header → body sections → tab bar/CTA.
- **Key components:** list (with real labels, not lorem).
- **States:** default / loading / empty / error / offline as relevant.
- **Primary action:** the one obvious next step.
- **Low cognitive load:** why it's effortless (what was removed, what's automatic).
- **Expo SDK 54 mapping:** packages used and any dev-build caveat.

Repeat for all screens, ordered by usage.

---

## Appendix · Grounding decisions
- **Inferred (not in SOW), excluded from mockups:** {{list}}.
- **Out of scope (web/admin/back-office):** {{list}}.
- **Open questions for the client:** {{list}}.
