# Web Implement

Turn the [web-ui](../web-ui/SKILL.md) deliverables — `WEB_APP_SCREENS_SPEC.md` + the approved mockups — into real **Next.js App Router** screens on the product-foundation stack. This is the web analog of [mobile-ui-implement](../mobile-ui-implement/SKILL.md), scoped to one document.

The mockup is the layout truth; the spec is the behavior/copy truth; the seeded database is the data truth. Screens are implemented *to* the approved mockups so the customer validates the same UI they signed off on.

## Hard rules

- **App shell first.** Build the persistent chrome (nav, sidebar, logo, user menu) exactly as the spec's app-shell section defines it, before any screen. Every screen renders inside it, so the set reads as one product.
- **Read the mockup before building its screen.** Open the screen's mockup image with the Read tool; it is authoritative for what is on screen and where.
- **No raw hex in screens.** Use Tailwind theme tokens + shadcn/ui components; colors, spacing, and radii come from the theme, not inline values.
- **Real data, not fixtures.** Screens fetch through TanStack Query hooks against the typed Hono RPC client (`hc<AppType>`), backed by the seeded database. Never import a `mock-data.ts` into a page.
- **Every screen has states.** Implement loading (skeletons), empty, and error states — not just the happy path — so the demo feels like a product.
- **Mockup-faithful.** Match layout, labels, and hierarchy to the image. Do not invent features the mockup and spec don't show.

## Workflow

Copy this checklist and track it:

```
- [ ] 1. Read the spec + every mockup image
- [ ] 2. Set up the theme tokens + shadcn/ui
- [ ] 3. Build the app shell (route group + layout)
- [ ] 4. Build screens in usage order, one at a time
- [ ] 5. Wire each screen to the API via TanStack Query
- [ ] 6. Acceptance-check each screen vs its mockup
```

**1. Read the inputs.** Read `WEB_APP_SCREENS_SPEC.md` (brand foundation, app shell, screen inventory, per-screen blocks) and open **every** mockup PNG with the Read tool. You cannot build a screen you have not looked at.

**2. Theme + components.** Encode the spec's brand foundation as the Tailwind theme (colors, fonts via `next/font`, radii) and install the shadcn/ui components the screens use. This is the web equivalent of `mobile-ui-implement`'s `tokens.ts` — one source of truth for design values.

**3. App shell.** Create the App Router layout that hosts the chrome. Use route groups to separate authed app screens from auth screens — e.g. `app/(dashboard)/layout.tsx` for the nav + sidebar shell, `app/(auth)/` for login. Transcribe the exact nav items, order, logo placement, and active-state treatment from the spec. This is the `00-shell` mockup made real.

**4-5. Screens.** Build one screen per pass, in the spec's usage order (auth/first-run → core loop → detail/reporting → settings):

- Place it at its App Router route inside the shell's route group.
- Compose it from shadcn/ui + theme tokens, matching the mockup's content regions top→bottom / left→right.
- Fetch data with a **TanStack Query hook** calling the typed Hono client; render the loading/empty/error states.
- Use the real seeded records — the screen should show believable domain data, not lorem ipsum.

**6. Acceptance check.** Before marking a screen done, put its mockup image side by side with the running screen and confirm: same layout and hierarchy, same real labels, chrome identical to the shell, all states present, no invented features, `tsc` + oxlint clean. Regenerate or fix any drift.

## Relationship to the POC bar

This guide operationalizes the "mockup-faithful screens" Tier-2 item in [POC_BAR.md](POC_BAR.md) and the "real data, not fixtures" rule. If a screen needs data from an external integration, it still fetches through the typed Hono API — the API route delegates to the typed adapter (`packages/shared` interface + `*-mock.ts`), so the screen code is production-real even while the edge is mocked.
