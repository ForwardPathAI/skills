---
name: engineering-projects-on-track
description: Calculates the share of ForwardPath Engineering team Linear projects (including sub-teams such as Pod 1 and Pod 2) that are on track from the latest project status update. Filters to In Progress and UAT projects only; on track means health onTrack, everything else counts off track. Use when the user asks for projects on track, engineering project health %, on-track ratio, portfolio status, or "how many projects are on track".
---

# Engineering Projects On Track

Report what percentage of active ForwardPath Engineering projects are **on track**, using each project's **latest** Linear project status update. Include the **parent team and all sub-teams** in scope.

## Scope (fixed defaults)

| Dimension | Value |
|-----------|--------|
| **Root team** | `ForwardPath Engineering` (also matches user phrases like "ForwardPath AI Engineering") |
| **Sub-teams** | All Linear sub-teams under the root (e.g. `Pod 1`, `Pod 2`) — see [Team scope](#team-scope) |
| **Project states** | `In Progress` **or** `UAT Testing` only (match `status.name` exactly; do not include Backlog, Planned, On Hold, Completed, Canceled) |
| **Health source** | Latest project status update (`get_status_updates`, `type: "project"`) |
| **On track** | `health === "onTrack"` on that update |
| **Off track** | `atRisk`, `offTrack`, or **no status update** |

`atRisk` counts as off track. Do not use project workflow state or priority as a proxy for health.

## Prerequisites

- Linear MCP (`plugin-linear-linear`) authenticated for the ForwardPath workspace.
- Stop and tell the user to connect Linear if MCP calls fail with auth errors.
- Stop if the root team lookup does not return a usable team with both `id` and `name`.
- Stop if any required MCP call fails (`list_teams`, any scoped team's `list_projects`, or `get_status_updates`) instead of reporting a partial percentage.

## Workflow

```
- [ ] Step 0: Resolve root team + sub-teams in scope (paginate `list_teams`)
- [ ] Step 1: List projects for each team in scope (paginate, dedupe)
- [ ] Step 2: Filter to In Progress + UAT Testing
- [ ] Step 3: Fetch latest status update per project
- [ ] Step 4: Classify and report
```

### Team scope

1. **Root team** — Use the user-named root team when provided; otherwise use `ForwardPath Engineering`. Call `get_team` with that query, confirm it returned a usable team with both `id` and `name`, then record both values.
2. **Sub-teams** — `list_teams` (paginate with `cursor` until `hasNextPage` is false). Include every team where `parent.id` equals the root team `id` (or `parent.name` equals the root name) when the response exposes `parent`.
3. **Fallback** — if team objects have no `parent` field, or parent matching returns no sub-teams, only infer workspace engineering pods (`Pod 1`, `Pod 2`) when the resolved root is `ForwardPath Engineering`. For any user-named root that resolves to another team, do not add inferred pods; include only the root unless sub-teams were discovered from `parent`.
4. **Teams in scope** = root + sub-teams. State the final list in the report (e.g. `ForwardPath Engineering, Pod 1, Pod 2`).

Projects may belong to multiple teams; count each project **once** (dedupe by project `id`).

### Step 1: List projects

For **each** team name in scope, call `list_projects` with `team: "<team name>"` and `limit: 50`. Paginate with `cursor` until `hasNextPage` is false.

Merge all results into one map keyed by project `id`. If the same project appears from multiple team queries, keep a single entry and record the scoped team name(s) whose queries returned it.

### Step 2: Filter projects

Keep projects where `status.name` is one of:

- `In Progress`
- `UAT Testing`

Record `name`, `url`, `status.name`, and the scoped team name(s) recorded in Step 1 for the report appendix. Do not list teams outside the final scope from raw `project.teams`.

### Step 3: Latest status update per project

For each in-scope project, call `get_status_updates`:

```json
{
  "type": "project",
  "project": "<project name>",
  "limit": 1,
  "orderBy": "createdAt"
}
```

Use the **first** returned update (newest by `createdAt`). Read `health`:

| `health` | Counts as |
|----------|-----------|
| `onTrack` | On track |
| `atRisk` | Off track |
| `offTrack` | Off track |
| (empty list) | Off track |

Display labels for humans: **On track**, **At risk**, **Off track**, **No update**.

Fetch updates in parallel when there are many projects.

### Step 4: Calculate and report

```
on_track = projects where latest health is onTrack
total    = all In Progress + UAT Testing projects in Step 2
pct      = round(on_track / total * 100)   # whole number; if total is 0, say so and skip %
```

**Primary line (required):**

```
<pct>% (<on_track>/<total>)
```

Example: `50% (10/20)`

**Supporting detail (brief):**

- Teams in scope (root + sub-teams) and state filter used
- Table of each project: name | project state | latest health | update date (`createdAt` of latest update, or "—")

Optional: link each project via its `url` from `list_projects`.

## Decision table

| Situation | Action |
|-----------|--------|
| User names a different root team | Use their team as root; still discover and include its sub-teams unless they override. |
| New sub-team added under Engineering | Pick it up via `parent` on paginated `list_teams`; use the Pod 1 / Pod 2 fallback only for the default Engineering root when `parent` is unavailable. |
| Workspace uses `In UAT` instead of `UAT Testing` | Include both names in the state filter if both exist; document which names were matched. |
| Project has updates but `health` is null | Treat as off track; note in the table. |
| `total` is 0 | Report no In Progress or UAT projects for the scoped teams — do not invent a percentage. |
| User wants only In Progress or only UAT | Narrow the state filter; recalculate. |
| Same project listed under root and a pod | Dedupe by project `id` before counting. |

## Anti-patterns

- Querying only the root team — pod-only projects (e.g. assigned only to `Pod 2`) are missed.
- Counting the same project twice because it appears on multiple team queries.
- Counting Backlog, Planned, On Hold, or Completed projects in the denominator.
- Including `ForwardPath Sales` or other non-Engineering sibling teams in scope.
- Using `list_projects` health fields — health lives on **status updates**, not the project record.
- Treating `atRisk` as on track.
- Using an older status update when a newer one exists (always `limit: 1`, `orderBy: "createdAt"`).
- Skipping pagination on `list_projects` when `hasNextPage` is true.
- Skipping pagination on `list_teams` before discovering sub-teams.

## Example output

```
Engineering projects on track (ForwardPath Engineering + Pod 1, Pod 2 · In Progress + UAT Testing):

50% (10/20)

| Project | State | Latest update |
|---------|-------|---------------|
| [ForwardPath] Portal | In Progress | On track (2026-05-26) |
| [Organigram] Auto Sale | UAT Testing | On track (2026-05-20) |
| [Kinectrics] Bid Vault / DB Migration & Tool Expansion | UAT Testing | At risk (2026-05-20) |
...
```
