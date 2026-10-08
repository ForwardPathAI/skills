---
name: setup-preview-env
description: Set up ephemeral per-pull-request Azure preview environments for a containerized application.
disable-model-invocation: true
---

# Setup Preview Environment

Build a **preview lane**: every eligible, approved pull request gets an isolated, testable Azure deployment, and closing it removes everything it created.

This skill authors application support, Terraform, GitHub Actions, scripts, tests, and runbooks. It does not mutate Azure, GitHub settings, DNS, or certificates without the user's explicit approval.

Read [REFERENCE.md](REFERENCE.md) before implementation. It records the reusable architecture and the traps found in the ButtconRAG reference.

Apply [azure-infra-setup](../azure-infra-setup/SKILL.md) for the existing shared `forwardpathai` registry, federated publishing, registry-mode-aware RBAC, and secret handling. The reference's direct PR OIDC publishing path is historical and unsupported. A same-repo or non-fork gate alone does not make PR code safe to execute with Azure credentials.

## 1. Establish the preview contract

1. Read the target repo's `AGENTS.md`/`CLAUDE.md`, deploy workflows, Terraform roots/modules, Dockerfiles, environment schema, authentication setup, and test commands.
2. Inspect the ButtconRAG source files listed in `REFERENCE.md`; use them as evidence, not copy-and-replace templates.
3. Resolve and record:
   - GitHub owner/repo, default branch, runner labels, action-pinning policy, and Terraform version.
   - Build context, Dockerfile, ACR image name, target port, and health endpoint for every deployable app.
   - Azure subscription, region, ACR, Terraform backend/bootstrap path, and existing dev/shared resource outputs.
   - Every mutable dependency: database, cache, queue, blob/object storage, vector collection, search index, external webhook, and auth redirect.
   - Which dependencies are per-PR, safely namespaced, read-only shared, or intentionally shared with an accepted risk.
   - Runtime configuration names as read by the application code. Never infer them from another repo.
   - Whether authentication requires a dedicated preview app registration and exact redirect URI.
   - Whether the default Container Apps domain is sufficient. Treat custom DNS as an optional branch.
4. Ask only for unresolved choices that materially change cost, isolation, security, or externally applied infrastructure.

_Done when:_ every deployed app and every mutable dependency is accounted for, all target-specific values are known, and no Buttcon identifier is being used as an unstated default.

## 2. Design the isolation boundary

Use two Terraform roots:

- `preview-shared`: one-time, low-churn resources such as the resource group, Log Analytics workspace, Container Apps environment, pre-created identities, and optional preview auth registration.
- `preview`: resources for one pull request, keyed by `pr_number`.

The per-PR root must derive names, tags, URLs, and data namespaces from `pr_number`. Give each PR a distinct backend key such as `preview/pr-<N>.tfstate`; do not use one shared state or rely on Terraform workspaces.

Prefer, in order:

1. A separate per-PR resource when inexpensive.
2. A collision-proof per-PR namespace when sharing is necessary.
3. Read-only sharing.
4. Explicitly accepted sharing with the blast radius documented.

Start with the Container Apps default domain unless custom DNS is required. A custom suffix adds wildcard DNS, certificate issuance, renewal, and URL/auth alignment obligations.

_Done when:_ the design states where every resource lives, how every mutable data path is isolated, how state is isolated, and what teardown must delete.

## 3. Make the application previewable

1. Ensure each app has a production container build and an unauthenticated health endpoint that checks startup readiness without exposing secrets.
2. Make browser configuration environment-specific. For Vite or another compile-time frontend, either:
   - bake the exact per-PR values into that PR's image; or
   - preserve explicit placeholders at build time and replace only an allowlist at container startup.
3. Trace backend settings from source to deployed environment variables. Verify CORS, cookie security/SameSite/domain, auth audience/tenant, database components, and proxy/forwarded-header behavior against the preview URLs.
4. Add namespace variables wherever a shared cache, vector store, queue, index, or object store could collide across PRs.

_Done when:_ the same images and runtime settings can boot under a unique PR URL without pointing writes at another PR or production.

## 4. Author Terraform

Create or adapt:

```text
infrastructure/terraform/environments/
  preview-shared/
    backend.tf
    main.tf
    outputs.tf
    variables.tf
    README.md
  preview/
    backend.tf
    main.tf
    outputs.tf
    variables.tf
    README.md
```

