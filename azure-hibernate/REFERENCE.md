# Azure Hibernate — lever catalog

Per-resource commands for the **hibernate** and **wake** branches. For each resource: how to detect it, what to record in the snapshot, the hibernate lever, the wake (restore) lever, and the caveats that decide whether the lever is safe.

The golden rule from SKILL.md holds for every entry: **record before you change, and never delete.** If a resource's only path to cheaper is recreation, stop and flag it.

---

## App Service Plan (`Microsoft.Web/serverfarms`)

This is the real App Service bill — the compute, not the apps on it.

- **Detect:** `az appservice plan list -g <rg> -o json`
- **Snapshot:** record plan name and `sku.name` (e.g. `P1v2`). Note whether any app on the plan uses deployment slots or `always_on` — those block the free tier.
- **Hibernate:** `az appservice plan update -g <rg> -n <plan> --sku F1`. If F1 is rejected (unsupported features in use), fall back to `--sku B1`.
- **Wake:** `az appservice plan update -g <rg> -n <plan> --sku <recorded sku>`
- **Saving / caveats:** P1v2 ≈ $70/mo → F1 = $0; B1 ≈ $13/mo. F1 limits: 60 CPU-min/day quota, no `always_on`, no custom-domain SSL, no slots, 1 GB storage. If the app needs any of these, use B1. SKU change is in-place and reversible. Plans that own deployment slots cannot move to F1.

## Web App / Function App (`Microsoft.Web/sites`)

- **Detect:** `az webapp list -g <rg> -o table` and `az functionapp list -g <rg> -o table`
- **Snapshot:** record each app's `state` (Running / Stopped).
- **Hibernate:** `az webapp stop -g <rg> -n <app>` (and `az functionapp stop ...`).
- **Wake:** `az webapp start -g <rg> -n <app>`
- **Saving / caveats:** **Stopping an app does not reduce the App Service Plan bill** — the plan is the cost. Stop apps to halt activity/outbound traffic, not to save money; the plan SKU above is the real lever. Consumption-plan Function Apps already bill per-execution, so stopping just prevents triggers.

## Azure SQL Database (`Microsoft.Sql/servers/databases`)

- **Detect:** `az sql server list -g <rg> -o table`, then `az sql db list -g <rg> -s <server> -o table`.
- **Snapshot:** record `edition`, `currentServiceObjectiveName`, `maxSizeBytes`, and whether it's serverless — `az sql db show -g <rg> -s <server> -n <db> --query "{edition:edition, slo:currentServiceObjectiveName, max:maxSizeBytes}"`.
- **Hibernate:**
  - Provisioned → `az sql db update -g <rg> -s <server> -n <db> --edition Basic --service-objective Basic` (Basic ≈ $5/mo, 2 GB cap).
  - Serverless → it auto-pauses when idle; optionally lower the floor: `az sql db update ... --min-capacity 0.5 --capacity 1`.
- **Wake:** `az sql db update -g <rg> -s <server> -n <db> --edition <recorded> --service-objective <recorded>`
- **Saving / caveats:** Basic caps the DB at 2 GB — if the DB is larger, the downgrade fails; record the size and skip/flag it. A regular SQL DB **cannot be paused**, only scaled. Serverless auto-pause is the cheapest hands-off option.
- **Elastic pool:** scale the pool instead — record `--capacity`, then `az sql elastic-pool update -g <rg> -s <server> -n <pool> --capacity <n>`.
- **Synapse / SQL DW dedicated pool:** this one *can* pause — `az sql dw pause -g <rg> -s <server> -n <pool>` / `az sql dw resume`. Large saving, fully reversible.

## Azure Cache for Redis (`Microsoft.Cache/Redis`)

