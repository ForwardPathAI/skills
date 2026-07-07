---
name: poc-to-product-architecture
description: Turn a Statement of Work and POC repository into a production system-design canvas — architecture, POC gap audit, Azure resource map, Bicep skeleton, security/reliability measures, and cost estimate, constrained to the Forward Path stack and customer-deployable Bicep. Use when the user says "productionize this POC", "turn this POC into a product", "SOW to architecture", "system design from SOW and POC", "make this POC production-ready", or mentions poc-to-product-architecture.
---

# POC to Product Architecture

Forward Path POCs prove feasibility; this skill turns a **Statement of Work** ($sow) and a **POC repository** ($pocLink, optional) into a production system-design deliverable: a Cursor canvas (`<app>-architecture.canvas.tsx`) that presents the architecture, POC gap audit, Azure resource map, Bicep skeleton, security/reliability measures, and cost estimate — constrained so the whole topology deploys to customer Azure tenants from a single parameterized Bicep template via container images in the shared ACR.

The skill is usually invoked **from inside the POC repo**. Reference bundled docs relative to this skill's directory (wherever `skills.sh` installed it), never an absolute install path.

## Prerequisites

- **$sow** — a SOW URL or file path (ask if not given).
- **$pocLink** — optional GitHub repo URL. If absent, Step 2 searches for a probable match.
- **`gh` CLI** authenticated — needed for org repo search and POC inspection when the POC is not the current repo.
- Read access to the **invoking repo** (the usual invocation context is inside the POC repo).
- Read [product-foundation/SKILL.md](../product-foundation/SKILL.md) for the target stack and [azure-infra-setup/SKILL.md](../azure-infra-setup/SKILL.md) for Azure conventions before designing.
- Bundled references in this skill directory:
  - [ARCHITECTURE_BAR.md](ARCHITECTURE_BAR.md) — production-quality checklist the design must pass.
  - [BICEP_CONSTRAINT.md](BICEP_CONSTRAINT.md) — deployability contract (ACR images, single parameterized Bicep, webhook install).
  - [CANVAS_GUIDE.md](CANVAS_GUIDE.md) — canvas authoring rules and required deliverable sections.

