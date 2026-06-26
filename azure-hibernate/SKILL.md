---
name: azure-hibernate
description: Hibernate a client project's Azure resource group to minimum cost once it's live in production, and wake it for retesting — reversible scale-down/stop of App Service Plans, web apps, SQL, Redis, and databases via the az CLI.
disable-model-invocation: true
---

# Azure Hibernate

Drive a client project's Azure costs to the floor once it's past UAT and live in production, **reversibly**, so it can be woken for retesting without re-provisioning. Every change is recorded before it's made, and undone by the **wake** branch.

Two branches, chosen from the user's intent:

- **hibernate** — scale or stop every cost-bearing resource down to its cheapest reversible state.
- **wake** — restore every resource to its recorded pre-hibernation state.

Everything runs through the **`az` CLI** against a single **resource group**.

## Rules

- **Never delete.** Scale down, stop, or pause only — deletion is not reversible. If the only way to shrink a resource is to recreate it (e.g. some Redis SKU changes), stop and flag it; do not do it.
- **Record before you change.** No resource is modified until its original state is in the snapshot file. Wake depends on it.
- **Confirm the target.** Echo the subscription and resource group and get explicit confirmation before any write. The wrong subscription is the expensive mistake.
- **Plan, then apply.** Present the full per-resource plan (lever + estimated saving + caveats) and get sign-off before the first write.

## Prerequisites

- `az` logged in — check with `az account show`. If it fails, stop and tell the user to run `az login`.
- `jq` on PATH.
- The resource group name. If the user doesn't give one, run `az group list -o table` and have them pick.

The per-resource commands (detect, snapshot, hibernate, wake, and each lever's caveats) live in **[REFERENCE.md](REFERENCE.md)**. Consult it for every resource type you find in steps below.

## Hibernate

1. **Set the target.** Confirm the subscription (`az account show`) and resource group; switch with `az account set --subscription <id>` if needed. Get the user's confirmation. _Done when:_ the user has confirmed the exact subscription + RG.
2. **Inventory.** Run `az resource list -g <rg> -o table`, then query each cost-bearing resource for its current SKU/tier/running state per [REFERENCE.md](REFERENCE.md). _Done when:_ every cost-bearing resource is listed with its current state — none left unclassified.
3. **Snapshot.** Write `azure-hibernate.<rg>.json` in the working directory recording, for every resource you intend to change, its current restorable state (SKU, tier, replica count, running state). Tag the group for portal visibility: `az group update -n <rg> --set tags.fp_hibernated=<date>` (use a real date from the user or system clock — never invent one). _Done when:_ the snapshot file holds an entry for every resource in the plan.
4. **Plan & confirm.** Present a table — resource → lever → cheapest reversible target → estimated monthly saving → caveats (Terraform drift, recreate risk, feature loss). Get sign-off. _Done when:_ the user has approved the plan.
5. **Apply.** Execute each approved lever via `az` (REFERENCE.md), then re-query each resource to verify it reached the target. _Done when:_ every approved resource reached its target state, or its failure is reported with the error.
6. **Report.** Summarize what changed, total estimated saving, the snapshot file path (tell the user to commit it), and the Terraform-drift warning below.

## Wake

1. **Set the target.** Same subscription + RG confirmation as hibernate step 1.
2. **Locate the snapshot.** Read `azure-hibernate.<rg>.json` from the working directory; if it's missing, ask the user for its path. _Done when:_ a snapshot with at least one resource entry is loaded. Without it, stop — there is no reliable restore source.
3. **Restore.** For each recorded resource, apply its wake command (REFERENCE.md) to return it to the recorded SKU/tier/running state, then re-query to verify. _Done when:_ every recorded resource matches its pre-hibernation state, or its failure is reported.
4. **Report.** Summarize what was restored, then remove the tag: `az group update -n <rg> --remove tags.fp_hibernated`.

## Terraform drift

Most of these projects are provisioned by Terraform, and these `az` changes are imperative — they bypass the IaC. So:

- A `terraform plan` will show drift and a `terraform apply` will **revert** the hibernation (or fail). Do not apply Terraform against a hibernated group unless you intend to wake it.
- If the project's Terraform already exposes hibernation-friendly variables (a SKU variable, `min_replicas`, etc.), prefer changing those and running `terraform apply` over the imperative levers — that's drift-free. The snapshot file still documents the original values.
