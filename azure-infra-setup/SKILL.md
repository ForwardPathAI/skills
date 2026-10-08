---
name: azure-infra-setup
description: Author or review Forward Path Azure infrastructure and deploy workflows in Terraform or Bicep, using the shared forwardpathai registry, federated image pushes, scoped RBAC, Key Vault, and Container Apps. Use for Azure infrastructure, ACR authentication, GitHub Actions deployments, app registrations, or customer image-pull wiring.
---

# Azure Infrastructure Setup

Forward Path custom builds run on **Azure only**. Prefer **Terraform** with per-environment config (`dev`, `production`, sometimes `staging`). **Bicep** is acceptable when the repo already uses it.

Default compute: **Azure Container Apps** (lower cost, simpler ops). Use **App Service** only when a customer explicitly requires it.

## Scope and existing infrastructure

This skill guides authoring and review. It does not itself authorize live deployments, credential rotation, deletion, or changes to shared infrastructure. Carry out live actions only within the user's requested scope.

Before choosing identities or permissions, inspect the repo's infra and workflows and, when accessible, the target tenant/subscription, existing registry resource ID, registry permission mode, and GitHub environment protections. Use read-only discovery. Do not guess missing IDs or claim live verification when only source files were reviewed.

When existing infra conflicts with the rules below, identify the conflict and prepare a scoped correction. Do not copy insecure settings as precedent or silently change org-wide registry settings to make one application work.

## Shared container registry

All custom builds pull and push through the org-wide registry:

| Setting | Value |
|---------|--------|
| Registry name | `forwardpathai` (all lowercase, no separators) |
| Scope | Shared across every application — do not create per-app ACRs |

Image references in infra and CI should use `forwardpathai.azurecr.io/<app-image>`.

- Resolve the existing registry through a Terraform data source or Bicep `existing` resource, including its actual subscription/resource group. Do not create, import into application state, replace, or delete the shared registry. Use an explicit provider alias or resource scope when it lives in another subscription.
- Do not create a per-app or customer ACR, or fall back to another registry when authentication fails. Diagnose identity, RBAC, tenant, and networking instead.
- ACR admin access and anonymous pull must remain disabled. Do not enable them or retrieve admin credentials with `az acr credential show` or ARM `listCredentials`. If either is already enabled, report it and prepare an org-scoped remediation; do not disable shared access as an incidental app change.

## Registry authentication

### Image push: federated identity only

Every automated image publish, including dev, release, promotion, and retry paths, **must** authenticate through workload identity federation. GitHub Actions uses OIDC with an Entra application/service principal or user-assigned managed identity.

The authentication chain must reach the registry, not just the Azure deployment:

1. The publishing job requests a GitHub OIDC token with job-level `id-token: write` and only the other permissions it needs, normally `contents: read`.
2. `azure/login` exchanges that token using client ID, tenant ID, and subscription ID. These IDs are configuration, not passwords.
3. `az acr login --name forwardpathai` authenticates Docker with the resulting short-lived Entra token before the build/push or promotion step. Select the registry's actual subscription when it differs from the deployment subscription.

Do not use stored ACR usernames/passwords, ACR scope-map tokens, registry admin credentials, service-principal client secrets/certificates, or secret-based `AZURE_CREDENTIALS` for publishing. This prohibition includes credentials stored in GitHub Secrets or Key Vault. Never reuse customer pull credentials in CI. A Docker login using a short-lived token obtained from the federated session is acceptable; do not log, output, upload, or persist that token beyond the job.

If OIDC login or push fails, diagnose the exact subject/audience, role assignment, registry mode, and network access. Do not add a password fallback, broaden RBAC, or open the shared registry firewall to bypass the failure.

### Image pull: runtime identity or customer pull credentials

