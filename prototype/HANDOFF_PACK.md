# Handoff Pack

What Step 7 writes into the **generated POC repo** so a future agent can build the product from it without re-deriving the SOW. This is the third commitment made real: the plan material lives *inside* the repo, next to the code it describes.

All filenames below are literal. Write them exactly.

## `AGENTS.md` (repo root)

The agent entrypoint — the first thing an agent reads when it opens the repo. Use [assets/AGENTS_TEMPLATE.md](assets/AGENTS_TEMPLATE.md). It must contain:

- A one-line product description.
- The stack in one sentence per layer, pointing at [product-foundation](../product-foundation/SKILL.md) as the standard.
- A repo map (what lives in each `apps/*` and `packages/*`).
- The commands to install, run, seed, build, typecheck, and lint.
- The instruction: **read `docs/poc/` before changing anything** — especially `POC_NOTES.md` (what's mocked) and `PRODUCT_ROADMAP.md` (what to build next).

## `docs/poc/POC_PLAN.md`

The scope decisions from Step 2, with SOW citations: chosen modules, data entities, screen inventory, and the 1–2 hero flows. This is the "why the POC looks like this" record.

## `docs/poc/SOW_TRACEABILITY.md`

One row per SOW requirement mapping it to its state in the repo. Use exactly this status vocabulary:

| Status | Meaning |
|--------|---------|
| `built` | Real, working product code in the POC. |
| `designed-only` | Mocked up and/or a static page, not yet functional. |
| `mocked-adapter` | Works via a typed mock adapter; real integration pending. |
| `not-started` | Not addressed in the POC. |

Columns: **SOW requirement | status | where in the repo (path)**. This is the same table shape [poc-to-product-architecture](../poc-to-product-architecture/SKILL.md) consumes in its Step 3, so the later gap audit is pre-seeded rather than re-derived.

## `docs/poc/POC_NOTES.md`

Every shortcut taken, from Tier 3 of [POC_BAR.md](POC_BAR.md). Use [assets/POC_NOTES_TEMPLATE.md](assets/POC_NOTES_TEMPLATE.md): a table of **shortcut | where (file) | why | production fix**, grouped under the gap-audit tags `demo-grade` / `missing` / `reusable`. Every mocked adapter, deferred integration, and demo-only simplification appears here with its fix.

## `docs/poc/PRODUCT_ROADMAP.md`

The post-approval build plan: an **ordered** list of work items to go POC → product. Each item names the exact files/interfaces to change. Typical items:

- Replace each `*-mock.ts` adapter with its real implementation (list them, from `POC_NOTES.md`).
- Harden auth (real Entra SSO, org RBAC, remove the dev credentials login).
- Real infra via [poc-to-product-architecture](../poc-to-product-architecture/SKILL.md) → [azure-infra-setup](../azure-infra-setup/SKILL.md) → [customer-deployment-package](../customer-deployment-package/SKILL.md).
- Add the test suite beyond smoke.
- Build out `designed-only` screens into functional ones.

## `docs/poc/DEMO_SCRIPT.md`

From Step 6: seeded logins per role + the exact click-path through each hero flow, so anyone can run the customer walkthrough.

## `docs/poc/design/`

The committed [web-ui](../web-ui/SKILL.md) / [mobile-ui](../mobile-ui/SKILL.md) outputs from Step 3 — the screen spec(s) and the approved mockups — so the design intent travels with the code.

## Why it lives in the repo

Chat context is lost; a repo is forever. Putting the plan material in `docs/poc/` + `AGENTS.md` means the next agent (or engineer) starts from the SOW-grounded plan, knows exactly what is real vs mocked, and has an ordered path to the product — the difference between "continue this codebase" and "reverse-engineer this codebase."
