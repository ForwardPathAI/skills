---
name: poc-from-sow
description: Turn a Statement of Work into a customer-validatable, continuation-ready POC codebase on the Forward Path stack — buildable, runnable, and demo-deployable — with an agent-ready handoff pack, closing with a poc-to-product-architecture run (canvas + DOCX) for the approval meeting. Use when the user says "POC from SOW", "build a POC", "prototype this SOW", "scaffold a proof of concept", "SOW to POC", or mentions poc-from-sow.
---

# POC from SOW

Forward Path wins work by showing, not telling. This skill turns a **Statement of Work** ($sow) into a **proof-of-concept codebase** the customer can click through to validate usage and UI/UX — and that the team then builds *on* after approval. The POC is the first increment of the real product, never a throwaway mockup.

Three commitments shape every step:

1. **Customer-validatable** — mockup-faithful UI with realistic seed data and a demo script, so the customer validates the proposed solution on a live app.
2. **Continuation-ready** — "real core, mocked edges": schema, auth, and API are real product code on the [product-foundation](../product-foundation/SKILL.md) stack from the first commit; only external integrations are mocked, behind typed adapters that get swapped post-approval — not rewritten.
3. **Agent-ready handoff** — enough written plan material lives inside the generated repo (`docs/poc/` + a root `AGENTS.md`) that a future agent can build the product from it without re-deriving the SOW.

The skill **composes** existing skills rather than duplicating them; it finishes by invoking [poc-to-product-architecture](../poc-to-product-architecture/SKILL.md) so the approval meeting gets both the live POC and the production-architecture canvas + DOCX.

```
SOW → POC plan → design (mockups) → scaffold → implement → package + deploy → handoff pack → architecture canvas + DOCX
```

## Prerequisites

- **$sow** — a SOW URL or file path (ask if not given).
- **Target directory** — where to create the new POC repo (ask if not given; default is a new sibling folder named for the product).
- **Bun** toolchain (never Node/npm/pnpm/Vite) and **Docker** for local Postgres/Redis — the generated POC runs on these.
- A **Gemini or OpenRouter key** for the design pass (Step 3) — [web-ui](../web-ui/SKILL.md) / [mobile-ui](../mobile-ui/SKILL.md) need it. If missing, stop and ask the user; do not silently downgrade.
- **`gh` CLI** authenticated if the repo will be pushed.
- Read these sibling skills before building — this skill orchestrates them:
  - [product-foundation/SKILL.md](../product-foundation/SKILL.md) — the target stack, conventions, and [SCAFFOLD.md](../product-foundation/SCAFFOLD.md).
  - [web-ui/SKILL.md](../web-ui/SKILL.md) and [mobile-ui/SKILL.md](../mobile-ui/SKILL.md) — screen specs + mockups.
  - [mobile-ui-implement/SKILL.md](../mobile-ui-implement/SKILL.md) — build mobile screens from mockups.
  - [azure-infra-setup/SKILL.md](../azure-infra-setup/SKILL.md) — the demo-deploy conventions.
  - [poc-to-product-architecture/SKILL.md](../poc-to-product-architecture/SKILL.md) — the closing architecture deliverable.
- Bundled references in this skill directory:
  - [POC_BAR.md](POC_BAR.md) — the quality bar every POC must pass (what survives approval, what is never allowed, what may be shortcut).
  - [WEB_IMPLEMENT.md](WEB_IMPLEMENT.md) — turn the web screen spec + mockups into Next.js App Router screens.
  - [HANDOFF_PACK.md](HANDOFF_PACK.md) — the agent-ready `docs/poc/` + `AGENTS.md` material to write.
  - [assets/POC_NOTES_TEMPLATE.md](assets/POC_NOTES_TEMPLATE.md), [assets/AGENTS_TEMPLATE.md](assets/AGENTS_TEMPLATE.md) — fill-in templates.

