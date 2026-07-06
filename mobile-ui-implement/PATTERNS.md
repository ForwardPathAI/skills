# Expo Go implementation patterns

Copy-adaptable recipes for building mockup screens in an **Expo Go-compatible** app. Blueprints link here by anchor (e.g. `PATTERNS.md#press-spring`). Everything below runs in Expo Go on SDK 54 — no development build, no custom native code.

## Expo Go safe-list

**Bundled in Expo Go — use freely:**

| Need | Module |
|---|---|
| Navigation | `expo-router` (file-based) — peers `react-native-screens`, `react-native-safe-area-context` (bundled) |
| Animation / gesture | `react-native-reanimated` (v4), `react-native-gesture-handler` |
| Long lists | `@shopify/flash-list` (bundled) — else core `FlatList` |
| Camera | `expo-camera` (`CameraView`, `onBarcodeScanned`) |
| Haptics | `expo-haptics` |
| Blur / gradient / vector | `expo-blur`, `expo-linear-gradient`, `react-native-svg` |
| Fast images | `expo-image` |
| Secrets / tokens | `expo-secure-store` |
| Local DB + KV | `expo-sqlite`, `expo-sqlite/kv-store` |
| Files / upload | `expo-file-system` |
| Background work | `expo-task-manager` + `expo-background-task` |
| Connectivity | `expo-network`, `@react-native-community/netinfo` (bundled) |
| SSO / OAuth | `expo-auth-session` + `expo-web-browser` + `expo-crypto` |
| Fonts / splash / status bar | `expo-font`, `expo-splash-screen`, `expo-status-bar` |
| Bottom sheet | `@gorhom/bottom-sheet` (pure JS on reanimated + gesture-handler) |

**NOT in Expo Go — never import; stub instead:**

| Wanted | Why blocked | Expo Go substitute / stub |
|---|---|---|
| `react-native-vision-camera` (live frame CV, blur/glare detection) | needs dev build | `expo-camera` preview + **post-capture** or timer-driven mock; `// TODO(dev-build)` |
| `react-native-mmkv` | needs dev build | `expo-sqlite/kv-store` |
| `react-native-msal` | needs dev build | `expo-auth-session` (OIDC + PKCE) |
| on-device OCR / ML | no first-party module | send image to backend; render mock parsed fields |
| any custom native module | not in Expo Go | flag in blueprint, stub with mock data |

> When unsure whether a module is in Expo Go, check the Expo SDK 54 docs before importing it.

---

## `theme/tokens.ts` usage

All screens import tokens; none define their own values.

```ts
import { colors, dark, type, space, radius } from '@/theme/tokens';

const s = StyleSheet.create({
  card: { backgroundColor: colors.surface, borderRadius: radius.card, padding: space[5] },
  title: { ...type.h2, color: colors.ink },
});
```

For light/dark, resolve a palette once (e.g. a `useTheme()` hook returning `colors` or `dark`) and reference it — never branch on hex inline.

---

## Layer stacking

Build the layers a blueprint lists in order; later layers sit above earlier ones.

```tsx
<View style={{ flex: 1 }}>
  {/* 1. Background */}
  <LinearGradient colors={[colors.petrol, colors.aqua]} style={StyleSheet.absoluteFill} />
  {/* 2. Chrome + 3. Content */}
  <SafeAreaView style={{ flex: 1 }} edges={['top']}>
    <Header />
    <FlashList data={...} renderItem={...} />
  </SafeAreaView>
  {/* 4. Overlays — absolute, above content */}
  <View style={{ position: 'absolute', bottom: space[5], left: space[5], right: space[5] }}>
    <Button variant="primary" label="Start audit" />
  </View>
  {/* 5. Modals/sheets — portalled above everything */}
  <BottomSheet ... />
</View>
```

- Full-bleed background: `StyleSheet.absoluteFill`.
- Floating CTA / chips: absolute, offset by `space` tokens; respect safe-area insets from `useSafeAreaInsets()`.
- Frosted chrome (dark screens): `expo-blur` `<BlurView intensity={30} tint="dark" />` behind controls.

---

## Animation recipes (Reanimated v4)

All worklet-based; New Architecture is on by default in SDK 54.

### press-spring — CTA / card press feedback {#press-spring}
```tsx
const scale = useSharedValue(1);
const aStyle = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));
// onPressIn:  scale.value = withSpring(0.96, { damping: 15, stiffness: 300 });
// onPressOut: scale.value = withSpring(1);
```
Pair primary-action presses with `Haptics.impactAsync(ImpactFeedbackStyle.Light)`.

### success-pop — confirm / valid-capture green check {#success-pop}
```tsx
const s = useSharedValue(0);
// on success:
s.value = withSequence(withSpring(1.15, { damping: 8 }), withSpring(1));
Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
```

### error-shake — invalid input / failed capture hint {#error-shake}
```tsx
const x = useSharedValue(0);
// on fail:
x.value = withSequence(withTiming(-6, { duration: 50 }), withRepeat(withTiming(6, { duration: 100 }), 3, true), withTiming(0, { duration: 50 }));
Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
```
Use with the `warning`/`critical` token color on the offending element.

### count-up — big stat numerals {#count-up}
```tsx
const n = useSharedValue(0);
useEffect(() => { n.value = withTiming(target, { duration: 900, easing: Easing.out(Easing.cubic) }); }, [target]);
const props = useAnimatedProps(() => ({ text: `${Math.round(n.value)}` }));
// render an Animated TextInput (editable=false) with animatedProps for on-UI-thread text.
```

### progress-ring — sync / coverage ring {#progress-ring}
`react-native-svg` `<Circle>` with animated `strokeDashoffset`:
```tsx
const p = useSharedValue(0); // 0..1
const animatedProps = useAnimatedProps(() => ({ strokeDashoffset: C * (1 - p.value) }));
// C = 2 * Math.PI * r; p.value = withTiming(0.6, { duration: 700 });
```

### skeleton — list/loading placeholders (not spinners) {#skeleton}
```tsx
const o = useSharedValue(0.4);
useEffect(() => { o.value = withRepeat(withTiming(1, { duration: 800 }), -1, true); }, []);
// apply o to opacity of gray token blocks shaped like the real content.
```

### shared-element — card → detail transition {#shared-element}
Use `expo-router` shared transitions or a Reanimated layout animation on a matching `sharedTransitionTag`. Keep it to 200–280ms ease-out. If it complicates the build, fall back to a standard native-stack push and note it.

### screen transitions {#transitions}
Default native-stack animation is fine. For custom timing use 200–280ms, ease-out; declare per-route in the `expo-router` `Stack.Screen` options.

---

## Haptics map

| Moment | Call |
|---|---|
| primary tap | `impactAsync(ImpactFeedbackStyle.Light)` |
| success / valid capture / confirm | `notificationAsync(Success)` |
| soft warning / low-confidence field | `notificationAsync(Warning)` |
| error / failed capture | `notificationAsync(Error)` |
| selection change (chips, toggles) | `selectionAsync()` |

---

## Camera (Expo Go)

`expo-camera` gives preview, photo capture, and barcode/QR via `onBarcodeScanned`. It does **not** expose live frame processors, so real-time blur/glare/quality checks are **not** possible in Expo Go. For a guided-capture screen:

- Render the viewfinder + a static/animated reticle overlay (SVG + Reanimated).
- Drive "valid frame" visually with a timer or the barcode-detected event, then `success-pop`.
- Do quality checks **after** capture (or server-side) and route to a re-capture state.
- Leave `// TODO(dev-build): react-native-vision-camera frame processor for live quality` where true live CV belongs.
