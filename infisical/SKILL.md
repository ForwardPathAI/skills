---
name: infisical
description: Forward Path's rules for app and CI/CD secrets. Infisical is the single source of truth, local `.env` files are banned, and Infisical Secret Syncs push secrets into GitHub and Azure Key Vault. Use when adding, reading, or rotating an env var or secret, setting up local dev or a new repo, finding a `.env` file, wiring GitHub Actions secrets, or populating Key Vault.
---

# Infisical

Forward Path keeps every app and CI/CD secret in **Infisical**. Infisical is the **single source of truth**: a secret's value is set there and nowhere else, and every other copy is either injected at process start or pushed by a sync.

- **Local dev:** wrap commands in the Infisical CLI, so secrets reach the process as env vars. No `.env`, `.env.local`, or `.env.development` file holds a value on disk.
- **CI/CD:** a **GitHub Secret Sync** pushes each environment's `/ci-cd` folder into the repo's GitHub secrets. Workflows read `${{ secrets.NAME }}` as normal.
- **Deployed runtime:** an **Azure Key Vault Secret Sync** pushes each environment's runtime secrets into that environment's vault. Apps read them through Key Vault references, per [azure-conventions](../azure-conventions/SECURITY.md).

Nobody edits a synced secret in GitHub or Key Vault. The next sync overwrites it.

## Handling values

Agents and engineers handle secret **names**, never values. Engineers enter values in the Infisical UI, never through an agent. When you work with secrets:

- Read names with `infisical sm secrets` only in its default masked table view. Never pass flags that print values, and never paste a value into chat, a commit, a PR, a log, or a command argument.
- Inject with `infisical sm run`. Never write secrets to a file with `infisical sm export` or a redirect.
- If a value shows up in your context anyway, stop, tell the user which secret leaked and where, and recommend rotation.

## CLI

Install with `brew install infisical/get-cli/infisical` (or `npm install -g @infisical/cli`), then `infisical login` once per machine. `infisical init` at the repo root links the Infisical project; commit the file it writes (`.infisical.yaml`, or `.infisical.json` on older CLIs). It holds the project ID only.

Current CLIs group secret commands under `sm` (`infisical sm run`). CLIs at 0.43.145 or earlier lack `sm` and use `infisical run`. Check the flags your installed version accepts with `infisical sm run --help` before you write a script.

## Project layout

One Infisical project per repo. Besides the deploy targets in [azure-conventions](../azure-conventions/SKILL.md) (`dev`, `prod`, and `staging` when the repo has it), add a `local` environment: local values (a Docker Postgres URL, localhost callbacks) differ from deployed dev, and each deployed environment's root syncs to its vault.

| Environment and path | Holds | Reaches |
|----------------------|-------|---------|
| `local` `/` | Secrets the app needs on a developer machine | `infisical sm run --env=local` |
| `dev`, `staging`, `prod` `/` | Runtime secrets for that deployed environment | That environment's Key Vault, via sync |
| `dev`, `staging`, `prod` `/ci-cd` | Secrets GitHub Actions needs for that environment | The matching GitHub environment, via sync |

When a local value matches deployed dev (a third-party API key), use an Infisical secret reference (`${dev.OPENAI_API_KEY}`) instead of copying the value. Put a secret in `/ci-cd` only when a workflow reads it. Azure OIDC client, tenant, and subscription IDs are config, not secrets; they may still live in `/ci-cd` so one place lists everything a workflow needs.

For a local value that differs per engineer (a personal API key, a local port), use an Infisical **personal** secret in `local`. It overrides the shared value for that engineer only, and replaces what `.env.local` used to do.

## Set up a repo

Use this for a new repo, or to move an existing repo off `.env` files.

