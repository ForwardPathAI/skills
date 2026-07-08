# POC Bar

The quality bar for a `poc-from-sow` POC. The governing rule: **every line survives customer approval.** The POC is the first increment of the real product, so the bar is higher than a throwaway demo — but it is still a POC, so some edges may be shortcut *as long as they are logged*.

This bar is reverse-engineered from the gap audit of the reference POC `PRS-PriceTagAudit` — a POC that looked good but was expensive to productionize because it took demo shortcuts in the core. Each "never" item below cites the real finding as its cautionary example. Do not repeat these.

## Tier 1 — Never (even in a POC)

These are the mistakes that force a rewrite. They are banned outright.

- **`typescript.ignoreBuildErrors` (or `eslint.ignoreDuringBuilds`)** — hiding type failures so the build is green is a lie. *(PRS: `apps/web/next.config.mjs`.)* Keep strict TS honest.
- **Hardcoded secrets or connection strings** — use env vars + `.env.example`; never commit values.
- **Client-side-only role switching** — roles must come from the server session, not a React context toggle the user can flip. *(PRS: `apps/web/lib/role-context.tsx`.)*
- **Stub login** — a login page that is just a `Link` to the dashboard with no real auth call. *(PRS: `apps/web/app/page.tsx`.)*
- **Pages importing fixture files when a schema exists** — screens must read from the seeded database via the API, not from a `mock-data.ts`. *(PRS: `apps/web/lib/mock-data.ts` consumed directly by dashboard pages.)*
- **Third-party calls inlined in route handlers** — external services go behind a typed adapter, not `fetch()` straight from a route. *(PRS: OpenAI called directly in `apps/web/app/api/capture/ocr/route.ts`.)*
- **Demo-only code paths** — code that only works for the seeded demo and would be deleted for production. If it ships in the POC, it must be the real thing (or a logged typed mock).

## Tier 2 — Always (the continuation-ready core)

These are real product code from the first commit. They are what makes the POC buildable, runnable, and continuable.

- **Real Drizzle schema + committed migrations + a realistic seed script** using SOW-domain data.
- **Auth actually wired** — Better Auth with Microsoft Entra SSO when credentials exist, else a clearly-marked dev credentials login seeded with the SOW's real roles.
- **Zod at every API boundary** — `zValidator` + `c.req.valid()`; never read `c.req.json()` raw.
- **Route constants**, the `{ data } / { error }` response contract, and the typed Hono RPC client (`hc<AppType>`).
- **Strict TypeScript**, oxlint clean, `bun run build` green — for real, not by ignoring errors.
- **Plain-language `README.md`** — what the product does, the stack per layer, and how to run it from a fresh clone.
- **Buildable containers** — a Dockerfile per app so the POC ships as images (same shape `poc-to-product-architecture` expects).
- **Mockup-faithful screens** with real loading / empty / error states, so the demo feels like a product.

## Tier 3 — Allowed shortcuts (must be logged in `POC_NOTES.md`)

A POC is not the finished product. These shortcuts are fine **only** when each one is recorded in `docs/poc/POC_NOTES.md` with its production fix, so the later productionize step (and the `poc-to-product-architecture` gap audit) can find them.

- **External integrations mocked behind typed adapters** — the interface lives in `packages/shared`; the mock is `*-mock.ts`. Swapping in the real implementation post-approval is a drop-in, not a rewrite.
- **Thin demo-only infra** — one Forward Path dev environment, consumption SKUs, no CI/CD, no VNet/private endpoints. The customer-tenant Bicep contract is `poc-to-product-architecture`'s job.
- **A single demo dataset** — one realistic seed, not multi-tenant volume or edge-case fixtures.
- **Minimal error handling** — happy path + the states shown in the mockups; not exhaustive failure modes.
- **No test suite beyond smoke** — a build/typecheck gate is enough for a POC; full coverage is post-approval.

## The test

Before calling the POC done, ask of every file: *if the customer approves tomorrow, do we keep this line or delete it?* If the honest answer is "delete," it belongs in Tier 3 with a `POC_NOTES.md` entry — or it violates Tier 1 and must be fixed now.