Stop and report anything missing before proceeding.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Ingest the SOW
- [ ] Step 2: POC plan (modules, entities, screens, hero flows) — confirm with user
- [ ] Step 3: Design pass (web-ui / mobile-ui mockups) — required
- [ ] Step 4: Scaffold on product-foundation
- [ ] Step 5: Implement to the POC bar
- [ ] Step 6: Package, run, deploy
- [ ] Step 7: Handoff pack
- [ ] Step 8: Production architecture deliverable (poc-to-product-architecture)
```

### Step 1: Ingest the SOW

Accept $sow as a URL or file. If a URL returns empty (JavaScript-rendered, e.g. Notion), use a browser tool to read the rendered text — same fallback as [web-ui](../web-ui/SKILL.md) step 1.

Extract and record: objectives/scope, roles/users, features, data entities, integrations, constraints, budget signals, phasing. Keep this extraction — Step 2, Step 3, and the Step 8 architecture run all reuse it.

Complete this step when every item is recorded and anything ambiguous is queued as an open question.

### Step 2: POC plan

Decide the shape of the POC, then get sign-off before building:

- **Modules** — which product-foundation modules apply: auth, a separate Hono `apps/api`, `apps/jobs` (BullMQ), `packages/ai`. Default core is web + database + shared.
- **Data entities** — the domain schema the SOW implies (the real Drizzle tables, not fixtures).
- **Screens** — the web (and mobile) screens needed to tell the SOW's story, in usage order.
- **Hero flows** — pick **1–2 flows that prove SOW feasibility end-to-end** (e.g. capture → extract → review). These are built fully and deeply; everything else supports them.

Write `docs/poc/POC_PLAN.md` (modules, entities, screens, hero flows) with SOW citations. **Confirm scope with the user before building anything** — this is the cheapest place to correct course.

Complete this step when `POC_PLAN.md` exists and the user has confirmed scope.

### Step 3: Design pass (required, not optional)

The customer validates UI/UX on this POC, so mockups anchor the build — screens are implemented *to* the approved mockups.

- Run [web-ui](../web-ui/SKILL.md) Phases 1+2 for the web screens (grounded spec `WEB_APP_SCREENS_SPEC.md` + style board, app shell, one image per screen).
- Run [mobile-ui](../mobile-ui/SKILL.md) if the SOW has mobile screens.
- Commit the specs + mockups into the generated repo under `docs/poc/design/`.

If no Gemini/OpenRouter key is available, **stop and ask the user** rather than silently downgrading to a spec-only path.

Complete this step when the screen spec(s) and mockups exist, are user-approved, and are committed under `docs/poc/design/`.

### Step 4: Scaffold on product-foundation

Follow [product-foundation SCAFFOLD.md](../product-foundation/SCAFFOLD.md) with the modules chosen in Step 2:

- Bun + Turborepo monorepo (`apps/*`, `packages/*`); `packages/shared` + `packages/database` as core.
- Strict TypeScript, oxlint, the `{ data } / { error }` API contract, route constants — get conventions right from the first commit.
- `docker-compose.yml` for local Postgres (and Redis when the jobs module is chosen).
- A plain-language `README.md` in the first commit: what the product does, the stack in one sentence per layer, and how to run it from a fresh clone.

Complete this step when the monorepo builds empty (`bun install` + `bun run build`) and the README's run instructions are accurate.

### Step 5: Implement to the POC bar

Build to [POC_BAR.md](POC_BAR.md) — *every line must survive customer approval*:

- **Schema + data** — real Drizzle domain schema, committed migrations, and a **realistic seed script** using SOW-domain data. Pages read from the database; never import fixture files like `mock-data.ts`.
- **Auth** — Better Auth wired for real: Microsoft Entra SSO when credentials exist, else a clearly-marked dev credentials login seeded with the SOW's actual roles. Never a client-side-only role switch or a stub `Link` login.
- **API** — typed Hono routes with `zValidator` at every boundary; route constants; typed RPC client (`hc<AppType>`).
- **Web screens** — implement per [WEB_IMPLEMENT.md](WEB_IMPLEMENT.md), faithful to the approved mockups, with real loading/empty/error states.
- **Mobile screens** — hand off to [mobile-ui-implement](../mobile-ui-implement/SKILL.md) (Mode A → Mode B).
- **External integrations** — mock behind **typed adapter interfaces**: the interface lives in `packages/shared`, the mock implementation is named `*-mock.ts`. Every mock is logged in `docs/poc/POC_NOTES.md` with its production fix.

Complete this step when the hero flows work end-to-end against the seeded database and every mocked edge is a typed adapter logged in POC_NOTES.

### Step 6: Package, run, deploy

The POC must be buildable, runnable, and demo-deployable:

- **Local** — from a fresh clone, `docker compose up` + `bun dev` works following **only** the README; the seed script yields a demo-ready dataset.
- **Containers** — a Dockerfile per app (web / api / jobs as applicable) so the POC ships as images from `forwardpathai.azurecr.io` — the same shape [poc-to-product-architecture](../poc-to-product-architecture/SKILL.md) later expects.
- **Demo deploy** — a deliberately thin deploy to one Forward Path Azure dev environment (Container Apps, consumption SKUs, [azure-infra-setup](../azure-infra-setup/SKILL.md) conventions) giving the customer a live URL. Full customer-tenant infra is post-approval work — keep this minimal.
- **Demo script** — write `docs/poc/DEMO_SCRIPT.md`: seeded logins per role + the exact click-path through each hero flow.

Complete this step when a fresh clone runs from the README alone, images build, and (when Azure access exists) the live demo URL works.

### Step 7: Handoff pack

Verify quality, then write the agent-ready pack:

- `bun run typecheck`, `bun run lint`, and `bun run build` pass.
- Walk `DEMO_SCRIPT.md` end-to-end to confirm the demo is real.
- Write the handoff pack per [HANDOFF_PACK.md](HANDOFF_PACK.md): root `AGENTS.md`, `docs/poc/POC_PLAN.md`, `docs/poc/SOW_TRACEABILITY.md`, `docs/poc/POC_NOTES.md`, `docs/poc/PRODUCT_ROADMAP.md`, `docs/poc/DEMO_SCRIPT.md`, and `docs/poc/design/`.

Complete this step when checks pass, the demo script is verified, and every handoff-pack file exists.

### Step 8: Production architecture deliverable

With the POC verified, invoke [poc-to-product-architecture](../poc-to-product-architecture/SKILL.md) against the **same SOW** and the fresh POC repo to produce the architecture **canvas + DOCX** into `docs/architecture/`. This run is cheap: Step 1's SOW extraction is reused, and `docs/poc/SOW_TRACEABILITY.md` + `docs/poc/POC_NOTES.md` pre-seed its gap audit (see that skill's Step 3).

The customer-approval meeting then gets both artifacts together: the **live POC** to validate UI/UX, and the **production architecture** showing what approval buys.

Report to the user:
- Repo path and state (builds, checks pass).
- Live demo URL (if deployed) and `DEMO_SCRIPT.md`.
- Design artifacts under `docs/poc/design/`.
- Architecture canvas + DOCX paths.
- The post-approval path: continued build per `docs/poc/PRODUCT_ROADMAP.md`.

Complete this step when the canvas + DOCX exist (or the user opted to skip) and the report is delivered.

## Decision table

| Situation | Action |
|---|---|
| No mobile screens in the SOW | Skip the mobile parts of Steps 3 and 5 (`mobile-ui` / `mobile-ui-implement`). |
| No Gemini/OpenRouter key for the design pass | Ask the user for a key; do not downgrade to spec-only silently. |
| SOW too large for a POC | Build the hero flows fully; ship remaining screens as designed-but-static pages, each logged in `POC_NOTES.md` as `designed-only`. |
| No Azure access | Local + Docker only; defer the demo deploy and note it in the report. |
| User wants the POC only (no architecture deliverable yet) | Skip Step 8 and name it as the pending next step in the report. |
| POC stack would deviate from product-foundation | Don't — the POC must be continuation-ready on the standard stack. If the SOW forces a genuine deviation, log it in `POC_NOTES.md` with the reason. |
| An external integration is needed by a hero flow | Mock it behind a typed adapter (`packages/shared` interface + `*-mock.ts`); never inline a third-party call in a route handler. |

## Anti-patterns

- Inventing SOW requirements not present in $sow, or building screens that were never mocked up.
- Fixture imports in pages (`mock-data.ts`-style) when a real schema exists — the POC must read from the seeded database.
- Stub auth: a client-side-only role switch or a login that is just a `Link` to the dashboard.
- Third-party calls inlined in route handlers instead of behind a typed adapter.
- `typescript.ignoreBuildErrors` or any demo-only code path that would be thrown away after approval.
- Skipping the Step 2 user confirmation, or skipping the required design pass.
- Restating a sibling skill's procedure here instead of linking it.
- Shipping without the handoff pack — a POC an agent can't continue from fails the third commitment.

## Additional resources

- Forward Path stack, conventions, and scaffold: [product-foundation/SKILL.md](../product-foundation/SKILL.md)
- Web screen spec + mockups: [web-ui/SKILL.md](../web-ui/SKILL.md)
- Mobile screen spec + mockups: [mobile-ui/SKILL.md](../mobile-ui/SKILL.md)
- Build mobile screens from mockups: [mobile-ui-implement/SKILL.md](../mobile-ui-implement/SKILL.md)
- Demo-deploy conventions: [azure-infra-setup/SKILL.md](../azure-infra-setup/SKILL.md)
- Closing architecture deliverable: [poc-to-product-architecture/SKILL.md](../poc-to-product-architecture/SKILL.md)
- Quality bar: [POC_BAR.md](POC_BAR.md)
- Web implementation guide: [WEB_IMPLEMENT.md](WEB_IMPLEMENT.md)
- Handoff pack format: [HANDOFF_PACK.md](HANDOFF_PACK.md)
