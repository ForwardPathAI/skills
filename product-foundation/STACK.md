# The Standard Stack

The canonical technology choices for Forward Path products, split into **core** (every project) and **module** (added when the project needs it). This is the single source of truth for what we build on and which versions.

## Version discipline

Versions below are the **baseline majors** for the current standard. The rule:

- **Match the major**, then take the **latest stable minor/patch** at scaffold time (`bun add <pkg>@latest` within the pinned major).
- **Pin shared versions in a Bun catalog** (root `package.json` `catalog`), so every workspace resolves the same version.
- Bump a **major deliberately** — as its own PR, across the whole monorepo, never incidentally.

Do not treat a version number here as "install exactly this" — treat it as "this major, newest stable within it."

## Core

Present in every project from the first commit.

| Concern | Choice | Baseline major |
|---------|--------|----------------|
| Package manager + runtime | Bun | 1.3.x |
| Monorepo orchestration | Turborepo | 2.x |
| Language | TypeScript (strict) | 5.x |
| Web framework | Next.js (App Router only) | 16.x |
| UI runtime | React | 19.x |
| Styling | Tailwind CSS (CSS-first, no `tailwind.config.js`) | 4.x |
| Components | shadcn/ui (base color zinc, RSC) + `next-themes` + `lucide-react` + `sonner` | latest |
| Client data | TanStack Query | 5.x |
| Validation | Zod | 4.x |
| ORM | Drizzle ORM + `drizzle-kit` | 1.x (rc) |
| Database | PostgreSQL | 16 |
| API typing | Hono + `hc<AppType>` RPC + `@hono/zod-validator` | Hono 4.x |
| Lint | oxlint | 1.x |
| Test | `bun test` (built-in runner) | — |
| Secrets (dev) | Infisical | — |
| Deploy | Azure Container Apps + Terraform + ACR | — |

**Package manager + runtime.** Bun does install, scripts, the API/jobs runtime, and tests. Never Node, npm, pnpm, or Vite. Docker images use `oven/bun` base. Pin the Bun version in CI (e.g. `BUN_VERSION`).

**Monorepo.** Standardize on the Turbo monorepo from day one even for a single app, so modules can be added without restructuring:

```
apps/       # deployable apps: web, (api), (jobs)
packages/   # shared libraries: database, shared, (auth), (ai), ...
```

Shared versions live in a Bun `catalog`; workspace packages reference them.

**Web.** Next.js App Router only — no `pages/`. Server Components are the default; add `"use client"` only where interactivity requires it. Async server pages fetch session/DB directly.

## Module

Add on top of the same core when the project needs the capability. Each is a workspace package or app, never inlined into `apps/web`.

| Module | Choice | Add when |
|--------|--------|----------|
| Separate backend | Hono API app on Bun (`apps/api`), mounted at `/api/v1` | The backend outgrows Next route handlers, or is shared by multiple clients |
| Background jobs | BullMQ + Redis (`apps/jobs`, `packages/redis`) | Work must run off the request path (queues, schedules, long tasks) |
| Auth | Better Auth + `@better-auth/sso` + organization + admin plugins | The product has users; Microsoft Entra ID SSO is the default provider |
| Embeddings | pgvector on the same Postgres | AI/semantic-search features |
| AI | Vercel AI SDK (`packages/ai`) + `@ai-sdk/azure` / OpenRouter | LLM features, tools, streaming |
| External SQL Server | `packages/mssql` (`mssql` driver) | Integrating a client's existing SQL Server |
| Email | React Email + Resend (`packages/email`) | Transactional email |
| Object storage | `packages/storage` (Vercel Blob / Azure / S3) | File uploads/downloads |

## API typing decision

How APIs are typed depends on whether the project has a **separate backend module**.

- **Single Next app (no API module):** type end-to-end with **shared Zod schemas** in `packages/shared` + Next **route handlers** and **server actions** that validate input with those schemas. Keep the `{ data }` / `{ error }` response contract so the shape is stable if a Hono API is added later.
- **With the Hono API module:** the API is the typed boundary. Compose routes with method chaining, validate every input with `zValidator`, export the composed `AppType`, and consume it from the web app with `hc<AppType>` so request/response types flow automatically. Never tRPC.

Details of the response contract and validation rules are in [CONVENTIONS.md](CONVENTIONS.md).

## Reference implementation

`PRS-Walmart-PRIME` is the working example of the full stack (web + Hono API + jobs + auth + AI + Azure). Two things in it are **legacy, not the standard**: SWR (superseded by TanStack Query) and Biome/Ultracite references in docs (superseded by oxlint). New work follows this doc, not those.
