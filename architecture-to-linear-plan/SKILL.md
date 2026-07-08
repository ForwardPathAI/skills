---
name: architecture-to-linear-plan
description: Turn a production-architecture deliverable (the poc-to-product-architecture canvas + DOCX) and any design mockups (web-ui / mobile-ui) into a consistent delivery plan — Linear milestones with proposed timelines and executable tickets covering both functional and design requirements — then, once approved, create the project, milestones, and issues in Linear via the Linear MCP. Use when the user says "plan the implementation", "turn the architecture into Linear tickets", "create milestones and tickets", "delivery plan", "build the roadmap in Linear", or mentions architecture-to-linear-plan.
---

# Architecture to Linear Plan

`poc-to-product-architecture` says *what to build*; this skill says *in what order, by when, and as which tickets* — and then writes that plan into Linear. It converts the architecture deliverable (canvas + DOCX) and any design mockups into a **delivery plan**: milestones with proposed timelines and executable tickets, each tracing back to an architecture section, SOW clause, or mockup. After the user approves the plan, it creates the Linear project, milestones, and issues through the Linear MCP.

Two properties define a good result:

1. **Consistent and traceable** — every milestone maps to a phase of the architecture's migration path; every ticket cites its source (architecture layer, SOW requirement, or a specific mockup) and carries a dependency, estimate, and priority. No orphan work, no invented scope.
2. **Executable, not aspirational** — each ticket meets the [issue-writer](../issue-writer/SKILL.md) bar (self-contained context, verification gates, hard scope, STOP conditions). Design tickets additionally pin the mockup and make visual fidelity an acceptance criterion, so UI/UX requirements are tracked, not assumed.

**Hard gate:** the skill produces a reviewable plan document **first** and creates nothing in Linear until the user explicitly approves. Linear writes are external, side-effecting, and hard to undo — the approval gate is not optional.

## Prerequisites

- **$architecture** — the `poc-to-product-architecture` deliverable in the repo (`docs/architecture/<app>-architecture.canvas.tsx` and/or the `.docx`). If it doesn't exist, offer to run [poc-to-product-architecture](../poc-to-product-architecture/SKILL.md) first — this skill is the step *after* it.
- **$design** (optional) — [web-ui](../web-ui/SKILL.md) / [mobile-ui](../mobile-ui/SKILL.md) outputs: a screen spec (`WEB_APP_SCREENS_SPEC.md` or the mobile equivalent) and mockups (`docs/poc/design/`, `mockups/`). When present, the plan must cover design requirements.
- **Linear MCP** — the `user-linear` MCP server, authenticated. Needed only for the final creation step; the plan document is produced without it. Before calling any tool, read its descriptor under the MCP tools folder (`save_project`, `save_milestone`, `save_issue`, `save_document`, and the `list_*` readers).
- Read [issue-writer/SKILL.md](../issue-writer/SKILL.md) — the ticket quality bar this skill enforces per issue. Read [product-foundation/SKILL.md](../product-foundation/SKILL.md) for the stack tickets are written against.
- Bundled references in this skill directory:
  - [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md) — how to derive milestones, tickets, estimates, and a timeline from the architecture + design inputs.
  - [LINEAR_SYNC.md](LINEAR_SYNC.md) — the Linear MCP creation protocol: entity mapping, field resolution, the approval gate, idempotency, and dependency wiring.
  - [assets/DELIVERY_PLAN_TEMPLATE.md](assets/DELIVERY_PLAN_TEMPLATE.md) — the reviewable plan document.
  - [assets/DESIGN_TICKET_TEMPLATE.md](assets/DESIGN_TICKET_TEMPLATE.md) — the design-ticket extension of the issue-writer template.

