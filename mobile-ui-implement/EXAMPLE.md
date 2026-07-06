# Worked example — PRS Price Tag Audit

A filled-in sample from Mode A to show the templates in use. Source: the PRS deck (`PRS_PriceTagAudit_Mobile_UI2.pdf`, burst to page PNGs) as layout truth + `MOBILE_APP_SCREENS_SPEC.md` as token/behavior truth. This is illustrative, not exhaustive — real runs emit the full `00-foundation.md`, `INDEX.md`, and every `NN-screen.md`.

---

## Excerpt — `ui-blueprints/00-foundation.md`

### 1. Design tokens → `theme/tokens.ts`
```ts
export const colors = {
  ink: '#252525',
  ink60: '#6B6B6B',
  ink30: '#C3C3C3',
  premiumGreen: '#00A475',   // primary action, valid capture, success
  greenPressed: '#008A62',
  greenTint: '#E6F6F0',
  petrol: '#002C39',         // dark capture chrome / gradient start
  aqua: '#2BB9A3',           // gradient end
  amber: '#FFB100',          // check-this / in-review
  magenta: '#C8004E',        // critical / major discrepancy
  navy: '#122044',
  surface: '#FFFFFF',
  surfaceSunken: '#F8F8F8',
  hairline: '#F0F0F0',
} as const;

export const dark = {
  background: '#001A22',            // petrol → #001A22 gradient end
  surface: 'rgba(255,255,255,0.06)', // frosted (expo-blur) controls
  onSurface: '#FFFFFF',
} as const;

export const type = {
  display: { fontSize: 34, lineHeight: 40, fontFamily: 'Tiempos-Light' },
  h1: { fontSize: 28, lineHeight: 34, fontWeight: '600' },
  h2: { fontSize: 22, lineHeight: 28, fontWeight: '600' },
  h3: { fontSize: 18, lineHeight: 24, fontWeight: '600' },
  body: { fontSize: 16, lineHeight: 24 },
  bodyStrong: { fontSize: 16, lineHeight: 24, fontWeight: '600' },
  caption: { fontSize: 13, lineHeight: 18 },
  overline: { fontSize: 11, lineHeight: 14, fontWeight: '500', letterSpacing: 0.66, textTransform: 'uppercase' },
} as const;

export const space = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32 } as const;
export const radius = { control: 12, card: 20, sheet: 28, pill: 999 } as const;
export const elevation = { card: { shadowColor: '#002C39', shadowOpacity: 0.08, shadowRadius: 24, shadowOffset: { width: 0, height: 8 }, elevation: 4 } } as const;
```

### 2. Navigation skeleton (expo-router)
```
app/
  _layout.tsx                  # root stack: splash → (auth) → (tabs)
  (auth)/sign-in.tsx           # S02
  (tabs)/_layout.tsx           # tabs: today | audits | profile
  (tabs)/today.tsx             # S05
  (tabs)/audits.tsx            # S16 discrepancy/history
  (tabs)/profile.tsx           # S20
  store/[id]/index.tsx         # S08 store detail
  session/[id]/start.tsx       # S09
  session/[id]/capture.tsx     # S10  (contextual — not a tab)
  session/[id]/review.tsx      # S12
  session/[id]/summary.tsx     # S14
```

### 3. Shared component inventory (excerpt)
- `Button` — primary/secondary CTA. Props `{ label, variant: 'primary'|'secondary'|'ghost', onPress, disabled? }`. Tokens `colors.premiumGreen`, `radius.control`, height 56. Recipe `PATTERNS.md#press-spring`.
- `HintChip` — single dark frosted hint. Props `{ text, tone: 'neutral'|'warning' }`. Tokens `dark.surface`, `colors.amber`, `radius.pill`. Recipe `PATTERNS.md#error-shake` on warning.
- `SyncChip` — offline/queued count. Props `{ queued: number, state: 'offline'|'uploading'|'synced' }`. Tokens `colors.amber`/`colors.premiumGreen`, `radius.pill`.
- `CaptureThumbnail` — last capture + running count. Props `{ uri, count, onPress }`. Tokens `radius.control`.
- `StoreCard`, `ProgressRing`, `SectionHeader`, `StatBadge`, `Skeleton` — used across Today/Stores/Summary.

### 4. Dependencies (Expo Go-safe)
```bash
npx expo install expo-router expo-camera expo-haptics expo-blur expo-linear-gradient \
  react-native-svg react-native-reanimated react-native-gesture-handler \
  @shopify/flash-list expo-image expo-secure-store expo-sqlite expo-file-system
```
> OUT OF SCOPE for Expo Go → stubbed per screen: live-frame CV (`react-native-vision-camera`), MMKV, MSAL.

---

## Full blueprint — `ui-blueprints/10-guided-capture.md`

# S10 · Guided Photo Capture

