---
name: azure-conventions
description: Forward Path Azure conventions — resource naming, environments, regions, Container Apps defaults, the shared forwardpathai registry, OIDC/RBAC, Key Vault, and known gotchas. Use when writing or reviewing Terraform or Bicep, naming Azure resources, building GitHub Actions deploy workflows, or wiring ACR auth, app registrations, or Key Vault.
---

# Azure Conventions

Forward Path custom builds run on **Azure only**. Prefer **Terraform** with per-environment config (`dev`, `production`, sometimes `staging`). **Bicep** is acceptable when the repo already uses it.

Default compute: **Azure Container Apps** (lower cost, simpler ops). Use **App Service** only when a customer explicitly requires it.

To inspect or debug live resources, use [azure-ops](../azure-ops/SKILL.md).

Read **[SECURITY.md](SECURITY.md)** before writing or reviewing any registry auth, deploy workflow, role assignment, federated credential, Terraform backend, Key Vault wiring, or network rule. Its rules apply to every Forward Path and customer-tenant deployment.

## Scope and existing infrastructure

This skill guides authoring and review. It does not itself authorize live deployments, credential rotation, deletion, or changes to shared infrastructure. Carry out live actions only within the user's requested scope.

Before choosing names, identities, or permissions, inspect the repo's infra and workflows and, when accessible, the target tenant/subscription and GitHub environment protections. Use read-only discovery. Do not guess missing IDs or claim live verification when only source files were reviewed.

When existing infra conflicts with these conventions, identify the conflict and prepare a scoped correction. Renaming a live resource usually means recreating it, so existing names stay unless the user asks for a migration.

## Naming

Pattern: **`<type>-<app>-<env>[-<component>]`**, lowercase, hyphen-separated, with [CAF abbreviations](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-abbreviations) for `<type>`. Examples below use app `orbit` for client `acme`.

- **`<app>`** — short product slug, 10 characters or fewer (`orbit`, not `orbit-insights-platform`). Prefix the client only when the slug alone is ambiguous (`acme-orbit`). Storage accounts use `<stapp>`: the same slug with hyphens removed (`acme-orbit` → `acmeorbit`).
- **`<env>`** — `dev`, `staging`, or `prod` in Azure names. GitHub environments and Terraform folders keep `production`; only Azure names shorten it, because of the Key Vault length limit.
- **`<component>`** — `web`, `api`, `jobs`, `migrate`, or a sidecar name (`gateway`). Omit it when the stack has one app.
- **Region** — omit by default. Add a short code (`eus2`, `cac`) only when one app/env runs in more than one region.

| Resource | Pattern | Example |
|----------|---------|---------|
| Resource group | `rg-<app>-<env>` | `rg-orbit-dev` |
| Log Analytics workspace | `log-<app>-<env>` | `log-orbit-dev` |
| Application Insights | `appi-<app>-<env>` | `appi-orbit-dev` |
| Container Apps environment | `cae-<app>-<env>` | `cae-orbit-dev` |
| Container App | `ca-<app>-<env>[-<component>]` | `ca-orbit-dev-api` |
| Container Apps job | `job-<app>-<env>-<task>` | `job-orbit-dev-migrate` |
| User-assigned identity | `id-<app>-<env>[-<component>]` | `id-orbit-dev-gateway` |
| Key Vault | `kv-<app>-<env>` (3–24 chars, globally unique) | `kv-orbit-prod` |
| Postgres Flexible Server | `psql-<app>-<env>` (globally unique) | `psql-orbit-dev` |
| Redis | `redis-<app>-<env>` | `redis-orbit-dev` |
| Azure OpenAI / AI Services | `oai-<app>-<env>` | `oai-orbit-dev` |
| Storage account | `st<stapp><env><suffix>` (3–24 chars, lowercase alphanumeric, globally unique; shorten the suffix to fit) | `storbitdev4f2a1c` |
| App Service plan / web app | `asp-<app>-<env>` / `app-<app>-<env>-<component>` | `app-orbit-dev-api` |
| Terraform state | `rg-<app>-tfstate`, `st<stapp>tfstate<suffix>` (24-char limit applies) | `rg-orbit-tfstate` |

Every resource group carries these tags: `application = <app>`, `environment = <env>`, `managed_by = terraform` (or `bicep`).

