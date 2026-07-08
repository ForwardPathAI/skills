# Design Ticket Template

The description template for a **design ticket** — implementing a screen to its approved mockup. It is the `issue-writer` template plus the design-specific sections below. Functional tickets use the `issue-writer` template unchanged; do not use this one for pure behavior/data work.

A design ticket's defining rule: **"renders" is not "done." Done is "matches the approved mockup, in every state, responsively, accessibly."**

Fill every section. Use "None" where a section doesn't apply — never omit.

```markdown
## Why this matters
[2–4 sentences: which SOW capability this screen serves and why it looks the way it does.
The customer validated this UI on the mockup — this ticket makes the real app match it.]

## Design source (authoritative)
- **Mockup:** [screen image](<link to mockups/NN-name.png>) — the layout truth.
- **Screen spec:** `WEB_APP_SCREENS_SPEC.md` §<screen> (or the mobile spec) — purpose, content regions, components, primary action, states.
- **App shell:** must match `mockups/00-shell.png` exactly (nav items, order, logo, active state).
- **Design tokens:** Tailwind theme / `tokens.ts` — no raw hex; colors, spacing, radii from tokens only.

## Current state
**Relevant files** (each with its role):
- `apps/web/app/(dashboard)/<route>/page.tsx` — screen to build (create) / to update
- `apps/web/components/<shell>` — the shell this screen renders inside

**Conventions to match** (with one exemplar):
- shadcn/ui + Tailwind tokens; TanStack Query hook against the typed Hono client (`hc<AppType>`); see `<exemplar screen>`.

## Commands
| Purpose   | Command            | Expected on success |
|-----------|--------------------|---------------------|
| Dev       | `bun dev`          | screen renders at the route |
| Typecheck | `bun run typecheck`| exit 0, no errors   |
| Lint      | `bun run lint`     | exit 0              |

## Scope
**In scope** (the only files to modify):
- `apps/web/app/(dashboard)/<route>/…`

**Out of scope** (do NOT touch):
- The shell components (unless this *is* the shell ticket) — [why].

## Requirements
- [ ] Layout matches the mockup region-for-region (top→bottom / left→right); same hierarchy and spacing rhythm.
- [ ] Real labels and copy from the mockup/spec (no lorem ipsum).
- [ ] Data comes from the seeded database via the typed API — no fixture imports.
- [ ] Primary action from the spec is wired.

## Visual fidelity acceptance
- [ ] Side-by-side with `<mockup>` — no material layout, type, color, or spacing drift.
- [ ] Chrome (nav/sidebar/logo/active state) identical to `00-shell`.
- [ ] Uses theme tokens only (grep shows no raw hex in the screen).

## States
- [ ] Loading (skeleton), empty, and error states implemented — not just the happy path.

## Responsive & accessibility
- [ ] Works at the spec's breakpoints (desktop landscape; + mobile if specified).
- [ ] Keyboard reachable; images have alt text; interactive controls have accessible names; contrast meets the mockup's intent.

## Done criteria
Machine-checkable. ALL must hold:
- [ ] `bun run typecheck` exits 0
- [ ] `bun run lint` exits 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] Screenshot attached to this issue matching the mockup

## STOP conditions
Stop and comment instead of improvising if:
- The mockup and the screen spec disagree on layout or content.
- The screen needs data/an API that doesn't exist yet (link the blocking functional ticket).
- Matching the mockup would require changing the shared shell.

## Dependencies
- **Blocked by:** [functional ticket providing the data/API, or None]
- **Blocks:** [None]

## Additional context
Written against commit `<short SHA>`, <YYYY-MM-DD>. Mockup: `mockups/NN-name.png`. Spec: `WEB_APP_SCREENS_SPEC.md` §<screen>.
```
