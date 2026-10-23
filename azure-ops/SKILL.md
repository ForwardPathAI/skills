---
name: azure-ops
description: Inspect and operate live Forward Path Azure apps with the az CLI — find an app's resources, stream or query logs, check revisions, replicas, images, identities, and secrets, and diagnose failed deploys, crash loops, 5xx errors, or broken database and Key Vault connections. Use when debugging or checking a deployed Azure app, tailing logs, or making an approved operational change such as a restart or rollback.
---

# Azure Ops

Inspect and operate deployed Forward Path apps through the **`az` CLI**. Resource names follow the [azure-conventions](../azure-conventions/SKILL.md#naming) naming table; use it to turn "orbit dev API" into `ca-orbit-dev-api` in `rg-orbit-dev`. Older stacks predate the convention, so locate before guessing.

For symptom-driven debugging (failed revision, crash loop, 502, database or Key Vault errors), follow **[PLAYBOOKS.md](PLAYBOOKS.md)**.

## Rules

- **Read-only by default.** `list`, `show`, `logs`, and `query` commands run freely. Anything that changes state is a **write**; see [Writes](#writes).
- **Name the target.** Before any write, echo subscription, resource group, and resource, and get the user's confirmation. Forward Path spans several subscriptions; the wrong one is the expensive mistake.
- **Secret values stay hidden.** List secret **names** only. Never run `az keyvault secret show`, `az containerapp secret show`/`list --show-values`, `az acr credential show`, `az postgres ... show-connection-string` with a password, or anything else that prints a credential. A diagnosis needs to know a secret exists and resolves, never its value.
- **Report evidence.** Quote the log line, revision state, or error that supports each conclusion, and say which checks you ran versus inferred.

## Setup

1. `az account show -o table`. If it fails, stop and ask the user to run `az login`.
2. `az extension add --name containerapp --upgrade` and `az extension add --name resource-graph` if missing.

## Locate an app

The user names an app and an environment; find its subscription and resource group across every subscription with Resource Graph:

```bash
az graph query -q "resources | where name contains '<app>' | project name, type, resourceGroup, subscriptionId" --first 100 -o table
```

Then pin the subscription for the rest of the session with `az account set --subscription <id>`, or pass `--subscription` to each command.

_Done when:_ you have the subscription, resource group, and the exact name of every resource in scope.

## Inspect

### Container Apps

| Need | Command |
|------|---------|
| Current state, image, ingress | `az containerapp show -n <ca> -g <rg> --query "{state:properties.runningStatus, image:properties.template.containers[].image, fqdn:properties.configuration.ingress.fqdn, port:properties.configuration.ingress.targetPort, latest:properties.latestRevisionName, ready:properties.latestReadyRevisionName}"` |
| Revisions and health | `az containerapp revision list -n <ca> -g <rg> --query "[].{name:name, active:properties.active, health:properties.healthState, state:properties.runningState, replicas:properties.replicas, traffic:properties.trafficWeight, created:properties.createdTime}" -o table` |
| Replicas | `az containerapp replica list -n <ca> -g <rg> [--revision <rev>] -o table` |
| Env vars (names, plain values, secret refs) | `az containerapp show -n <ca> -g <rg> --query "properties.template.containers[].env"` |
| Secret wiring (names, Key Vault URLs, identity) | `az containerapp secret list -n <ca> -g <rg>` (no `--show-values`) |
| Registry identity | `az containerapp show -n <ca> -g <rg> --query properties.configuration.registries` |
| Jobs | `az containerapp job execution list -n <job> -g <rg> -o table` |

When `latestRevisionName` differs from `latestReadyRevisionName`, the newest deploy never became ready. Start with the failed-revision playbook.

### Logs

**Live or recent** (last 300 lines max):

```bash
az containerapp logs show -n <ca> -g <rg> --follow --tail 100 --format text           # app stdout/stderr
az containerapp logs show -n <ca> -g <rg> --type system --tail 100 --format text       # platform events: pulls, probes, scaling
az containerapp job logs show -n <job> -g <rg> --container <container> --tail 100 --format text
```

Add `--revision <rev>` to read a revision that is not the latest. Run `--follow` as a background command with a bound, since it never exits on its own.

**History and search** go to Log Analytics. Get the workspace ID from the Container Apps environment:

```bash
az containerapp env show -n <cae> -g <rg> --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId -o tsv
az monitor log-analytics query -w <workspace-id> --analytics-query "<kql>" -o table
```

| Table | Holds | Key columns |
|-------|-------|-------------|
| `ContainerAppConsoleLogs_CL` | App stdout/stderr | `ContainerAppName_s`, `RevisionName_s`, `ContainerName_s`, `Stream_s`, `Log_s` |
| `ContainerAppSystemLogs_CL` | Platform events | `ContainerAppName_s`, `RevisionName_s`, `Reason_s`, `Type_s`, `Log_s` |

Environments wired through diagnostic settings write `ContainerAppConsoleLogs` and `ContainerAppSystemLogs` (no `_CL`) instead; check which exists before querying.

```kusto
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h) and ContainerAppName_s == "<ca>"
| where Log_s has_any ("error", "exception", "fatal")
| project TimeGenerated, RevisionName_s, Log_s
| order by TimeGenerated desc
| take 100
```

**Application Insights** (`appi-<app>-<env>`), when present, holds requests, dependencies, and exceptions:

```bash
az monitor app-insights query --app <appi> -g <rg> --analytics-query "exceptions | where timestamp > ago(1h) | summarize count() by type, outerMessage | top 20 by count_"
```

**App Service** apps: `az webapp log tail -n <app> -g <rg>`.

### Images

| Need | Command |
|------|---------|
| Recent tags for a repo | `az acr repository show-tags -n forwardpathai --repository <client>/<app>-<component> --orderby time_desc --top 10 -o table` |
| Digest behind a tag | `az acr manifest list-metadata -r forwardpathai -n <client>/<app>-<component> --query "[?tags && contains(tags, '<tag>')].{digest:digest, created:createdTime}" -o table` |

Compare against the image the app runs (Container Apps `show` above) to confirm which build is live.

### Data and secrets

| Need | Command |
|------|---------|
| Postgres state and network | `az postgres flexible-server show -n <psql> -g <rg> --query "{state:state, version:version, sku:sku.name, public:network.publicNetworkAccess}"` |
| Postgres firewall | `az postgres flexible-server firewall-rule list -n <psql> -g <rg> -o table` |
| Key Vault secret names | `az keyvault secret list --vault-name <kv> --query "[].{name:name, enabled:attributes.enabled, expires:attributes.expires}" -o table` |
| An identity's roles | `az role assignment list --assignee <principal-id> --all --query "[].{role:roleDefinitionName, scope:scope}" -o table` |

Get a user-assigned identity's principal ID with `az identity show -n <id> -g <rg> --query principalId -o tsv`.

## Writes

Each write needs the confirmation in [Rules](#rules), and you re-inspect afterwards to show it took effect.

| Action | Command |
|--------|---------|
| Restart a revision | `az containerapp revision restart -n <ca> -g <rg> --revision <rev>` |
| Roll back traffic (multiple-revision mode) | `az containerapp ingress traffic set -n <ca> -g <rg> --revision-weight <good-rev>=100` |
| Reactivate an older revision | `az containerapp revision activate -n <ca> -g <rg> --revision <rev>` |
| Deploy a specific image | `az containerapp update -n <ca> -g <rg> --image forwardpathai.azurecr.io/<repo>@<digest>` |
| Rerun a job | `az containerapp job start -n <job> -g <rg>` |

These changes bypass Terraform. The next `terraform apply` reverts anything the code doesn't also hold (image, scale, traffic), so tell the user which change needs to land in the repo. Prefer the repo's deploy workflow over `az containerapp update` when the fix is a new image.

Deletion, scaling to zero in production, role assignments, firewall changes, and secret rotation are out of scope for this skill. Hand them back to the user or to an infra change under [azure-conventions](../azure-conventions/SKILL.md).

## Report

End with: what you checked (commands and the resources they hit), what you found with the quoted evidence, the likely cause, and the next action. Mark which next actions are writes awaiting approval.
