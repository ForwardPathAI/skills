# Conventions

Cross-cutting code conventions for every Forward Path product. These are the single source of truth for style; a project's own `AGENTS.md` may override, and takes precedence when it does.

## TypeScript

Strict everywhere. Root `tsconfig.json`:

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "verbatimModuleSyntax": true,
    "moduleResolution": "bundler",
    "jsx": "react-jsx"
  }
}
```

- `import type { ... }` for type-only imports (enforced by `verbatimModuleSyntax`).
- **No `enum`** — use `as const` arrays/objects and derive the union type.
- **No `any`**, no non-null assertions (`!`). Model absence explicitly.
- Path aliases: `@prime/*` (or your scope) → `packages/*/src`; `@/*` → the web app root.

## Naming

| Kind | Convention | Example |
|------|------------|---------|
| Files | kebab-case | `use-azure-deployments.ts`, `deployment-form-dialog.tsx` |
| Components | PascalCase | `ChatHeader` |
| Functions / vars | camelCase | `getUserById`, `isLoading` |
| Constants | SCREAMING_SNAKE or grouped `as const` objects | `SYSTEM_ORG_SLUG`, `AUTH_ROUTES` |
| Types | PascalCase | `Chat`, `AzureDeploymentListItem` |
| DB tables | kebab / snake column names | `organization_settings` |
| Workspace packages | `@<scope>/<name>` | `@prime/database` |

## Foldering

Colocate feature-private code; share only what is reused.

```
apps/web/
  app/
    (app)/           # authenticated route group
      <feature>/
        page.tsx     # server component page
        _components/  # feature-private components (barrel via index.ts)
    (auth)/          # public auth route group
    api/             # route handlers (auth, proxy)
  hooks/             # cross-feature data hooks (TanStack Query)
  components/ui/     # shadcn primitives
  lib/               # utils, routes, api-client, env
```

- **Route groups** separate authenticated (`(app)`) from public (`(auth)`).
- Feature-private components live in `_components/` next to the page; shared UI lives in `components/`.
- Cross-cutting libraries are workspace packages: schema/queries in `packages/database`, Zod schemas in `packages/shared`, API routes in `packages/api`.

## Validation

Zod at every trust boundary. Shared reusable schemas live in `packages/shared/src/validators`:

```ts
export const emailSchema = z.email({ error: 'Invalid email address' })
export const idSchema = z.uuid({ error: 'Invalid ID format' })
```

Never parse untrusted input by hand. In Hono, never call `c.req.json()` raw — validate then read:

```ts
.post('/', authMiddleware, zValidator('json', createThingSchema), async (c) => {
  const input = c.req.valid('json') // typed + validated
})
```

## API contract

Every API response is wrapped, so clients discriminate on shape, not status alone:

```ts
return c.json({ data })          // success
return c.json({ error: '...' }, 400) // failure
```

Hono routes for RPC compatibility:

1. **Method chaining** (`.get().post().patch()`) — required for `hc<AppType>` inference.
2. **`zValidator`** on every input (`'json'`, `'query'`, `'param'`).
3. **`{ data }` / `{ error }`** wrapper on every response.
4. **Export the composed `AppType`** for the client.

Client consumes the exported type — request/response types flow automatically:

```ts
import { hc } from 'hono/client'
import type { AppType } from '@prime/api'

export const api = hc<AppType>(baseUrl)
const res = await api.api.v1.admin['azure-deployments'].$get()
```

For the browser, use relative URLs and let a Next catch-all proxy to the API; resolve the base URL server-side from `API_URL`.

## Route constants

Never hardcode route strings. Define them once in `lib/routes` and import:

```ts
// good
router.push(AUTH_ROUTES.login)
// bad
router.push('/login')
```

## Client data

- **TanStack Query** for client fetching/mutations. Configure one `QueryClient` in a provider; sensible defaults: `staleTime` ~60s, `refetchOnWindowFocus: false`, `retry: 3` (queries) / `retry: 1` (mutations).
- **Query keys are structured factories** (`deploymentKeys.list()`), not ad-hoc arrays, so invalidation is precise.
- Query functions call the typed Hono RPC client, not bare `fetch`.

## Database

- Schema per domain in `packages/database/src/schema/*.ts`; queries in `packages/database/src/queries`.
- UUID primary keys (`uuid().primaryKey().defaultRandom()`), `timestamp` with `defaultNow()`.
- Derive types with Drizzle's `InferSelectModel` — do not hand-write row types.
- Migration workflow: edit schema → `bun run db:generate` (writes SQL to `drizzle/`) → `bun run db:migrate`. The API app runs migrations on boot.

## Testing

- `bun test` only. Import from `bun:test`:

```ts
import { test, expect } from 'bun:test'
```

- Files: `*.test.ts(x)` preferred, colocated with the code or in `__tests__/`.
- Coverage on in `bunfig.toml`; CI runs `bun test --coverage` with Postgres + Redis service containers.

## Env & secrets

- Bun auto-loads `.env` from the workspace root; document every var in `.env.example`.
- **Infisical** wraps dev commands (`infisical run --env=dev -- ...`); production injects Azure Key Vault references into Container Apps.
- Validate required secrets at app startup (fail fast on missing `DATABASE_URL`, `BETTER_AUTH_SECRET`, `REDIS_URL`, `ENCRYPTION_KEY`, etc.).

## Lint & format

- **oxlint** is the linter (`bun run lint` → `oxlint .`). Do not add Biome/Ultracite.
- Notable rules: `eqeqeq`, `consistent-type-imports`, `react/jsx-key`.
