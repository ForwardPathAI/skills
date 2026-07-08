# Work Breakdown

How to turn the architecture deliverable + design mockups into milestones, tickets, estimates, and a proposed timeline. The output of this document is the raw material for `docs/delivery/DELIVERY_PLAN.md`.

The rule throughout: **every milestone and ticket traces to a source** — an architecture section, a SOW requirement, a gap-audit finding, or a specific mockup. If it has no source, it is not in the plan.

## Inputs → work items

Read the architecture **canvas** (source of truth) and, when present, the design spec + mockups. Map each section to work items:

| Source section (poc-to-product-architecture) | Produces |
|---|---|
| §2 SOW traceability (`new` / `deferred` / `covered by POC`) | The master requirement list — every `new`/`deferred` item needs at least one ticket; `covered by POC` items may still need a hardening ticket. |
| §3 POC gap audit (`demo-grade` / `missing` / `reusable`) | `demo-grade` → a "replace for production" ticket; `missing` → a build ticket; `reusable` → no ticket (note as carried over). |
| §4 Architecture layers (web / api / data / jobs / auth / ai) | Foundation tickets: Drizzle schema + migrations, auth wiring, each API surface, jobs workers, AI module. |
| §5–6 Azure resource map + Bicep skeleton | Infra tickets (hand off to [azure-infra-setup](../azure-infra-setup/SKILL.md)): Bicep template, ACR/OIDC, Key Vault, Container Apps, Postgres, Redis/storage. |
| §7 Security & reliability | Hardening tickets: authz, secrets, backups, health/liveness, logging/metrics. |
| §9 Phased migration path | **Milestone candidates** — one milestone per phase. |
| §10 Risks & open questions | Either a spike/ticket (if actionable) or a plan-level assumption/risk (if a decision the user must make). |

If a `poc-from-sow` handoff exists, `docs/poc/PRODUCT_ROADMAP.md` is the pre-ordered work list (replace each `*-mock.ts` adapter, harden auth, real infra, tests) and `docs/poc/POC_NOTES.md` names the exact files each ticket touches — use them to make tickets concrete.

## Functional vs design tickets

- **Functional ticket** — behavior/data/infra work. Grounded in the architecture layers + product-foundation conventions. Uses the [issue-writer](../issue-writer/SKILL.md) description template.
- **Design ticket** — implementing a screen to its mockup. One per screen or tight screen group, **app shell first** (nav/sidebar/logo), then screens in the spec's usage order. Uses [assets/DESIGN_TICKET_TEMPLATE.md](assets/DESIGN_TICKET_TEMPLATE.md), which adds the mockup link, the screen-spec block reference, and visual-fidelity / states / responsive / accessibility acceptance.

Prefer **vertical slices**: a screen ticket and the API + schema it needs are sequenced together (or combined when small) so each milestone produces something demoable. When a screen depends on a functional ticket, wire `blockedBy`; when the design is independent (static content), it can run in parallel.

Every mockup image must appear in at least one design ticket — this is checked by the design-coverage matrix in the plan. A screen that is `designed-only` in `SOW_TRACEABILITY.md` still gets a ticket (its acceptance is "matches mockup," with functionality noted as a follow-up).

## Milestones

- One milestone per architecture migration phase. If the architecture has no phasing, derive milestones by dependency layer:
  1. **Foundation** — scaffold, schema + migrations, auth, CI, base infra.
  2. **Core flows** — the SOW's hero flows end to end (API + screens), app shell + primary screens.
  3. **Integrations** — replace mocked adapters with real services; secondary screens.
  4. **Hardening + launch** — security/reliability items, observability, deploy to customer tenant, remaining `deferred` scope.
- Each milestone must be **independently demoable** and have a one-line exit criterion (what the customer can see/do when it's done).
- Order milestones so nothing is blocked by a later milestone. Schema/auth precede features; app shell precedes screens; adapter replacement precedes the flow that needs the real integration.

## Estimation

- Default scale: **Fibonacci points** `1, 2, 3, 5, 8` where one point ≈ a half-day of focused work; a single ticket should not exceed **8** (≈ 4 hours × 2) — if it would, split it.
- Estimate every ticket. Roll points up per milestone; convert to a duration using a stated assumption (default: **1 developer, ~8 points/week** effective) — record the assumption in the plan so the user can rescale.
- If the target Linear team uses a different estimation scale (t-shirt, hours), ask and convert; the `estimate` field is a plain number, so match the team's convention.

## Timeline

- Turn per-milestone durations into **target dates**: milestone 1 target = start + duration 1; each subsequent milestone target = previous target + its duration, honoring cross-milestone dependencies.
- The project's `startDate` = the agreed start; `targetDate` = the last milestone's target.
- If the team runs **cycles** (sprints), optionally map milestones/tickets onto upcoming cycles (`list_cycles`) instead of raw dates.
- Present all dates as **proposals with their assumptions** (team size, velocity, start date). The user adjusts before anything is created in Linear.

## Dependencies & priority

- Wire `blockedBy` / `blocks` from the ordering above; keep the graph acyclic.
- Priority default: foundation + hero-flow tickets **High**, everything else **Medium**, explicit risks/blockers **Urgent**, nice-to-haves **Low** — override from SOW signals.
- Labels: apply only labels that already exist in the workspace (resolve in [LINEAR_SYNC.md](LINEAR_SYNC.md)); suggest a `design` vs `functional` label split if the workspace has them.