**Image repositories** in `forwardpathai`: `<client>/<app>-<component>` for release images, e.g. `forwardpathai.azurecr.io/acme/orbit-api`. When the registry runs in ABAC mode, new setups publish dev images to a separate `<client>/dev/<app>-<component>` repository so dev publishers cannot write release repositories (see [SECURITY.md](SECURITY.md#app-registration-and-rbac)). Under legacy RBAC mode the split gives no isolation, so dev and release share one repository.

**Hostnames**: `[<env>.]<component>.<app>.<client>.forwardpath.ai`; production drops the env prefix. Examples: `dev.app.orbit.acme.forwardpath.ai`, `app.orbit.acme.forwardpath.ai`.

## CI/CD and image tags

Each application lives in its own GitHub repo.

| Trigger | Target | Image tags | Effect |
|---------|--------|------------|--------|
| Merge to `main` | **Dev** | `dev` | Publish image, deploy/restart dev Container Apps (or equivalent) |
| **GitHub Release** (semver tag, e.g. `v1.2.3`) | **Production** | release version **and** `latest` | Promote prod to the released image |

Default prod promotion tags are **`latest`** plus the release semver. Use other tags (`prod`, an environment name) only when the repo already standardizes on them. Production deploys by digest; see [SECURITY.md](SECURITY.md#pipeline-trust-boundaries).

## Terraform environments

Structure Terraform with explicit environments:

```
environments/
  dev/
  production/
  staging/       # optional
```

- Separate state per environment (separate backend key or workspace), on a backend that meets [SECURITY.md](SECURITY.md#terraform-state-and-secrets).
- Non-secret config may differ per env (SKU, replica count, hostname).

## Regions

Preferred regions: **East US 2** and **Canada Central**. Customer data-residency requirements take precedence; check them before choosing or changing a region.

Pick one region per stack and keep dependent resources (Postgres, Container Apps environment, Key Vault) in the **same** region.

## Container Apps defaults

When greenfielding infra:

1. **Log Analytics workspace** + **Container Apps Environment** in the chosen region.
2. **Container App** with image from `forwardpathai.azurecr.io/<client>/<app>-<component>`.
3. **User-assigned managed identity**, created before the app, configured as the app's registry identity with pull-only permissions. Customer-tenant apps use the customer pull-credential path in [SECURITY.md](SECURITY.md#image-pull-runtime-identity-or-customer-pull-credentials).
4. Ingress, min/max replicas, and CPU/memory sized per environment. External ingress only for intended public endpoints; internal services and workers stay private or have ingress disabled. HTTPS only, `allowInsecure: false`.
5. Env vars: plain config inline; sensitive values from Key Vault references.

Scale-to-zero and consumption-friendly SKUs are preferred for dev and smaller prod workloads unless the customer contract requires always-on App Service.

## Gotchas

- **East US Postgres capacity.** Postgres Flexible Server creation in East US hits capacity and quota errors. Build new stacks in East US 2 or Canada Central rather than splitting Postgres into a different region from the rest of the stack.
- **Key Vault names outlive deletion.** Soft delete and purge protection hold a deleted vault's name for the retention period, so `terraform destroy` then `apply` with the same name fails. Recover the vault (`az keyvault recover`) rather than renaming it.
- **Global name collisions.** Key Vault, storage account, and Postgres server names are DNS names, unique across all of Azure. Storage accounts take a short random suffix; Key Vault and Postgres rely on the `<app>-<env>` pair being distinct.
- **Platform-owned resource groups.** `ME_<cae>_<rg>_<region>` groups belong to Container Apps workload-profile environments; `NetworkWatcherRG`, `DefaultResourceGroup-*`, and `*_managed` groups belong to other Azure services. Leave them out of Terraform and never delete them; they go away with their parent.
- **First deploy of a private image.** A system-assigned identity does not exist until the app does, so the first image pull fails. Create the user-assigned identity and its pull role before the Container App.
- **Custom domains.** The Container Apps managed certificate needs the CNAME and `asuid` TXT records in DNS before binding. Order DNS before the domain binding in Terraform, or bind in a second apply.

## Authoring checklist

Before finishing infra or a deploy workflow, confirm:

```
- [ ] Names follow the Naming table; tags application / environment / managed_by set on every resource group
- [ ] Images use existing shared ACR `forwardpathai` at `<client>/<app>-<component>` (dev at `<client>/dev/<app>-<component>` under ABAC); no new registry or shared-registry ownership in app state
- [ ] Every push/promotion/retry uses OIDC through registry login; no stored publishing credentials or password fallback
- [ ] Forward Path runtime pulls use a pre-created user-assigned identity; customer tokens are per-customer/app and repository-scoped read-only
- [ ] No admin credentials, anonymous pull, or registry/firewall bypasses
- [ ] Main → dev deploy tags image `dev`; GitHub Release → prod tags semver + `latest`, deploys by digest
- [ ] Separate CI principals per repo/env; exact OIDC subject/audience matches the job and protected environment
- [ ] RBAC matches the existing registry mode; repository conditions applied where supported; legacy exposure documented
- [ ] Bootstrap privileges separated from deploy CI; dev cannot deploy prod or read prod secrets
- [ ] Actions pinned to verified SHAs; PR builds have no cloud access; previews publish/deploy only through trusted protected orchestration
- [ ] Region meets customer residency requirements; East US 2 or Canada Central when unconstrained; whole stack in one region
- [ ] Secrets referenced from Key Vault; no values in git, tfvars, outputs, handoff archives, or routine Terraform state inputs
- [ ] Encrypted remote state with OIDC and env-scoped access; unavoidable secret persistence explicitly documented
- [ ] HTTPS enforced; public ingress intentional; data/secret services private or explicitly restricted
- [ ] Terraform split across dev / production (and staging if used)
- [ ] Compute is Container Apps unless customer requires App Service
- [ ] SECURITY.md verification pass done; source checks reported separately from live checks
```

## Terraform vs Bicep

| Use Terraform when | Use Bicep when |
|--------------------|----------------|
| Repo already has `environments/` Terraform layout | Repo is ARM/Bicep-native or customer template is Bicep |
| You need modules shared with other Forward Path apps | Single-file Azure deployment aligned with MS samples |

The same conventions and [SECURITY.md](SECURITY.md) rules apply regardless of tool.

## Pull requests

PR bodies for infra changes name the environments and RBAC assignments they change.