- **Detect:** `az redis list -g <rg> -o table`
- **Snapshot:** record `sku.name` (Basic/Standard/Premium), `sku.family` (C/P), `sku.capacity`.
- **Hibernate:** `az redis update -n <name> -g <rg> --sku Basic --vm-size c0` — only within supported transitions.
- **Wake:** `az redis update -n <name> -g <rg> --sku <recorded> --vm-size <recorded family+capacity>`
- **Saving / caveats:** **No pause, no free tier** — the smallest is Basic C0 (≈ $16/mo). Scaling down across SKU families (Premium → Basic, or to a smaller cluster) is **not supported in place** — it would require delete + recreate, which loses data and isn't reversible. If the recorded SKU can't be reached by `az redis update`, stop and flag; **do not delete**. Scaling is also slow (10–60 min) and briefly disrupts the cache.

## PostgreSQL / MySQL Flexible Server (`Microsoft.DBforPostgreSQL/flexibleServers`, `Microsoft.DBforMySQL/flexibleServers`)

The best database lever — compute billing actually stops.

- **Detect:** `az postgres flexible-server list -g <rg> -o table` (and `az mysql flexible-server list ...`)
- **Snapshot:** record `state`; if also scaling, record the `sku.name`.
- **Hibernate:** `az postgres flexible-server stop -g <rg> -n <name>` (and `az mysql flexible-server stop ...`).
- **Wake:** `az postgres flexible-server start -g <rg> -n <name>`
- **Saving / caveats:** stopping halts all compute billing and is fully reversible (storage still bills). Azure **auto-restarts a stopped flexible server after 7 days** — for long hibernation, re-stop periodically, or also scale the SKU down (`--sku-name Standard_B1ms`). Legacy single-server SKUs can't be stopped — scale tier/storage only.

## Container Apps (`Microsoft.App/containerApps`)

- **Detect:** `az containerapp list -g <rg> -o table`
- **Snapshot:** record `properties.template.scale.minReplicas`.
- **Hibernate:** `az containerapp update -n <name> -g <rg> --min-replicas 0` (scales to zero when idle).
- **Wake:** `az containerapp update -n <name> -g <rg> --min-replicas <recorded>`
- **Saving / caveats:** only saves on the Consumption workload profile; Dedicated profiles still bill for the environment. The Container Apps Environment itself may carry a base cost — note it but don't try to delete it.

## Application Gateway (`Microsoft.Network/applicationGateways`)

- **Detect:** `az network application-gateway list -g <rg> -o table`
- **Snapshot:** record name (running state is implied — it's running if billing).
- **Hibernate:** `az network application-gateway stop -g <rg> -n <name>`
- **Wake:** `az network application-gateway start -g <rg> -n <name>`
- **Saving / caveats:** App Gateway is ≈ $125+/mo — stopping is a big, fully reversible win. Routing is down while stopped (fine for hibernation).

## Virtual Machine (`Microsoft.Compute/virtualMachines`)

- **Detect:** `az vm list -g <rg> -o table`
- **Snapshot:** record `powerState`.
- **Hibernate:** `az vm deallocate -g <rg> -n <name>` — **deallocate, not stop.** Plain `az vm stop` still bills for compute; deallocate releases it.
- **Wake:** `az vm start -g <rg> -n <name>`
- **Saving / caveats:** disks still cost while deallocated.

## Cosmos DB (`Microsoft.DocumentDB/databaseAccounts`)

- **Detect:** `az cosmosdb list -g <rg> -o table`
- **Snapshot:** record provisioned throughput / autoscale max per container or database.
- **Hibernate:** lower the autoscale max — `az cosmosdb sql container throughput update ... --max-throughput 1000`.
- **Saving / caveats:** provisioned ↔ serverless cannot be switched after creation, so throughput is the only safe knob. Nuanced — confirm the per-container values with the user before changing.

## Leave alone (negligible cost)

Storage accounts, Key Vault, managed identities, DNS zones, attached public IPs (leave attached so wake is clean). For **Log Analytics** with high ingest, consider a daily cap (`az monitor log-analytics workspace update ... --daily-quota-gb <n>`) rather than touching the workspace.

## Unknown resource types

For any cost-bearing resource not in this catalog: record its full current config with `az resource show --ids <id>` before touching it, prefer a stop/scale operation, **never delete**, and if no reversible lever exists, flag it to the user rather than guessing.