- **Forward Path-hosted apps:** use a dedicated managed identity with read-only image permissions. Prefer a pre-created user-assigned identity so the first private-image deployment can authenticate. Configure the app's registry entry to use that identity; merely assigning a role is insufficient. Verify ACR's ARM-audience authentication setting supports managed-identity pulls. Treat any required shared-registry setting change as separate scoped work.
- **Customer-tenant deployments:** a username/password is allowed for **pull only**. Use a unique ACR token per customer/application with a custom scope map listing only that customer's image repositories. Grant `content/read`; add `metadata/read` only when tag/manifest discovery needs it. Grant no write/delete actions, wildcard repositories, or registry-wide system scope maps. Do not distribute ACR admin credentials or a CI principal's credentials.
- Customer pull-token passwords belong in 1Password for handoff and the customer's Key Vault for runtime use. Wire the registry password through a Container App secret backed by a Key Vault reference. Document expiry, rotation, revocation, and an owner; never paste values into git, chat, deployment instructions, or handoff archives. Use [customer-deployment-package](../customer-deployment-package/SKILL.md) for the complete handoff.
- A managed identity in the customer's tenant does not automatically have access to Forward Path's registry. Do not assume a same-tenant `AcrPull` assignment solves cross-tenant access.

## CI/CD and image tags

Each application lives in its own GitHub repo.

| Trigger | Target | Image tags | Effect |
|---------|--------|------------|--------|
| Merge to `main` | **Dev** | `dev` | Publish image, deploy/restart dev Container Apps (or equivalent) |
| **GitHub Release** (semver tag, e.g. `v1.2.3`) | **Production** | release version **and** `latest` | Promote prod to the released image |

Do not invent alternate prod tags (`prod`, environment name in tag, etc.) unless the repo already standardizes on them — default prod promotion tag is **`latest`** plus the semver from the release.

Deploy production using the resolved image digest, or a release tag enforced as immutable. Publish `latest` for compatibility, but do not deploy production by that mutable tag. Record the release-to-digest mapping for rollback.

Pin third-party GitHub Actions to verified full commit SHAs. Publish/deploy only from trusted main merges or published releases. Pull-request checks must not receive publishing/deployment identities; never run untrusted PR code under `pull_request_target` with Azure access.

## App registration and RBAC

Azure now expects **narrow RBAC** assignments. Do **not** grant subscription-wide `Owner` or `Contributor` to the CI principal.

Select data-plane roles based on the **existing registry's permission mode**, not a copied example:

| Registry permission mode | Federated publisher | Runtime pull identity |
|--------------------------|---------------------|-----------------------|
| RBAC Registry + ABAC Repository Permissions | `Container Registry Repository Writer`, conditioned on this app's repositories | `Container Registry Repository Reader`, conditioned on this app's repositories |
| RBAC Registry Permissions | `AcrPush` scoped to the existing registry | `AcrPull` scoped to the existing registry |

`AcrPush`/`AcrPull` are registry-wide and are not honored in ABAC-enabled mode. Legacy RBAC cannot isolate repositories with those roles. Document that exposure and recommend a separately planned ABAC migration; do not switch a shared registry's mode inside an app deployment. Do not grant registry administration or deletion permissions just to push images. Add only narrowly scoped read permissions if registry discovery requires them.

Use separate CI principals per repo **and environment**, plus separate runtime identities. The dev principal must have no production deployment or secret access. Where ABAC is available, new setups should separate dev and release image repositories and condition each publisher's role on its repositories. Separate repositories alone do not isolate writers under legacy `AcrPush`. Repository permissions also do not isolate tags within a repository; flag these limitations for existing setups, and pin production deployments to digests.

The deployment principal gets only the resource-group/resource-scoped operations it needs. It must not receive `Owner`, `User Access Administrator`, RBAC administration, or directory-wide application permissions as a deployment convenience. Keep identity creation and role-assignment bootstrap separate from routine CI. If bootstrap needs elevated permissions, use an authorized administrator or a narrowly constrained bootstrap identity; do not leave those privileges on the publisher.

Configure federated credentials with issuer `https://token.actions.githubusercontent.com`, audience `api://AzureADTokenExchange`, and the exact subject emitted by the target job. Each publishing/deployment job must declare the matching GitHub `environment`. Legacy subject examples are:

```
repo:<org>/<repo>:environment:dev
repo:<org>/<repo>:environment:production
```