1. Create the Infisical project and its environments, or confirm they exist. Ask the user to do this in the Infisical UI if you lack access.
2. Run `infisical init` at the repo root and commit the config file.
3. Inventory every secret the code reads: the startup env validation, `process.env` / `Bun.env` / `import.meta.env` reads, Docker Compose interpolation, workflow `secrets.*` references, Key Vault references in infra, and any existing `.env*` files (names only). Give the user the list of names to create, split by environment and path per the layout above. The user enters the values.
4. Wrap every script that needs secrets:

   ```json
   {
     "scripts": {
       "dev": "infisical sm run --env=local -- next dev",
       "db:migrate": "infisical sm run --env=local -- drizzle-kit migrate"
     }
   }
   ```

   Wrap the outermost command (`infisical sm run --env=local -- docker compose up`, `infisical sm run --env=local -- turbo dev`) so child processes inherit the env. Remove `dotenv` imports, `--env-file` flags, and Compose `env_file:` entries that point at `.env` files. Compose passes only the names a service lists into its container, so list each secret the service needs under its `environment:` (`- DATABASE_URL`, with no value, forwards the host's value). Confirm the containers start without printing their env.
5. Keep `.env.example` as the list of names with a one-line comment each and **no values**. Make `.gitignore` ignore every other env file:

   ```gitignore
   .env*
   !.env.example
   ```

6. Replace any README step that says "copy `.env.example` to `.env`" with: install the CLI, `infisical login`, then `bun run dev`.
7. Set up the GitHub and Key Vault syncs (next sections).
8. Delete existing `.env*` files that hold values only after the user confirms every value is in Infisical. Ask before deleting; a local file may be the only copy. If a `.env` with real values was ever committed, tell the user the values are in git history and must be rotated.

_Done when_ the app starts through the wrapped scripts with no `.env*` file but `.env.example` on disk, `git ls-files` shows no env file but `.env.example`, nothing in the code loads a dotenv file, and every name the code reads exists in Infisical.

## GitHub sync (CI/CD)

Create one GitHub Secret Sync per deployed environment, in the Infisical project's Secret Syncs, using the org's GitHub connection:

| Setting | Value |
|---------|-------|
| Source | Environment (`dev`, `prod`, ...) and path `/ci-cd` |
| Scope | **Repository Environment**, targeting the GitHub environment the deploy jobs declare (`dev`, `production`) |
| Initial Sync Behavior | Overwrite Destination Secrets |
| Auto-Sync | On |
| Key Schema | `{{secretKey}}` |

Environment scope keeps prod secrets behind GitHub environment protection rules, which plain repository secrets skip. Use **Repository** scope only for a secret every job needs and no job can get through an environment. Use **Organization** scope with selected repositories only for a secret shared across repos, synced from one Infisical project that owns it.

Overwrite deletes any GitHub secret in that scope that Infisical lacks, and GitHub cannot export secret values back to Infisical. Before enabling a sync on a repo that already has GitHub secrets, list them (`gh secret list --env <name>`, `gh secret list`), and have the user add each still-needed value to Infisical from its original source. Then enable the sync.

_Done when_ each deployed environment has an enabled GitHub sync whose last run succeeded, `gh secret list --env <name>` shows exactly the names in that environment's `/ci-cd` folder, and every `secrets.*` reference in `.github/workflows/` resolves to a synced name.

## Key Vault sync (deployed runtime)

Create one Azure Key Vault Secret Sync per deployed environment, targeting that environment's own vault:

| Setting | Value |
|---------|-------|
| Source | Environment (`dev`, `prod`, ...) and path `/` |
| Destination | Vault Base URL of that environment's vault (`https://<vault>.vault.azure.net`) |
| Initial Sync Behavior | **Import Secrets (Prioritize Azure Key Vault)** for a vault that already holds secrets; Overwrite Destination Secrets for an empty one |
| Auto-Sync | On |
| Key Schema | `{{secretKey}}` |

Rules that come with it:

- **Names change.** Key Vault forbids underscores, so the sync writes `DATABASE_URL` as `DATABASE-URL`. Infra references the hyphenated vault name; the app's env var keeps the underscore. Two Infisical names that map to one vault name (`FOO_BAR` and `FOO-BAR`) stop the sync, so keep names unique after the swap.
- **Infisical owns the vault's values.** Terraform/Bicep creates the vault, RBAC, and references, but never `azurerm_key_vault_secret` resources or secret values for synced names. Engineers rotate in Infisical, not the portal. A secret that must stay outside Infisical (such as a customer ACR pull password set by another process) belongs in a separate vault the sync never targets. Disable Secret Deletion does not keep it out: the initial import copies every vault secret into Infisical.
- **Least privilege.** The Infisical Azure connection needs `secrets/list`, `get`, `set`, and `recover`: assign `Key Vault Secrets Officer` on each synced vault only, never the resource group or subscription. Use a separate connection or assignment per environment so the dev sync cannot write the prod vault.
- **Reference without a version.** Use `https://<vault>.vault.azure.net/secrets/<NAME>` with no version suffix. Container Apps then picks up a rotated value within 30 minutes and restarts active revisions that read it as an env var. A pinned version never sees the rotation.
- **Customer tenants are out of scope.** Customer-deployed apps use the customer's own vault and values, per [customer-deployment-package](../customer-deployment-package/SKILL.md). Never sync Forward Path's Infisical into a customer vault.

_Done when_ each deployed environment has an enabled Key Vault sync whose last run succeeded, every Key Vault reference in infra names a hyphenated secret that exists in that environment's root, and no Terraform/Bicep resource sets a synced secret's value.

## Add or rotate a secret

1. Add a name the app reads to its startup env validation, so a missing value fails fast. Leave workflow-only names (in `/ci-cd` alone) out of it. Add every new name to `.env.example` with a one-line comment.
2. Tell the user where it belongs: `local` `/` for local dev, each deployed environment's `/` for runtime, `/ci-cd` for workflows. The user enters or rotates the value in Infisical. Auto-sync pushes it.
3. For a new runtime secret, add the unversioned Key Vault reference (hyphenated name) and env var wiring in infra. A rotation reaches running Container Apps within 30 minutes; restart the revision to apply it sooner.

## References

- [Infisical CLI](https://infisical.com/docs/cli/usage)
- [GitHub Secret Sync](https://infisical.com/docs/integrations/secret-syncs/github)
- [Azure Key Vault Secret Sync](https://infisical.com/docs/integrations/secret-syncs/azure-key-vault)