Requirements:

- Reuse the repo's modules and provider constraints where sound; do not clone modules unnecessarily.
- Reuse the existing remote-state backend. If none exists, add a separately confirmed bootstrap path before preview roots depend on it.
- Export stable shared outputs consumed by the per-PR root and CI.
- Set preview Container Apps to scale to zero where startup latency permits and cap replicas conservatively.
- Use the Azure control plane to create per-PR managed resources when CI cannot safely reach their data plane.
- Prefer pre-created managed identity plus Key Vault references and read-only registry permissions matched to the shared registry's RBAC/ABAC mode. Any platform-limitation fallback must follow azure-infra-setup's secret/state rules. A scoped ACR token may be considered for runtime pulls only; publishing always uses federation.
- Keep secrets out of git, workflow literals, Terraform variables files, logs, and outputs.
- Generate and commit provider lock files. Never copy `.terraform/`, `*.tfstate`, plan files, certificates, or generated credentials.

_Done when:_ shared and per-PR plans have stable ownership, per-PR state cannot collide, secret handling is explicit, and all created resources are representable by teardown.

## 5. Wire identity and authentication

Use a dedicated preview CI principal and a protected GitHub `preview` environment. Restrict that environment to the trusted default branch, require deployment review, and prevent protection bypass. Verify the repo's GitHub plan supports these controls; if it does not, report the missing gate rather than creating an unprotected environment.

For the trusted publish/deploy jobs that declare `environment: preview`, document the actual emitted federated subject. A legacy example is:

```text
issuer:   https://token.actions.githubusercontent.com
subject:  repo:<owner>/<repo>:environment:preview
audience: api://AzureADTokenExchange
```

Do not provision a raw `pull_request` federated credential for publishing or deployment. Request `id-token: write` only in protected jobs; PR checks/builds receive no OIDC permissions or Azure credentials. Scope the CI principal only to the preview resource group, preview image repositories where ABAC supports isolation, preview state storage, and specific shared resources it must manage. Keep dev/production deployment and secret access out of this principal.

If the app uses Entra/MSAL:

1. Prefer one preview app registration with the required API scope.
2. Do not let concurrent per-PR Terraform states each own the registration's full redirect URI list.
3. Add/remove one exact per-PR URI with an idempotent, conflict-retrying helper using optimistic concurrency.
4. Enforce Entra's redirect-URI limit and remove the URI during every cleanup path.

_Done when:_ only trusted protected jobs can authenticate to Azure, PR builds cannot obtain that identity, and browser/backend auth values agree on tenant, client, audience, scope, origin, and redirect URI.

## 6. Build the deploy workflow

Separate the PR build workflow from `.github/workflows/deploy-preview.yml`:

1. Trigger isolated builds on `pull_request` `opened`, `synchronize`, `reopened`, and `ready_for_review`. Skip drafts and forks for the preview lane. Check out the exact PR head SHA and build on disposable runners without OIDC, Azure/runtime secrets, write-capable GitHub tokens, or access to dev/production networks. Keep runners and caches separate from privileged jobs.
2. Export images as artifacts tied to that build run and full commit SHA. Do not push images or run Terraform from the PR build job.
3. Trigger the trusted default-branch deploy workflow with `workflow_run` after that build completes successfully. A validated maintainer `workflow_dispatch` recovery entry point is also acceptable. Check the expected workflow ID, source repository, event, run ID, PR number, and full head SHA through GitHub API data. Reject forks, closed/draft PRs, failed builds, missing metadata, or a head SHA that no longer matches the PR.
4. Require approval through the protected `preview` environment before OIDC publishing/deployment. Show the exact PR, source run, and full SHA for review, then recheck eligibility after approval. A new SHA requires a new build and approval.
5. On a fresh privileged runner, use only pinned actions and scripts from the trusted default-branch revision. Retrieve image artifacts by the verified run/artifact IDs, check integrity and expected image identity, and treat their contents as untrusted data. Load/push images without running them; never source artifact files or execute PR scripts, Terraform, install hooks, or Docker builds in this job. Do not restore PR-written caches. Metadata must be validated and passed as quoted data, never interpolated into shell source.
6. Authenticate through OIDC and `az acr login --name forwardpathai`, then publish immutable `pr-<N>-<short-sha>` tags to the preview image repositories and record the registry digests. A mutable `pr-<N>` tag is optional convenience, never the Terraform deployment source.
7. Initialize shared state, then `key=preview/pr-<N>.tfstate`. Apply Terraform and helpers from the trusted default-branch revision using the resolved image digests and validated target inputs. Infrastructure changes proposed by a PR must be reviewed and merged before the privileged preview lane uses them.
8. Register the exact auth redirect after the final web URL is known. Capture web/API outputs, poll health with bounded retries, upsert one marker-based sticky PR comment, and emit a job summary without secrets.

