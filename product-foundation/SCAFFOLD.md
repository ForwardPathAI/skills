# Scaffold a New Project

Bootstrap a new Forward Path product on the standard stack. Run every command with **Bun**. Substitute `@prime` with the project's own scope.

Copy this checklist and track progress:

```
- [ ] Step 1: Decide modules
- [ ] Step 2: Bun + Turbo monorepo skeleton
- [ ] Step 3: Shared config (tsconfig, catalog, oxlint, bunfig)
- [ ] Step 4: packages/shared + packages/database
- [ ] Step 5: apps/web (Next + Tailwind + shadcn + TanStack Query)
- [ ] Step 6: Chosen modules (api / jobs / auth / ai)
- [ ] Step 7: Infra, secrets, README, first commit
```

## Step 1: Decide modules

Confirm with the user which **modules** the project needs before generating anything — this fixes the app/package layout. See [STACK.md](STACK.md) for the module list. Defaults: web + database + shared (core). Add `apps/api` if the backend is shared or heavy; `apps/jobs` for background work; auth/ai packages as needed.

## Step 2: Monorepo skeleton

```bash
mkdir my-product && cd my-product
bun init -y
```

Root `package.json` — Bun workspaces + catalog + Turbo scripts:

```jsonc
{
  "name": "my-product",
  "private": true,
  "packageManager": "bun@1.3.3",
  "workspaces": {
    "packages": ["packages/*", "apps/*"],
    "catalog": {
      "next": "16.1.1",
      "react": "19.2.4",
      "react-dom": "19.2.4",
      "drizzle-orm": "1.0.0-rc.1",
      "zod": "^4.1.13",
      "@tanstack/react-query": "^5.100.9",
      "hono": "^4.12.25",
      "tailwindcss": "^4.1.13",
      "typescript": "^5.6.3"
    }
  },
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "typecheck": "turbo run typecheck",
    "lint": "turbo run lint",
    "test": "bun test",
    "db:generate": "turbo run generate --filter=@prime/database",
    "db:migrate": "turbo run migrate --filter=@prime/database",
    "db:studio": "turbo run studio --filter=@prime/database"
  },
  "devDependencies": { "turbo": "^2.9.18", "oxlint": "^1.68.0" }
}
```

Add `turbo.json` with `dev`, `build`, `typecheck`, `lint` tasks (build depends on `^build`). Take the latest stable within each pinned major (see [STACK.md](STACK.md) version discipline).

## Step 3: Shared config

Root `tsconfig.json` (strict — full flags in [CONVENTIONS.md](CONVENTIONS.md)):

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "verbatimModuleSyntax": true,
    "moduleResolution": "bundler",
    "types": ["bun-types"],
    "jsx": "react-jsx",
    "paths": { "@prime/*": ["packages/*/src"] }
  }
}
```

`.oxlintrc.json` at root (`eqeqeq`, `consistent-type-imports`, `react/jsx-key`). `bunfig.toml` for tests:

```toml
[test]
coverage = true
coverageDir = "./coverage"
coverageReporter = ["text", "lcov"]
```

## Step 4: packages/shared + packages/database

`packages/shared` — Zod validators reused across apps:

```ts
// packages/shared/src/validators/index.ts
import { z } from 'zod'
export const emailSchema = z.email({ error: 'Invalid email address' })
export const idSchema = z.uuid({ error: 'Invalid ID format' })
```

`packages/database` — Drizzle + Postgres. Install `drizzle-orm pg`, dev `drizzle-kit`.

```ts
// packages/database/drizzle.config.ts
import { defineConfig } from 'drizzle-kit'
export default defineConfig({
  schema: './src/schema/index.ts',
  out: './drizzle',
  dialect: 'postgresql',
  dbCredentials: { url: process.env.DATABASE_URL || '', ssl: false },
})
```

```ts
// packages/database/src/client.ts
import { drizzle } from 'drizzle-orm/node-postgres'
import pg from 'pg'

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL || '' })
export const db = drizzle({ client: pool })
```

Provide a local Postgres via `docker-compose.yml` (`pgvector/pgvector:pg16` if embeddings are a module, else `postgres:16`). Package scripts: `generate` → `drizzle-kit generate`, `migrate` → `drizzle-kit migrate`, `studio` → `drizzle-kit studio`.

## Step 5: apps/web

```bash
cd apps && bun create next-app@latest web --ts --app --tailwind --no-src-dir
cd web && bunx shadcn@latest init   # base color: zinc, CSS variables
```

`next.config.ts` for the monorepo + standalone Docker output:

```ts
import type { NextConfig } from 'next'
const nextConfig: NextConfig = {
  output: 'standalone',
  turbopack: { root: '../..' },
}
export default nextConfig
```

TanStack Query provider:

```ts
// apps/web/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query'
export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: 60_000, refetchOnWindowFocus: false, retry: 3 },
      mutations: { retry: 1 },
    },
  })
}
```

Wrap the `(app)` layout in a `QueryClientProvider` using `makeQueryClient()`. Add `lib/routes.ts` for route constants and `lib/utils.ts` with `cn()` (`clsx` + `tailwind-merge`).

## Step 6: Chosen modules

Only the modules chosen in Step 1.

- **apps/api** (Hono on Bun): entry `bun --hot src/index.ts`, mount routes at `/api/v1`, run DB migrations on boot, export `AppType`. Add a Next catch-all `app/api/v1/[...path]` proxy to `API_URL`. See the API contract in [CONVENTIONS.md](CONVENTIONS.md).
- **apps/jobs** (BullMQ + Redis): add `packages/redis` (ioredis), Redis to `docker-compose.yml`.
- **auth** (`packages/auth`): Better Auth + `@better-auth/sso` + `organization` + `admin` plugins, Drizzle adapter, Microsoft social provider. Next handler via `toNextJsHandler(auth)` at `app/api/auth/[...all]`.
- **ai** (`packages/ai`): Vercel AI SDK + `@ai-sdk/azure` / OpenRouter; Zod-typed tools.

## Step 7: Infra, secrets, README

1. **Secrets:** `.infisical.json` + `.env.example` documenting every var. Validate required secrets at startup.
2. **Infra:** use the [azure-infra-setup](../azure-infra-setup/SKILL.md) skill — Terraform → Azure Container Apps, ACR, Key Vault, GitHub OIDC. Multi-stage Bun Dockerfile per app (`turbo prune`, `oven/bun` base).
3. **CI:** GitHub Actions — lint (`oxlint`), typecheck, `bun test --coverage` (Postgres + Redis services), build, `bun pm audit`.
4. **README:** plain-language, per the collaboration section of [SKILL.md](SKILL.md) — a non-engineer can follow setup.
5. **First commit** with everything above; ship via [open-pr](../open-pr/SKILL.md).