- **Mockup:** `mockups/07-guided-capture.png`  ← open this before building
- **Theme:** dark
- **Route:** `app/session/[id]/capture.tsx`
- **Purpose:** capture one price tag with live-feeling guidance and instant green-check confidence.
- **Depends on:** `HintChip`, `SyncChip`, `CaptureThumbnail`, `Button`; tokens `colors`, `dark`, `space`, `radius`, `type`.

## Layers (build in this order)
### 1. Background
Full-bleed live `expo-camera` `CameraView`. Behind/over it a subtle `petrol` vignette so overlays stay legible. Recipe: `PATTERNS.md#camera`.

### 2. Chrome
Safe-area edges: top + bottom. Status bar: light.
- Header left: `End` button with X icon (confirm dialog before leaving).
- Header right: aisle chip "Aisle 12", flash toggle, voice-prompt toggle.
Tab bar: none (capture is contextual).

### 3. Content (top → bottom)
- `HintChip` "Hold steady" — single, centered near top, one hint at a time.
- Badge "QR found" with check — appears top-center when a QR decodes.
- `ReticleOverlay` (SVG + Reanimated) framing the tag; turns `colors.premiumGreen` on valid, `colors.amber` on invalid; big green check pops on valid.
- Parsed-preview mini-card over the tag ("Samsung RF28…", "$2,199") mirroring the mockup.

### 4. Overlays (absolute)
- Bottom-center: `Shutter` 72px with thin progress ring (`PATTERNS.md#progress-ring`).
- Bottom-left: `CaptureThumbnail` uri + count "84" → navigate to review.
- Bottom-right: `SyncChip` queued "13 queued" → navigate to queue.

### 5. Modals / sheets
End-session confirm dialog. Quality-fail → S11 re-capture sheet over frozen frame.

## States
| State | Trigger | What changes |
|---|---|---|
| detecting | default | amber reticle, "Hold steady" hint |
| valid | frame passes checks | green reticle + check pop + success haptic; shutter armed |
| invalid | blur/glare/angle | amber reticle + single fix hint + `error-shake` |
| processing | after shutter | brief spinner on thumbnail |
| offline | no network | captures queue silently; `SyncChip` shows queued count |
| permission revoked | camera denied | inline recover card + `Linking.openSettings()` |

## Interactions
| Element | Action |
|---|---|
| Shutter | capture photo → write to `expo-file-system` → enqueue → count++ |
| Thumbnail | navigate to `session/[id]/review` |
| SyncChip | navigate to capture queue |
| End | confirm dialog → pop to store detail |
| Flash / voice / aisle | toggle local state |

## Animations & haptics
| Trigger | Effect | Package | Recipe | Source |
|---|---|---|---|---|
| valid frame | reticle→green + check pop | reanimated + expo-haptics | PATTERNS.md#success-pop | spec |
| invalid frame | amber shake on hint chip | reanimated + expo-haptics | PATTERNS.md#error-shake | spec |
| shutter press | scale press + light haptic | reanimated + expo-haptics | PATTERNS.md#press-spring | inferred-default |
| shutter capture | progress ring sweep | react-native-svg | PATTERNS.md#progress-ring | spec |

## Data (mock)
```ts
export const mockCapture = {
  sessionId: 'sess_6817',
  aisle: 'Aisle 12',
  count: 84,
  queued: 13,
  lastThumbUri: undefined, // use a placeholder tile until camera writes one
  parsedPreview: { brand: 'Samsung', model: 'RF28…', price: '$2,199' },
};
```

## Expo Go mapping / stubs
- Camera preview + photo + QR → `expo-camera` (`CameraView`, `onBarcodeScanned`).
- **Live frame quality (blur/glare/angle) → NOT in Expo Go.** Stub: drive "valid" from the barcode-detected event or a 1.5s timer, then `success-pop`; do real quality checks post-capture (route to S11). Leave `// TODO(dev-build): react-native-vision-camera frame processor for live quality`.
- Capture write + queue → `expo-file-system` + `expo-sqlite` queue; auto-flush on connectivity.
- Haptics → `expo-haptics`. Frosted controls → `expo-blur`.

## Files to create / modify
- `app/session/[id]/capture.tsx` (new)
- `components/ReticleOverlay.tsx` (new — screen-specific)
- `components/Shutter.tsx` (new — screen-specific)
- shared `HintChip`, `SyncChip`, `CaptureThumbnail` already built in foundation.

## Acceptance checklist (compare against `mockups/07-guided-capture.png`)
- [ ] Full-bleed dark camera viewfinder with petrol chrome.
- [ ] `End` top-left; aisle "Aisle 12" + flash + voice top-right.
- [ ] Single centered hint chip; only ONE hint visible at a time.
- [ ] Reticle frames the tag; green + check on valid, amber on invalid.
- [ ] "QR found" badge appears on decode.
- [ ] 72px shutter bottom-center with progress ring.
- [ ] Thumbnail + count "84" bottom-left; `SyncChip` "13 queued" bottom-right.
- [ ] Success haptic on valid; error shake+haptic on invalid.
- [ ] No raw hex / magic numbers; only tokens, shared components, PATTERNS recipes.
