# ButtconRAG Preview Reference

Use ButtconRAG as a case study, not a template. Read the current files before relying on this summary because its preview lane evolved through live pipeline failures.

## Source manifest

From the workspace root, inspect:

- `ButtconRAG/.github/workflows/deploy-preview.yml`
- `ButtconRAG/.github/workflows/teardown-preview.yml`
- `ButtconRAG/.github/workflows/terraform-bootstrap.yml`
- `ButtconRAG/.github/scripts/retry-terraform-oidc.sh`
- `ButtconRAG/infrastructure/terraform/environments/preview-shared/`
- `ButtconRAG/infrastructure/terraform/environments/preview/`
- `ButtconRAG/infrastructure/terraform/environments/dev/`
- `ButtconRAG/infrastructure/terraform/modules/key-vault/`
- `ButtconRAG/infrastructure/terraform/modules/container-app/`
- `ButtconRAG/scripts/preview/update-redirect-uris.sh`
- `ButtconRAG/scripts/preview/test-update-redirect-uris-logic.sh`
- `ButtconRAG/scripts/preview/test-update-redirect-uris-mock.sh`
- `ButtconRAG/src/ForwardPath.Web/Dockerfile`
- `ButtconRAG/src/ForwardPath.Web/docker-entrypoint.d/40-inject-vite-env.sh`
- `ButtconRAG/src/ForwardPath.Web/src/services/msalConfig.js`
- `ButtconRAG/src/ForwardPath.Server/app/core/config.py`
- `ButtconRAG/src/ForwardPath.Server/app/main.py`

Use `git log -- <paths>` to recover the sequence and rationale when current comments conflict.

## Architecture that transferred well

ButtconRAG separates long-lived shared capacity from PR-owned resources:

- `preview-shared` owns one resource group, Log Analytics workspace, Container Apps environment, a managed identity, and the preview Entra application. The current per-PR apps use an ACR token instead of that identity for image pulls.
- `preview` owns two Container Apps, a PR database, a stable PR JWT secret, namespaced cache/vector settings, and URLs for one PR.
- Remote state keys are `preview/shared.tfstate` and `preview/pr-<N>.tfstate`.
- Resource names, tags, database name, cache prefix, vector prefix, image tag, and URLs include the PR number.

The deploy workflow:

- skips drafts and forks before privileged work;
- checks out the exact PR head;
- builds backend and frontend images tagged `pr-<N>-<sha>`;
- initializes one PR-specific state;
- applies Terraform;
- adds the exact Entra redirect URI;
- polls API `/health` and the web root;
- upserts a marker-based sticky PR comment.

The teardown workflow:

- runs on PR close or as a reusable workflow;
- checks for state before destroy;
- removes the Entra redirect URI;
- deletes the state blob only after successful destroy;
- updates the sticky comment.

These are the reusable load-bearing ideas: a shared/per-PR split, immutable deployment tags, explicit state isolation, privileged-event gates, lifecycle symmetry, bounded smoke checks, and idempotent reporting.

## Lessons from the live rollout

### Trace runtime configuration from code

ButtconRAG initially supplied `DATABASE_URL`, but its settings model actually assembled the engine URL from `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`. A plausible environment variable is not proof that the application reads it.

The SPA uses Vite, which normally bakes `VITE_*` values into static assets. Its Dockerfile deliberately preserves literal placeholders when preview build arguments are omitted, and an entrypoint replaces an allowlist at container startup. Without that mechanism, per-PR API and login URLs cannot be injected after image build.

### Prefer control-plane provisioning

CI could not reliably reach the dev PostgreSQL data plane. The final design creates the per-PR database with `azurerm_postgresql_flexible_server_database`; the application creates its own extension/schema at startup. Use the control plane when the provider supports the operation.

### Identity propagation can defeat same-apply references

ButtconRAG observed Container Apps failing to resolve ACR and Key Vault references when a user-assigned identity and its role assignments were created in the same apply. Sleep and RBAC propagation resources did not make the path reliable.

Its current fallback is:

- a pre-created pull-only ACR scoped token whose password is held in Key Vault; and
- secret values read by Terraform and injected as Container App secrets.

Do not generalize that fallback. It increases out-of-band setup and places sensitive values in Terraform state. First try a pre-created identity with aged role assignments. Use the fallback only with a documented rotation and state-protection story.

### Shared dev credentials weaken isolation

The preview database has a unique name, but the app receives the dev PostgreSQL server-admin credential. That credential can reach the real dev database, so database-name isolation does not constrain a compromised preview. Prefer a scoped per-PR role when the data plane is reachable, a dedicated preview server, or an explicitly accepted dev-tier risk.