Do not allow a new commit to interrupt `terraform apply`. Use non-cancelling per-PR infrastructure concurrency, or split cancellable builds from a serialized non-cancelling apply stage.

_Done when:_ an eligible approved PR builds one exact commit without cloud access, trusted protected orchestration publishes its images and applies one isolated state, both app surfaces are healthy, and the URLs appear once. Never claim a workflow_run trigger or an environment name alone establishes this boundary.

## 7. Build the teardown workflow

Add `.github/workflows/teardown-preview.yml`:

1. Run teardown from a trusted default-branch workflow on same-repo PR `closed`, for example a metadata-only `pull_request_target` handler; also expose a validated manual/reusable recovery entry point. Use the protected preview environment and environment-scoped OIDC. Validate the source repo/PR number and its ownership of preview state; never check out or execute PR code. Keep destroy modules/helpers on the trusted default-branch revision and retain compatibility with existing preview state.
2. Use the same per-PR concurrency key as deploy, with cancellation disabled.
3. Check whether the state blob exists; absence is a successful no-op.
4. Initialize the exact per-PR state and destroy with the same required variables.
5. Remove the exact auth redirect and any non-Terraform namespace or external registration.
6. Delete state and lock blobs only after successful destroy. A failed destroy must retain state for recovery.
7. Update the sticky comment and job summary.

If orphan recovery is required, implement a scheduled reconciler that compares preview state keys/resources with open PRs and invokes teardown. Never claim a sweeper exists merely because `workflow_call` exists.

_Done when:_ close, manual recovery, repeated cleanup, missing state, and failed destroy all have safe, idempotent outcomes with no state loss.

## 8. Document and bootstrap

Write runbooks for:

- required GitHub configuration, protected preview environment, approval process, and environment-scoped OIDC fields;
- exact RBAC scopes;
- Terraform state bootstrap and recovery;
- shared-root initialization/apply and outputs;
- creation and rotation of any runtime pull-only ACR token or Key Vault secret; no publishing passwords;
- firewall or network rules required for preview runtime traffic;
- reproducible non-secret shared-root inputs, such as a committed `.tfvars.example`;
- data-sharing risks;
- manual teardown and orphan recovery;
- custom DNS records, certificate storage, owner, and automated renewal if that branch is used.

Before any external write, show the user the subscription, resource groups, app registration, roles, DNS names, and estimated persistent cost, then ask for confirmation. Apply `preview-shared` once only after approval.

_Done when:_ another engineer can finish every external prerequisite from the runbook without discovering an unnamed value or permission.

## 9. Prove the lane

Run all applicable checks:

1. `terraform fmt -check -recursive`.
2. `terraform init -backend=false` and `terraform validate` for both roots, or the repo's safe equivalent.
3. `actionlint` and YAML parsing for workflows.
4. `shellcheck` plus focused tests for helper scripts.
5. Container builds and runtime-config checks.
6. Static consistency: image names, ports, state keys, outputs, URL construction, environment variables, secret names, redirect add/remove, and deploy/destroy inputs. Verify the build has no cloud access, artifact/run/SHA provenance is checked, privileged code comes from the trusted default branch, and changed PR heads cannot reuse approval.
7. Diff scan proving no secret, `.terraform/`, state, plan, certificate, or unrelated generated file was added.

With approval, open a test PR and observe deploy, authentication, smoke checks, synchronization, and close teardown. Do not call the lane complete from static validation alone; report live validation as pending when it was not run.

_Done when:_ every applicable static check passes and live lifecycle evidence either passes or is explicitly handed off as the only remaining validation.

## Handoff

Report:

- files added or changed;
- shared versus per-PR resources;
- required GitHub/Azure/DNS actions and which were not executed;
- data and secret-isolation decisions;
- validation commands and results;
- preview URLs and cleanup evidence when live-tested;
- any accepted risk or remaining blocker.
