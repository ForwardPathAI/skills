# Architecture Bar

Every production architecture produced by `poc-to-product-architecture` must pass this checklist before the canvas is written. Iterate on the design until every item passes, or convert a failure into an explicit Risks entry in the deliverable.

## Security

- [ ] Secrets are stored only as Key Vault references — secret **names** documented, values never appear in the deliverable, Bicep skeleton, or canvas.
- [ ] Each Container App has a managed identity with `AcrPull` on the shared registry `forwardpathai`.
- [ ] RBAC is narrow — no subscription-wide `Owner` or `Contributor` on CI principals; scoped roles only.
- [ ] Zod validation at every API boundary (`zValidator` + `c.req.valid()`); never read `c.req.json()` raw.
- [ ] Auth via Better Auth + Microsoft SSO with org RBAC when the SOW defines users/roles.
- [ ] Internal-only services (workers, job processors) have no public ingress.
- [ ] Third-party API keys are customer-supplied secret names in Key Vault, not Forward Path-provided values.

## Reliability

- [ ] Health probes configured on every Container App (liveness and readiness).
- [ ] Production min replicas ≥ 1 for user-facing services (scale-to-zero allowed for dev and background workers).
- [ ] Log Analytics workspace wired to the Container Apps environment.
- [ ] PostgreSQL Flexible Server with point-in-time recovery (PITR) and backups enabled.
- [ ] Rollback story stated: image tag `dev` for main-branch deploys; semver + `latest` for GitHub Release production deploys.
- [ ] Region is **East US 2** or **Canada Central** — never East US for new Postgres Flexible Server workloads.

## Budget

- [ ] Consumption plans and burstable SKUs by default unless the SOW or scale requirements justify always-on SKUs.
- [ ] Per-resource monthly cost estimate table is present in the deliverable.
- [ ] Any resource whose cost is driven by SOW scale assumptions is flagged in the cost table or caption.
- [ ] If the SOW gave budget signals, the total estimate is checked against them and any overrun is noted in Risks.

## Maintainability

- [ ] Product-foundation monorepo seams: Zod schemas in `packages/shared`, DB access in `packages/database`, typed routes exported into `AppType` for the Hono RPC client.
- [ ] Modules are workspace packages (`packages/*`) or apps (`apps/*`) — never inlined into `apps/web`.
- [ ] Plain-language README obligation noted (what the product does, stack in one sentence per layer, how to run it).
- [ ] Each deviation from the product-foundation stack is stated with a reason in the deliverable.
