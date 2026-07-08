# POC Notes — <Product Name>

Every shortcut this POC takes, so productionizing is a checklist, not an investigation. Grouped by the gap-audit tags the `poc-to-product-architecture` skill consumes. Fill in each table; delete rows that don't apply. Only Tier 3 shortcuts from the `poc-from-sow` POC bar belong here.

## demo-grade — exists but must be replaced for production

Things that work in the POC via a mock or simplification and need the real implementation post-approval.

| Shortcut | Where (file) | Why | Production fix |
|----------|--------------|-----|----------------|
| Example: `<Integration>` behind a typed mock | `packages/shared/<name>.ts` (interface) + `apps/api/.../<name>-mock.ts` | No live credentials / access during POC | Implement the real adapter against the interface; swap in via env |
| Example: dev credentials login | `packages/auth/...` | Entra app registration not provisioned yet | Wire Microsoft Entra SSO + org RBAC; remove dev login |
| | | | |

## missing — no POC trace yet

SOW requirements not addressed in the POC (e.g. `designed-only` screens, deferred features).

| Requirement | Where it should live | Why deferred | Production fix |
|-------------|----------------------|--------------|----------------|
| Example: `<screen>` is static | `apps/web/app/(dashboard)/<route>` | Out of the hero flows | Wire to API + real data per `WEB_IMPLEMENT.md` |
| | | | |

## reusable — production-ready as-is

POC code that is already real product code and should be kept.

| Asset | Where (file) | Notes |
|-------|--------------|-------|
| Example: domain schema + migrations | `packages/database/src/schema` | Real Drizzle schema; keep |
| Example: typed Hono routes | `apps/api/src/routes` | Zod-validated; keep |
| | | |
