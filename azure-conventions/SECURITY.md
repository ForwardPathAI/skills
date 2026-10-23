# Azure Security Rules

Registry, identity, RBAC, secret, and pipeline rules for Forward Path Azure infra. [SKILL.md](SKILL.md) holds naming, layout, and defaults.

## Shared container registry

All custom builds pull and push through the org-wide registry:

| Setting | Value |
|---------|--------|
| Registry name | `forwardpathai` (all lowercase, no separators) |
| Scope | Shared across every application — do not create per-app ACRs |

Image references in infra and CI should use `forwardpathai.azurecr.io/<client>/<app>-<component>` (see [SKILL.md](SKILL.md#naming)).

- For Forward Path-managed infrastructure, resolve the existing registry through a Terraform data source or Bicep `existing` resource, including its actual subscription/resource group. Use an explicit provider alias or resource scope when it lives in another subscription. Customer-tenant templates use `forwardpathai.azurecr.io` and customer pull-secret references without querying Forward Path's registry resource or including Forward Path subscription IDs. Do not create, import into application state, replace, or delete the shared registry.
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

## Pipeline trust boundaries

Deploy production using the resolved image digest, or a release tag enforced as immutable. Publish `latest` for compatibility, but do not deploy production by that mutable tag. Record the release-to-digest mapping for rollback.

Pin third-party GitHub Actions to verified full commit SHAs. Dev/production publishing and deployment run only from trusted main merges or published releases. PR previews use the separate protected publishing path in [setup-preview-env](../setup-preview-env/SKILL.md): isolated builds without cloud access, then trusted default-branch orchestration with a protected preview environment and an environment-scoped OIDC identity. Pull-request check/build jobs must not receive publishing/deployment identities. Privileged jobs must not execute PR-controlled code, scripts, Terraform, workflow definitions, or artifact contents, including under `pull_request_target` or `workflow_run`.

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

## Terraform state and secrets

- Use an encrypted remote backend with locking, restricted Entra access, and audit logging. Authenticate CI to the backend with OIDC, not storage account keys or SAS tokens. Scope backend access to the required state container; separate storage/access boundaries when dev and production need identity isolation. Different backend keys alone do not enforce access isolation.
- **Never** put secrets in `*.tfvars`, committed vars, or Terraform state inputs for values that should stay in Key Vault.
- `sensitive = true` hides display; it does **not** remove values from state or plans. Do not read Key Vault secret values through Terraform data sources or generate/store ordinary password resources just to pass values to apps. Pass secret IDs and runtime references instead.
- If resource creation requires a secret value, verify that the selected provider/version supports an ephemeral/write-only path, or document a separate secure bootstrap. A Key Vault data source or a Bicep `@secure()` parameter does not prove the whole path avoids persistence. Treat any unavoidable state/plan exposure as an explicit design limitation with restricted access and rotation, never as a silent exception.
- Keep state, saved plans, crash logs, and `.terraform/` out of git and public artifacts. Do not print raw state or secret-bearing plan JSON in review output.

## Secrets (Key Vault)

| Do | Don't |
|----|-------|
| Store connection strings, API keys, passwords, signing keys in **Key Vault** | Commit secrets to git, `terraform.tfvars`, or CI vars for prod |
| Use Container Apps Key Vault-backed secrets and env `secretRef`; use `@Microsoft.KeyVault` for App Service | Retrieve secret values into Terraform or inline them into app configuration |

Engineers create and rotate Key Vault secrets through the portal or secure CLI input. Keep values out of command arguments, shell history, logs, and agent transcripts. Infrastructure code should **wire references only** (secret name, URI, RBAC for the app identity to `get`).

Document required secret **names** in README or Terraform variable descriptions — not the values.

Use Key Vault RBAC and grant runtime identities `Key Vault Secrets User` only on the required vault/secrets. Separate vaults and access by environment; CI should not read application secrets merely to deploy references. Enable soft delete and purge protection for new vaults. Keep rotation and recovery ownership documented.

## Network

Keep databases, caches, state storage, and Key Vault on private networking where supported by the chosen architecture. When public access is necessary, document the reason and restrict it to required clients; do not add unrestricted firewall rules or broad "allow Azure services" bypasses to resolve connectivity. Require TLS with certificate verification and disable anonymous access. Preserve stricter existing network controls.

## Verification

Before marking the checklist complete, inspect every publish/deploy workflow, reusable workflow, called script, and Terraform/Bicep module in scope. Trace authentication all the way to the push operation and runtime pull configuration. Search for credential login inputs, `ACR_USERNAME`/`ACR_PASSWORD`, `AZURE_CREDENTIALS`, client secrets, `listCredentials`, admin/anonymous settings, registry creation, broad role assignments, raw secret data sources, and open firewall rules. Distinguish prohibited publishing passwords from permitted customer pull-secret references and ephemeral federated tokens.

Run the repo's relevant formatting, validation, and IaC/security checks. Review the Terraform plan or Bicep what-if when authorized and available, without exposing secrets. If live deployment verification is in scope, confirm the intended principal can push its image, runtime pulls succeed, and customer token permissions exclude writes and other customers' repositories. Never test denied access by modifying another app's image. Report source checks separately from live checks, and list unresolved findings rather than checking them off.

Consult these primary references when implementing or reviewing the corresponding feature; verify behavior against the versions actually used:

- [GitHub OIDC for Azure](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure)
- [GitHub Actions untrusted-code and artifact boundaries](https://docs.github.com/en/actions/reference/security/secure-use#mitigating-the-risks-of-untrusted-code-checkout)
- [ACR authentication](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-authentication) and [RBAC/ABAC roles](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-rbac-built-in-roles-overview)
- [ACR token scope maps for customer pulls](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-token-based-repository-permissions)
- [Container Apps managed-identity pulls](https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull) and [Key Vault-backed secrets](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets)
- [Terraform sensitive data and state](https://developer.hashicorp.com/terraform/language/manage-sensitive-data)
