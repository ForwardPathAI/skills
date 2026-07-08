# Canvas Guide

How to author the architecture deliverable produced by `poc-to-product-architecture`. This guide is self-contained so the skill works even when the running agent has not read Cursor's canvas skill.

The canvas is the **interactive source of truth** and keeps the Bicep skeleton and mermaid diagram source inline. Its companion — a shareable DOCX report with the same sections but **rendered** diagrams and **no** literal Bicep/mermaid source — is covered in [DOCX_GUIDE.md](DOCX_GUIDE.md). Keep the two in sync: when the design changes, regenerate both.

## File rules

- Exactly **one** `.canvas.tsx` file per deliverable.
- Imports **only** from `cursor/canvas` — no relative imports, no npm packages, no Node built-ins.
- **Default-export** the top-level component.
- Embed **all data inline** — no `fetch()`, no network calls.
- Colors only via `useHostTheme()` tokens — no hardcoded hex values.
- **No slop patterns:** no gradients, emojis, box-shadows, rainbow coloring, giant text, or decorative borders.
- **No empty states** — if a section has no data, omit it entirely. If the entire canvas would be empty, do not produce a canvas; tell the user what's missing.
- Every chart and table must be self-describing: title naming the specific metric, axis labels with units, legend when multiple series, source/time-range caption.

## Dual write

Write the **same** canvas file content to both locations:

| Location | Purpose |
|----------|---------|
| `docs/architecture/<app>-architecture.canvas.tsx` in the POC repo | Version-controlled source of truth |
| `/Users/<user>/.cursor/projects/<workspace>/canvases/<app>-architecture.canvas.tsx` | Render duplicate (opens beside the chat) |

The repo copy is authoritative. The managed copy is a render duplicate only.

Before finishing, verify the repo copy is git-visible:

```bash
git status --short docs/architecture/
```

If ignored, relocate or ask before changing ignore rules.

## Required sections

Present these sections **in order**. Each maps to content gathered in Steps 1–4.

### 1. Executive overview

What the product is and a one-paragraph architecture summary. Name the target stack (product-foundation) and deployment model (Container Apps + Bicep webhook install).

### 2. SOW traceability

Requirement → component mapping table. Every SOW requirement from Step 1 appears **exactly once** with status:
- `covered by POC`
- `new`
- `deferred`

### 3. POC gap audit

Findings from Step 3. Omit this section if the user stated there is no POC. Each finding tagged:
- `demo-grade` — exists but must be replaced for production
- `missing` — no POC trace
- `reusable` — production-ready as-is

Every finding cites a file path in $pocRepo or a SOW clause; uncited judgments are marked `inferred`.

### 4. Architecture layers

Map the product onto product-foundation layers:
- Web (`apps/web` — Next.js App Router)
- API (`apps/api` or Next route handlers — Hono RPC)
- Data (`packages/database` — Drizzle + PostgreSQL)
- Jobs (`apps/jobs` — BullMQ + Redis, if needed)
- Auth (Better Auth + Microsoft SSO, if SOW has users/roles)
- AI (`packages/ai` — Vercel AI SDK, if needed)

State any deviations from product-foundation and why.

### 5. Azure resource map

Every resource the Bicep skeleton declares, with SKU and region. Include: Log Analytics, Container Apps environment, Key Vault, each Container App, PostgreSQL Flexible Server, and any extras (Redis, storage).

### 6. Bicep skeleton

A code block following the section list in [BICEP_CONSTRAINT.md](BICEP_CONSTRAINT.md): parameters, Log Analytics, Container Apps environment, Key Vault, ACR pull wiring, per-service Container Apps, PostgreSQL, extras, outputs. Use real resource types and parameter names — not a complete working template.

This section is **canvas-only**: the DOCX report omits the literal Bicep (and mermaid) source and instead points readers at the next-step skills. See [DOCX_GUIDE.md](DOCX_GUIDE.md).

### 7. Security and reliability

The passed items from [ARCHITECTURE_BAR.md](ARCHITECTURE_BAR.md), stated as **decisions** not aspirations. Group under Security and Reliability headings.

### 8. Cost estimate

Per-resource monthly cost table. Include a caption stating scale assumptions. If budget signals were absent from the SOW, default to consumption/scale-to-zero SKUs and say so in the caption.

### 9. Phased migration path

POC → production phases aligned to SOW phasing. Each phase lists what gets built, migrated, or replaced.

### 10. Risks and open questions

Including:
- Bicep-contract conflicts (requirements that cannot be webhook-installed)
- `inferred` items awaiting user confirmation
- Budget overruns vs. SOW signals
- Stack deviations and their trade-offs

## Fallback

If the running agent has no canvas support, write the same ten sections to `docs/architecture/ARCHITECTURE.md` with mermaid diagrams replacing visual components. Preserve the same section order and content requirements.

## Reporting

In the Step 5 report, include:
- File paths: the canvas (managed copy as a clickable canvas link using its full absolute path) and, when produced, the generated DOCX report (see [DOCX_GUIDE.md](DOCX_GUIDE.md)).
- Deviations from product-foundation (if any).
- Top risks from section 10.
- Next-step skills: [azure-infra-setup](../azure-infra-setup/SKILL.md) for full Bicep authoring, [customer-deployment-package](../customer-deployment-package/SKILL.md) for the customer handoff.
