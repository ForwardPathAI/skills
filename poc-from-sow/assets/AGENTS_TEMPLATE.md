# AGENTS.md — <Product Name>

<One sentence: what this product does and for whom.>

This repository started as a **POC generated from the SOW** and is built to continue into the real product. **Read `docs/poc/` before changing anything** — especially `docs/poc/POC_NOTES.md` (what is mocked and why) and `docs/poc/PRODUCT_ROADMAP.md` (the ordered path to product).

## Stack

Built on the Forward Path `product-foundation` standard. In one line per layer:

- Runtime / package manager: **Bun** (never Node/npm/pnpm).
- Monorepo: **Turborepo** — `apps/*`, `packages/*`.
- Web: **Next.js** App Router + **Tailwind** + **shadcn/ui**.
- API: **Hono RPC** + **Zod** (`zValidator`); typed client `hc<AppType>`.
- Data: **Drizzle** + **PostgreSQL** (`packages/database`).
- Client data: **TanStack Query**.
- Auth: **Better Auth** + Microsoft Entra SSO + org RBAC.
- <Jobs: **BullMQ** + Redis (`apps/jobs`) — if applicable.>
- <AI: Vercel AI SDK (`packages/ai`) — if applicable.>

## Repo map

```
apps/
  web/    — Next.js UI (screens per docs/poc/design/)
  api/    — Hono RPC API            (if applicable)
  jobs/   — BullMQ workers          (if applicable)
  mobile/ — Expo app                (if applicable)
packages/
  database/ — Drizzle schema + migrations + seed
  shared/   — Zod schemas, route constants, integration adapter interfaces
  auth/     — Better Auth config
docs/
  poc/      — POC plan, SOW traceability, notes, product roadmap, demo script, design/
  architecture/ — production architecture canvas + DOCX (from poc-to-product-architecture)
```

## Commands

```bash
bun install            # install
docker compose up -d   # local Postgres (+ Redis if jobs)
bun run db:migrate     # apply migrations
bun run db:seed        # load the demo dataset
bun dev                # run the app(s)
bun run typecheck      # strict TS
bun run lint           # oxlint
bun run build          # production build
```

## Conventions

Follow product-foundation: strict TypeScript, `import type`, `as const` over enums, `{ data } / { error }` API responses, route constants, Zod at every boundary. External integrations live behind typed adapters (`packages/shared` interface + `*-mock.ts` in the POC) — replace the mock, keep the interface.
