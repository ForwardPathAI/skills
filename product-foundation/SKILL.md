---
name: product-foundation
description: The standard stack and conventions for building Forward Path products — Bun monorepo, Next.js App Router, Hono RPC APIs, Drizzle/Postgres, TanStack Query, Better Auth, Azure. Use when scaffolding a new repo or app, starting a project, adding a backend/API/auth/jobs module, or deciding how a Forward Path product should be built; and whenever an agent needs the canonical stack, versions, or code conventions.
---

# Product Foundation

The **standard** for how Forward Path builds products: one opinionated stack, one set of conventions, applied from the first commit so technical and non-technical people can collaborate on the same codebase.

The stack is tiered into two ideas — use them throughout:

- **core** — present in *every* project from day one.
- **module** — added only when the project needs it, on top of the same core.

The reference implementation is the `PRS-Walmart-PRIME` monorepo; this skill distills it into a reusable standard. Full detail lives in three docs, read the one the task needs:

- [STACK.md](STACK.md) — the canonical stack, pinned major versions, version discipline, and the API-typing decision.
- [CONVENTIONS.md](CONVENTIONS.md) — TypeScript, naming, foldering, validation, the API response contract, testing, and env.
- [SCAFFOLD.md](SCAFFOLD.md) — step-by-step bootstrap of a new repo with real config files.

## The stack at a glance

| Layer | core | module (add when needed) |
|-------|------|--------------------------|
| Package manager + runtime | **Bun** (never Node/npm/pnpm/Vite) | — |
| Monorepo | **Turborepo** (`apps/*`, `packages/*`) | — |
| Web | **Next.js** App Router + **React**, RSC by default | — |
| UI | **Tailwind** + **shadcn/ui** + `next-themes` | — |
| Client data | **TanStack Query** | — |
| Validation | **Zod** (shared schemas in `packages/shared`) | — |
| Database | **Drizzle** + **PostgreSQL** | pgvector (embeddings), MSSQL (`packages/mssql`, external SQL Server) |
| API typing | **Hono RPC** `hc<AppType>` + `zValidator` (never tRPC) | — |
| Backend | Next route handlers + server actions | separate **Hono API** app on Bun |
| Lint / test | **oxlint** + **bun test** | — |
| Auth | — | **Better Auth** + Microsoft SSO + org RBAC |
| Jobs | — | **BullMQ** + Redis (`apps/jobs`) |
| AI | — | Vercel AI SDK (`packages/ai`) |
| Secrets | **Infisical** (dev) → Azure Key Vault (prod) | — |
| Deploy | **Azure Container Apps** via **Terraform** + ACR | — |

Exact major versions and the update rule are in [STACK.md](STACK.md).

## Non-negotiables

These are settled. Do not reintroduce the alternatives.

- **Bun** for install, scripts, runtime, and tests — never Node, npm, pnpm, Vite, jest, or vitest.
- **Drizzle + PostgreSQL** — never a different ORM or a raw-SQL layer by default.
- **Zod at every boundary** — never read `c.req.json()` raw; always `zValidator` + `c.req.valid()`.
- **Hono RPC** for typed APIs — never tRPC.
- **TanStack Query** for client data. (PRIME still has legacy SWR; new work does not add SWR.)
- **oxlint** for linting. (PRIME docs mention Biome/Ultracite; that is stale — do not use them.)
- **Strict TypeScript**, `import type`, `as const` arrays instead of enums, `{ data }` / `{ error }` API responses, route constants over hardcoded paths. Full rules in [CONVENTIONS.md](CONVENTIONS.md).

## Workflows

Pick the branch that matches the task.

### Scaffold a new project

1. Confirm which **modules** the project needs (auth, separate API, jobs, AI) before writing anything — this decides the app/package layout.
2. Follow [SCAFFOLD.md](SCAFFOLD.md) top to bottom: Bun + Turbo monorepo, `apps/web`, `packages/database`, `packages/shared`, config files, then each chosen module.
3. Apply [CONVENTIONS.md](CONVENTIONS.md) as you create files — get naming, TS config, and the API contract right from the first commit.
4. Provision infra with the [azure-infra-setup](../azure-infra-setup/SKILL.md) skill; ship deploy via Azure Container Apps.
5. Write the plain-language README (see below) as part of the initial commit, not later.

### Add a module to an existing project

1. Read the target project's `AGENTS.md`/`CLAUDE.md` first — honor project-specific overrides over this skill's defaults.
2. Match the existing layout: modules are workspace packages (`packages/*`) or apps (`apps/*`), never inlined into `apps/web`.
3. Wire the module through the standard seams — Zod schemas in `packages/shared`, DB access in `packages/database`, typed routes exported into `AppType` for the RPC client.

### Consult a convention

Answer stack or code-style questions from [STACK.md](STACK.md) and [CONVENTIONS.md](CONVENTIONS.md) rather than guessing — these are the single source of truth for the standard.

## Building with non-technical collaborators

A Forward Path product is legible to PMs, designers, and clients, not just engineers. Two obligations:

- **Every repo ships a plain-language `README.md`** — what the product does, the stack in one plain sentence per layer, and how to run it, written so a non-engineer can follow the setup. No unexplained jargon.
- **Translate feature requests into the standard architecture.** When a non-technical collaborator describes a feature in plain language, map it explicitly onto the layers before coding: which **schema** change (Drizzle), which **API** route or server action (Hono + Zod), which **query hook** (TanStack Query), which **UI** (shadcn). State that mapping back to them in plain terms so they can confirm scope.

## Related skills

- [azure-infra-setup](../azure-infra-setup/SKILL.md) — author the Terraform/Bicep infra for the deploy target.
- [open-pr](../open-pr/SKILL.md) — ship the work as a Linear-linked PR.
- [qa-test-plan](../qa-test-plan/SKILL.md) — generate a customer-shareable QA plan from the app surface.
