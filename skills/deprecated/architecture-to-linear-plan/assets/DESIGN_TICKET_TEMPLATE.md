# Design Ticket Template

The description template for a **design ticket** — implementing a screen to its approved mockup. It is the `issue-writer` template plus the design-specific sections below. Functional tickets use the `issue-writer` template unchanged; do not use this one for pure behavior/data work.

A design ticket's defining rule: **"renders" is not "done." Done is "matches the approved mockup, in every state, responsively, accessibly."**

Fill every section. Write "None" where a section doesn't apply.

```markdown
## Why
[2–4 sentences: which SOW capability this screen serves and why it looks the way it does.
The customer validated this UI on the mockup — this ticket makes the real app match it.]

## What to build
[The screen at <route>, matching the mockup, wired to real data, with its primary action working.]

## Design source (authoritative)
- **Mockup:** [screen image](<link to mockups/NN-name.png>) — the layout truth.
- **Screen spec:** `WEB_APP_SCREENS_SPEC.md` §<screen> (or the mobile spec) — purpose, content regions, components, primary action, states.
- **App shell:** must match `mockups/00-shell.png` exactly (nav items, order, logo, active state).
- **Design tokens:** Tailwind theme / `tokens.ts` — no raw hex; colors, spacing, radii from tokens only.

## Acceptance criteria
- [ ] Layout matches the mockup region-for-region (top→bottom / left→right); same hierarchy and spacing rhythm.
- [ ] Real labels and copy from the mockup/spec (no lorem ipsum).
- [ ] Data comes from the seeded database via the typed API — no fixture imports.
- [ ] Primary action from the spec is wired.
- [ ] Side-by-side with `<mockup>` — no material layout, type, color, or spacing drift; screenshot attached to this issue.
- [ ] Chrome (nav/sidebar/logo/active state) identical to `00-shell`.
- [ ] Uses theme tokens only (grep shows no raw hex in the screen).
- [ ] Loading (skeleton), empty, and error states implemented — not just the happy path.
- [ ] Works at the spec's breakpoints (desktop landscape; + mobile if specified).
- [ ] Keyboard reachable; images have alt text; interactive controls have accessible names; contrast meets the mockup's intent.
- [ ] `bun run typecheck` and `bun run lint` exit 0.

## Out of scope
- The shared shell (unless this *is* the shell ticket) — [why].

+++ Agent notes

**Spec:** [Delivery plan document link]

**Decisions:**
- shadcn/ui + Tailwind tokens; TanStack Query hook against the typed Hono client (`hc<AppType>`).

**Starting points:**
- The dashboard route group in `apps/web` — where this screen lives.
- Match: `<exemplar screen>`.

**Test seam:** [Component or e2e test to model after, or None]

**Ask first if:**
- The mockup and the screen spec disagree on layout or content.
- The screen needs data or an API that doesn't exist yet (link the blocking functional ticket).
- Matching the mockup would require changing the shared shell.

+++
```
