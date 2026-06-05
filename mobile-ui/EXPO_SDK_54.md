# Expo SDK 54 — capability & package map (grounding reference)

Use this to keep every screen and feature in the spec **technically feasible on Expo SDK 54**. If a SOW feature has no Expo-feasible path, flag it in the spec instead of drawing it.

## Platform baseline
- **Expo SDK 54** ≈ **React Native 0.81**, **React 19.1**, **New Architecture on by default**.
- iOS deployment target **15.1+**; Android **minSdk 24**, target/compile SDK 36 (16 KB page support).
- Distribution: **EAS Build**. **Expo Go** only runs modules bundled in the SDK; anything else needs a **development build**.
- Reanimated v4 requires the New Architecture (default in 54).

## Managed-first rule
Prefer first-party `expo-*` modules. A third-party native module (e.g. VisionCamera, MMKV, MSAL) is allowed **only via a development build** — note that cost explicitly in the spec. Never assume custom native code runs in Expo Go.

## Capability → package map
| Need | Use on Expo SDK 54 | Notes / constraints |
|---|---|---|
| Corporate SSO (Microsoft Entra ID, Okta, Google) | `expo-auth-session` + `expo-web-browser` + `expo-crypto` | OIDC + PKCE in managed workflow. Avoid `react-native-msal` (needs dev build). |
| Token / secret storage | `expo-secure-store` | Keychain / Keystore backed. |
| Biometric unlock | `expo-local-authentication` | Face ID / Touch ID / fingerprint. |
| Camera capture | `expo-camera` (`CameraView`) | Photo, video, **barcode/QR via `onBarcodeScanned`**. |
| Live frame processing / on-device CV (blur, glare, real-time detect) | **Not in `expo-camera`** | Do **post-capture** checks, or server-side; for true frame processors use `react-native-vision-camera` (**dev build**). |
| OCR / ML extraction | No first-party OCR | **Send image to backend** (recommended), or dev-build an ML lib. Keep CV/OCR server-side by default. |
| Image display & caching | `expo-image` | Fast, cached, blurhash. |
| Pick / edit / compress images | `expo-image-picker`, `expo-image-manipulator` | Resize/compress before upload. |
| Save to / read device media | `expo-media-library` | |
| Local relational store / offline queue | `expo-sqlite` | Async API + transactions; ideal for capture + sync queue. |
| Simple key-value (MMKV-like) | `expo-sqlite/kv-store` | Managed-workflow KV. `react-native-mmkv` needs a dev build. |
| File read/write + upload | `expo-file-system` | `uploadAsync`/streaming for media upload. |
| Background sync / deferred work | `expo-task-manager` + `expo-background-task` | `expo-background-fetch` is **deprecated**. Queue in SQLite, flush on connectivity. |
| Connectivity state | `expo-network` (one-shot) and/or `@react-native-community/netinfo` (listeners) | Both Expo-compatible. |
| Navigation | `expo-router` (file-based) **or** `@react-navigation/native` (native-stack + bottom-tabs) | Peers: `react-native-screens`, `react-native-safe-area-context`. |
| Animation & gesture | `react-native-reanimated` (v4) + `react-native-gesture-handler` | Worklet-based, New-Arch only. |
| Long / virtualized lists | `@shopify/flash-list` | |
| Haptics | `expo-haptics` | Success/warn/error feedback. |
| Frosted blur / gradients / vector | `expo-blur`, `expo-linear-gradient`, `react-native-svg` | SVG for charts, icons, motifs. |
| SF Symbols (iOS) | `expo-symbols` | |
| Fonts / splash / status bar | `expo-font`, `expo-splash-screen`, `expo-status-bar` | |
| Push / local notifications | `expo-notifications` | Remote push needs FCM/APNs; Android push limited in Expo Go (use dev build). |
| Localization / i18n | `expo-localization` (+ `i18n-js` or `lingui`) | |
| OTA updates | `expo-updates` | Via EAS Update. |
| Audio / video | `expo-audio`, `expo-video` | `expo-av` is removed/deprecated. |

## Common pitfalls to ground against
- **Real-time camera CV** (e.g. live blur/glare/quality on the preview): not possible with `expo-camera`. Spec it as **post-capture analysis** or **server-side**, or call out a VisionCamera **dev build**.
- **MMKV / MSAL / VisionCamera**: not in Expo Go → development build required.
- **Heavy on-device ML/OCR**: prefer backend inference; keep the device thin.
- **Push to Android in Expo Go**: use a development build.

> When unsure about a specific module's SDK 54 status, verify against the official Expo SDK 54 docs (or Context7 if available) before committing it to the spec.
