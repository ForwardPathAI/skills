# Bicep Constraint

The deployability contract that shapes every architecture produced by `poc-to-product-architecture`. If a SOW requirement cannot survive this contract, surface it as an explicit risk in the deliverable — do not silently break the contract.

## Contract

- Every compute piece ships as a **container image** pushed to `forwardpathai.azurecr.io/<app-image>`.
- The full topology is expressible as **one parameterized Bicep template** (modules allowed, single entry point) that an **external webhook** runs to install into an external customer Azure tenant.
- **No manual portal steps** in the install path — everything the customer needs must be deployable from the template plus documented parameters.
- Customer-supplied parameters: subscription/tenant context, resource group, region, environment name, ACR pull credentials (delivered out-of-band), and every third-party secret **name** the customer must populate in their Key Vault.

## Sanitization

Inherited from [customer-deployment-package](../customer-deployment-package/SKILL.md). The Bicep skeleton and any external variant must **not** contain:

| Remove / externalize | Keep / parameterize |
|----------------------|---------------------|
| Forward Path subscription IDs, internal RBAC principals | Customer-supplied subscription/tenant, resource group, region |
| Hardcoded secret values, connection strings | Secret **names** + Key Vault references the customer populates |
| Forward Path-only CI/OIDC federation subjects | Image references + instructions to pull from `forwardpathai.azurecr.io` |
| Internal hostnames, internal-only resources | Customer-facing inputs as documented `@description` parameters |

## Skeleton section list

The canvas's Bicep skeleton must present these sections **in order**, with real resource types and parameter names — not a complete working template:

1. **Parameters** — `customerSubscriptionId`, `resourceGroupName`, `location` (East US 2 or Canada Central), `environmentName`, `acrPullUsername`, `acrPullPassword` (secure), plus per-service image tags and any customer Key Vault secret name parameters.
2. **Log Analytics workspace** — `Microsoft.OperationalInsights/workspaces`.
3. **Container Apps environment** — `Microsoft.App/managedEnvironments`, wired to Log Analytics.
4. **Key Vault** — `Microsoft.KeyVault/vaults`, with access policies or RBAC for app managed identities.
5. **ACR pull credential wiring** — registry secret on the Container Apps environment for `forwardpathai.azurecr.io`.
6. **Container App per service** — `Microsoft.App/containerApps`, one block per service (web, API, jobs, etc.):
   - Image ref: `forwardpathai.azurecr.io/<app-image>:<tag>`
   - Ingress (external for user-facing, internal for workers)
   - Health probes (liveness + readiness)
   - Scale rules (min/max replicas)
   - Env vars split: plain config inline, sensitive values as Key Vault secret refs
7. **PostgreSQL Flexible Server** — `Microsoft.DBforPostgreSQL/flexibleServers` + database, with firewall/VNet stance documented.
8. **Module-driven extras** (when the SOW requires them):
   - Redis (`Microsoft.Cache/redis`) for BullMQ jobs
   - Storage account (`Microsoft.Storage/storageAccounts`) for file uploads or exports
9. **Outputs** — app FQDNs, resource IDs the webhook reports back to the installer.

## Skeleton vs. full template

The skeleton in the canvas is an **outline with real resource types and parameter names** — not a complete working template. Full Bicep authoring is deferred to:

- [azure-infra-setup/SKILL.md](../azure-infra-setup/SKILL.md) — internal infra and CI/CD wiring.
- [customer-deployment-package/SKILL.md](../customer-deployment-package/SKILL.md) — customer-facing external variant and deployment handoff.

Link both as next steps in the Step 5 report.

## Image and tag conventions

| Trigger | Target | Image tags |
|---------|--------|------------|
| Merge to `main` | Dev | `dev` |
| GitHub Release (semver, e.g. `v1.2.3`) | Production | release version **and** `latest` |

All images pull from `forwardpathai.azurecr.io` — do not create per-app ACRs.