Verify the actual subject format before provisioning; GitHub also supports subjects containing immutable repository/owner IDs and customized subjects. Do not assume the legacy examples fit every repo, use wildcard trust, or authorize the `pull_request` subject for publishing.

Configure GitHub environment deployment restrictions for the intended branches/tags and production protection rules appropriate to the release process. An environment name alone does not restrict which workflow can request its identity. Do not weaken existing protections to make a workflow pass.

## Terraform environments

Structure Terraform with explicit environments:

```
environments/
  dev/
  production/    # or prod/
  staging/       # optional
```

- Separate state per environment (separate backend key or workspace).
- Use an encrypted remote backend with locking, restricted Entra access, and audit logging. Authenticate CI to the backend with OIDC, not storage account keys or SAS tokens. Scope backend access to the required state container; separate storage/access boundaries when dev and production need identity isolation. Different backend keys alone do not enforce access isolation.
- Non-secret config may differ per env (SKU, replica count, hostname).
- **Never** put secrets in `*.tfvars`, committed vars, or Terraform state inputs for values that should stay in Key Vault.
- `sensitive = true` hides display; it does **not** remove values from state or plans. Do not read Key Vault secret values through Terraform data sources or generate/store ordinary password resources just to pass values to apps. Pass secret IDs and runtime references instead.
- If resource creation requires a secret value, verify that the selected provider/version supports an ephemeral/write-only path, or document a separate secure bootstrap. A Key Vault data source or a Bicep `@secure()` parameter does not prove the whole path avoids persistence. Treat any unavoidable state/plan exposure as an explicit design limitation with restricted access and rotation, never as a silent exception.
- Keep state, saved plans, crash logs, and `.terraform/` out of git and public artifacts. Do not print raw state or secret-bearing plan JSON in review output.

## Regions

Avoid **East US** for new Postgres Flexible Server workloads when capacity or quota errors appear — Forward Path has hit regional limits there.

Preferred regions:

- **East US 2**
- **Canada Central**

Pick one region per stack and keep dependent resources (Postgres, Container Apps environment, Key Vault) in the **same** region.

Customer data-residency requirements take precedence over region preferences. Do not relocate workloads or choose a fallback region without checking those requirements.

## Secrets (Key Vault)

| Do | Don't |
|----|-------|
| Store connection strings, API keys, passwords, signing keys in **Key Vault** | Commit secrets to git, `terraform.tfvars`, or CI vars for prod |
| Use Container Apps Key Vault-backed secrets and env `secretRef`; use `@Microsoft.KeyVault` for App Service | Retrieve secret values into Terraform or inline them into app configuration |

Engineers create and rotate Key Vault secrets through the portal or secure CLI input. Keep values out of command arguments, shell history, logs, and agent transcripts. Infrastructure code should **wire references only** (secret name, URI, RBAC for the app identity to `get`).

Document required secret **names** in README or Terraform variable descriptions — not the values.

Use Key Vault RBAC and grant runtime identities `Key Vault Secrets User` only on the required vault/secrets. Separate vaults and access by environment; CI should not read application secrets merely to deploy references. Enable soft delete and purge protection for new vaults. Keep rotation and recovery ownership documented.

## Container Apps defaults

When greenfielding infra:

1. **Log Analytics workspace** + **Container Apps Environment** in the chosen region.
2. **Container App** with image from `forwardpathai.azurecr.io/...`.
3. **Managed identity** on the app, registry authentication, and pull-only permissions appropriate to the registry mode. Customer-tenant apps follow the customer pull-credential path above.
4. Ingress, min/max replicas, and CPU/memory appropriate to dev vs prod modules. External ingress only for intended public endpoints; internal services/workers stay private or have ingress disabled. Require HTTPS and set `allowInsecure: false` for HTTP ingress.
5. Env vars: plain config inline; sensitive values from Key Vault references.

Scale-to-zero and consumption-friendly SKUs are preferred for dev and smaller prod workloads unless the customer contract requires always-on App Service.

