# Delivery Plan — <Product Name>

> Reviewable plan produced by `architecture-to-linear-plan`. **Nothing is created in Linear until this is approved.** Edit scope, ordering, estimates, dates, team, or project, then approve.

- **Source architecture:** `docs/architecture/<app>-architecture.canvas.tsx` (+ DOCX)
- **Design inputs:** `docs/poc/design/` (<N> web mockups / <N> mobile mockups) — or "none; design tickets pending a web-ui/mobile-ui pass"
- **Target Linear team:** <Team> · **Project:** <new: "…" | reuse: "…">
- **Written against commit:** `<short SHA>`, <YYYY-MM-DD>

## Timeline assumptions

- Start date: <YYYY-MM-DD> · Team size: <n developer(s)> · Assumed velocity: <~8 points/week/dev>
- Estimation scale: Fibonacci points (1/2/3/5/8), 1 pt ≈ half a day. Adjust if the team's scale differs.

## Milestones

| # | Milestone | Exit criterion (demoable) | Points | Proposed target |
|---|-----------|---------------------------|:------:|-----------------|
| 1 | Foundation | Schema + auth + CI live | <n> | <YYYY-MM-DD> |
| 2 | Core flows | Hero flow(s) end to end | <n> | <YYYY-MM-DD> |
| 3 | Integrations | Real adapters replace mocks | <n> | <YYYY-MM-DD> |
| 4 | Hardening + launch | Deployed to customer tenant | <n> | <YYYY-MM-DD> |

## Tickets by milestone

### Milestone 1 — Foundation

| Title | Type | Pts | Priority | Depends on | Source |
|-------|------|:---:|----------|------------|--------|
| Add Drizzle schema + migrations for <entities> | functional | 3 | High | — | Arch §4 data |
| Wire Better Auth + Entra SSO with <roles> | functional | 5 | High | schema | Arch §4 auth / SOW §<n> |
| Implement app shell (nav/sidebar/logo) | design | 3 | High | — | `mockups/00-shell.png` |

### Milestone 2 — Core flows

| Title | Type | Pts | Priority | Depends on | Source |
|-------|------|:---:|----------|------------|--------|
| <Hero flow> API surface | functional | 5 | High | schema, auth | Arch §4 api / SOW §<n> |
| <Screen> to mockup | design | 3 | High | API above | `mockups/02-<name>.png` |

_(repeat per milestone)_

## Design coverage matrix

Every mockup must map to at least one ticket.

| Mockup | Screen | Ticket(s) | Functional dependency |
|--------|--------|-----------|-----------------------|
| `mockups/00-shell.png` | App shell | M1: Implement app shell | — |
| `mockups/02-<name>.png` | <Screen> | M2: <Screen> to mockup | <Hero flow> API |

## Assumptions & risks (from architecture §10)

- <Open question / inferred item awaiting confirmation, or decision the user must make.>
- <Budget/scope risk carried from the architecture.>

## Approval

- [ ] Scope, milestones, and ticket set are correct
- [ ] Estimates and timeline are acceptable
- [ ] Target team + project confirmed
- [ ] **Approved to create in Linear**
