---
name: azure-infra-setup
description: Author Forward Path Azure infrastructure in Terraform or Bicep for custom application builds — shared ACR, GitHub OIDC/RBAC, dev/prod environments, regions, Key Vault secrets, and Container Apps. Use when writing or reviewing Azure infra, Terraform, Bicep, Container Apps, ACR, GitHub Actions deploy workflows, app registrations, or Key Vault wiring.
---

# Azure Infrastructure Setup

Forward Path custom builds run on **Azure only**. Prefer **Terraform** with per-environment config (`dev`, `production`, sometimes `staging`). **Bicep** is acceptable when the repo already uses it.

Default compute: **Azure Container Apps** (lower cost, simpler ops). Use **App Service** only when a customer explicitly requires it.

## Shared container registry

All custom builds pull and push through the org-wide registry:

| Setting | Value |
|---------|--------|
| Registry name | `forwardpathai` (all lowercase, no separators) |
| Scope | Shared across every application — do not create per-app ACRs |

Image references in infra and CI should use `forwardpathai.azurecr.io/<app-image>`.

## CI/CD and image tags

Each application lives in its own GitHub repo.

| Trigger | Target | Image tags | Effect |
|---------|--------|------------|--------|
| Merge to `main` | **Dev** | `dev` | Publish image, deploy/restart dev Container Apps (or equivalent) |
| **GitHub Release** (semver tag, e.g. `v1.2.3`) | **Production** | release version **and** `latest` | Promote prod to the released image |

Do not invent alternate prod tags (`prod`, environment name in tag, etc.) unless the repo already standardizes on them — default prod promotion tag is **`latest`** plus the semver from the release.

GitHub Actions should use **OIDC federation** (app registration + federated credential per repo/environment), not long-lived client secrets in the workflow file.

## App registration and RBAC (not broad roles)

Azure now expects **narrow RBAC** assignments. Do **not** grant subscription-wide `Owner` or `Contributor` to the CI principal.

Typical minimum roles for a deploy pipeline:

| Principal | Resource | Role |
|-----------|----------|------|
| GitHub Actions OIDC SP | `forwardpathai` ACR | `AcrPush` (build/push on release and main) |
| Container App / managed identity | `forwardpathai` ACR | `AcrPull` |
| GitHub Actions OIDC SP | Target resource group (or scoped resources) | Least privilege needed to deploy Container Apps, update config, restart revisions — often custom role or resource-specific roles, not Contributor on the subscription |

Federated credential subject pattern (adjust per repo):

```
repo:<org>/<repo>:environment:dev
repo:<org>/<repo>:environment:production
```

When adding a new app, create **dedicated** app registration / federated credentials and **scoped** role assignments — copying a working repo’s workflow without matching RBAC on the new resource group is a common failure mode.

## Terraform environments

Structure Terraform with explicit environments:

```
environments/
  dev/
  production/    # or prod/
  staging/       # optional
```

- Separate state per environment (separate backend key or workspace).
- Non-secret config may differ per env (SKU, replica count, hostname).
- **Never** put secrets in `*.tfvars`, committed vars, or Terraform state inputs for values that should stay in Key Vault.

## Regions

Avoid **East US** for new Postgres Flexible Server workloads when capacity or quota errors appear — Forward Path has hit regional limits there.

Preferred regions:

- **East US 2**
- **Canada Central**

Pick one region per stack and keep dependent resources (Postgres, Container Apps environment, Key Vault) in the **same** region.

## Secrets (Key Vault)

| Do | Don't |
|----|-------|
| Store connection strings, API keys, passwords, signing keys in **Key Vault** | Commit secrets to git, `terraform.tfvars`, or CI vars for prod |
| Reference secrets via Key Vault secret IDs / Container App secret refs / `@Microsoft.KeyVault` | Generate secrets in Terraform and check them into state without a rotation story |

Engineers **manually** create and rotate Key Vault secrets in the portal or CLI. Infrastructure code should **wire references only** (secret name, URI, RBAC for the app identity to `get`).

Document required secret **names** in README or Terraform variable descriptions — not the values.

## Container Apps defaults

When greenfielding infra:

1. **Log Analytics workspace** + **Container Apps Environment** in the chosen region.
2. **Container App** with image from `forwardpathai.azurecr.io/...`.
3. **Managed identity** on the app with `AcrPull` on `forwardpathai`.
4. Ingress, min/max replicas, and CPU/memory appropriate to dev vs prod modules.
5. Env vars: plain config inline; sensitive values from Key Vault references.

Scale-to-zero and consumption-friendly SKUs are preferred for dev and smaller prod workloads unless the customer contract requires always-on App Service.

## Authoring checklist

Before finishing infra or a deploy workflow, confirm:

```
- [ ] Images use shared ACR `forwardpathai` (no new registry)
- [ ] Main → dev deploy tags image `dev`
- [ ] GitHub Release → prod tags semver + `latest`
- [ ] GitHub OIDC app registration + federated credentials for this repo/env
- [ ] RBAC is scoped (AcrPush/AcrPull + deploy roles), not subscription Contributor
- [ ] Region is East US 2 or Canada Central (not East US unless already locked)
- [ ] Secrets referenced from Key Vault; none in tfvars or git
- [ ] Terraform split across dev / production (and staging if used)
- [ ] Compute is Container Apps unless customer requires App Service
```

## Terraform vs Bicep

| Use Terraform when | Use Bicep when |
|--------------------|----------------|
| Repo already has `environments/` Terraform layout | Repo is ARM/Bicep-native or customer template is Bicep |
| You need modules shared with other Forward Path apps | Single-file Azure deployment aligned with MS samples |

Apply the same rules (ACR, tags, OIDC, Key Vault, regions, RBAC) regardless of tool.

## Pull requests

When infra changes ship with application work, follow team PR conventions (Linear issue code in branch/PR title when applicable). Infra-only repos still benefit from describing which environments and RBAC assignments changed in the PR body.