Stop and report anything missing before proceeding.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Ingest the SOW
- [ ] Step 2: Locate the POC
- [ ] Step 3: Audit the POC
- [ ] Step 4: Design the production architecture
- [ ] Step 5: Produce the deliverable
```

### Step 1: Ingest the SOW

Accept $sow as a URL or file. If a URL returns empty (JavaScript-rendered, e.g. Notion), use a browser tool to read the rendered text — same fallback as [web-ui](../web-ui/SKILL.md) step 1.

Extract and record:
- Objectives and scope
- Roles/users
- Features
- Data entities
- Integrations
- Constraints
- **Budget signals**
- Phasing

Complete this step when every extracted item is recorded and anything ambiguous is queued as an open question for the canvas Risks section.

### Step 2: Locate the POC

- If $pocLink is given, use it.
- Else if the current working repo looks like the POC (invocation from inside the POC repo is the expected case), propose it as the match.
- Else search the GitHub org: `gh repo list <org>` and `gh search repos` with SOW keywords; rank candidates by name/description/README similarity to the SOW.

**Always confirm the selected repo with the user before auditing.** Never audit an unconfirmed match.

Complete this step when a confirmed $pocRepo exists (or the user states there is no POC — in which case Step 3 is skipped and the canvas omits the POC gap-audit section).

### Step 3: Audit the POC

Inventory $pocRepo against the SOW.

- **Stack inventory:** languages, frameworks, package manager, DB, auth, hosting artifacts (Dockerfiles, infra files).
- **Coverage:** which SOW requirements the POC already implements.
- **Demo-grade findings:** hardcoded secrets, missing auth, SQLite/in-memory storage, no tests, no error handling, single-file architecture — anything that must be replaced for production.
- **Missing:** SOW requirements with no POC trace.

Every finding cites a file path in $pocRepo or a SOW clause; judgments without a citation are marked `inferred`.

Complete this step when every SOW requirement from Step 1 has a status: `covered` / `demo-grade` / `missing`.

### Step 4: Design the production architecture

- Map the product onto the [product-foundation](../product-foundation/SKILL.md) stack (Bun monorepo, Turborepo, Next.js App Router, Hono RPC, Drizzle + PostgreSQL, TanStack Query, Zod, Better Auth, Azure Container Apps). Decide which **modules** apply (auth, separate Hono API, BullMQ jobs, AI) from the SOW.
- Apply [azure-infra-setup](../azure-infra-setup/SKILL.md) conventions: shared registry `forwardpathai` (image refs `forwardpathai.azurecr.io/<app-image>`), OIDC federation for CI, narrow RBAC, Key Vault for secrets, preferred regions **East US 2** or **Canada Central**, Container Apps as default compute.
- Keep every choice inside the [BICEP_CONSTRAINT.md](BICEP_CONSTRAINT.md) contract.
- Run the design through [ARCHITECTURE_BAR.md](ARCHITECTURE_BAR.md); iterate until every checklist item passes or a failure is converted into a Risks entry.
- Estimate per-resource monthly cost; if the SOW gave budget signals, check the total against them.

Complete this step when the bar passes, the Bicep skeleton outline exists, and the cost table is filled.

### Step 5: Produce the deliverable

Write the canvas per [CANVAS_GUIDE.md](CANVAS_GUIDE.md) to **both** locations:
1. `docs/architecture/<app>-architecture.canvas.tsx` in the POC repo (version-controlled source of truth).
2. The IDE managed canvases directory `/Users/<user>/.cursor/projects/<workspace>/canvases/<app>-architecture.canvas.tsx` (render duplicate).

Verify the repo copy is git-visible (`git status --short docs/architecture/`); if ignored, relocate or ask before changing ignore rules — same rule as [customer-deployment-package](../customer-deployment-package/SKILL.md) Step 6.

Report to the user:
- Both file paths (the managed one as a clickable canvas link).
- Deviations from product-foundation (if any).
- Top risks.
- Next-step skills: [azure-infra-setup](../azure-infra-setup/SKILL.md) for full Bicep authoring, [customer-deployment-package](../customer-deployment-package/SKILL.md) for the customer handoff.

Complete this step when both copies exist, the canvas type-checks (the canvas edit result reports no errors), and the report is delivered.

## Decision table

| Situation | Action |
|---|---|
| POC not found by search | Ask the user for the link; never guess-audit a repo the user has not confirmed. |
| POC stack conflicts with product-foundation | Keep the POC stack only if migration cost is disproportionate to SOW scope; state the deviation and reason in the canvas. |
| A SOW requirement cannot be expressed within the Bicep/webhook contract | Include it in the canvas Risks section with a proposed alternative; do not drop it silently. |
| No canvas support in the running agent | Fall back to `docs/architecture/ARCHITECTURE.md` with mermaid diagrams, same required sections per [CANVAS_GUIDE.md](CANVAS_GUIDE.md). |
| Budget signals absent from the SOW | Default to consumption/scale-to-zero SKUs and say so in the cost table caption. |
| User states there is no POC | Skip Step 3; omit the POC gap-audit section from the deliverable. |
| A design element has no SOW or POC citation | Mark it `inferred` and list it in Risks. |

## Anti-patterns

- Inventing SOW requirements not present in $sow.
- Auditing an unconfirmed repo.
- Designing resources that need portal-only/manual setup (breaks the webhook install path).
- Putting secret **values** anywhere in the deliverable — document secret **names** only.
- Producing a markdown table dump in chat instead of the canvas artifact.
- Writing the canvas only to chat instead of the two required file locations.
- Creating per-app ACRs instead of using the shared `forwardpathai` registry.
- Designing topology that cannot be expressed as one parameterized Bicep template.
- Stating security/reliability measures as aspirations instead of concrete decisions.

## Additional resources

- Forward Path stack and conventions: [product-foundation/SKILL.md](../product-foundation/SKILL.md)
- Forward Path Azure conventions: [azure-infra-setup/SKILL.md](../azure-infra-setup/SKILL.md)
- Customer deployment handoff: [customer-deployment-package/SKILL.md](../customer-deployment-package/SKILL.md)
- Production-quality checklist: [ARCHITECTURE_BAR.md](ARCHITECTURE_BAR.md)
- Bicep deployability contract: [BICEP_CONSTRAINT.md](BICEP_CONSTRAINT.md)
- Canvas deliverable guide: [CANVAS_GUIDE.md](CANVAS_GUIDE.md)
