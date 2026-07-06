# Blueprint templates

Two templates. Mode A writes `00-foundation.md` once, then one `NN-screen-name.md` per screen. Fill every field. Keep values as **token references** (e.g. `colors.premiumGreen`, `space.20`), never raw hex or magic numbers, except inside `theme/tokens.ts` itself.

---

## `ui-blueprints/00-foundation.md`

```markdown
# Foundation — <App name>

Source: <mockup folder / PDF> + <spec path, if any>. Target: Expo Go (SDK 54, React Native).

## 1. Design tokens → `theme/tokens.ts`
Paste-ready. Screens import from here; no screen defines its own colors/sizes.

​```ts
export const colors = {
  ink: '#252525',
  ink60: '#6B6B6B',
  // ...one entry per token in the palette, light + dark where they differ
} as const;

export const dark = { background: '#001A22', surface: 'rgba(255,255,255,0.06)' /* ... */ } as const;

export const type = {
  display: { fontSize: 34, lineHeight: 40, fontFamily: 'Serif-Light' },
  h1: { fontSize: 28, lineHeight: 34, fontWeight: '600' },
  body: { fontSize: 16, lineHeight: 24 },
  // ...full scale
} as const;

export const space = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32 } as const;
export const radius = { control: 12, card: 20, sheet: 28, pill: 999 } as const;
export const elevation = { card: { /* shadow tokens */ } } as const;
​```

## 2. Navigation skeleton (expo-router)
File layout + which screen renders where. Example:
​```
app/
  _layout.tsx            # root stack: splash → (auth) → (tabs)
  (tabs)/_layout.tsx     # bottom tabs: today | audits | profile
  (tabs)/today.tsx       # S05
  session/[id]/capture.tsx  # S10 (contextual, not a tab)
​```
List each route → screen id.

## 3. Shared component inventory
Every component used on 2+ screens. For each: name, one-line purpose, props interface, tokens used, and the recipe/pattern it relies on.

### `<ComponentName>`
- Purpose: <one line>
- Props:
  ​```ts
  interface <ComponentName>Props { /* ... */ }
  ​```
- Tokens: <colors.x, radius.card, ...>
- Notes: <variants, states, PATTERNS.md recipe if animated>

## 4. Dependencies to install
Only Expo Go-safe packages, with the exact install command. Flag any dev-build-only need here as "OUT OF SCOPE for Expo Go → stubbed per screen".
```

---

## `ui-blueprints/NN-screen-name.md`

```markdown
# S<NN> · <Screen name>

- **Mockup:** `mockups/NN-screen-name.png`  ← open this before building
- **Theme:** light | dark
- **Route:** <expo-router path from foundation §2>
- **Purpose:** one sentence — the single job of this screen.
- **Depends on:** <shared components + tokens this screen needs from 00-foundation.md>

## Layers (build in this order)
### 1. Background
<solid colors.x | LinearGradient a→b | expo-image full-bleed>. Recipe: <PATTERNS.md#...>

### 2. Chrome
Safe-area edges: <top/bottom>. Status bar: <light|dark>. Header: <left / title / right, with exact copy>. Tab bar: <shown? which tab active | none>.

### 3. Content (top → bottom)
Component tree with EXACT transcribed copy from the mockup:
- `SectionHeader` "TODAY'S COVERAGE"
- `ProgressRing` value 0.6, label "3 of 5 stores"
- `StoreCard`
  - retailer chip "Home Depot"
  - title "Southlake #6817"
  - meta "142 SKUs · Electronics, Appliances"
  - `Button` variant=primary "Start"
- ...

### 4. Overlays (absolute)
<floating CTA pinned bottom / sync chip top-right / toast>. Give position + z-order.

### 5. Modals / sheets
<bottom sheet contents, or "none">.

## States
| State | Trigger | What changes |
|---|---|---|
| default | — | <...> |
| loading | fetch pending | <skeletons for which parts> |
| empty | no data | <copy + illustration> |
| error | fetch failed | <inline banner + retry> |
| offline | no network | <cached + sync chip count> |

## Interactions
| Element | Action |
|---|---|
| `Start` button | navigate to <route> with `{ storeId }` |
| store card | navigate to <route> |
| ... | ... |

## Animations & haptics
| Trigger | Effect | Package | Recipe | Source |
|---|---|---|---|---|
| CTA press | spring scale 1→0.96→1 | reanimated | PATTERNS.md#press-spring | inferred-default |
| capture valid | green check pop + success haptic | reanimated + expo-haptics | PATTERNS.md#success-pop | spec |
| numbers appear | count-up | reanimated | PATTERNS.md#count-up | spec |

## Data (mock)
​```ts
// Mock shape Mode B should render until a backend is wired.
export const mock<Screen> = { /* realistic, on-domain values — never lorem */ };
​```

## Expo Go mapping / stubs
- <capability> → <expo module>.
- <dev-build-only capability> → **stub**: <exact fallback behavior + `// TODO(dev-build): ...` marker>.

## Files to create / modify
- `app/<route>.tsx` (new)
- `components/<Shared>.tsx` (only if not already built in foundation)

## Acceptance checklist (compare against the mockup image)
- [ ] Background matches (<gradient / color>).
- [ ] Header shows "<exact title>" with <serif/grotesque> + right-side <control>.
- [ ] <N> content sections present in order, with the transcribed copy.
- [ ] Primary CTA is <color> "<label>", <height>px, pinned <where>.
- [ ] Semantic colors used correctly (green=go, amber=check, magenta/critical=problem).
- [ ] States render (loading skeletons, empty, offline) per the table.
- [ ] Animations fire on the listed triggers; no raw hex or magic numbers in the file.
```
