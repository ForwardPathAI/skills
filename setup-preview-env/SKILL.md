---
name: setup-preview-env
description: Set up ephemeral per-pull-request Azure preview environments for a containerized application.
disable-model-invocation: true
---

# Setup Preview Environment

Build a **preview lane**: every eligible pull request gets an isolated, testable Azure deployment, and closing it removes everything it created.

This skill authors application support, Terraform, GitHub Actions, scripts, tests, and runbooks. It does not mutate Azure, GitHub settings, DNS, or certificates without the user's explicit approval.

Read [REFERENCE.md](REFERENCE.md) before implementation. It records the reusable architecture and the traps found in the ButtconRAG reference.

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
- Prefer pre-created managed identity plus Key Vault references and `AcrPull`. Use direct secret values or an ACR scoped token only after reproducing a platform limitation; document the exposure, rotation, and Terraform-state impact.
- Keep secrets out of git, workflow literals, Terraform variables files, logs, and outputs.
- Generate and commit provider lock files. Never copy `.terraform/`, `*.tfstate`, plan files, certificates, or generated credentials.

_Done when:_ shared and per-PR plans have stable ownership, per-PR state cannot collide, secret handling is explicit, and all created resources are representable by teardown.

## 5. Wire identity and authentication

For GitHub Actions OIDC, document a federated credential with:

```text
issuer:   https://token.actions.githubusercontent.com
subject:  repo:<owner>/<repo>:pull_request
audience: api://AzureADTokenExchange
```

Environment-scoped `dev` or `production` credentials do not authenticate a `pull_request` run. Scope the CI principal only to the preview resource group, ACR push, state blobs, and specific shared resources it must manage.

If the app uses Entra/MSAL:

1. Prefer one preview app registration with the required API scope.
2. Do not let concurrent per-PR Terraform states each own the registration's full redirect URI list.
3. Add/remove one exact per-PR URI with an idempotent, conflict-retrying helper using optimistic concurrency.
4. Enforce Entra's redirect-URI limit and remove the URI during every cleanup path.

_Done when:_ the workflow identity can authenticate from PR events with least privilege, and browser/backend auth values agree on tenant, client, audience, scope, origin, and redirect URI.

## 6. Build the deploy workflow

Add `.github/workflows/deploy-preview.yml` following the repo's workflow conventions:

1. Trigger on `pull_request` `opened`, `synchronize`, `reopened`, and `ready_for_review`.
2. Gate before privileged jobs. Skip drafts and forks; never build or execute fork-controlled code with cloud credentials.
3. Check out the PR head SHA explicitly.
4. Build and push immutable `pr-<N>-<short-sha>` images. A mutable `pr-<N>` tag is optional convenience, never the Terraform deployment source.
5. Initialize shared state, then per-PR state with `key=preview/pr-<N>.tfstate`.
6. Apply using the immutable tag and explicit target variables.
7. Register the exact auth redirect only after the final web URL is known.
8. Capture web/API outputs, poll health with bounded retries, and upsert one marker-based sticky PR comment.
9. Emit a job summary without secrets.

Do not allow a new commit to interrupt `terraform apply`. Use non-cancelling per-PR infrastructure concurrency, or split cancellable builds from a serialized non-cancelling apply stage.

_Done when:_ a same-repo, non-draft PR deterministically builds one commit, applies one isolated state, proves both app surfaces healthy, and reports the URLs once.

## 7. Build the teardown workflow

Add `.github/workflows/teardown-preview.yml`:

1. Trigger on same-repo PR `closed`; also expose a validated manual/reusable recovery entry point.
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

- required GitHub secrets and OIDC fields;
- exact RBAC scopes;
- Terraform state bootstrap and recovery;
- shared-root initialization/apply and outputs;
- creation and rotation of any out-of-band ACR token or Key Vault secret;
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
6. Static consistency: image names, ports, state keys, outputs, URL construction, environment variables, secret names, redirect add/remove, and deploy/destroy inputs.
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