Keep databases, caches, state storage, and Key Vault on private networking where supported by the chosen architecture. When public access is necessary, document the reason and restrict it to required clients; do not add unrestricted firewall rules or broad "allow Azure services" bypasses to resolve connectivity. Require TLS with certificate verification and disable anonymous access. Preserve stricter existing network controls.

## Authoring checklist

Before finishing infra or a deploy workflow, confirm:

```
- [ ] Images use existing shared ACR `forwardpathai`; no new registry or shared-registry ownership in app state
- [ ] Every push/promotion/retry uses OIDC through registry login; no stored publishing credentials or password fallback
- [ ] Forward Path runtime pulls use managed identity; customer tokens are per-customer/app and repository-scoped read-only
- [ ] No admin credentials, anonymous pull, or registry/firewall bypasses
- [ ] Main → dev deploy tags image `dev`
- [ ] GitHub Release → prod tags semver + `latest`
- [ ] Separate CI principals per repo/env; exact OIDC subject/audience matches the job and protected environment
- [ ] RBAC matches the existing registry mode; repository conditions applied where supported; legacy exposure documented
- [ ] Bootstrap privileges separated from deploy CI; dev cannot deploy prod or read prod secrets
- [ ] Production image digest or immutable release tag; dev write access cannot overwrite release images where isolation is supported
- [ ] Actions pinned to verified SHAs; untrusted PRs cannot publish/deploy
- [ ] Region meets customer residency requirements; prefer East US 2 or Canada Central when unconstrained
- [ ] Secrets referenced from Key Vault; no values in git, tfvars, outputs, handoff archives, or routine Terraform state inputs
- [ ] Encrypted remote state with OIDC and env-scoped access; unavoidable secret persistence explicitly documented
- [ ] HTTPS enforced; public ingress intentional; data/secret services private or explicitly restricted
- [ ] Terraform split across dev / production (and staging if used)
- [ ] Compute is Container Apps unless customer requires App Service
```

## Terraform vs Bicep

| Use Terraform when | Use Bicep when |
|--------------------|----------------|
| Repo already has `environments/` Terraform layout | Repo is ARM/Bicep-native or customer template is Bicep |
| You need modules shared with other Forward Path apps | Single-file Azure deployment aligned with MS samples |

Apply the same rules (ACR, tags, OIDC, Key Vault, regions, RBAC) regardless of tool.

## Verification

Before marking the checklist complete, inspect every publish/deploy workflow, reusable workflow, called script, and Terraform/Bicep module in scope. Trace authentication all the way to the push operation and runtime pull configuration. Search for credential login inputs, `ACR_USERNAME`/`ACR_PASSWORD`, `AZURE_CREDENTIALS`, client secrets, `listCredentials`, admin/anonymous settings, registry creation, broad role assignments, raw secret data sources, and open firewall rules. Distinguish prohibited publishing passwords from permitted customer pull-secret references and ephemeral federated tokens.

Run the repo's relevant formatting, validation, and IaC/security checks. Review the Terraform plan or Bicep what-if when authorized and available, without exposing secrets. If live deployment verification is in scope, confirm the intended principal can push its image, runtime pulls succeed, and customer token permissions exclude writes and other customers' repositories. Never test denied access by modifying another app's image. Report source checks separately from live checks, and list unresolved findings rather than checking them off.

Consult these primary references when implementing or reviewing the corresponding feature; verify behavior against the versions actually used:

- [GitHub OIDC for Azure](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure)
- [ACR authentication](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-authentication) and [RBAC/ABAC roles](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-rbac-built-in-roles-overview)
- [ACR token scope maps for customer pulls](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-token-based-repository-permissions)
- [Container Apps managed-identity pulls](https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull) and [Key Vault-backed secrets](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets)
- [Terraform sensitive data and state](https://developer.hashicorp.com/terraform/language/manage-sensitive-data)

## Pull requests

When infra changes ship with application work, follow team PR conventions (Linear issue code in branch/PR title when applicable). Infra-only repos still benefit from describing which environments and RBAC assignments changed in the PR body.