Stop and report anything missing before proceeding.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Locate the inputs (architecture + design)
- [ ] Step 2: Extract the work breakdown
- [ ] Step 3: Shape milestones + propose the timeline
- [ ] Step 4: Draft tickets to the issue-writer bar (functional + design)
- [ ] Step 5: Write the delivery plan + get approval  ← HARD GATE
- [ ] Step 6: Create it in Linear via the MCP
```

### Step 1: Locate the inputs

- Find the architecture deliverable: the canvas `.canvas.tsx` and/or DOCX in `docs/architecture/`. Read the canvas — it is the source of truth and carries every section (SOW traceability, architecture layers, phased migration path, risks, cost).
- Find design deliverables if any: a screen spec plus mockups under `docs/poc/design/`, `mockups/`, or as named by the user. Note whether the SOW has web screens, mobile screens, or both.
- Find `poc-from-sow` handoff material if present: `docs/poc/PRODUCT_ROADMAP.md` (ordered post-approval work), `docs/poc/SOW_TRACEABILITY.md`, `docs/poc/POC_NOTES.md` — these pre-seed the work breakdown.

If the architecture deliverable is absent, stop and offer to run [poc-to-product-architecture](../poc-to-product-architecture/SKILL.md); do not invent an architecture.

Complete this step when the architecture is loaded and the design inputs are inventoried (present or confirmed absent).

### Step 2: Extract the work breakdown

Following [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md), turn the inputs into a flat list of **work items**, each with a source citation:

- **Phases → milestone candidates** from the architecture's phased migration path (canvas §9) and/or `PRODUCT_ROADMAP.md`.
- **Functional work items** from the architecture layers + SOW traceability + gap audit (e.g. schema, auth, each API surface, jobs, integrations replacing mocked adapters, infra/Bicep, observability).
- **Design work items** from the screen spec + mockups — one per screen or screen group (app shell first), each pointing at its mockup image and its per-screen spec block.

Every work item cites where it came from. Items with no source are dropped or flagged, never invented.

Complete this step when every architecture section and every mockup is represented by at least one work item, and every SOW requirement is traceable to one.

### Step 3: Shape milestones + propose the timeline

- Group work items into **milestones** aligned to the migration phases; prefer **vertical slices** (a screen + its API + schema) so each milestone is demoable.
- Order milestones and items by dependency (schema/auth before features; app shell before screens; mocked-adapter replacement before the flows that need it).
- **Estimate** each ticket and roll up to a proposed duration per milestone; turn durations into target dates (or cycles) — see [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md) for the estimation scale and sequencing. Timelines are **proposals** the user adjusts.

Complete this step when every ticket has an estimate + dependencies and every milestone has an ordered ticket set and a proposed target date.

### Step 4: Draft tickets to the issue-writer bar

For each work item, write a ticket meeting the [issue-writer](../issue-writer/SKILL.md) bar — self-contained context (paths, excerpts, conventions from the architecture/repo), verification gates as commands, an explicit in/out-of-scope list, and STOP conditions. Set priority, labels, estimate, and `blocks`/`blockedBy` relations.

- **Functional tickets** use the issue-writer description template, grounded in the architecture layers and product-foundation conventions.
- **Design tickets** use [assets/DESIGN_TICKET_TEMPLATE.md](assets/DESIGN_TICKET_TEMPLATE.md): the issue-writer template plus the mockup link, the screen-spec reference, and **visual-fidelity + states + responsive + accessibility** acceptance criteria. A screen is not "done" because it renders — it is done when it matches the approved mockup.

Complete this step when every work item has a ticket that would pass the issue-writer quality bar.

### Step 5: Write the delivery plan + get approval  ← HARD GATE

Write `docs/delivery/DELIVERY_PLAN.md` from [assets/DELIVERY_PLAN_TEMPLATE.md](assets/DELIVERY_PLAN_TEMPLATE.md): the project summary, the milestone table with proposed dates, a per-milestone ticket list (title, type, estimate, priority, dependencies, source), and a **design-coverage matrix** (every mockup → its ticket(s)). Include the assumptions behind the timeline and which Linear team/project it will target.

Present the plan and **ask for explicit approval**. Do not call any Linear write tool yet. Let the user adjust scope, ordering, estimates, dates, team, or project. Re-render the plan until they approve.

Complete this step when `DELIVERY_PLAN.md` exists and the user has explicitly approved creating it in Linear.

### Step 6: Create it in Linear via the MCP

Follow [LINEAR_SYNC.md](LINEAR_SYNC.md) exactly:

1. **Resolve targets** with the `list_*` readers first: team, existing/target project, labels (apply only labels that exist), cycles, and assignees. Confirm the team + project with the user.
2. **Create/reuse the project** (`save_project`) with start/target dates from the timeline.
3. **Create milestones** (`save_milestone`) with target dates.
4. **Create issues** (`save_issue`) with description, milestone, estimate, priority, labels, and mockup links; then wire `blocks`/`blockedBy` relations in a second pass.
5. **Create a grouping document** (`save_document`) — the plan overview + milestone/ticket table — and link its URL into the tickets.
6. **Idempotent re-runs:** check for existing project/milestones/issues by name before creating; update instead of duplicating.

Report: the Linear project + document URLs, milestones with dates, the count of issues created per milestone, and the `docs/delivery/DELIVERY_PLAN.md` path. Never print secret values or the raw remote URL.

Complete this step when the Linear artifacts exist (or the user chose plan-only), and the report is delivered.

## Decision table

| Situation | Action |
|---|---|
| No architecture deliverable in the repo | Stop; offer to run [poc-to-product-architecture](../poc-to-product-architecture/SKILL.md) first. |
| No design mockups | Build functional tickets only; note in the plan that design tickets are pending a `web-ui`/`mobile-ui` pass. |
| Mockups exist but no screen spec | Create design tickets from the images; flag the missing spec as a plan assumption. |
| SOW/architecture has no phasing | Derive milestones by dependency layers (foundation → core flows → integrations → hardening) and say so in the plan. |
| Linear MCP unavailable or unauthenticated | Deliver `DELIVERY_PLAN.md` only; report that Linear creation is pending auth. |
| User has not approved the plan | Never call a Linear write tool. The plan document is the only output until approval. |
| A needed label doesn't exist in Linear | Ask before creating it (`create_issue_label`); never silently invent label names. |
| Re-run after tickets already exist | Match by name and update; never create duplicate projects/milestones/issues. |
| A ticket would exceed ~4 focused hours | Split it (see [issue-writer splitting](../issue-writer/splitting.md)); prefer vertical slices. |

## Anti-patterns

- Creating Linear issues before the user approves the plan document.
- Inventing scope, milestones, or tickets not traceable to the architecture, SOW, or a mockup.
- Tickets that fail the issue-writer bar — vague acceptance ("make it work"), no scope boundary, no STOP conditions.
- Design work folded silently into functional tickets so visual fidelity is never tracked.
- Applying labels that don't exist in the workspace, or inventing project/team names instead of resolving them via `list_*`.
- Duplicating projects/milestones/issues on a re-run instead of updating by name.
- Putting secret values or the PAT-bearing remote URL into a ticket, document, or command output.
- Restating the issue-writer or poc-to-product-architecture procedure here instead of linking it.

## Additional resources

- Produce the architecture this skill plans from: [poc-to-product-architecture/SKILL.md](../poc-to-product-architecture/SKILL.md)
- Per-ticket quality bar: [issue-writer/SKILL.md](../issue-writer/SKILL.md) and [splitting.md](../issue-writer/splitting.md)
- Design inputs: [web-ui/SKILL.md](../web-ui/SKILL.md), [mobile-ui/SKILL.md](../mobile-ui/SKILL.md)
- Target stack tickets are written against: [product-foundation/SKILL.md](../product-foundation/SKILL.md)
- Work breakdown rules: [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md)
- Linear MCP protocol: [LINEAR_SYNC.md](LINEAR_SYNC.md)