### Auth redirects are shared mutable state

One Entra app registration serves all previews. Per-PR Terraform cannot safely own its complete SPA redirect list because concurrent applies would overwrite each other. ButtconRAG mutates one URI through Microsoft Graph with:

- exact add/remove operations;
- idempotence;
- etag-based optimistic concurrency;
- retry on conflict, throttle, and transient failure;
- a hard check against the 256-URI limit.

The app registration makes the CI service principal an owner and grants `Application.ReadWrite.OwnedBy`, avoiding tenant-wide `Application.ReadWrite.All`.

### PR OIDC has a different subject

The working federated subject is `repo:<owner>/<repo>:pull_request`. Credentials scoped to `repo:<owner>/<repo>:environment:dev` or `production` do not match PR-triggered jobs.

Fork PRs must not receive this identity. A fork gate after checkout or after a build has started is too late if that job already has cloud credentials.

### URL construction has one source

The browser origin, API URL, CORS origin, cookie policy, MSAL redirect, Terraform outputs, smoke tests, and sticky comment must use the same effective domain. ButtconRAG supports the Container Apps default domain and an optional custom environment suffix.

Its custom suffix requires:

- wildcard DNS and an `asuid` verification record;
- a wildcard certificate uploaded to the Container Apps environment;
- manual or automated certificate renewal;
- the same suffix passed through Terraform and CI.

Do not add custom DNS during the first tracer deployment unless it is a requirement.

## Gaps not to copy

- The runbooks still describe per-app managed identities and Key Vault references in places, while the current Terraform injects values and uses an ACR token. Validate code and update docs together.
- The pull-only ACR token and `preview-acr-pull-password` Key Vault secret are required by current Terraform, but their creation and rotation are not documented.
- The preview Container Apps environment requires runtime access through a manually maintained dev PostgreSQL firewall rule. Codify it or document how CAE outbound-IP changes are detected and applied.
- `preview-shared` has required non-secret inputs but no committed example values file. Preserve reproducibility with a safe `.tfvars.example` or exact runbook commands.
- Teardown comments mention a nightly sweeper, but no scheduled sweeper workflow is present. A reusable workflow is not a reconciler.
- Deploy uses workflow-level `cancel-in-progress: true`; a synchronize event can interrupt Terraform apply and leave a lock or partial operation. Serialize non-cancelling infrastructure work per PR.
- Teardown has `workflow_call` but no direct manual trigger. Provide a validated recovery path that an operator can invoke.
- The custom certificate has a manual renewal path. Production use needs a named owner and alert or automation before expiry.
- Names, state accounts, image paths, tenant IDs, branding, ports, secret names, cache names, database parsing, and health paths are Buttcon-specific.
- Migration cleanup scripts such as `forget-legacy-data-plane-resources.sh` repair old state. Do not copy them into a fresh implementation.

## Target-specific inventory

Before implementation, derive these values from the target:

- organization, repository, default branch, eligible PR policy;
- runner and pinned action SHAs;
- Terraform version, providers, backend resource group/account/container, shared and PR keys;
- Azure subscription, tenant, region, preview resource group, shared ACR;
- app components, build contexts, Dockerfiles, image repositories, ports, CPU/memory, scale bounds, health paths;
- frontend build-time versus runtime configuration;
- backend environment schema and secret names;
- database provisioning, migration ownership, and credentials;
- cache, queue, vector, search, object storage, and webhook namespaces;
- authentication tenant/client/audience/scope/redirect/cookie/CORS behavior;
- default domain or custom suffix, DNS owner, certificate owner, and renewal mechanism;
- GitHub secret names, OIDC service principal object ID, federated credential, and exact RBAC scopes;
- smoke-test readiness budget and cleanup recovery policy.

Any unresolved item is a design decision, not a placeholder to fill with a Buttcon value.

## Consistency invariants

Validate all of these before handoff:

- Deploy and teardown compute the same PR number, state key, resource names, and redirect URI.
- Terraform deploys the immutable image tag built from the checked-out SHA.
- Each frontend URL appears identically in runtime config, CORS, cookies, auth redirect, output, smoke test, and PR comment.
- Every mutable dependency is isolated or explicitly accepted as shared.
- Every created resource, namespace, redirect, secret, and state lock has a cleanup owner.
- State survives a failed destroy.
- Fork code never runs in a job that can mint the Azure OIDC token.
- Draft events cannot cancel an active infrastructure operation.
- Logs, outputs, comments, summaries, and plans do not print secret values.
- Documentation describes the implementation that actually exists.
